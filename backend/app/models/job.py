"""
Job data models for background processing
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    """Type of job"""
    DOWNLOAD_MEETINGS = "download_meetings"
    IMPORT_MEETING = "import_meeting"
    SYNC_ALL = "sync_all"
    CLEANUP = "cleanup"

class JobError(BaseModel):
    """Job error information"""
    timestamp: datetime = Field(..., description="Error timestamp")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retry_count: int = Field(0, description="Number of retries attempted")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobProgress(BaseModel):
    """Job progress information"""
    current_step: str = Field(..., description="Current processing step")
    total_steps: int = Field(..., description="Total number of steps")
    completed_steps: int = Field(0, description="Number of completed steps")
    current_item: Optional[str] = Field(None, description="Current item being processed")
    processed_items: int = Field(0, description="Number of processed items")
    total_items: Optional[int] = Field(None, description="Total number of items to process")

    @property
    def step_percentage(self) -> float:
        """Calculate step completion percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100

    @property
    def item_percentage(self) -> Optional[float]:
        """Calculate item processing percentage"""
        if self.total_items is None or self.total_items == 0:
            return None
        return (self.processed_items / self.total_items) * 100

    @property
    def overall_percentage(self) -> float:
        """Calculate overall progress percentage"""
        # Use item percentage if available, otherwise step percentage
        return self.item_percentage or self.step_percentage

class Job(BaseModel):
    """Job model for background processing"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique job identifier")
    type: JobType = Field(..., description="Job type")
    status: JobStatus = Field(JobStatus.PENDING, description="Current job status")
    name: str = Field(..., description="Human-readable job name")
    description: Optional[str] = Field(None, description="Job description")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    # Progress tracking
    progress: Optional[JobProgress] = Field(None, description="Job progress information")

    # Results and errors
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    errors: List[JobError] = Field(default_factory=list, description="Job errors")

    # Configuration
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")
    retry_count: int = Field(0, description="Number of retries attempted")
    max_retries: int = Field(3, description="Maximum number of retries")

    # Metadata
    user_id: Optional[str] = Field(None, description="User who created the job")
    priority: int = Field(1, ge=1, le=5, description="Job priority (1=low, 5=high)")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "job_123",
                "type": "download_meetings",
                "status": "running",
                "name": "Download Recent Meetings",
                "description": "Download all meetings from the last 30 days",
                "created_at": "2024-01-15T10:00:00Z",
                "started_at": "2024-01-15T10:01:00Z",
                "progress": {
                    "current_step": "Downloading transcripts",
                    "total_steps": 4,
                    "completed_steps": 2,
                    "processed_items": 15,
                    "total_items": 25
                },
                "config": {
                    "date_from": "2023-12-15",
                    "include_transcripts": True,
                    "include_highlights": True
                },
                "priority": 2
            }
        }

    @validator('name')
    def validate_name(cls, v):
        """Validate job name"""
        if not v.strip():
            raise ValueError('Job name cannot be empty')
        return v.strip()

    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        """Ensure completed_at is after started_at"""
        if v and 'started_at' in values and values['started_at'] and v < values['started_at']:
            raise ValueError('completed_at must be after started_at')
        return v

    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None

    @property
    def duration_formatted(self) -> str:
        """Get formatted job duration"""
        duration = self.duration
        if not duration:
            return "Not started"

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    @property
    def is_active(self) -> bool:
        """Check if job is currently active"""
        return self.status in [JobStatus.PENDING, JobStatus.RUNNING]

    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    @property
    def success_rate(self) -> float:
        """Calculate success rate for jobs with items"""
        if not self.progress or not self.progress.total_items:
            return 100.0 if self.status == JobStatus.COMPLETED else 0.0

        successful_items = self.progress.processed_items - len(self.errors)
        return (successful_items / self.progress.total_items) * 100

    def add_error(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the job"""
        error = JobError(
            timestamp=datetime.utcnow(),
            error_code=error_code,
            message=message,
            details=details,
            retry_count=self.retry_count
        )
        self.errors.append(error)
        self.updated_at = datetime.utcnow()

    def update_progress(self, **kwargs):
        """Update job progress"""
        if not self.progress:
            self.progress = JobProgress(
                current_step="Starting",
                total_steps=1,
                completed_steps=0
            )

        # Update progress fields
        for key, value in kwargs.items():
            if hasattr(self.progress, key):
                setattr(self.progress, key, value)

        self.updated_at = datetime.utcnow()

    def start(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete(self, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result:
            self.result = result

    def fail(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.add_error(error_code, message, details)

    def cancel(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries

    def retry(self):
        """Retry the job"""
        if not self.can_retry():
            raise ValueError("Job cannot be retried")

        self.retry_count += 1
        self.status = JobStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.updated_at = datetime.utcnow()

        # Reset progress
        if self.progress:
            self.progress.completed_steps = 0
            self.progress.processed_items = 0
            self.progress.current_step = "Retrying"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.dict(exclude_none=True)

class JobRequest(BaseModel):
    """Request model for creating jobs"""
    type: JobType = Field(..., description="Job type")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")
    priority: int = Field(1, ge=1, le=5, description="Job priority")

    @validator('name')
    def validate_name(cls, v):
        """Validate job name"""
        if not v.strip():
            raise ValueError('Job name cannot be empty')
        return v.strip()

class JobResponse(BaseModel):
    """Response model for job operations"""
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total pages")
    total: int = Field(..., description="Total jobs count")
    page_size: int = Field(..., description="Items per page")
    results: List[Job] = Field(..., description="Job results")

class JobFilters(BaseModel):
    """Filters for job queries"""
    status: Optional[JobStatus] = Field(None, description="Filter by status")
    type: Optional[JobType] = Field(None, description="Filter by type")
    user_id: Optional[str] = Field(None, description="Filter by user")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Filter by priority")
    date_from: Optional[str] = Field(None, description="Filter by creation date from")
    date_to: Optional[str] = Field(None, description="Filter by creation date to")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=100, description="Items per page")

    @validator('date_from', 'date_to')
    def validate_dates(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Date must be in ISO format')
        return v

class JobStats(BaseModel):
    """Job statistics model"""
    total_jobs: int = Field(0, description="Total jobs count")
    pending_jobs: int = Field(0, description="Pending jobs count")
    running_jobs: int = Field(0, description="Running jobs count")
    completed_jobs: int = Field(0, description="Completed jobs count")
    failed_jobs: int = Field(0, description="Failed jobs count")
    cancelled_jobs: int = Field(0, description="Cancelled jobs count")
    average_duration_seconds: float = Field(0, description="Average job duration")
    success_rate: float = Field(0, description="Overall success rate")

    @property
    def active_jobs(self) -> int:
        """Get count of active jobs"""
        return self.pending_jobs + self.running_jobs

    @property
    def finished_jobs(self) -> int:
        """Get count of finished jobs"""
        return self.completed_jobs + self.failed_jobs + self.cancelled_jobs