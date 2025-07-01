from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Union
from uuid import UUID
from ..models.position import PositionType


class PositionBase(BaseModel):
    ticker: str
    position_type: PositionType
    confidence: float
    reasoning: str
    catalysts: List[Dict[str, Any]] = []


class PositionCreate(PositionBase):
    supporting_articles: List[str] = []  # Changed from UUID to str for JSONB storage
    analysis_session_id: UUID


class PositionResponse(PositionBase):
    id: UUID
    supporting_articles: List[str]  # Changed from UUID to str for consistency
    created_at: datetime
    analysis_session_id: UUID

    class Config:
        from_attributes = True