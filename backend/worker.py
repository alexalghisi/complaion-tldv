#!/usr/bin/env python3
"""
Celery worker script for Complaion tl;dv Integration
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Celery app
from celery_config import celery_app

def main():
    """Main worker function"""
    # Worker configuration
    worker_name = os.getenv('CELERY_WORKER_NAME', 'worker')
    concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', 4))
    loglevel = os.getenv('CELERY_WORKER_LOGLEVEL', 'INFO')
    queues = os.getenv('CELERY_WORKER_QUEUES', 'default,meetings,jobs,cleanup')

    logger.info(f"Starting Celery worker: {worker_name}")
    logger.info(f"Concurrency: {concurrency}")
    logger.info(f"Log level: {loglevel}")
    logger.info(f"Queues: {queues}")

    # Start worker
    celery_app.worker_main([
        'worker',
        f'--hostname={worker_name}@%h',
        f'--concurrency={concurrency}',
        f'--loglevel={loglevel}',
        f'--queues={queues}',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ])

if __name__ == '__main__':
    main()