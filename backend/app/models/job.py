"""
Modello per Job/Processi di sincronizzazione
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    SYNC_MEETINGS = "sync_meetings"
    DOWNLOAD_TRANSCRIPT = "download_transcript"
    DOWNLOAD_HIGHLIGHTS = "download_highlights"
    DOWNLOAD_VIDEO = "download_video"

class Job(BaseModel):
    """Job di elaborazione"""
    id: str = Field(..., description="ID univoco del job")
    job_type: JobType = Field(..., description="Tipo di job")
    status: JobStatus = Field(JobStatus.PENDING, description="Stato del job")
    meeting_id: Optional[str] = Field(None, description="ID meeting associato")

    # Progress tracking
    progress_percentage: float = Field(0.0, description="Percentuale di completamento")
    current_step: Optional[str] = Field(None, description="Step corrente")
    total_steps: int = Field(1, description="Numero totale di step")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Durata del job in secondi"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_finished(self) -> bool:
        """Se il job è terminato"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobCreate(BaseModel):
    """Dati per creare un nuovo job"""
    job_type: JobType
    meeting_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class JobUpdate(BaseModel):
    """Dati per aggiornare un job"""
    status: Optional[JobStatus] = None
    progress_percentage: Optional[float] = None
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None