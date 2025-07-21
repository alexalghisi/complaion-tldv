except Exception as e:
logger.error(f"Error retrying job {job_id}: {e}")
raise

# =====================================
# Celery Monitoring Endpoints
# =====================================

@app.route('/api/celery/status', methods=['GET'])
@handle_api_errors
@rate_limit(max_requests=20, per_seconds=3600)
def get_celery_status():
    """Get Celery worker status"""
    try:
        inspect = celery_app.control.inspect()

        # Get worker information
        active_workers = inspect.active() or {}
        registered_tasks = inspect.registered() or {}
        worker_stats = inspect.stats() or {}

        status = {
            'workers': {
                'active_count': len(active_workers),
                'worker_names': list(active_workers.keys()),
                'active_tasks': sum(len(tasks) for tasks in active_workers.values()),
            },
            'tasks': {
                'registered_count': sum(len(tasks) for tasks in registered_tasks.values()),
                'registered_tasks': list(set().union(*registered_tasks.values())) if registered_tasks else []
            },
            'queues': {
                'default': 'available',
                'meetings': 'available',
                'jobs': 'available'
            }"""
Main Flask application for Complaion tl;dv Integration
Enhanced with complete API endpoints and error handling
"""
        from flask import Flask, request, jsonify, g
        from flask_cors import CORS
        from dotenv import load_dotenv
        import os
        import logging
        from datetime import datetime
        from typing import Dict, Any, Optional

        # Load environment variables
        load_dotenv()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['TLDV_API_KEY'] = os.getenv('TLDV_API_KEY')
    app.config['FIREBASE_PROJECT_ID'] = os.getenv('FIREBASE_PROJECT_ID')

    # Enable CORS for frontend integration
    CORS(app, origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:3001",
        os.getenv('FRONTEND_URL', '')  # Production frontend URL
    ])

    # Initialize decorators
    from utils.decorators import init_redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    init_redis(redis_url)

    # Import services and models
    from services.tldv_service import TLDVService, TLDVAPIError
    from services.firebase_service import FirebaseService
    from models.meeting import Meeting, MeetingFilters, MeetingImportRequest
    from models.job import Job, JobRequest, JobFilters, JobStatus, JobType
    from utils.decorators import (
        rate_limit, handle_api_errors, log_execution_time,
        validate_json, require_tldv_api, cache_response
    )

    # Import Celery tasks
    from tasks.meeting_tasks import download_meetings_job, download_single_meeting
    from tasks.job_tasks import retry_failed_job, generate_job_report
    from celery_config import celery_app

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    @handle_api_errors
    def health_check():
        """Health check endpoint with service status"""
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {}
        }

        # Check tl;dv API
        try:
            tldv_service = TLDVService()
            tldv_status = tldv_service.get_api_status()
            status['services']['tldv'] = tldv_status
        except Exception as e:
            logger.error(f"tl;dv health check failed: {e}")
            status['services']['tldv'] = {'accessible': False, 'error': str(e)}

        # Check Firebase
        try:
            firebase_service = FirebaseService()
            firebase_connected = firebase_service.test_connection()
            status['services']['firebase'] = {'accessible': firebase_connected}
        except Exception as e:
            logger.error(f"Firebase health check failed: {e}")
            status['services']['firebase'] = {'accessible': False, 'error': str(e)}

        return jsonify(status)

    # API routes prefix
    @app.route('/api/', methods=['GET'])
    @handle_api_errors
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': 'Complaion tl;dv Integration API',
            'version': '1.0.0',
            'description': 'Backend API for tl;dv meeting data integration',
            'endpoints': {
                'health': '/health',
                'jobs': '/api/jobs',
                'meetings': '/api/meetings',
                'import': '/api/import'
            },
            'documentation': 'https://github.com/alexalghisi/complaion-tldv'
        })

    # =====================================
    # Jobs Endpoints
    # =====================================

    @app.route('/api/jobs', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=100, per_seconds=3600)
    @cache_response(expire_seconds=60)
    def get_jobs():
        """Get jobs with filtering and pagination"""
        try:
            # Parse query parameters
            filters = JobFilters(
                status=request.args.get('status'),
                type=request.args.get('type'),
                user_id=request.args.get('user_id'),
                priority=int(request.args.get('priority')) if request.args.get('priority') else None,
                date_from=request.args.get('date_from'),
                date_to=request.args.get('date_to'),
                page=int(request.args.get('page', 1)),
                limit=int(request.args.get('limit', 50))
            )

            firebase_service = FirebaseService()
            jobs_data = firebase_service.get_jobs(
                limit=filters.limit,
                status=filters.status.value if filters.status else None
            )

            # Convert to Job objects
            jobs = []
            for job_data in jobs_data:
                try:
                    job = Job(**job_data)
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse job {job_data.get('id', 'unknown')}: {e}")
                    continue

            return jsonify({
                'jobs': [job.dict() for job in jobs],
                'total': len(jobs),
                'page': filters.page,
                'pageSize': filters.limit
            })

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            raise

    @app.route('/api/jobs', methods=['POST'])
    @handle_api_errors
    @validate_json(['type', 'name'])
    @rate_limit(max_requests=10, per_seconds=3600)
    @require_tldv_api()
    def create_job():
        """Create a new job"""
        try:
            data = g.json_data

            # Validate job request
            job_request = JobRequest(**data)

            # Create job object
            job = Job(
                type=job_request.type,
                name=job_request.name,
                description=job_request.description,
                config=job_request.config,
                priority=job_request.priority
            )

            # Save to Firebase
            firebase_service = FirebaseService()
            job_id = firebase_service.create_job(job.dict())
            job.id = job_id

            logger.info(f"Created job {job_id}: {job.name}")

            # Queue job for background processing based on type
            if job_request.type == JobType.DOWNLOAD_MEETINGS:
                # Extract filters from config
                config = job_request.config or {}
                filters_dict = config.get('filters', {})

                # Queue the download job
                task_result = download_meetings_job.apply_async(
                    args=[job_id, filters_dict],
                    countdown=5  # Start after 5 seconds
                )

                logger.info(f"Queued download job {job_id} with task ID: {task_result.id}")

            elif job_request.type == JobType.IMPORT_MEETING:
                # Handle import meeting job
                config = job_request.config or {}
                meeting_data = config.get('meeting_data', {})

                task_result = download_single_meeting.apply_async(
                    args=[job_id, meeting_data],
                    countdown=2
                )

                logger.info(f"Queued import job {job_id} with task ID: {task_result.id}")

            else:
                logger.warning(f"Unknown job type: {job_request.type}")

            return jsonify({
                'success': True,
                'job_id': job_id,
                'job': job.dict(),
                'message': 'Job created and queued successfully'
            }), 201

        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise

    @app.route('/api/jobs/<job_id>', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=200, per_seconds=3600)
    def get_job(job_id: str):
        """Get specific job details"""
        try:
            firebase_service = FirebaseService()
            job_data = firebase_service.get_job(job_id)

            if not job_data:
                return jsonify({
                    'error': 'Job not found',
                    'message': f'Job {job_id} does not exist'
                }), 404

            job = Job(**job_data)

            return jsonify({
                'job': job.dict(),
                'success': True
            })

        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            raise

    @app.route('/api/jobs/<job_id>/retry', methods=['POST'])
    @handle_api_errors
    @rate_limit(max_requests=5, per_seconds=3600)
    def retry_job(job_id: str):
        """Retry a failed job"""
        try:
            firebase_service = FirebaseService()
            job_data = firebase_service.get_job(job_id)

            if not job_data:
                return jsonify({
                    'error': 'Job not found',
                    'message': f'Job {job_id} does not exist'
                }), 404

            job = Job(**job_data)

            if not job.can_retry():
                return jsonify({
                    'error': 'Cannot retry job',
                    'message': f'Job is in {job.status} status or max retries exceeded'
                }), 400

            # Retry the job using Celery task
            retry_result = retry_failed_job.apply_async(args=[job_id])

            logger.info(f"Initiated retry for job {job_id}")

            return jsonify({
                'success': True,
                'job': job.dict(),
                'message': 'Job retry initiated',
                'retry_task_id': retry_result.id
            })

        except Exception as e:
            logger.error(f"Error retrying job {job_id}: {e}")
            raise

    # =====================================
    # Meetings Endpoints
    # =====================================

    @app.route('/api/meetings', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=100, per_seconds=3600)
    @cache_response(expire_seconds=300)
    def get_meetings():
        """Get meetings with filtering and pagination"""
        try:
            # Parse query parameters
            filters = MeetingFilters(
                query=request.args.get('query'),
                page=int(request.args.get('page', 1)),
                limit=int(request.args.get('limit', 50)),
                date_from=request.args.get('date_from'),
                date_to=request.args.get('date_to'),
                only_participated=request.args.get('only_participated', '').lower() == 'true',
                meeting_type=request.args.get('meeting_type'),
                job_id=request.args.get('job_id')
            )

            # Get from Firebase first
            firebase_service = FirebaseService()
            local_meetings = firebase_service.get_meetings(
                limit=filters.limit,
                job_id=filters.job_id
            )

            # If we have local data, return it
            if local_meetings:
                meetings = []
                for meeting_data in local_meetings:
                    try:
                        meeting = Meeting(**meeting_data)
                        meetings.append(meeting)
                    except Exception as e:
                        logger.warning(f"Failed to parse meeting {meeting_data.get('id', 'unknown')}: {e}")
                        continue

                return jsonify({
                    'meetings': [meeting.dict() for meeting in meetings],
                    'total': len(meetings),
                    'page': filters.page,
                    'pageSize': filters.limit,
                    'source': 'local'
                })

            # Otherwise, get from tl;dv API
            tldv_service = TLDVService()
            response = tldv_service.get_meetings(filters)

            return jsonify({
                'meetings': [meeting.dict() for meeting in response.results],
                'total': response.total,
                'page': response.page,
                'pages': response.pages,
                'pageSize': response.page_size,
                'source': 'tldv_api'
            })

        except TLDVAPIError as e:
            logger.error(f"tl;dv API error getting meetings: {e}")
            return jsonify({
                'error': 'tl;dv API error',
                'message': str(e),
                'status_code': e.status_code
            }), 503
        except Exception as e:
            logger.error(f"Error getting meetings: {e}")
            raise

    @app.route('/api/meetings/<meeting_id>', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=200, per_seconds=3600)
    @cache_response(expire_seconds=600)
    def get_meeting(meeting_id: str):
        """Get specific meeting details"""
        try:
            include_transcript = request.args.get('include_transcript', 'true').lower() == 'true'
            include_highlights = request.args.get('include_highlights', 'true').lower() == 'true'

            # Try Firebase first
            firebase_service = FirebaseService()
            meeting_data = firebase_service.get_meeting(meeting_id)

            if meeting_data:
                meeting = Meeting(**meeting_data)
                result = {'meeting': meeting.dict(), 'source': 'local'}
            else:
                # Get from tl;dv API
                tldv_service = TLDVService()
                meeting_details = tldv_service.get_meeting_with_details(
                    meeting_id,
                    include_transcript=include_transcript,
                    include_highlights=include_highlights
                )

                result = {
                    'meeting': meeting_details['meeting'].dict(),
                    'source': 'tldv_api'
                }

                if include_transcript and meeting_details.get('transcript'):
                    result['transcript'] = meeting_details['transcript'].dict()

                if include_highlights and meeting_details.get('highlights'):
                    result['highlights'] = meeting_details['highlights'].dict()

            return jsonify(result)

        except TLDVAPIError as e:
            if e.status_code == 404:
                return jsonify({
                    'error': 'Meeting not found',
                    'message': f'Meeting {meeting_id} does not exist'
                }), 404
            logger.error(f"tl;dv API error getting meeting {meeting_id}: {e}")
            return jsonify({
                'error': 'tl;dv API error',
                'message': str(e)
            }), 503
        except Exception as e:
            logger.error(f"Error getting meeting {meeting_id}: {e}")
            raise

    @app.route('/api/meetings/<meeting_id>/transcript', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=100, per_seconds=3600)
    @cache_response(expire_seconds=3600)
    def get_meeting_transcript(meeting_id: str):
        """Get meeting transcript"""
        try:
            tldv_service = TLDVService()
            transcript = tldv_service.get_transcript(meeting_id)

            if not transcript:
                return jsonify({
                    'error': 'Transcript not found',
                    'message': f'Transcript for meeting {meeting_id} is not available'
                }), 404

            return jsonify({
                'transcript': transcript.dict(),
                'success': True
            })

        except TLDVAPIError as e:
            if e.status_code == 404:
                return jsonify({
                    'error': 'Transcript not found',
                    'message': f'Transcript for meeting {meeting_id} is not available'
                }), 404
            raise
        except Exception as e:
            logger.error(f"Error getting transcript for {meeting_id}: {e}")
            raise

    @app.route('/api/meetings/<meeting_id>/highlights', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=100, per_seconds=3600)
    @cache_response(expire_seconds=3600)
    def get_meeting_highlights(meeting_id: str):
        """Get meeting highlights"""
        try:
            tldv_service = TLDVService()
            highlights = tldv_service.get_highlights(meeting_id)

            if not highlights:
                return jsonify({
                    'error': 'Highlights not found',
                    'message': f'Highlights for meeting {meeting_id} are not available'
                }), 404

            return jsonify({
                'highlights': highlights.dict(),
                'success': True
            })

        except TLDVAPIError as e:
            if e.status_code == 404:
                return jsonify({
                    'error': 'Highlights not found',
                    'message': f'Highlights for meeting {meeting_id} are not available'
                }), 404
            raise
        except Exception as e:
            logger.error(f"Error getting highlights for {meeting_id}: {e}")
            raise

    # =====================================
    # Import Endpoints
    # =====================================

    @app.route('/api/import', methods=['POST'])
    @handle_api_errors
    @validate_json(['name', 'url'])
    @rate_limit(max_requests=5, per_seconds=3600)
    @require_tldv_api()
    def import_meeting():
        """Import a meeting from URL"""
        try:
            data = g.json_data

            # Validate import request
            import_request = MeetingImportRequest(**data)

            # Import via tl;dv API
            tldv_service = g.tldv_service
            result = tldv_service.import_meeting(import_request)

            logger.info(f"Meeting import initiated: {import_request.name}")

            return jsonify({
                'success': result.get('success', True),
                'job_id': result.get('jobId'),
                'message': result.get('message', 'Import started successfully')
            })

        except Exception as e:
            logger.error(f"Error importing meeting: {e}")
            raise

    # =====================================
    # Statistics Endpoints
    # =====================================

    @app.route('/api/stats', methods=['GET'])
    @handle_api_errors
    @rate_limit(max_requests=50, per_seconds=3600)
    @cache_response(expire_seconds=300)
    def get_stats():
        """Get system statistics"""
        try:
            firebase_service = FirebaseService()

            # Get job stats
            jobs_data = firebase_service.get_jobs(limit=1000)  # Get all jobs for stats
            job_stats = {
                'total_jobs': len(jobs_data),
                'pending_jobs': len([j for j in jobs_data if j.get('status') == 'pending']),
                'running_jobs': len([j for j in jobs_data if j.get('status') == 'running']),
                'completed_jobs': len([j for j in jobs_data if j.get('status') == 'completed']),
                'failed_jobs': len([j for j in jobs_data if j.get('status') == 'failed'])
            }

            # Get meeting stats
            meetings_data = firebase_service.get_meetings(limit=1000)  # Get all meetings for stats
            meeting_stats = {
                'total_meetings': len(meetings_data),
                'meetings_with_transcript': len([m for m in meetings_data if m.get('transcript_available')]),
                'meetings_with_highlights': len([m for m in meetings_data if m.get('highlights_available')])
            }

            return jsonify({
                'jobs': job_stats,
                'meetings': meeting_stats,
                'last_updated': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Internal server error: {error}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    return app

if __name__ == '__main__':
    app = create_app()

    # Development server configuration
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))

    logger.info(f"Starting Flask server on port {port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)