import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog
from ..core.database import get_db


class ActivityLogService:
    """Service for logging and retrieving activity/error logs"""
    
    def __init__(self, db: Session):
        self.db = db

    def log_activity(
        self,
        level: str,
        category: str, 
        action: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None
    ) -> ActivityLog:
        """Log an activity/error to the database"""
        
        activity = ActivityLog(
            level=level.upper(),
            category=category,
            action=action,
            message=message,
            details=details or {},
            session_id=session_id
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        # Also log to standard logging
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.log(log_level, f"[{category}:{action}] {message}")
        
        return activity

    def log_error(
        self,
        category: str,
        action: str, 
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None
    ) -> ActivityLog:
        """Log an error with context"""
        
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        return self.log_activity(
            level="ERROR",
            category=category,
            action=action,
            message=f"{action} failed: {str(error)}",
            details=details,
            session_id=session_id
        )

    def log_scraping_error(
        self,
        source: str,
        error: Exception,
        url: Optional[str] = None,
        session_id: Optional[UUID] = None
    ) -> ActivityLog:
        """Log scraping-specific errors"""
        
        context = {"source": source}
        if url:
            context["url"] = url
            
        return self.log_error(
            category="scraping",
            action=f"scrape_{source}",
            error=error,
            context=context,
            session_id=session_id
        )

    def log_llm_error(
        self,
        model: str,
        error: Exception,
        prompt_type: str = "unknown",
        session_id: Optional[UUID] = None
    ) -> ActivityLog:
        """Log LLM API errors"""
        
        context = {
            "model": model,
            "prompt_type": prompt_type
        }
        
        return self.log_error(
            category="llm",
            action="api_call",
            error=error,
            context=context,
            session_id=session_id
        )

    def log_analysis_progress(
        self,
        action: str,
        message: str,
        session_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Log analysis progress"""
        
        return self.log_activity(
            level="INFO",
            category="analysis",
            action=action,
            message=message,
            details=details,
            session_id=session_id
        )

    def log_scraping_start(
        self,
        source: str,
        session_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Log start of scraping from a source"""
        
        return self.log_activity(
            level="INFO",
            category="scraping",
            action=f"start_{source}",
            message=f"Starting to scrape news from {source.title()}",
            details=details,
            session_id=session_id
        )

    def log_scraping_success(
        self,
        source: str,
        article_count: int,
        session_id: UUID,
        headlines: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Log successful scraping with headlines"""
        
        log_details = details or {}
        log_details.update({
            "source": source,
            "article_count": article_count,
            "headlines": headlines[:10] if headlines else []  # Limit to first 10 headlines
        })
        
        return self.log_activity(
            level="INFO",
            category="scraping",
            action=f"scraped_{source}",
            message=f"Successfully scraped {article_count} articles from {source.title()}",
            details=log_details,
            session_id=session_id
        )

    def log_headline_filtering(
        self,
        total_articles: int,
        selected_articles: int,
        session_id: UUID,
        selected_headlines: Optional[List[Dict]] = None,
        reasoning: Optional[str] = None
    ) -> ActivityLog:
        """Log headline filtering process"""
        
        details = {
            "total_articles": total_articles,
            "selected_articles": selected_articles,
            "selection_rate": f"{(selected_articles/total_articles*100):.1f}%" if total_articles > 0 else "0%",
            "selected_headlines": selected_headlines[:5] if selected_headlines else [],  # Show first 5
            "llm_reasoning": reasoning
        }
        
        return self.log_activity(
            level="INFO",
            category="analysis",
            action="filter_headlines",
            message=f"LLM filtered {selected_articles} relevant headlines from {total_articles} total articles",
            details=details,
            session_id=session_id
        )

    def log_content_scraping(
        self,
        url: str,
        success: bool,
        session_id: UUID,
        content_length: Optional[int] = None,
        error: Optional[str] = None
    ) -> ActivityLog:
        """Log individual article content scraping"""
        
        details = {
            "url": url,
            "success": success,
            "content_length": content_length,
            "error": error
        }
        
        if success:
            message = f"Successfully scraped content from {url} ({content_length} chars)"
            level = "INFO"
        else:
            message = f"Failed to scrape content from {url}: {error}"
            level = "WARNING"
        
        return self.log_activity(
            level=level,
            category="scraping",
            action="scrape_content",
            message=message,
            details=details,
            session_id=session_id
        )

    def log_llm_analysis(
        self,
        model: str,
        action: str,
        article_title: str,
        session_id: UUID,
        analysis_result: Optional[Dict] = None,
        reasoning: Optional[str] = None
    ) -> ActivityLog:
        """Log LLM analysis of individual articles"""
        
        details = {
            "model": model,
            "article_title": article_title,
            "analysis_result": analysis_result,
            "reasoning": reasoning
        }
        
        return self.log_activity(
            level="INFO",
            category="llm",
            action=action,
            message=f"LLM analyzed article: {article_title[:100]}...",
            details=details,
            session_id=session_id
        )

    def log_position_generation(
        self,
        ticker: str,
        position_type: str,
        confidence: float,
        session_id: UUID,
        reasoning: Optional[str] = None,
        catalyst: Optional[str] = None
    ) -> ActivityLog:
        """Log trading position generation"""
        
        details = {
            "ticker": ticker,
            "position_type": position_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "catalyst": catalyst
        }
        
        return self.log_activity(
            level="INFO",
            category="analysis",
            action="generate_position",
            message=f"Generated {position_type} position for {ticker} (confidence: {confidence:.2f})",
            details=details,
            session_id=session_id
        )

    def get_recent_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        category: Optional[str] = None,
        session_id: Optional[UUID] = None
    ) -> List[ActivityLog]:
        """Get recent activity logs with optional filtering"""
        
        query = self.db.query(ActivityLog).order_by(ActivityLog.timestamp.desc())
        
        if level:
            query = query.filter(ActivityLog.level == level.upper())
        if category:
            query = query.filter(ActivityLog.category == category)
        if session_id:
            query = query.filter(ActivityLog.session_id == session_id)
            
        return query.limit(limit).all()

    def get_error_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get summary of errors in the last N hours"""
        
        from sqlalchemy import func
        from datetime import datetime, timezone, timedelta
        
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Count errors by category
        error_counts = (
            self.db.query(
                ActivityLog.category,
                func.count(ActivityLog.id).label('count')
            )
            .filter(
                ActivityLog.level == 'ERROR',
                ActivityLog.timestamp >= since
            )
            .group_by(ActivityLog.category)
            .all()
        )
        
        # Get total error count
        total_errors = (
            self.db.query(func.count(ActivityLog.id))
            .filter(
                ActivityLog.level == 'ERROR',
                ActivityLog.timestamp >= since
            )
            .scalar()
        )
        
        return {
            "total_errors": total_errors,
            "errors_by_category": {row.category: row.count for row in error_counts},
            "time_window_hours": hours
        }