from sqlalchemy import Column, String, DateTime, Float, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum
from ..core.database import Base


class PositionType(enum.Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SHORT = "SHORT"
    STRONG_SHORT = "STRONG_SHORT"


class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String, nullable=False, index=True)
    position_type = Column(Enum(PositionType), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    supporting_articles = Column(JSONB, default=[])  # Array of article IDs
    catalysts = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analysis_session_id = Column(UUID(as_uuid=True), index=True)

    __table_args__ = (
        Index('ix_positions_ticker_created', 'ticker', 'created_at'),
        Index('ix_positions_session_created', 'analysis_session_id', 'created_at'),
    )