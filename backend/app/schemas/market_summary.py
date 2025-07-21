from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from ..models.market_summary import AnalysisTypeEnum


class MarketSummaryBase(BaseModel):
    """Base schema for MarketSummary with common fields"""
    summary_data: Dict[str, Any] = Field(..., description="Complete LLM-generated market summary data")
    analysis_type: AnalysisTypeEnum = Field(..., description="Type of analysis: 'full' or 'headlines'")
    model_used: str = Field(..., description="LLM model used for analysis")
    data_sources: Dict[str, Any] = Field(default_factory=dict, description="Counts of articles/analyses/positions used")


class MarketSummaryCreate(MarketSummaryBase):
    """Schema for creating a new market summary"""
    session_id: UUID = Field(..., description="UUID of the analysis session")


class MarketSummaryResponse(MarketSummaryBase):
    """Schema for API responses with full market summary data"""
    id: UUID = Field(..., description="Unique identifier for the market summary")
    session_id: UUID = Field(..., description="UUID of the analysis session")
    generated_at: datetime = Field(..., description="Timestamp when summary was generated")
    
    class Config:
        from_attributes = True


class MarketSummaryListItem(BaseModel):
    """Schema for listing market summaries (lightweight version)"""
    id: UUID = Field(..., description="Unique identifier for the market summary")
    session_id: UUID = Field(..., description="UUID of the analysis session")
    generated_at: datetime = Field(..., description="Timestamp when summary was generated")
    analysis_type: AnalysisTypeEnum = Field(..., description="Type of analysis: 'full' or 'headlines'")
    model_used: str = Field(..., description="LLM model used for analysis")
    article_count: int = Field(0, description="Number of articles analyzed")
    position_count: int = Field(0, description="Number of positions generated")
    
    class Config:
        from_attributes = True