from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID


class AnalysisBase(BaseModel):
    ticker: Optional[str] = None
    sentiment_score: float
    confidence: float
    catalysts: List[Dict[str, Any]] = []
    reasoning: str
    llm_model: str


class AnalysisCreate(AnalysisBase):
    article_id: UUID
    raw_response: Optional[Dict[str, Any]] = None


class AnalysisResponse(AnalysisBase):
    id: UUID
    article_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True