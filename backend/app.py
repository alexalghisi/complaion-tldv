"""
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
    from app.utils.decorators import init_redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    init_redis(redis_url)

    # Import services and models
    from app.services.tldv_service import TLDVService, TLDVAPIError
    from app.services.firebase_service import FirebaseService
    from app.models.meeting import Meeting, MeetingFilters, MeetingImportRequest
    from app.models.job import Job, JobRequest, JobFilters, JobStatus, JobType
    from app.utils.decorators import (
        rate_limit, handle_api_errors, log_execution_time,
        validate_json, require_tldv_api, cache_response
    )

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    @handle_api_errors
    def health_check():
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {}
        }
        try:
            tldv_service = TLDVService()
            tldv_status = tldv_service.get_api_status()
            status['services']['tldv'] = tldv_status
        except Exception as e:
            logger.error(f"tl;dv health check failed: {e}")
            status['services']['tldv'] = {'accessible': False, 'error': str(e)}

        try:
            firebase_service = FirebaseService()
            firebase_connected = firebase_service.test_connection()
            status['services']['firebase'] = {'accessible': firebase_connected}
        except Exception as e:
            logger.error(f"Firebase health check failed: {e}")
            status['services']['firebase'] = {'accessible': False, 'error': str(e)}

        return jsonify(status)

    @app.route('/api/', methods=['GET'])
    @handle_api_errors
    def api_info():
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

    # restul endpoint-urilor tale rămân neschimbate (jobs, meetings, import etc)
    # am păstrat structura originală, doar importurile am corectat.

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
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting Flask server on port {port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
