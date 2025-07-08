from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from ...core.database import get_db
from ...schemas.analysis_request import AnalysisRequest, AnalysisResponse
from ...services.analysis_service import AnalysisService
from ...services.llm_service import LLMService
from ...services.crud import article_crud, analysis_crud, position_crud

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
    """Get the latest market summary based on recent analysis data"""
    
    # Get recent articles from the last 24 hours
    from ...models.article import Article
    from ...models.analysis import Analysis
    from ...models.position import Position
    
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_articles = db.query(Article).filter(
        Article.scraped_at >= since
    ).order_by(Article.scraped_at.desc()).limit(50).all()
    
    # Get recent analyses from the last 24 hours
    recent_analyses = db.query(Analysis).filter(
        Analysis.created_at >= since
    ).order_by(Analysis.created_at.desc()).limit(100).all()
    
    # Get recent positions from the last 24 hours
    recent_positions = db.query(Position).filter(
        Position.created_at >= since
    ).order_by(Position.created_at.desc()).limit(20).all()
    
    if not recent_articles and not recent_analyses:
        return {
            "summary": "No recent analysis data available for market summary.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": {
                "articles_analyzed": 0,
                "sentiment_analyses": 0,
                "positions_generated": 0
            }
        }
    
    # Convert to dict format for LLM
    articles_data = []
    for article in recent_articles:
        articles_data.append({
            'title': article.title,
            'source': article.source,
            'ticker': article.ticker,
            'content': article.content,
            'scraped_at': article.scraped_at.isoformat()
        })
    
    analyses_data = []
    for analysis in recent_analyses:
        analyses_data.append({
            'ticker': analysis.ticker,
            'sentiment_score': analysis.sentiment_score,
            'confidence': analysis.confidence,
            'catalysts': analysis.catalysts,
            'reasoning': analysis.reasoning
        })
    
    positions_data = []
    for position in recent_positions:
        positions_data.append({
            'ticker': position.ticker,
            'position_type': position.position_type.value if hasattr(position.position_type, 'value') else str(position.position_type),
            'confidence': position.confidence,
            'reasoning': position.reasoning
        })
    
    # Generate market summary using LLM
    llm_service = LLMService()
    try:
        from ...config.models import DEFAULT_MODEL
        summary = await llm_service.generate_market_summary(
            articles_data, analyses_data, positions_data, DEFAULT_MODEL
        )
        return summary
    except Exception as e:
        return {
            "error": str(e),
            "summary": f"Unable to generate market summary: {str(e)}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": {
                "articles_analyzed": len(articles_data),
                "sentiment_analyses": len(analyses_data),
                "positions_generated": len(positions_data)
            }
        }