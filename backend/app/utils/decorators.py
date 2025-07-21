"""
Utility decorators for the backend application
"""
import functools
import time
import logging
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, g
import redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Redis client for rate limiting (will be initialized in app)
redis_client: Optional[redis.Redis] = None

def init_redis(redis_url: str):
    """Initialize Redis client for decorators"""
    global redis_client
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()  # Test connection
        logger.info("Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis: {e}")
        redis_client = None

def rate_limit(max_requests: int = 100, per_seconds: int = 3600, key_func: Optional[Callable] = None):
    """
    Rate limiting decorator

    Args:
        max_requests: Maximum number of requests allowed
        per_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: uses IP)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client:
                # If Redis is not available, skip rate limiting
                logger.warning("Rate limiting skipped - Redis not available")
                return f(*args, **kwargs)

            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                key = f"rate_limit:{request.environ.get('REMOTE_ADDR', 'unknown')}"

            try:
                # Check current count
                current = redis_client.get(key)
                if current is None:
                    # First request in time window
                    redis_client.setex(key, per_seconds, 1)
                elif int(current) >= max_requests:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded for key: {key}")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per {per_seconds} seconds',
                        'retry_after': redis_client.ttl(key)
                    }), 429
                else:
                    # Increment counter
                    redis_client.incr(key)

            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Continue without rate limiting if Redis fails

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def require_api_key(f):
    """
    Decorator to require API key authentication
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('x-api-key')

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide an API key in the X-API-Key header'
            }), 401

        # Here you could validate the API key against a database
        # For now, we'll just check if it exists
        if len(api_key) < 10:  # Basic validation
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 401

        # Store API key in Flask's g object for use in the view
        g.api_key = api_key

        return f(*args, **kwargs)

    return decorated_function

def log_execution_time(f):
    """
    Decorator to log function execution time
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(f"{f.__name__} executed in {execution_time:.3f} seconds")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{f.__name__} failed after {execution_time:.3f} seconds: {e}")
            raise

    return decorated_function

def handle_api_errors(f):
    """
    Decorator to handle and format API errors consistently
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)

        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400

        except PermissionError as e:
            logger.warning(f"Permission error in {f.__name__}: {e}")
            return jsonify({
                'error': 'Permission denied',
                'message': str(e)
            }), 403

        except FileNotFoundError as e:
            logger.warning(f"Not found error in {f.__name__}: {e}")
            return jsonify({
                'error': 'Not found',
                'message': str(e)
            }), 404

        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500

    return decorated_function

def cache_response(expire_seconds: int = 300, key_func: Optional[Callable] = None):
    """
    Decorator to cache response data in Redis

    Args:
        expire_seconds: Cache expiration time in seconds
        key_func: Function to generate cache key (default: uses request path and args)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client:
                # If Redis is not available, skip caching
                return f(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func()
            else:
                cache_key = f"cache:{request.path}:{hash(str(request.args))}"

            try:
                # Try to get cached response
                cached_response = redis_client.get(cache_key)
                if cached_response:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    import json
                    return json.loads(cached_response)

                # No cache hit, execute function
                result = f(*args, **kwargs)

                # Cache the result
                import json
                redis_client.setex(cache_key, expire_seconds, json.dumps(result))
                logger.debug(f"Cached response for key: {cache_key}")

                return result

            except Exception as e:
                logger.error(f"Caching error: {e}")
                # Continue without caching if Redis fails
                return f(*args, **kwargs)

        return decorated_function
    return decorator

def validate_json(required_fields: Optional[list] = None):
    """
    Decorator to validate JSON request data

    Args:
        required_fields: List of required field names
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Invalid content type',
                    'message': 'Request must be JSON'
                }), 400

            data = request.get_json()
            if data is None:
                return jsonify({
                    'error': 'Invalid JSON',
                    'message': 'Request body must contain valid JSON'
                }), 400

            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'message': f'Required fields: {", ".join(missing_fields)}'
                    }), 400

            # Store validated data in Flask's g object
            g.json_data = data

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def require_tldv_api():
    """
    Decorator to ensure tl;dv API is accessible
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Import here to avoid circular imports
            from services.tldv_service import TLDVService

            try:
                tldv_service = TLDVService()
                if not tldv_service.validate_api_key():
                    return jsonify({
                        'error': 'tl;dv API unavailable',
                        'message': 'Cannot connect to tl;dv API or invalid API key'
                    }), 503

                # Store service instance in Flask's g object
                g.tldv_service = tldv_service

                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"tl;dv API check failed: {e}")
                return jsonify({
                    'error': 'tl;dv API error',
                    'message': 'Failed to connect to tl;dv API'
                }), 503

        return decorated_function
    return decorator

def async_task(f):
    """
    Decorator to mark a function as an async task (for Celery)
    This is a placeholder - actual implementation would use Celery decorators
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just execute synchronously
        # In a real implementation, this would use celery.task
        logger.info(f"Executing async task: {f.__name__}")
        return f(*args, **kwargs)

    return decorated_function

def retry_on_failure(max_retries: int = 3, delay_seconds: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to retry function execution on failure

    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            last_exception = None
            delay = delay_seconds

            for attempt in range(max_retries + 1):
                try:
                    return f(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(f"{f.__name__} failed on attempt {attempt + 1}, retrying in {delay}s: {e}")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"{f.__name__} failed after {max_retries + 1} attempts: {e}")

            # Re-raise the last exception
            raise last_exception

        return decorated_function
    return decorator

class PerformanceMonitor:
    """Context manager for monitoring performance"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time

            if exc_type:
                logger.error(f"Operation '{self.operation_name}' failed after {duration:.3f}s: {exc_val}")
            else:
                logger.info(f"Operation '{self.operation_name}' completed in {duration:.3f}s")

        return False  # Don't suppress exceptions