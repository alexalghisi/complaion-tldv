"""
Modelli dati per l'integrazione tl;dv
"""

from .meeting import Meeting, MeetingCreate, MeetingUpdate
from .transcript import Transcript, TranscriptSegment
from .highlights import Highlights, Highlight
from .job import Job, JobStatus, JobCreate

__all__ = [
    "Meeting",
    "MeetingCreate",
    "MeetingUpdate",
    "Transcript",
    "TranscriptSegment",
    "Highlights",
    "Highlight",
    "Job",
    "JobStatus",
    "JobCreate"
]