"""
Transcript data models with Pydantic validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class TranscriptSegment(BaseModel):
    """Individual transcript segment with speaker and timing"""
    speaker: str = Field(..., description="Speaker name or identifier")
    text: str = Field(..., description="Spoken text content")
    start_time: float = Field(..., ge=0, description="Segment start time in seconds")
    end_time: float = Field(..., ge=0, description="Segment end time in seconds")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Transcription confidence score")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

    @validator('text')
    def validate_text(cls, v):
        """Ensure text is not empty"""
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

    @validator('speaker')
    def validate_speaker(cls, v):
        """Clean speaker name"""
        return v.strip() if v else "Unknown Speaker"

    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time

    @property
    def formatted_time(self) -> str:
        """Get formatted time range (MM:SS - MM:SS)"""
        def format_seconds(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        return f"{format_seconds(self.start_time)} - {format_seconds(self.end_time)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)

class Transcript(BaseModel):
    """Complete transcript for a meeting"""
    id: str = Field(..., description="Unique transcript identifier")
    meeting_id: str = Field(..., description="Associated meeting ID")
    data: List[TranscriptSegment] = Field(..., description="List of transcript segments")
    language: Optional[str] = Field('en', description="Transcript language code")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    # Metadata
    total_duration: Optional[float] = Field(None, description="Total transcript duration in seconds")
    word_count: Optional[int] = Field(None, description="Total word count")
    speaker_count: Optional[int] = Field(None, description="Number of unique speakers")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "transcript_123",
                "meeting_id": "653663ac7c8dbd00130f11d9",
                "data": [
                    {
                        "speaker": "John Doe",
                        "text": "Welcome everyone to our weekly sync meeting.",
                        "start_time": 0.0,
                        "end_time": 3.5,
                        "confidence": 0.95
                    },
                    {
                        "speaker": "Jane Smith",
                        "text": "Thanks John. Let me start with the product updates.",
                        "start_time": 4.0,
                        "end_time": 7.2,
                        "confidence": 0.92
                    }
                ],
                "language": "en",
                "total_duration": 1800.5,
                "word_count": 2500,
                "speaker_count": 4
            }
        }

    @validator('data')
    def validate_segments(cls, v):
        """Validate transcript segments"""
        if not v:
            raise ValueError('Transcript must have at least one segment')

        # Check for overlapping segments
        sorted_segments = sorted(v, key=lambda x: x.start_time)
        for i in range(len(sorted_segments) - 1):
            current = sorted_segments[i]
            next_seg = sorted_segments[i + 1]
            if current.end_time > next_seg.start_time:
                # Allow small overlaps (up to 0.5 seconds)
                if current.end_time - next_seg.start_time > 0.5:
                    raise ValueError(f'Overlapping segments detected: {current.formatted_time} and {next_seg.formatted_time}')

        return v

    @property
    def speakers(self) -> List[str]:
        """Get list of unique speakers"""
        return list(set(segment.speaker for segment in self.data))

    @property
    def full_text(self) -> str:
        """Get complete transcript text"""
        return ' '.join(segment.text for segment in self.data)

    @property
    def duration_formatted(self) -> str:
        """Get formatted total duration"""
        if not self.total_duration:
            return "Unknown"

        hours = int(self.total_duration // 3600)
        minutes = int((self.total_duration % 3600) // 60)
        seconds = int(self.total_duration % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def get_text_by_speaker(self, speaker: str) -> str:
        """Get all text spoken by a specific speaker"""
        segments = [seg.text for seg in self.data if seg.speaker == speaker]
        return ' '.join(segments)

    def get_segments_in_range(self, start_time: float, end_time: float) -> List[TranscriptSegment]:
        """Get segments within a time range"""
        return [
            seg for seg in self.data
            if seg.start_time >= start_time and seg.end_time <= end_time
        ]

    def search_text(self, query: str, case_sensitive: bool = False) -> List[TranscriptSegment]:
        """Search for text in transcript"""
        if not case_sensitive:
            query = query.lower()

        matching_segments = []
        for segment in self.data:
            text = segment.text if case_sensitive else segment.text.lower()
            if query in text:
                matching_segments.append(segment)

        return matching_segments

    def calculate_metrics(self):
        """Calculate and update transcript metrics"""
        if self.data:
            # Calculate total duration
            last_segment = max(self.data, key=lambda x: x.end_time)
            self.total_duration = last_segment.end_time

            # Calculate word count
            self.word_count = sum(len(seg.text.split()) for seg in self.data)

            # Calculate speaker count
            self.speaker_count = len(self.speakers)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.dict(exclude_none=True)

    def to_srt_format(self) -> str:
        """Export transcript in SRT subtitle format"""
        srt_content = []

        for i, segment in enumerate(self.data, 1):
            # Format timestamps for SRT
            def format_srt_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

            start_time = format_srt_time(segment.start_time)
            end_time = format_srt_time(segment.end_time)

            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(f"{segment.speaker}: {segment.text}")
            srt_content.append("")  # Empty line

        return "\n".join(srt_content)

    def to_vtt_format(self) -> str:
        """Export transcript in WebVTT format"""
        vtt_content = ["WEBVTT", ""]

        for segment in self.data:
            # Format timestamps for VTT
            def format_vtt_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = seconds % 60
                return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

            start_time = format_vtt_time(segment.start_time)
            end_time = format_vtt_time(segment.end_time)

            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(f"{segment.speaker}: {segment.text}")
            vtt_content.append("")  # Empty line

        return "\n".join(vtt_content)

class TranscriptSearchRequest(BaseModel):
    """Request model for transcript search"""
    query: str = Field(..., description="Search query")
    case_sensitive: bool = Field(False, description="Case sensitive search")
    speaker_filter: Optional[str] = Field(None, description="Filter by specific speaker")
    time_range: Optional[Dict[str, float]] = Field(None, description="Time range filter")

    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()

    @validator('time_range')
    def validate_time_range(cls, v):
        """Validate time range"""
        if v:
            if 'start' not in v or 'end' not in v:
                raise ValueError('time_range must contain start and end times')
            if v['start'] >= v['end']:
                raise ValueError('start time must be less than end time')
        return v