from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID


class ActivityLogBase(BaseModel):
    level: str
    category: str
    action: str
    message: str
    details: Dict[str, Any] = {}
    session_id: Optional[UUID] = None


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogResponse(ActivityLogBase):
    id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True


class ActivityLogSummary(BaseModel):
    total_errors: int
    errors_by_category: Dict[str, int]
    time_window_hours: int