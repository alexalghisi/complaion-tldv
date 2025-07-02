"""
Modello per Highlights/Note da tl;dv
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class HighlightSource(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"

class Topic(BaseModel):
    """Topic di un highlight"""
    title: str
    summary: str

class Highlight(BaseModel):
    """Singolo highlight"""
    text: str = Field(..., description="Testo dell'highlight")
    start_time: float = Field(..., description="Tempo iniziale in secondi")
    source: HighlightSource = Field(..., description="Sorgente dell'highlight")
    topic: Optional[Topic] = None

class Highlights(BaseModel):
    """Collezione di highlights per un meeting"""
    meeting_id: str = Field(..., description="ID del meeting associato")
    data: List[Highlight] = Field(..., description="Lista degli highlights")

    # Campi aggiunti per il nostro sistema
    firebase_id: Optional[str] = Field(None, description="ID documento Firebase")
    storage_path: Optional[str] = Field(None, description="Path su Firebase Storage")
    total_highlights: int = Field(0, description="Numero totale di highlights")
    manual_highlights: int = Field(0, description="Numero di highlights manuali")
    auto_highlights: int = Field(0, description="Numero di highlights automatici")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __init__(self, **data):
        super().__init__(**data)
        # Calcola automaticamente le statistiche
        if self.data:
            self.total_highlights = len(self.data)
            self.manual_highlights = sum(1 for h in self.data if h.source == HighlightSource.MANUAL)
            self.auto_highlights = sum(1 for h in self.data if h.source == HighlightSource.AUTO)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }