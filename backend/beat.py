#!/usr/bin/env python3
"""
Celery beat scheduler script for periodic tasks
"""
import os
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
    """Main beat function"""
    logger.info("Starting Celery beat scheduler")

    # Beat configuration
    loglevel = os.getenv('CELERY_BEAT_LOGLEVEL', 'INFO')
    schedule_file = os.getenv('CELERY_BEAT_SCHEDULE_FILE', 'celerybeat-schedule')

    logger.info(f"Log level: {loglevel}")
    logger.info(f"Schedule file: {schedule_file}")

    # Start beat
    celery_app.start([
        'celery',
        'beat',
        f'--loglevel={loglevel}',
        f'--schedule={schedule_file}',
        '--pidfile=celerybeat.pid'
    ])

if __name__ == '__main__':
    main()