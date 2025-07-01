from sqlalchemy import Column, String, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(String, nullable=False, index=True)  # 'finviz' or 'biztoc'
    ticker = Column(String, index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True))
    is_processed = Column(Boolean, default=False, index=True)
    article_metadata = Column(JSONB, default={})

    __table_args__ = (
        Index('ix_articles_ticker_scraped', 'ticker', 'scraped_at'),
        Index('ix_articles_source_scraped', 'source', 'scraped_at'),
    )