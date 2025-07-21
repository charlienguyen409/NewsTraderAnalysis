from sqlalchemy import Column, String, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum
from ..core.database import Base


class AnalysisTypeEnum(PyEnum):
    FULL = "full"
    HEADLINES = "headlines"


class MarketSummary(Base):
    __tablename__ = "market_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    summary_data = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    analysis_type = Column(Enum(AnalysisTypeEnum), nullable=False)
    model_used = Column(String, nullable=False)
    data_sources = Column(JSONB, default={})
    
    __table_args__ = (
        Index('ix_market_summaries_session_generated', 'session_id', 'generated_at'),
        Index('ix_market_summaries_analysis_type_generated', 'analysis_type', 'generated_at'),
        Index('ix_market_summaries_model_generated', 'model_used', 'generated_at'),
    )