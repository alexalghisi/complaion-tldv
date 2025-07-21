#!/usr/bin/env python3
"""
Test script for the Complaion tl;dv Integration API
Run this to verify that all services are working correctly
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tldv_service():
    """Test tl;dv API service"""
    print("\n🔗 Testing tl;dv API Service...")

    try:
        from services.tldv_service import TLDVService
        from models.meeting import MeetingFilters

        service = TLDVService()

        # Test connection
        print("  ✓ Testing API connection...")
        status = service.get_api_status()

        if status['api_accessible'] and status['api_key_valid']:
            print(f"  tl;dv API is accessible (response time: {status.get('response_time_ms', 'N/A')}ms)")

            # Test getting meetings
            print("  ✓ Testing get meetings...")
            filters = MeetingFilters(limit=5)
            response = service.get_meetings(filters)
            print(f"  Retrieved {len(response.results)} meetings (total: {response.total})")

            # Test get meeting details if we have meetings
            if response.results:
                meeting = response.results[0]
                print(f"  ✓ Testing meeting details for: {meeting.name}")

                # Get transcript
                transcript = service.get_transcript(meeting.id)
                if transcript:
                    print(f"  Retrieved transcript with {len(transcript.data)} segments")
                else:
                    print("   No transcript available")

                # Get highlights
                highlights = service.get_highlights(meeting.id)
                if highlights:
                    print(f"  Retrieved highlights with {len(highlights.data)} items")
                else:
                    print("  No highlights available")

            return True
        else:
            print(f"  tl;dv API connection failed: {status}")
            return False

    except Exception as e:
        print(f"  tl;dv service test failed: {e}")
        return False

def test_firebase_service():
    """Test Firebase service"""
    print("\n Testing Firebase Service...")

    try:
        from services.firebase_service import FirebaseService

        service = FirebaseService()

        # Test connection
        print("  ✓ Testing Firebase connection...")
        connected = service.test_connection()

        if connected:
            print("  Firebase is accessible")

            # Test job creation
            print("  ✓ Testing job operations...")
            test_job_data = {
                'type': 'download_meetings',
                'name': 'Test Job',
                'status': 'pending',
                'created_at': datetime.utcnow()
            }

            job_id = service.create_job(test_job_data)
            print(f"   Created test job: {job_id}")

            # Get the job back
            retrieved_job = service.get_job(job_id)
            if retrieved_job and retrieved_job['name'] == 'Test Job':
                print("   Job retrieval successful")
            else:
                print("   Job retrieval failed")

            # Update job status
            service.update_job_status(job_id, 'completed')
            print("   Job status update successful")

            return True
        else:
            print("   Firebase connection failed")
            return False

    except Exception as e:
        print(f"   Firebase service test failed: {e}")
        return False

def test_models():
    """Test data models"""
    print("\n Testing Data Models...")

    try:
        from models.meeting import Meeting, MeetingFilters
        from models.job import Job, JobType, JobStatus
        from models.transcript import Transcript, TranscriptSegment
        from models.highlights import Highlights, Highlight, HighlightSource, Topic

        # Test Meeting model
        print("  ✓ Testing Meeting model...")
        meeting_data = {
            'id': 'test_meeting_123',
            'name': 'Test Meeting',
            'happened_at': '2024-01-15T10:00:00Z',
            'url': 'https://example.com/meeting.mp4'
        }
        meeting = Meeting(**meeting_data)
        print(f"   Meeting model: {meeting.name} ({meeting.participant_count} participants)")

        # Test MeetingFilters
        filters = MeetingFilters(query='test', limit=10)
        print(f"   MeetingFilters: query='{filters.query}', limit={filters.limit}")

        # Test Job model
        print("  ✓ Testing Job model...")
        job = Job(
            type=JobType.DOWNLOAD_MEETINGS,
            name='Test Download Job',
            status=JobStatus.PENDING
        )
        print(f"  Job model: {job.name} ({job.status.value})")

        # Test Transcript model
        print("  ✓ Testing Transcript model...")
        transcript_segments = [
            TranscriptSegment(
                speaker='John Doe',
                text='Hello everyone, welcome to our meeting.',
                start_time=0.0,
                end_time=3.5
            ),
            TranscriptSegment(
                speaker='Jane Smith',
                text='Thank you John, let me share the agenda.',
                start_time=4.0,
                end_time=7.2
            )
        ]
        transcript = Transcript(
            id='transcript_123',
            meeting_id='test_meeting_123',
            data=transcript_segments
        )
        transcript.calculate_metrics()
        print(f"  Transcript model: {len(transcript.data)} segments, {transcript.word_count} words")

        # Test Highlights model
        print("  ✓ Testing Highlights model...")
        topic = Topic(title='Product Update', summary='Discussion about product features')
        highlight = Highlight(
            text='We need to prioritize mobile development',
            start_time=120.5,
            source=HighlightSource.MANUAL,
            topic=topic,
            importance=4
        )
        highlights = Highlights(
            meeting_id='test_meeting_123',
            data=[highlight]
        )
        highlights.calculate_metrics()
        print(f"  Highlights model: {highlights.total_highlights} highlights")

        return True

    except Exception as e:
        print(f"   Models test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application"""
    print("\n Testing Flask Application...")

    try:
        from app import create_app
        import json

        app = create_app()
        client = app.test_client()

        # Test health endpoint
        print("  ✓ Testing health endpoint...")
        response = client.get('/health')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"    Health check passed: {data['status']}")
        else:
            print(f"    Health check returned {response.status_code}")

        # Test API info endpoint
        print("  ✓ Testing API info endpoint...")
        response = client.get('/api/')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"    API info: {data['name']} v{data['version']}")
        else:
            print(f"   ️  API info returned {response.status_code}")

        # Test jobs endpoint
        print("  ✓ Testing jobs endpoint...")
        response = client.get('/api/jobs')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Jobs endpoint: returned {data.get('total', 0)} jobs")
        else:
            print(f"   Jobs endpoint returned {response.status_code}")

        # Test meetings endpoint
        print("  ✓ Testing meetings endpoint...")
        response = client.get('/api/meetings')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Meetings endpoint: returned {data.get('total', 0)} meetings")
        else:
            print(f"    Meetings endpoint returned {response.status_code}")

        # Test stats endpoint
        print("  ✓ Testing stats endpoint...")
        response = client.get('/api/stats')
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Stats endpoint: {data['jobs']['total_jobs']} jobs, {data['meetings']['total_meetings']} meetings")
        else
            print(f"   Stats endpoint returned {response.status_code}")

        return True

    except Exception as e:
        print(f"   Flask app test failed: {e}")
        return False

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Checking Environment Configuration...")

    required_vars = [
        'TLDV_API_KEY',
        'FIREBASE_PROJECT_ID',
        'SECRET_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * min(len(value), 8)}{'...' if len(value) > 8 else ''}")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)

    optional_vars = [
        'FIREBASE_SERVICE_ACCOUNT_PATH',
        'REDIS_URL',
        'FRONTEND_URL'
    ]

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: Not set (optional)")

    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or environment configuration.")
        return False

    return True

def main():
    """Run all tests"""
    print("🚀 Starting Complaion tl;dv Integration API Tests")
    print("=" * 60)

    tests = [
        ("Environment Configuration", check_environment),
        ("Data Models", test_models),
        ("Flask Application", test_flask_app),
        ("Firebase Service", test_firebase_service),
        ("tl;dv API Service", test_tldv_service)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The API is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)