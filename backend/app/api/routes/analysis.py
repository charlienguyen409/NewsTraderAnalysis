from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from ...core.database import get_db
from ...schemas.analysis_request import AnalysisRequest, AnalysisResponse
from ...services.analysis_service import AnalysisService

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