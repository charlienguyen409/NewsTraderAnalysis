from pydantic import BaseModel, validator
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from .position import PositionResponse
from ..config.models import DEFAULT_MODEL, validate_model_id


class AnalysisRequest(BaseModel):
    max_positions: Optional[int] = 10
    min_confidence: Optional[float] = 0.7
    llm_model: str = DEFAULT_MODEL
    sources: List[str] = ["finviz", "biztoc"]
    
    @validator('llm_model')
    def validate_llm_model(cls, v):
        """Validate and normalize the LLM model"""
        return validate_model_id(v)
    
    @validator('max_positions')
    def validate_max_positions(cls, v):
        """Validate max_positions is in reasonable range"""
        if v < 1 or v > 50:
            raise ValueError('max_positions must be between 1 and 50')
        return v
    
    @validator('min_confidence')
    def validate_min_confidence(cls, v):
        """Validate min_confidence is between 0 and 1"""
        if v < 0.0 or v > 1.0:
            raise ValueError('min_confidence must be between 0.0 and 1.0')
        return v


class AnalysisResponse(BaseModel):
    session_id: UUID
    positions: List[PositionResponse]
    total_articles_analyzed: int
    analysis_duration: float
    created_at: datetime