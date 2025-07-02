"""
Modello per Transcript da tl;dv
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TranscriptSegment(BaseModel):
    """Segmento singolo del transcript"""
    speaker: str = Field(..., description="Nome del parlante")
    text: str = Field(..., description="Testo del segmento")
    start_time: float = Field(..., description="Tempo iniziale in secondi")
    end_time: float = Field(..., description="Tempo finale in secondi")

class Transcript(BaseModel):
    """Transcript completo di un meeting"""
    id: str = Field(..., description="ID del transcript")
    meeting_id: str = Field(..., description="ID del meeting associato")
    data: List[TranscriptSegment] = Field(..., description="Segmenti del transcript")

    # Campi aggiunti per il nostro sistema
    firebase_id: Optional[str] = Field(None, description="ID documento Firebase")
    storage_path: Optional[str] = Field(None, description="Path su Firebase Storage")
    word_count: int = Field(0, description="Numero di parole totali")
    duration_seconds: float = Field(0, description="Durata totale in secondi")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __init__(self, **data):
        super().__init__(**data)
        # Calcola automaticamente durata e word count
        if self.data:
            self.duration_seconds = max(segment.end_time for segment in self.data)
            self.word_count = sum(len(segment.text.split()) for segment in self.data)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }