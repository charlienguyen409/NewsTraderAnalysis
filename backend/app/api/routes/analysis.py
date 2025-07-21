from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from ...core.database import get_db
from ...schemas.analysis_request import AnalysisRequest, AnalysisResponse
from ...services.analysis_service import AnalysisService
from ...services.llm_service import LLMService
from ...services.crud import article_crud, analysis_crud, position_crud, market_summary_crud

router = APIRouter()


@router.post("/start/", response_model=dict)
@router.post("/start", response_model=dict)  # Handle requests without trailing slash
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session_id = uuid4()
    
    analysis_service = AnalysisService(db)
    background_tasks.add_task(
        analysis_service.run_analysis,
        session_id=session_id,
        request=request
    )
    
    return {
        "session_id": session_id,
        "message": "Analysis started",
        "status": "processing"
    }


@router.post("/headlines/", response_model=dict)
@router.post("/headlines", response_model=dict)  # Handle requests without trailing slash
async def start_headline_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session_id = uuid4()
    
    analysis_service = AnalysisService(db)
    background_tasks.add_task(
        analysis_service.run_headline_analysis,
        session_id=session_id,
        request=request
    )
    
    return {
        "session_id": session_id,
        "message": "Headline analysis started",
        "status": "processing"
    }


@router.get("/status/{session_id}/")
async def get_analysis_status(session_id: UUID, db: Session = Depends(get_db)):
    analysis_service = AnalysisService(db)
    status = analysis_service.get_analysis_status(session_id)
    return status


@router.get("/market-summary/", response_model=Dict[str, Any])
@router.get("/market-summary", response_model=Dict[str, Any])  # Handle requests without trailing slash
async def get_latest_market_summary(db: Session = Depends(get_db)):
    """Get the latest cached market summary from the database"""
    
    # Fetch the most recent market summary from the database
    latest_summary = market_summary_crud.get_latest_market_summary(db)
    
    if not latest_summary:
        return {
            "message": "No market analysis has been run yet.",
            "summary": "Please trigger a market analysis first to generate a market summary.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": {
                "articles_analyzed": 0,
                "sentiment_analyses": 0,
                "positions_generated": 0
            },
            "analysis_session": None,
            "analysis_type": None,
            "model_used": None
        }
    
    # Build response with cached summary data and metadata
    response = {
        **latest_summary.summary_data,  # Unpack the LLM-generated summary
        "analysis_session_id": latest_summary.session_id,
        "analysis_type": latest_summary.analysis_type.value,
        "model_used": latest_summary.model_used,
        "data_sources": latest_summary.data_sources,
        "cache_metadata": {
            "summary_id": latest_summary.id,
            "generated_at": latest_summary.generated_at.isoformat(),
            "is_cached": True,
            "cache_age_hours": round(
                (datetime.now(timezone.utc) - latest_summary.generated_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600, 1
            )
        }
    }
    
    return response