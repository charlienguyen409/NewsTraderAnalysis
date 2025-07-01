from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    level = Column(String, nullable=False, index=True)  # 'INFO', 'WARNING', 'ERROR'
    category = Column(String, nullable=False, index=True)  # 'scraping', 'llm', 'analysis', 'system'
    action = Column(String, nullable=False)  # Specific action taken
    message = Column(Text, nullable=False)  # Human readable message
    details = Column(JSONB, default={})  # Additional structured data
    session_id = Column(UUID(as_uuid=True), index=True)  # Analysis session if applicable
    
    __table_args__ = (
        Index('ix_activity_logs_timestamp_level', 'timestamp', 'level'),
        Index('ix_activity_logs_category_timestamp', 'category', 'timestamp'),
    )