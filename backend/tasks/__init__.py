"""
Celery tasks for async job processing
"""

from .meeting_tasks import (
    download_meetings_job,
    download_single_meeting,
    process_meeting_transcript,
    process_meeting_highlights,
    sync_meeting_data
)

from .job_tasks import (
    update_job_status,
    update_job_progress,
    cleanup_failed_jobs,
    update_job_statistics
)

from .cleanup_tasks import (
    cleanup_expired_jobs,
    cleanup_old_logs,
    optimize_database
)

__all__ = [
    # Meeting tasks
    'download_meetings_job',
    'download_single_meeting',
    'process_meeting_transcript',
    'process_meeting_highlights',
    'sync_meeting_data',

    # Job tasks
    'update_job_status',
    'update_job_progress',
    'cleanup_failed_jobs',
    'update_job_statistics',

    # Cleanup tasks
    'cleanup_expired_jobs',
    'cleanup_old_logs',
    'optimize_database'
]