"""
Highlights/Notes data models with Pydantic validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class HighlightSource(str, Enum):
    """Source of the highlight"""
    MANUAL = "manual"
    AUTO = "auto"

class Topic(BaseModel):
    """Topic information for highlights"""
    title: str = Field(..., description="Topic title")
    summary: str = Field(..., description="Topic summary")

    @validator('title', 'summary')
    def validate_not_empty(cls, v):
        """Ensure fields are not empty"""
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class Highlight(BaseModel):
    """Individual highlight/note from a meeting"""
    text: str = Field(..., description="Highlight text content")
    start_time: float = Field(..., ge=0, description="Highlight start time in seconds")
    source: HighlightSource = Field(..., description="Highlight source (manual/auto)")
    topic: Optional[Topic] = Field(None, description="Associated topic")
    end_time: Optional[float] = Field(None, ge=0, description="Highlight end time in seconds")
    importance: Optional[int] = Field(None, ge=1, le=5, description="Importance level (1-5)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Associated tags")
    speaker: Optional[str] = Field(None, description="Speaker associated with highlight")

    @validator('text')
    def validate_text(cls, v):
        """Ensure text is not empty"""
        if not v.strip():
            raise ValueError('Highlight text cannot be empty')
        return v.strip()

    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end_time is after start_time if provided"""
        if v is not None and 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be greater than start_time')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags"""
        if v:
            # Remove empty tags and duplicates
            cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
            return cleaned_tags
        return []

    @property
    def duration(self) -> Optional[float]:
        """Get highlight duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def formatted_time(self) -> str:
        """Get formatted time"""
        def format_seconds(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        if self.end_time:
            return f"{format_seconds(self.start_time)} - {format_seconds(self.end_time)}"
        else:
            return f"at {format_seconds(self.start_time)}"

    @property
    def importance_label(self) -> str:
        """Get importance level label"""
        if not self.importance:
            return "Normal"

        labels = {
            1: "Low",
            2: "Normal",
            3: "Medium",
            4: "High",
            5: "Critical"
        }
        return labels.get(self.importance, "Normal")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)

class Highlights(BaseModel):
    """Complete highlights collection for a meeting"""
    meeting_id: str = Field(..., description="Associated meeting ID")
    data: List[Highlight] = Field(..., description="List of highlights")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    # Metadata
    total_highlights: Optional[int] = Field(None, description="Total number of highlights")
    manual_highlights: Optional[int] = Field(None, description="Number of manual highlights")
    auto_highlights: Optional[int] = Field(None, description="Number of auto highlights")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "meeting_id": "653663ac7c8dbd00130f11d9",
                "data": [
                    {
                        "text": "We need to prioritize the mobile app development for Q2",
                        "start_time": 450.5,
                        "source": "manual",
                        "importance": 4,
                        "tags": ["mobile", "q2", "priority"],
                        "topic": {
                            "title": "Mobile Development",
                            "summary": "Discussion about mobile app priorities"
                        },
                        "speaker": "Product Manager"
                    },
                    {
                        "text": "Budget allocation for the new marketing campaign",
                        "start_time": 890.2,
                        "source": "auto",
                        "importance": 3,
                        "tags": ["budget", "marketing"],
                        "topic": {
                            "title": "Marketing Budget",
                            "summary": "Budget discussion for upcoming campaigns"
                        }
                    }
                ],
                "total_highlights": 15,
                "manual_highlights": 8,
                "auto_highlights": 7
            }
        }

    @validator('data')
    def validate_highlights(cls, v):
        """Validate highlights list"""
        if not v:
            raise ValueError('Highlights must contain at least one item')
        return v

    @property
    def topics(self) -> List[str]:
        """Get list of unique topics"""
        topics = []
        for highlight in self.data:
            if highlight.topic and highlight.topic.title not in topics:
                topics.append(highlight.topic.title)
        return topics

    @property
    def all_tags(self) -> List[str]:
        """Get all unique tags"""
        all_tags = set()
        for highlight in self.data:
            if highlight.tags:
                all_tags.update(highlight.tags)
        return list(all_tags)

    @property
    def speakers(self) -> List[str]:
        """Get list of speakers with highlights"""
        speakers = set()
        for highlight in self.data:
            if highlight.speaker:
                speakers.add(highlight.speaker)
        return list(speakers)

    def get_highlights_by_source(self, source: HighlightSource) -> List[Highlight]:
        """Get highlights by source type"""
        return [h for h in self.data if h.source == source]

    def get_highlights_by_importance(self, min_importance: int = 3) -> List[Highlight]:
        """Get highlights with minimum importance level"""
        return [
            h for h in self.data
            if h.importance and h.importance >= min_importance
        ]

    def get_highlights_by_tag(self, tag: str) -> List[Highlight]:
        """Get highlights with specific tag"""
        tag_lower = tag.lower()
        return [
            h for h in self.data
            if h.tags and tag_lower in h.tags
        ]

    def get_highlights_by_topic(self, topic_title: str) -> List[Highlight]:
        """Get highlights for specific topic"""
        return [
            h for h in self.data
            if h.topic and h.topic.title.lower() == topic_title.lower()
        ]

    def get_highlights_by_speaker(self, speaker: str) -> List[Highlight]:
        """Get highlights from specific speaker"""
        return [
            h for h in self.data
            if h.speaker and h.speaker.lower() == speaker.lower()
        ]

    def get_highlights_in_time_range(self, start_time: float, end_time: float) -> List[Highlight]:
        """Get highlights within time range"""
        return [
            h for h in self.data
            if start_time <= h.start_time <= end_time
        ]

    def search_highlights(self, query: str, case_sensitive: bool = False) -> List[Highlight]:
        """Search highlights by text content"""
        if not case_sensitive:
            query = query.lower()

        matching_highlights = []
        for highlight in self.data:
            text = highlight.text if case_sensitive else highlight.text.lower()
            if query in text:
                matching_highlights.append(highlight)

        return matching_highlights

    def calculate_metrics(self):
        """Calculate and update highlights metrics"""
        if self.data:
            self.total_highlights = len(self.data)
            self.manual_highlights = len([h for h in self.data if h.source == HighlightSource.MANUAL])
            self.auto_highlights = len([h for h in self.data if h.source == HighlightSource.AUTO])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.dict(exclude_none=True)

    def to_summary_text(self) -> str:
        """Generate a text summary of all highlights"""
        if not self.data:
            return "No highlights available."

        summary_parts = []

        # Group by topic
        topic_groups = {}
        unassigned = []

        for highlight in self.data:
            if highlight.topic:
                topic_title = highlight.topic.title
                if topic_title not in topic_groups:
                    topic_groups[topic_title] = []
                topic_groups[topic_title].append(highlight)
            else:
                unassigned.append(highlight)

        # Format topic groups
        for topic_title, highlights in topic_groups.items():
            summary_parts.append(f"\n## {topic_title}")
            for highlight in highlights:
                summary_parts.append(f"- {highlight.text} ({highlight.formatted_time})")

        # Add unassigned highlights
        if unassigned:
            summary_parts.append(f"\n## Other Highlights")
            for highlight in unassigned:
                summary_parts.append(f"- {highlight.text} ({highlight.formatted_time})")

        return "\n".join(summary_parts)

class HighlightFilters(BaseModel):
    """Filters for highlight queries"""
    source: Optional[HighlightSource] = Field(None, description="Filter by source")
    min_importance: Optional[int] = Field(None, ge=1, le=5, description="Minimum importance level")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    topic: Optional[str] = Field(None, description="Filter by topic")
    speaker: Optional[str] = Field(None, description="Filter by speaker")
    time_range: Optional[Dict[str, float]] = Field(None, description="Time range filter")
    search_query: Optional[str] = Field(None, description="Text search query")

    @validator('time_range')
    def validate_time_range(cls, v):
        """Validate time range"""
        if v:
            if 'start' not in v or 'end' not in v:
                raise ValueError('time_range must contain start and end times')
            if v['start'] >= v['end']:
                raise ValueError('start time must be less than end time')
        return v

class HighlightStats(BaseModel):
    """Statistics for highlights"""
    total_highlights: int = Field(0, description="Total highlights count")
    manual_highlights: int = Field(0, description="Manual highlights count")
    auto_highlights: int = Field(0, description="Auto highlights count")
    average_importance: float = Field(0, description="Average importance level")
    most_common_tags: List[str] = Field(default_factory=list, description="Most common tags")
    topics_count: int = Field(0, description="Number of unique topics")
    speakers_count: int = Field(0, description="Number of speakers with highlights")

    @property
    def manual_percentage(self) -> float:
        """Calculate percentage of manual highlights"""
        if self.total_highlights == 0:
            return 0.0
        return (self.manual_highlights / self.total_highlights) * 100

    @property
    def auto_percentage(self) -> float:
        """Calculate percentage of auto highlights"""
        if self.total_highlights == 0:
            return 0.0
        return (self.auto_highlights / self.total_highlights) * 100