#!/usr/bin/env python3
"""
Management script for Complaion tl;dv Integration
"""
import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Complaion tl;dv Integration Management CLI"""
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def runserver(host, port, debug):
    """Run the Flask development server"""
    os.environ['FLASK_ENV'] = 'development' if debug else 'production'
    os.environ['FLASK_DEBUG'] = '1' if debug else '0'

    click.echo(f"Starting Flask server on {host}:{port} (debug={debug})")

    from app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=debug)

@cli.command()
@click.option('--concurrency', default=4, help='Number of worker processes')
@click.option('--loglevel', default='INFO', help='Logging level')
@click.option('--queues', default='default,meetings,jobs,cleanup', help='Queues to process')
@click.option('--name', default='worker', help='Worker name')
def worker(concurrency, loglevel, queues, name):
    """Run Celery worker"""
    os.environ['CELERY_WORKER_CONCURRENCY'] = str(concurrency)
    os.environ['CELERY_WORKER_LOGLEVEL'] = loglevel
    os.environ['CELERY_WORKER_QUEUES'] = queues
    os.environ['CELERY_WORKER_NAME'] = name

    click.echo(f"Starting Celery worker: {name}")
    click.echo(f"Concurrency: {concurrency}, Queues: {queues}")

    from worker import main
    main()

@cli.command()
@click.option('--loglevel', default='INFO', help='Logging level')
def beat(loglevel):
    """Run Celery beat scheduler"""
    os.environ['CELERY_BEAT_LOGLEVEL'] = loglevel

    click.echo("Starting Celery beat scheduler")

    from beat import main
    main()

@cli.command()
@click.option('--port', default=5555, help='Flower port')
def flower(port):
    """Run Celery Flower monitoring"""
    click.echo(f"Starting Flower on port {port}")

    from celery_config import celery_app
    celery_app.start([
        'celery',
        'flower',
        f'--port={port}',
        f'--broker={os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")}'
    ])

@cli.command()
def test():
    """Run tests"""
    click.echo("Running tests...")

    # Run test script
    result = subprocess.run([sys.executable, 'test_api.py'], capture_output=True, text=True)

    click.echo(result.stdout)
    if result.stderr:
        click.echo("Errors:", err=True)
        click.echo(result.stderr, err=True)

    sys.exit(result.returncode)

@cli.command()
def setup():
    """Run setup script"""
    click.echo("Running setup...")

    result = subprocess.run([sys.executable, 'setup.py'], capture_output=True, text=True)

    click.echo(result.stdout)
    if result.stderr:
        click.echo("Errors:", err=True)
        click.echo(result.stderr, err=True)

    sys.exit(result.returncode)

@cli.command()
def shell():
    """Start interactive Python shell with app context"""
    click.echo("Starting interactive shell...")

    from app import create_app
    from services.tldv_service import TLDVService
    from services.firebase_service import FirebaseService
    from models import *

    app = create_app()

    with app.app_context():
        # Make services available in shell
        tldv = TLDVService()
        firebase = FirebaseService()

        click.echo("Available objects:")
        click.echo("  app - Flask application")
        click.echo("  tldv - TLDVService instance")
        click.echo("  firebase - FirebaseService instance")
        click.echo("  models.* - All data models")

        # Start IPython shell if available, otherwise regular Python
        try:
            import IPython
            IPython.embed(colors='neutral')
        except ImportError:
            import code
            code.interact(local=locals())

@cli.command()
@click.option('--processes', default=1, help='Number of processes to start')
def dev(processes):
    """Start development environment with all services"""
    click.echo("Starting development environment...")

    processes_list = []

    try:
        # Start Redis if not running
        click.echo("Starting Redis...")
        redis_proc = subprocess.Popen([
            'redis-server', '--port', '6379', '--daemonize', 'yes'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)  # Give Redis time to start

        # Start Celery worker
        click.echo("Starting Celery worker...")
        worker_proc = subprocess.Popen([
            sys.executable, 'manage.py', 'worker',
            '--concurrency', str(processes),
            '--name', 'dev-worker'
        ])
        processes_list.append(worker_proc)

        # Start Celery beat
        click.echo("Starting Celery beat...")
        beat_proc = subprocess.Popen([
            sys.executable, 'manage.py', 'beat'
        ])
        processes_list.append(beat_proc)

        # Start Flask app
        click.echo("Starting Flask app...")
        flask_proc = subprocess.Popen([
            sys.executable, 'manage.py', 'runserver',
            '--debug'
        ])
        processes_list.append(flask_proc)

        click.echo("Development environment started!")
        click.echo("Services:")
        click.echo("  Flask API: http://localhost:5000")
        click.echo("  Redis: localhost:6379")
        click.echo(f"  Celery Worker: {processes} processes")
        click.echo("  Celery Beat: Periodic tasks")
        click.echo("")
        click.echo("Press Ctrl+C to stop all services")

        # Wait for interrupt
        try:
            while True:
                time.sleep(1)

                # Check if any process died
                for proc in processes_list:
                    if proc.poll() is not None:
                        click.echo(f"Process {proc.pid} died unexpectedly")
                        raise KeyboardInterrupt

        except KeyboardInterrupt:
            click.echo("\nShutting down services...")

    except Exception as e:
        click.echo(f"Error starting development environment: {e}", err=True)

    finally:
        # Cleanup processes
        for proc in processes_list:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as e:
                click.echo(f"Error stopping process {proc.pid}: {e}", err=True)

@cli.command()
def status():
    """Check status of all services"""
    click.echo("Checking service status...")

    # Check Flask API
    try:
        import requests
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            click.echo("✅ Flask API: Running")
        else:
            click.echo(f"⚠️ Flask API: Responded with {response.status_code}")
    except Exception:
        click.echo("❌ Flask API: Not running")

    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        click.echo("✅ Redis: Running")
    except Exception:
        click.echo("❌ Redis: Not running")

    # Check Celery workers
    try:
        from celery_config import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            click.echo(f"✅ Celery Workers: {len(active_workers)} active")
            for worker in active_workers.keys():
                click.echo(f"   - {worker}")
        else:
            click.echo("❌ Celery Workers: No active workers")
    except Exception as e:
        click.echo(f"❌ Celery Workers: Error checking ({e})")

    # Check services connectivity
    try:
        from services.tldv_service import TLDVService
        tldv = TLDVService()
        status = tldv.get_api_status()

        if status['api_accessible'] and status['api_key_valid']:
            click.echo("✅ tl;dv API: Connected")
        else:
            click.echo("⚠️ tl;dv API: Connection issues")
    except Exception:
        click.echo("❌ tl;dv API: Cannot connect")

    try:
        from services.firebase_service import FirebaseService
        firebase = FirebaseService()
        connected = firebase.test_connection()

        if connected:
            click.echo("✅ Firebase: Connected")
        else:
            click.echo("❌ Firebase: Cannot connect")
    except Exception:
        click.echo("❌ Firebase: Error connecting")

@cli.command()
@click.argument('job_id')
def job_status(job_id):
    """Get status of a specific job"""
    try:
        from services.firebase_service import FirebaseService
        firebase = FirebaseService()

        job_data = firebase.get_job(job_id)
        if not job_data:
            click.echo(f"Job {job_id} not found", err=True)
            return

        from models.job import Job
        job = Job(**job_data)

        click.echo(f"Job: {job.name}")
        click.echo(f"Status: {job.status.value}")
        click.echo(f"Type: {job.type.value}")
        click.echo(f"Created: {job.created_at}")
        click.echo(f"Started: {job.started_at}")
        click.echo(f"Completed: {job.completed_at}")
        click.echo(f"Duration: {job.duration_formatted}")
        click.echo(f"Retry count: {job.retry_count}/{job.max_retries}")

        if job.progress:
            click.echo(f"Progress: {job.progress.overall_percentage:.1f}%")
            click.echo(f"Current step: {job.progress.current_step}")

        if job.errors:
            click.echo(f"Errors: {len(job.errors)}")
            for error in job.errors[-3:]:  # Show last 3 errors
                click.echo(f"  - {error.message}")

    except Exception as e:
        click.echo(f"Error getting job status: {e}", err=True)

@cli.command()
@click.argument('meeting_id')
def meeting_info(meeting_id):
    """Get information about a specific meeting"""
    try:
        from services.firebase_service import FirebaseService
        firebase = FirebaseService()

        meeting_data = firebase.get_meeting(meeting_id)
        if not meeting_data:
            # Try tl;dv API
            from services.tldv_service import TLDVService
            tldv = TLDVService()

            try:
                meeting = tldv.get_meeting(meeting_id)
                meeting_data = meeting.dict()
                click.echo("(Data from tl;dv API)")
            except Exception:
                click.echo(f"Meeting {meeting_id} not found", err=True)
                return

        from models.meeting import Meeting
        meeting = Meeting(**meeting_data)

        click.echo(f"Meeting: {meeting.name}")
        click.echo(f"Date: {meeting.happened_at}")
        click.echo(f"Participants: {meeting.participant_count}")
        click.echo(f"Transcript available: {meeting.transcript_available}")
        click.echo(f"Highlights available: {meeting.highlights_available}")
        click.echo(f"Video URL: {meeting.video_url or 'Not available'}")

        if meeting.organizer:
            click.echo(f"Organizer: {meeting.organizer.name} ({meeting.organizer.email})")

    except Exception as e:
        click.echo(f"Error getting meeting info: {e}", err=True)

@cli.command()
@click.option('--clean-jobs', is_flag=True, help='Clean up old jobs')
@click.option('--clean-logs', is_flag=True, help='Clean up old logs')
@click.option('--optimize-db', is_flag=True, help='Optimize database')
def cleanup(clean_jobs, clean_logs, optimize_db):
    """Run cleanup tasks"""
    if not any([clean_jobs, clean_logs, optimize_db]):
        click.echo("Please specify at least one cleanup option")
        return

    from celery_config import celery_app

    if clean_jobs:
        click.echo("Cleaning up old jobs...")
        from tasks.cleanup_tasks import cleanup_expired_jobs
        result = cleanup_expired_jobs.apply().get(timeout=60)
        click.echo(f"Cleaned up {result.get('archived_jobs', 0)} jobs")

    if clean_logs:
        click.echo("Cleaning up old logs...")
        from tasks.cleanup_tasks import cleanup_old_logs
        result = cleanup_old_logs.apply().get(timeout=60)
        click.echo(f"Deleted {result.get('files_deleted', 0)} log files")

    if optimize_db:
        click.echo("Optimizing database...")
        from tasks.cleanup_tasks import optimize_database
        result = optimize_database.apply().get(timeout=60)
        click.echo(f"Optimized {result.get('collections_optimized', 0)} collections")

if __name__ == '__main__':
    cli()