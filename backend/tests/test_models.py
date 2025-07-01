import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.article import Article
from app.models.analysis import Analysis
from app.models.position import Position, PositionType


def test_article_creation(db_session):
    article = Article(
        url="https://example.com/test-article",
        title="Test Article",
        content="This is test content",
        source="test",
        ticker="AAPL"
    )
    
    db_session.add(article)
    db_session.commit()
    
    assert article.id is not None
    assert article.url == "https://example.com/test-article"
    assert article.title == "Test Article"
    assert article.source == "test"
    assert article.ticker == "AAPL"
    assert article.is_processed is False


def test_analysis_creation(db_session):
    # First create an article
    article = Article(
        url="https://example.com/test-article",
        title="Test Article",
        source="test"
    )
    db_session.add(article)
    db_session.commit()
    
    # Create analysis
    analysis = Analysis(
        article_id=article.id,
        ticker="AAPL",
        sentiment_score=0.8,
        confidence=0.9,
        catalysts=[{"type": "earnings", "description": "Beat expectations"}],
        reasoning="Strong earnings beat",
        llm_model="gpt-4"
    )
    
    db_session.add(analysis)
    db_session.commit()
    
    assert analysis.id is not None
    assert analysis.article_id == article.id
    assert analysis.sentiment_score == 0.8
    assert analysis.confidence == 0.9
    assert len(analysis.catalysts) == 1


def test_position_creation(db_session):
    session_id = uuid4()
    
    position = Position(
        ticker="AAPL",
        position_type=PositionType.STRONG_BUY,
        confidence=0.85,
        reasoning="Strong bullish sentiment",
        analysis_session_id=session_id
    )
    
    db_session.add(position)
    db_session.commit()
    
    assert position.id is not None
    assert position.ticker == "AAPL"
    assert position.position_type == PositionType.STRONG_BUY
    assert position.confidence == 0.85
    assert position.analysis_session_id == session_id