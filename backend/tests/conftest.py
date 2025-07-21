import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.analysis_service import AnalysisService
from .mocks import (
    LLMResponseFactory,
    CatalystFactory,
    ArticleFactory,
    AnalysisFactory,
    MockLLMService,
    TestDatasets,
    create_test_session_id
)

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Analysis service fixtures
@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing"""
    return MockLLMService()


@pytest.fixture
def mock_analysis_service(db_session):
    """Create an analysis service with mocked dependencies"""
    with patch('app.services.analysis_service.NewsScraper'), \
         patch('app.services.analysis_service.LLMService') as mock_llm_class:
        
        # Create mock LLM service instance
        mock_llm_service = MockLLMService()
        mock_llm_class.return_value = mock_llm_service
        
        # Create analysis service with mocked dependencies
        analysis_service = AnalysisService(db_session)
        analysis_service.llm_service = mock_llm_service
        
        yield analysis_service


@pytest.fixture
def sample_articles():
    """Create sample articles for testing"""
    return ArticleFactory.create_multiple_articles(10)


@pytest.fixture
def sample_analyses():
    """Create sample analyses for testing"""
    return AnalysisFactory.create_multiple_analyses(10)


@pytest.fixture
def sample_catalysts():
    """Create sample catalysts for testing"""
    return CatalystFactory.create_multiple_catalysts(5)


@pytest.fixture
def test_session_id():
    """Create a test session ID"""
    return create_test_session_id()


@pytest.fixture
def earnings_season_dataset():
    """Get earnings season test dataset"""
    return TestDatasets.get_earnings_season_dataset()


@pytest.fixture
def fda_approval_dataset():
    """Get FDA approval test dataset"""
    return TestDatasets.get_fda_approval_dataset()


@pytest.fixture
def mixed_sentiment_dataset():
    """Get mixed sentiment test dataset"""
    return TestDatasets.get_mixed_sentiment_dataset()


# Mock response fixtures
@pytest.fixture
def mock_sentiment_response():
    """Create a mock sentiment analysis response"""
    return LLMResponseFactory.create_sentiment_response()


@pytest.fixture
def mock_headlines_response():
    """Create a mock headlines filtering response"""
    return LLMResponseFactory.create_headlines_response()


@pytest.fixture
def mock_position_response():
    """Create a mock position recommendation response"""
    return LLMResponseFactory.create_position_response()


@pytest.fixture
def mock_market_summary_response():
    """Create a mock market summary response"""
    return LLMResponseFactory.create_market_summary_response()


@pytest.fixture
def mock_error_response():
    """Create a mock error response"""
    return LLMResponseFactory.create_error_response()


# Utility fixtures
@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client"""
    redis_mock = Mock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.keys.return_value = []
    redis_mock.delete.return_value = 0
    return redis_mock


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    openai_mock = Mock()
    openai_mock.chat.completions.create = AsyncMock()
    return openai_mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    anthropic_mock = Mock()
    anthropic_mock.messages.create = AsyncMock()
    return anthropic_mock