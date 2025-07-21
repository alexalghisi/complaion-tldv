"""
Celery configuration for async job processing
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

def make_celery(app_name='complaion_tldv'):
    """Create and configure Celery instance"""
    celery = Celery(
        app_name,
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
        include=['tasks.meeting_tasks', 'tasks.job_tasks']
    )

    # Celery configuration
    celery.conf.update(
        # Task settings
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,

        # Result backend settings
        result_expires=3600,  # 1 hour
        result_backend_transport_options={'master_name': 'mymaster'},

        # Task routing
        task_routes={
            'tasks.meeting_tasks.*': {'queue': 'meetings'},
            'tasks.job_tasks.*': {'queue': 'jobs'},
            'tasks.cleanup_tasks.*': {'queue': 'cleanup'}
        },

        # Worker settings
        worker_max_tasks_per_child=1000,
        worker_disable_rate_limits=False,
        worker_prefetch_multiplier=1,

        # Task execution settings
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_soft_time_limit=1800,  # 30 minutes
        task_time_limit=2100,       # 35 minutes

        # Retry settings
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,

        # Beat schedule (for periodic tasks)
        beat_schedule={
            'cleanup-expired-jobs': {
                'task': 'tasks.cleanup_tasks.cleanup_expired_jobs',
                'schedule': 3600.0,  # Every hour
            },
            'update-job-stats': {
                'task': 'tasks.job_tasks.update_job_statistics',
                'schedule': 300.0,   # Every 5 minutes
            },
        },

        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
    )

    return celery

# Create global Celery instance
celery_app = make_celery()

# Task decorator for easier imports
task = celery_app.task

if __name__ == '__main__':
    celery_app.start()