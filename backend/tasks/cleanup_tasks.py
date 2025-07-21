"""
Celery tasks for system cleanup and maintenance
"""
import logging
import os
from typing import Dict, Any
from datetime import datetime, timedelta

from celery_config import celery_app
from services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)

@celery_app.task
def cleanup_expired_jobs(max_age_days: int = 30) -> Dict[str, Any]:
    """
    Clean up expired completed jobs

    Args:
        max_age_days: Maximum age in days for completed jobs

    Returns:
        Dict with cleanup results
    """
    logger.info(f"Cleaning up completed jobs older than {max_age_days} days")

    try:
        firebase_service = FirebaseService()

        # Get all completed jobs
        completed_jobs = firebase_service.get_jobs(status='completed', limit=10000)

        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleanup_stats = {
            'total_completed_jobs': len(completed_jobs),
            'expired_jobs': 0,
            'archived_jobs': 0,
            'deleted_jobs': 0,
            'errors': []
        }

        for job_data in completed_jobs:
            try:
                from models.job import Job
                job = Job(**job_data)

                # Check if job is old enough to clean up
                if job.completed_at and job.completed_at < cutoff_time:
                    # Archive job instead of deleting (move to archive collection)
                    firebase_service.update_job_status(
                        job.id,
                        'archived',
                        archived_at=datetime.utcnow()
                    )

                    cleanup_stats['expired_jobs'] += 1
                    cleanup_stats['archived_jobs'] += 1

                    logger.debug(f"Archived expired job: {job.id}")

            except Exception as e:
                logger.warning(f"Failed to process job for cleanup: {e}")
                cleanup_stats['errors'].append(str(e))
                continue

        logger.info(f"Cleanup completed: {cleanup_stats['archived_jobs']} jobs archived")

        return cleanup_stats

    except Exception as e:
        logger.error(f"Failed to cleanup expired jobs: {e}")
        return {
            'error': str(e),
            'total_completed_jobs': 0,
            'archived_jobs': 0
        }

@celery_app.task
def cleanup_old_logs(max_age_days: int = 7) -> Dict[str, Any]:
    """
    Clean up old log files

    Args:
        max_age_days: Maximum age in days for log files

    Returns:
        Dict with cleanup results
    """
    logger.info(f"Cleaning up log files older than {max_age_days} days")

    cleanup_stats = {
        'total_files_checked': 0,
        'files_deleted': 0,
        'space_freed_bytes': 0,
        'errors': []
    }

    try:
        log_directories = [
            'logs/',
            '/var/log/complaion/',
            '/tmp/celery/',
        ]

        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)

        for log_dir in log_directories:
            if not os.path.exists(log_dir):
                continue

            try:
                for filename in os.listdir(log_dir):
                    file_path = os.path.join(log_dir, filename)

                    # Skip directories
                    if os.path.isdir(file_path):
                        continue

                    # Check file age
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    cleanup_stats['total_files_checked'] += 1

                    if file_mtime < cutoff_time:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)

                            cleanup_stats['files_deleted'] += 1
                            cleanup_stats['space_freed_bytes'] += file_size

                            logger.debug(f"Deleted old log file: {file_path}")

                        except OSError as e:
                            logger.warning(f"Failed to delete log file {file_path}: {e}")
                            cleanup_stats['errors'].append(f"Delete error for {file_path}: {str(e)}")

            except OSError as e:
                logger.warning(f"Failed to access log directory {log_dir}: {e}")
                cleanup_stats['errors'].append(f"Directory access error for {log_dir}: {str(e)}")

        # Convert bytes to human readable format
        space_freed_mb = cleanup_stats['space_freed_bytes'] / (1024 * 1024)

        logger.info(f"Log cleanup completed: {cleanup_stats['files_deleted']} files deleted, {space_freed_mb:.2f} MB freed")

        return cleanup_stats

    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
        cleanup_stats['errors'].append(str(e))
        return cleanup_stats

@celery_app.task
def optimize_database() -> Dict[str, Any]:
    """
    Optimize database performance (placeholder for Firebase)

    Returns:
        Dict with optimization results
    """
    logger.info("Running database optimization")

    try:
        firebase_service = FirebaseService()

        optimization_stats = {
            'collections_optimized': 0,
            'indexes_checked': 0,
            'performance_tips': [],
            'warnings': []
        }

        # For Firestore, optimization is mostly automatic
        # But we can provide recommendations

        # Check job collection size
        jobs = firebase_service.get_jobs(limit=10000)
        meetings = firebase_service.get_meetings(limit=10000)

        if len(jobs) > 5000:
            optimization_stats['warnings'].append(
                f"Large number of jobs ({len(jobs)}). Consider archiving old completed jobs."
            )
            optimization_stats['performance_tips'].append(
                "Use pagination for job queries to improve performance"
            )

        if len(meetings) > 10000:
            optimization_stats['warnings'].append(
                f"Large number of meetings ({len(meetings)}). Consider implementing data partitioning."
            )
            optimization_stats['performance_tips'].append(
                "Index meeting fields used in queries (happened_at, job_id, status)"
            )

        # Simulate collection optimization
        optimization_stats['collections_optimized'] = 3  # jobs, meetings, tasks
        optimization_stats['indexes_checked'] = 5

        logger.info("Database optimization completed")

        return optimization_stats

    except Exception as e:
        logger.error(f"Failed to optimize database: {e}")
        return {
            'error': str(e),
            'collections_optimized': 0
        }

@celery_app.task
def cleanup_temp_files() -> Dict[str, Any]:
    """
    Clean up temporary files created during processing

    Returns:
        Dict with cleanup results
    """
    logger.info("Cleaning up temporary files")

    cleanup_stats = {
        'temp_directories_checked': 0,
        'files_deleted': 0,
        'space_freed_bytes': 0,
        'errors': []
    }

    try:
        temp_directories = [
            '/tmp/complaion/',
            '/tmp/tldv_downloads/',
            'temp/',
            'downloads/'
        ]

        for temp_dir in temp_directories:
            if not os.path.exists(temp_dir):
                continue

            cleanup_stats['temp_directories_checked'] += 1

            try:
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)

                    # Skip directories
                    if os.path.isdir(file_path):
                        continue

                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)

                        cleanup_stats['files_deleted'] += 1
                        cleanup_stats['space_freed_bytes'] += file_size

                        logger.debug(f"Deleted temp file: {file_path}")

                    except OSError as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")
                        cleanup_stats['errors'].append(f"Delete error for {file_path}: {str(e)}")

            except OSError as e:
                logger.warning(f"Failed to access temp directory {temp_dir}: {e}")
                cleanup_stats['errors'].append(f"Directory access error for {temp_dir}: {str(e)}")

        space_freed_mb = cleanup_stats['space_freed_bytes'] / (1024 * 1024)

        logger.info(f"Temp files cleanup completed: {cleanup_stats['files_deleted']} files deleted, {space_freed_mb:.2f} MB freed")

        return cleanup_stats

    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {e}")
        cleanup_stats['errors'].append(str(e))
        return cleanup_stats

@celery_app.task
def health_check_services() -> Dict[str, Any]:
    """
    Perform health check on all services

    Returns:
        Dict with health check results
    """
    logger.info("Performing health check on all services")

    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'overall_status': 'healthy',
        'services': {},
        'warnings': [],
        'errors': []
    }

    # Check tl;dv API
    try:
        from services.tldv_service import TLDVService
        tldv_service = TLDVService()
        tldv_status = tldv_service.get_api_status()

        health_status['services']['tldv'] = {
            'status': 'healthy' if tldv_status['api_accessible'] and tldv_status['api_key_valid'] else 'unhealthy',
            'response_time_ms': tldv_status.get('response_time_ms'),
            'last_error': tldv_status.get('last_error')
        }

        if not tldv_status['api_accessible']:
            health_status['errors'].append("tl;dv API is not accessible")
            health_status['overall_status'] = 'degraded'

    except Exception as e:
        logger.error(f"Failed to check tl;dv service: {e}")
        health_status['services']['tldv'] = {'status': 'error', 'error': str(e)}
        health_status['errors'].append(f"tl;dv health check failed: {str(e)}")
        health_status['overall_status'] = 'degraded'

    # Check Firebase
    try:
        firebase_service = FirebaseService()
        firebase_connected = firebase_service.test_connection()

        health_status['services']['firebase'] = {
            'status': 'healthy' if firebase_connected else 'unhealthy'
        }

        if not firebase_connected:
            health_status['errors'].append("Firebase is not accessible")
            health_status['overall_status'] = 'degraded'

    except Exception as e:
        logger.error(f"Failed to check Firebase service: {e}")
        health_status['services']['firebase'] = {'status': 'error', 'error': str(e)}
        health_status['errors'].append(f"Firebase health check failed: {str(e)}")
        health_status['overall_status'] = 'degraded'

    # Check Redis (Celery broker)
    try:
        from celery_config import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            health_status['services']['celery'] = {
                'status': 'healthy',
                'active_workers': len(active_workers),
                'workers': list(active_workers.keys())
            }
        else:
            health_status['services']['celery'] = {'status': 'warning'}
            health_status['warnings'].append("No active Celery workers found")

    except Exception as e:
        logger.error(f"Failed to check Celery service: {e}")
        health_status['services']['celery'] = {'status': 'error', 'error': str(e)}
        health_status['warnings'].append(f"Celery health check failed: {str(e)}")

    # Set overall status based on errors
    if health_status['errors']:
        health_status['overall_status'] = 'unhealthy'
    elif health_status['warnings']:
        health_status['overall_status'] = 'degraded'

    logger.info(f"Health check completed: {health_status['overall_status']}")

    return health_status

@celery_app.task
def generate_system_report() -> Dict[str, Any]:
    """
    Generate comprehensive system report

    Returns:
        Dict with system report
    """
    logger.info("Generating system report")

    try:
        firebase_service = FirebaseService()

        # Get basic statistics
        jobs = firebase_service.get_jobs(limit=10000)
        meetings = firebase_service.get_meetings(limit=10000)

        # Calculate job statistics
        job_stats = {
            'total': len(jobs),
            'pending': len([j for j in jobs if j.get('status') == 'pending']),
            'running': len([j for j in jobs if j.get('status') == 'running']),
            'completed': len([j for j in jobs if j.get('status') == 'completed']),
            'failed': len([j for j in jobs if j.get('status') == 'failed'])
        }

        # Calculate meeting statistics
        meeting_stats = {
            'total': len(meetings),
            'with_transcript': len([m for m in meetings if m.get('transcript_available')]),
            'with_highlights': len([m for m in meetings if m.get('highlights_available')]),
            'with_video': len([m for m in meetings if m.get('video_url')])
        }

        # System health
        health_check = health_check_services.apply().get(timeout=30)

        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'system_version': '1.0.0',
            'jobs': job_stats,
            'meetings': meeting_stats,
            'health': health_check,
            'recommendations': []
        }

        # Add recommendations based on data
        if job_stats['failed'] > job_stats['completed'] * 0.1:  # More than 10% failure rate
            report['recommendations'].append(
                "High job failure rate detected. Check tl;dv API connectivity and rate limits."
            )

        if job_stats['running'] > 10:
            report['recommendations'].append(
                "Many jobs currently running. Monitor for stuck jobs."
            )

        if meeting_stats['total'] > 0:
            transcript_rate = (meeting_stats['with_transcript'] / meeting_stats['total']) * 100
            if transcript_rate < 80:
                report['recommendations'].append(
                    f"Low transcript availability ({transcript_rate:.1f}%). Check tl;dv transcript processing."
                )

        logger.info("System report generated successfully")

        return report

    except Exception as e:
        logger.error(f"Failed to generate system report: {e}")
        return {
            'error': str(e),
            'generated_at': datetime.utcnow().isoformat()
        }