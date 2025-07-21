"""
Celery tasks for meeting data processing
"""
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from celery import current_task
from celery.exceptions import Retry

from celery_config import celery_app
from services.tldv_service import TLDVService, TLDVAPIError
from services.firebase_service import FirebaseService
from models.meeting import Meeting, MeetingFilters
from models.job import Job, JobStatus, JobProgress, JobType
from models.transcript import Transcript
from models.highlights import Highlights

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def download_meetings_job(self, job_id: str, filters_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main task to download meetings from tl;dv API

    Args:
        job_id: Job identifier
        filters_dict: Meeting filters as dictionary

    Returns:
        Dict with job results
    """
    logger.info(f"Starting download meetings job: {job_id}")

    # Initialize services
    firebase_service = FirebaseService()
    tldv_service = TLDVService()

    try:
        # Update job status to running
        firebase_service.update_job_status(
            job_id,
            JobStatus.RUNNING.value,
            started_at=datetime.utcnow()
        )

        # Convert filters dict to MeetingFilters object
        filters = MeetingFilters(**filters_dict)

        # Initialize progress tracking
        progress = JobProgress(
            current_step="Fetching meetings list",
            total_steps=4,
            completed_steps=0
        )

        firebase_service.update_job_status(
            job_id,
            JobStatus.RUNNING.value,
            progress=progress.dict()
        )

        # Step 1: Get all meetings from tl;dv
        logger.info(f"Job {job_id}: Fetching meetings from tl;dv API")

        all_meetings = []
        current_page = 1
        total_pages = 1

        def progress_callback(page, total_pages_cb, meetings):
            nonlocal total_pages
            total_pages = total_pages_cb

            progress.current_step = f"Fetching meetings (page {page}/{total_pages})"
            progress.total_items = None  # Unknown until we get all pages
            progress.processed_items = len(all_meetings)

            firebase_service.update_job_status(
                job_id,
                JobStatus.RUNNING.value,
                progress=progress.dict()
            )

        # Get all meetings in batches
        meetings = tldv_service.get_all_meetings_batch(
            filters=filters,
            callback=progress_callback
        )

        if not meetings:
            # Complete job with empty result
            result = {
                'total_meetings': 0,
                'processed_meetings': 0,
                'failed_meetings': 0,
                'message': 'No meetings found matching the criteria'
            }

            firebase_service.update_job_status(
                job_id,
                JobStatus.COMPLETED.value,
                completed_at=datetime.utcnow(),
                result=result
            )

            return result

        # Step 2: Update progress with total count
        progress.completed_steps = 1
        progress.current_step = "Processing meetings"
        progress.total_items = len(meetings)
        progress.processed_items = 0

        firebase_service.update_job_status(
            job_id,
            JobStatus.RUNNING.value,
            progress=progress.dict()
        )

        # Step 3: Process each meeting
        processed_meetings = 0
        failed_meetings = 0
        errors = []

        for i, meeting in enumerate(meetings):
            try:
                logger.info(f"Job {job_id}: Processing meeting {meeting.id} ({i+1}/{len(meetings)})")

                # Update progress
                progress.current_step = f"Processing meeting: {meeting.name}"
                progress.current_item = meeting.id
                progress.processed_items = i

                firebase_service.update_job_status(
                    job_id,
                    JobStatus.RUNNING.value,
                    progress=progress.dict()
                )

                # Process meeting asynchronously
                result = download_single_meeting.apply_async(
                    args=[job_id, meeting.dict()],
                    countdown=i * 2  # Stagger requests to avoid rate limiting
                )

                # Store task ID for tracking
                meeting.job_id = job_id

                processed_meetings += 1

                # Small delay to avoid overwhelming the API
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Job {job_id}: Failed to process meeting {meeting.id}: {e}")
                failed_meetings += 1
                errors.append({
                    'meeting_id': meeting.id,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })

        # Step 4: Complete job
        progress.completed_steps = 4
        progress.current_step = "Finalizing"
        progress.processed_items = len(meetings)

        result = {
            'total_meetings': len(meetings),
            'processed_meetings': processed_meetings,
            'failed_meetings': failed_meetings,
            'errors': errors,
            'duration_seconds': (datetime.utcnow() - datetime.utcnow()).total_seconds()
        }

        firebase_service.update_job_status(
            job_id,
            JobStatus.COMPLETED.value,
            completed_at=datetime.utcnow(),
            result=result,
            progress=progress.dict()
        )

        logger.info(f"Job {job_id} completed: {processed_meetings}/{len(meetings)} meetings processed")

        return result

    except TLDVAPIError as e:
        logger.error(f"Job {job_id}: tl;dv API error: {e}")

        firebase_service.update_job_status(
            job_id,
            JobStatus.FAILED.value,
            completed_at=datetime.utcnow(),
            errors=[{
                'error_code': 'TLDV_API_ERROR',
                'message': str(e),
                'status_code': e.status_code,
                'timestamp': datetime.utcnow().isoformat()
            }]
        )

        raise

    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error: {e}", exc_info=True)

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Job {job_id}: Retrying in {self.default_retry_delay} seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=self.default_retry_delay)

        # Max retries reached
        firebase_service.update_job_status(
            job_id,
            JobStatus.FAILED.value,
            completed_at=datetime.utcnow(),
            errors=[{
                'error_code': 'UNEXPECTED_ERROR',
                'message': str(e),
                'retries': self.request.retries,
                'timestamp': datetime.utcnow().isoformat()
            }]
        )

        raise

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def download_single_meeting(self, job_id: str, meeting_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download and process a single meeting

    Args:
        job_id: Parent job identifier
        meeting_dict: Meeting data as dictionary

    Returns:
        Dict with processing results
    """
    meeting = Meeting(**meeting_dict)
    logger.info(f"Processing single meeting: {meeting.id} for job {job_id}")

    firebase_service = FirebaseService()
    tldv_service = TLDVService()

    try:
        # Save basic meeting info
        meeting.job_id = job_id
        meeting_id = firebase_service.save_meeting(meeting.dict())

        result = {
            'meeting_id': meeting_id,
            'transcript_saved': False,
            'highlights_saved': False,
            'video_uploaded': False,
            'errors': []
        }

        # Process transcript
        try:
            transcript = tldv_service.get_transcript(meeting.id)
            if transcript:
                firebase_service.save_transcript(meeting.id, transcript.dict())
                result['transcript_saved'] = True

                # Update meeting with transcript availability
                firebase_service.save_meeting({
                    **meeting.dict(),
                    'transcript_available': True
                })

                logger.info(f"Saved transcript for meeting {meeting.id}")
        except Exception as e:
            logger.warning(f"Failed to process transcript for meeting {meeting.id}: {e}")
            result['errors'].append(f"Transcript error: {str(e)}")

        # Process highlights
        try:
            highlights = tldv_service.get_highlights(meeting.id)
            if highlights:
                firebase_service.save_highlights(meeting.id, highlights.dict())
                result['highlights_saved'] = True

                # Update meeting with highlights availability
                firebase_service.save_meeting({
                    **meeting.dict(),
                    'highlights_available': True
                })

                logger.info(f"Saved highlights for meeting {meeting.id}")
        except Exception as e:
            logger.warning(f"Failed to process highlights for meeting {meeting.id}: {e}")
            result['errors'].append(f"Highlights error: {str(e)}")

        # Upload video if URL is available
        if meeting.url:
            try:
                video_url = firebase_service.upload_video(meeting.id, meeting.url)
                if video_url:
                    result['video_uploaded'] = True

                    # Update meeting with video URL
                    firebase_service.save_meeting({
                        **meeting.dict(),
                        'video_url': video_url
                    })

                    logger.info(f"Uploaded video for meeting {meeting.id}")
            except Exception as e:
                logger.warning(f"Failed to upload video for meeting {meeting.id}: {e}")
                result['errors'].append(f"Video upload error: {str(e)}")

        logger.info(f"Completed processing meeting {meeting.id}")
        return result

    except Exception as e:
        logger.error(f"Failed to process meeting {meeting.id}: {e}")

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying meeting {meeting.id} in {self.default_retry_delay} seconds")
            raise self.retry(exc=e, countdown=self.default_retry_delay)

        # Max retries reached
        return {
            'meeting_id': meeting.id,
            'transcript_saved': False,
            'highlights_saved': False,
            'video_uploaded': False,
            'errors': [f"Processing failed after {self.request.retries} retries: {str(e)}"]
        }

@celery_app.task(bind=True, max_retries=2)
def process_meeting_transcript(self, meeting_id: str) -> Dict[str, Any]:
    """
    Process transcript for a specific meeting

    Args:
        meeting_id: Meeting identifier

    Returns:
        Dict with processing results
    """
    logger.info(f"Processing transcript for meeting: {meeting_id}")

    firebase_service = FirebaseService()
    tldv_service = TLDVService()

    try:
        transcript = tldv_service.get_transcript(meeting_id)

        if not transcript:
            return {
                'success': False,
                'message': 'Transcript not available',
                'meeting_id': meeting_id
            }

        # Save transcript
        firebase_service.save_transcript(meeting_id, transcript.dict())

        # Update meeting record
        meeting_data = firebase_service.get_meeting(meeting_id)
        if meeting_data:
            meeting_data['transcript_available'] = True
            firebase_service.save_meeting(meeting_data)

        logger.info(f"Successfully processed transcript for meeting {meeting_id}")

        return {
            'success': True,
            'meeting_id': meeting_id,
            'segments_count': len(transcript.data),
            'duration': transcript.total_duration,
            'word_count': transcript.word_count
        }

    except Exception as e:
        logger.error(f"Failed to process transcript for meeting {meeting_id}: {e}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)

        return {
            'success': False,
            'message': str(e),
            'meeting_id': meeting_id
        }

@celery_app.task(bind=True, max_retries=2)
def process_meeting_highlights(self, meeting_id: str) -> Dict[str, Any]:
    """
    Process highlights for a specific meeting

    Args:
        meeting_id: Meeting identifier

    Returns:
        Dict with processing results
    """
    logger.info(f"Processing highlights for meeting: {meeting_id}")

    firebase_service = FirebaseService()
    tldv_service = TLDVService()

    try:
        highlights = tldv_service.get_highlights(meeting_id)

        if not highlights:
            return {
                'success': False,
                'message': 'Highlights not available',
                'meeting_id': meeting_id
            }

        # Save highlights
        firebase_service.save_highlights(meeting_id, highlights.dict())

        # Update meeting record
        meeting_data = firebase_service.get_meeting(meeting_id)
        if meeting_data:
            meeting_data['highlights_available'] = True
            firebase_service.save_meeting(meeting_data)

        logger.info(f"Successfully processed highlights for meeting {meeting_id}")

        return {
            'success': True,
            'meeting_id': meeting_id,
            'highlights_count': len(highlights.data),
            'manual_highlights': highlights.manual_highlights,
            'auto_highlights': highlights.auto_highlights
        }

    except Exception as e:
        logger.error(f"Failed to process highlights for meeting {meeting_id}: {e}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)

        return {
            'success': False,
            'message': str(e),
            'meeting_id': meeting_id
        }

@celery_app.task
def sync_meeting_data(meeting_id: str) -> Dict[str, Any]:
    """
    Sync meeting data from tl;dv to local storage

    Args:
        meeting_id: Meeting identifier

    Returns:
        Dict with sync results
    """
    logger.info(f"Syncing meeting data: {meeting_id}")

    firebase_service = FirebaseService()
    tldv_service = TLDVService()

    try:
        # Get meeting details from tl;dv
        meeting_details = tldv_service.get_meeting_with_details(
            meeting_id,
            include_transcript=True,
            include_highlights=True
        )

        # Save meeting
        meeting = meeting_details['meeting']
        firebase_service.save_meeting(meeting.dict())

        results = {
            'meeting_synced': True,
            'transcript_synced': False,
            'highlights_synced': False
        }

        # Save transcript if available
        if meeting_details.get('transcript'):
            firebase_service.save_transcript(meeting_id, meeting_details['transcript'].dict())
            results['transcript_synced'] = True

        # Save highlights if available
        if meeting_details.get('highlights'):
            firebase_service.save_highlights(meeting_id, meeting_details['highlights'].dict())
            results['highlights_synced'] = True

        logger.info(f"Successfully synced meeting {meeting_id}")
        return results

    except Exception as e:
        logger.error(f"Failed to sync meeting {meeting_id}: {e}")
        return {
            'meeting_synced': False,
            'error': str(e)
        }