from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    catalysts = Column(JSONB, default=[])
    reasoning = Column(Text)
    llm_model = Column(String, nullable=False)
    raw_response = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("Article", backref="analyses")

    __table_args__ = (
        Index('ix_analyses_ticker_created', 'ticker', 'created_at'),
        Index('ix_analyses_sentiment_confidence', 'sentiment_score', 'confidence'),
    )