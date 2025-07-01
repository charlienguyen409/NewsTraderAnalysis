from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...core.database import get_db
from ...services.activity_log_service import ActivityLogService
from ...schemas.activity_log import ActivityLogResponse, ActivityLogSummary

router = APIRouter()


@router.get("/", response_model=List[ActivityLogResponse])
@router.get("", response_model=List[ActivityLogResponse])  # Handle requests without trailing slash
async def get_activity_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(INFO|WARNING|ERROR)$"),
    category: Optional[str] = Query(None, regex="^(scraping|llm|analysis|system)$"),
    session_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get recent activity logs with optional filtering"""
    activity_service = ActivityLogService(db)
    logs = activity_service.get_recent_logs(
        limit=limit,
        level=level,
        category=category,
        session_id=session_id
    )
    return logs


@router.get("/summary/", response_model=ActivityLogSummary)
@router.get("/summary", response_model=ActivityLogSummary)  # Handle requests without trailing slash
async def get_error_summary(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db)
):
    """Get error summary for the last N hours"""
    activity_service = ActivityLogService(db)
    summary = activity_service.get_error_summary(hours=hours)
    return summary


@router.get("/errors/", response_model=List[ActivityLogResponse])
@router.get("/errors", response_model=List[ActivityLogResponse])  # Handle requests without trailing slash
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None, regex="^(scraping|llm|analysis|system)$"),
    session_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get recent errors only"""
    activity_service = ActivityLogService(db)
    logs = activity_service.get_recent_logs(
        limit=limit,
        level="ERROR",
        category=category,
        session_id=session_id
    )
    return logs