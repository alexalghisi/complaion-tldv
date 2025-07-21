"""
Celery tasks for job management and monitoring
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from celery import current_task

from celery_config import celery_app
from services.firebase_service import FirebaseService
from models.job import Job, JobStatus, JobProgress

logger = logging.getLogger(__name__)

@celery_app.task
def update_job_status(job_id: str, status: str, **kwargs) -> bool:
    """
    Update job status in database

    Args:
        job_id: Job identifier
        status: New status
        **kwargs: Additional fields to update

    Returns:
        True if successful
    """
    logger.info(f"Updating job {job_id} status to: {status}")

    try:
        firebase_service = FirebaseService()

        update_data = {
            'status': status,
            'updated_at': datetime.utcnow(),
            **kwargs
        }

        firebase_service.update_job_status(job_id, status, **kwargs)

        logger.info(f"Successfully updated job {job_id} status")
        return True

    except Exception as e:
        logger.error(f"Failed to update job {job_id} status: {e}")
        return False

@celery_app.task
def update_job_progress(job_id: str, progress_data: Dict[str, Any]) -> bool:
    """
    Update job progress information

    Args:
        job_id: Job identifier
        progress_data: Progress data dictionary

    Returns:
        True if successful
    """
    logger.debug(f"Updating job {job_id} progress: {progress_data}")

    try:
        firebase_service = FirebaseService()

        firebase_service.update_job_status(
            job_id,
            JobStatus.RUNNING.value,
            progress=progress_data,
            updated_at=datetime.utcnow()
        )

        return True

    except Exception as e:
        logger.error(f"Failed to update job {job_id} progress: {e}")
        return False

@celery_app.task
def cleanup_failed_jobs(max_age_hours: int = 168) -> Dict[str, Any]:
    """
    Clean up old failed jobs (default: 1 week)

    Args:
        max_age_hours: Maximum age in hours for failed jobs

    Returns:
        Dict with cleanup results
    """
    logger.info(f"Cleaning up failed jobs older than {max_age_hours} hours")

    try:
        firebase_service = FirebaseService()

        # Get all failed jobs
        failed_jobs = firebase_service.get_jobs(status='failed', limit=1000)

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0

        for job_data in failed_jobs:
            try:
                job = Job(**job_data)

                # Check if job is old enough to clean up
                if job.created_at and job.created_at < cutoff_time:
                    # In a real implementation, you would delete the job
                    # For now, we'll just mark it as cleaned
                    firebase_service.update_job_status(
                        job.id,
                        'cleaned',
                        cleaned_at=datetime.utcnow()
                    )
                    cleaned_count += 1

            except Exception as e:
                logger.warning(f"Failed to process job for cleanup: {e}")
                continue

        result = {
            'cleaned_jobs': cleaned_count,
            'total_failed_jobs': len(failed_jobs),
            'cutoff_time': cutoff_time.isoformat()
        }

        logger.info(f"Cleanup completed: {cleaned_count} jobs cleaned")
        return result

    except Exception as e:
        logger.error(f"Failed to cleanup failed jobs: {e}")
        return {
            'error': str(e),
            'cleaned_jobs': 0
        }

@celery_app.task
def update_job_statistics() -> Dict[str, Any]:
    """
    Update job statistics and metrics

    Returns:
        Dict with statistics
    """
    logger.info("Updating job statistics")

    try:
        firebase_service = FirebaseService()

        # Get all jobs for statistics
        all_jobs = firebase_service.get_jobs(limit=10000)

        stats = {
            'total_jobs': len(all_jobs),
            'pending_jobs': 0,
            'running_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'cancelled_jobs': 0,
            'average_duration_seconds': 0,
            'success_rate': 0,
            'last_updated': datetime.utcnow().isoformat()
        }

        total_duration = 0
        completed_jobs_with_duration = 0

        for job_data in all_jobs:
            try:
                job = Job(**job_data)

                # Count by status
                if job.status == JobStatus.PENDING:
                    stats['pending_jobs'] += 1
                elif job.status == JobStatus.RUNNING:
                    stats['running_jobs'] += 1
                elif job.status == JobStatus.COMPLETED:
                    stats['completed_jobs'] += 1

                    # Calculate duration for completed jobs
                    if job.duration:
                        total_duration += job.duration
                        completed_jobs_with_duration += 1

                elif job.status == JobStatus.FAILED:
                    stats['failed_jobs'] += 1
                elif job.status == JobStatus.CANCELLED:
                    stats['cancelled_jobs'] += 1

            except Exception as e:
                logger.warning(f"Failed to process job for stats: {e}")
                continue

        # Calculate averages
        if completed_jobs_with_duration > 0:
            stats['average_duration_seconds'] = total_duration / completed_jobs_with_duration

        # Calculate success rate
        total_finished = stats['completed_jobs'] + stats['failed_jobs'] + stats['cancelled_jobs']
        if total_finished > 0:
            stats['success_rate'] = (stats['completed_jobs'] / total_finished) * 100

        # Store statistics (in a real implementation, you might store this in a separate collection)
        logger.info(f"Job statistics updated: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Failed to update job statistics: {e}")
        return {'error': str(e)}

@celery_app.task
def monitor_stuck_jobs(max_runtime_hours: int = 2) -> Dict[str, Any]:
    """
    Monitor and handle stuck jobs

    Args:
        max_runtime_hours: Maximum runtime before considering a job stuck

    Returns:
        Dict with monitoring results
    """
    logger.info(f"Monitoring stuck jobs (max runtime: {max_runtime_hours} hours)")

    try:
        firebase_service = FirebaseService()

        # Get all running jobs
        running_jobs = firebase_service.get_jobs(status='running', limit=1000)

        cutoff_time = datetime.utcnow() - timedelta(hours=max_runtime_hours)
        stuck_jobs = []
        recovered_jobs = []

        for job_data in running_jobs:
            try:
                job = Job(**job_data)

                # Check if job has been running too long
                if job.started_at and job.started_at < cutoff_time:
                    logger.warning(f"Found stuck job: {job.id} (running for {job.duration} seconds)")

                    # Mark job as failed
                    firebase_service.update_job_status(
                        job.id,
                        JobStatus.FAILED.value,
                        completed_at=datetime.utcnow(),
                        errors=[{
                            'error_code': 'JOB_TIMEOUT',
                            'message': f'Job exceeded maximum runtime of {max_runtime_hours} hours',
                            'timestamp': datetime.utcnow().isoformat()
                        }]
                    )

                    stuck_jobs.append({
                        'job_id': job.id,
                        'name': job.name,
                        'runtime_seconds': job.duration,
                        'started_at': job.started_at.isoformat() if job.started_at else None
                    })

            except Exception as e:
                logger.warning(f"