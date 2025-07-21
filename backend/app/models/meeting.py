"""
Meeting data models with Pydantic validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class Organizer(BaseModel):
    """Meeting organizer information"""
    name: str
    email: str

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class Invitee(BaseModel):
    """Meeting invitee information"""
    name: str
    email: str

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class Meeting(BaseModel):
    """Meeting data model from tl;dv API"""
    id: str = Field(..., description="Unique meeting identifier")
    name: str = Field(..., description="Meeting name/title")
    happened_at: str = Field(..., description="Meeting date/time in ISO format")
    url: Optional[str] = Field(None, description="Meeting recording URL")
    organizer: Optional[Organizer] = Field(None, description="Meeting organizer")
    invitees: Optional[List[Invitee]] = Field(default_factory=list, description="Meeting invitees")
    template: Optional[str] = Field(None, description="Meeting template")
    extra_properties: Optional[str] = Field(None, description="Additional meeting properties")

    # Internal fields (added by our system)
    job_id: Optional[str] = Field(None, description="Associated job ID")
    video_url: Optional[str] = Field(None, description="Stored video URL")
    transcript_available: bool = Field(False, description="Transcript available flag")
    highlights_available: bool = Field(False, description="Highlights available flag")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record update timestamp")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "653663ac7c8dbd00130f11d9",
                "name": "Weekly Team Sync",
                "happened_at": "2024-01-15T10:00:00Z",
                "url": "https://example.com/recording.mp4",
                "organizer": {
                    "name": "John Doe",
                    "email": "john@company.com"
                },
                "invitees": [
                    {
                        "name": "Jane Smith",
                        "email": "jane@company.com"
                    }
                ],
                "job_id": "job_123",
                "transcript_available": True,
                "highlights_available": True
            }
        }

    @validator('happened_at')
    def validate_happened_at(cls, v):
        """Validate ISO date format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('happened_at must be in ISO format')
        return v

    @validator('url', 'video_url')
    def validate_url(cls, v):
        """Validate URL format"""
        if v and not re.match(r'^https?://', v):
            raise ValueError('URL must start with http:// or https://')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.dict(exclude_none=True)

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (placeholder for future implementation)"""
        return "N/A"

    @property
    def participant_count(self) -> int:
        """Get total participant count"""
        count = 1 if self.organizer else 0  # Organizer
        count += len(self.invitees) if self.invitees else 0  # Invitees
        return count

class MeetingImportRequest(BaseModel):
    """Request model for importing meetings"""
    name: str = Field(..., description="Meeting name")
    url: str = Field(..., description="Public meeting recording URL")
    happened_at: Optional[str] = Field(None, description="Meeting date in ISO format")
    dry_run: bool = Field(False, description="Test import without persistence")

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format and accessibility"""
        if not re.match(r'^https?://', v):
            raise ValueError('URL must start with http:// or https://')

        # Additional validation for supported formats
        supported_formats = ['.mp3', '.mp4', '.wav', '.m4a', '.mkv', '.mov', '.avi', '.wma', '.flac']
        if not any(v.lower().endswith(fmt) for fmt in supported_formats):
            raise ValueError(f'URL must point to a supported format: {", ".join(supported_formats)}')

        return v

    @validator('happened_at')
    def validate_happened_at(cls, v):
        """Validate ISO date format if provided"""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('happened_at must be in ISO format')
        return v

class MeetingResponse(BaseModel):
    """Response model for meeting operations"""
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total pages")
    total: int = Field(..., description="Total meetings count")
    page_size: int = Field(..., description="Items per page")
    results: List[Meeting] = Field(..., description="Meeting results")

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "pages": 5,
                "total": 142,
                "page_size": 50,
                "results": [
                    {
                        "id": "653663ac7c8dbd00130f11d9",
                        "name": "Weekly Team Sync",
                        "happened_at": "2024-01-15T10:00:00Z",
                        "transcript_available": True,
                        "highlights_available": True
                    }
                ]
            }
        }

class MeetingFilters(BaseModel):
    """Filters for meeting queries"""
    query: Optional[str] = Field(None, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=100, description="Items per page")
    date_from: Optional[str] = Field(None, description="Start date filter")
    date_to: Optional[str] = Field(None, description="End date filter")
    only_participated: bool = Field(False, description="Only meetings user participated in")
    meeting_type: Optional[str] = Field(None, description="Meeting type: internal or external")
    job_id: Optional[str] = Field(None, description="Filter by job ID")
    has_transcript: Optional[bool] = Field(None, description="Filter by transcript availability")
    has_highlights: Optional[bool] = Field(None, description="Filter by highlights availability")

    @validator('meeting_type')
    def validate_meeting_type(cls, v):
        """Validate meeting type"""
        if v and v not in ['internal', 'external']:
            raise ValueError('meeting_type must be "internal" or "external"')
        return v

    @validator('date_from', 'date_to')
    def validate_dates(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Date must be in ISO format')
        return v

class MeetingStats(BaseModel):
    """Meeting statistics model"""
    total_meetings: int = Field(0, description="Total meetings count")
    meetings_with_transcript: int = Field(0, description="Meetings with transcript")
    meetings_with_highlights: int = Field(0, description="Meetings with highlights")
    meetings_with_video: int = Field(0, description="Meetings with video")
    total_duration_minutes: int = Field(0, description="Total duration in minutes")
    average_duration_minutes: float = Field(0, description="Average duration in minutes")
    last_meeting_date: Optional[str] = Field(None, description="Most recent meeting date")

    @property
    def transcript_percentage(self) -> float:
        """Calculate percentage of meetings with transcripts"""
        if self.total_meetings == 0:
            return 0.0
        return (self.meetings_with_transcript / self.total_meetings) * 100

    @property
    def highlights_percentage(self) -> float:
        """Calculate percentage of meetings with highlights"""
        if self.total_meetings == 0:
            return 0.0
        return (self.meetings_with_highlights / self.total_meetings) * 100