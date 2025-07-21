"""
Integration test configuration and fixtures for external service tests.

This module provides shared fixtures and configuration for integration tests
of external service interactions.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional
import redis
import aiohttp

from tests.mocks import (
    MockHTMLResponseFactory,
    MockRSSResponseFactory,
    MockAPIResponseFactory,
    MockRedisFactory,
    MockSessionFactory,
    MockScenarios,
    MockServiceConfig,
    ServiceStatus,
    create_mock_environment
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing"""
    return MockRedisFactory.create_redis_client(
        available=True,
        hit_rate=0.8,
        memory_usage="10MB"
    )


@pytest.fixture
def mock_redis_unavailable():
    """Create a mock Redis client that's unavailable"""
    return MockRedisFactory.create_redis_client(available=False)


@pytest.fixture
def mock_redis_with_data():
    """Create a mock Redis client with pre-populated data"""
    cache_data = {
        "llm_cache:sentiment:gpt-4o-mini:test123": {
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "catalysts": [],
            "reasoning": "Cached analysis"
        },
        "llm_cache:headlines:gpt-4o-mini:test456": {
            "selected_headlines": [
                {"index": 1, "reasoning": "Cached headline selection"}
            ]
        }
    }
    return MockRedisFactory.create_cache_with_data(cache_data)


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session for testing"""
    return MockSessionFactory.create_session(
        response_factory=MockHTMLResponseFactory.create_finviz_response,
        status_code=200,
        response_delay=0.1
    )


@pytest.fixture
def mock_failing_session():
    """Create a mock aiohttp session that fails"""
    return MockSessionFactory.create_failing_session()


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    client = Mock()
    client.chat.completions.create = AsyncMock()
    
    # Default successful response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"sentiment_score": 0.8, "confidence": 0.9, "catalysts": [], "reasoning": "Test analysis"}'
    
    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    client = Mock()
    client.messages.create = AsyncMock()
    
    # Default successful response
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = '{"sentiment_score": 0.7, "confidence": 0.85, "catalysts": [], "reasoning": "Test analysis"}'
    
    client.messages.create.return_value = mock_response
    return client


@pytest.fixture
def sample_finviz_html():
    """Sample FinViz HTML response for testing"""
    return MockHTMLResponseFactory.create_finviz_response(articles_count=5)


@pytest.fixture
def sample_biztoc_html():
    """Sample BizToc HTML response for testing"""
    return MockHTMLResponseFactory.create_biztoc_response(articles_count=8)


@pytest.fixture
def sample_rss_feed():
    """Sample RSS feed XML for testing"""
    return MockRSSResponseFactory.create_reuters_feed()


@pytest.fixture
def sample_article_content():
    """Sample article content HTML for testing"""
    return MockHTMLResponseFactory.create_article_content_response(
        title="Test Article",
        content="This is a test article about financial markets."
    )


@pytest.fixture
def healthy_services_scenario():
    """Scenario with all services healthy"""
    return MockScenarios.healthy_services()


@pytest.fixture
def degraded_services_scenario():
    """Scenario with some services degraded"""
    return MockScenarios.degraded_services()


@pytest.fixture
def services_down_scenario():
    """Scenario with services down"""
    return MockScenarios.services_down()


@pytest.fixture
def rate_limited_scenario():
    """Scenario with rate limited services"""
    return MockScenarios.rate_limited_services()


@pytest.fixture
def mock_environment(healthy_services_scenario):
    """Create a complete mock environment"""
    return create_mock_environment(healthy_services_scenario)


@pytest.fixture
def integration_config():
    """Integration test configuration"""
    return {
        "timeout": 30,
        "max_retries": 3,
        "rate_limit": {
            "requests_per_minute": 10,
            "burst_size": 5
        },
        "cache": {
            "enabled": True,
            "ttl": 3600,
            "max_size": 1000
        },
        "scraping": {
            "max_concurrent": 10,
            "request_timeout": 30,
            "retry_delay": 1
        }
    }


@pytest.fixture
def test_environment_vars():
    """Set up test environment variables"""
    original_vars = {}
    test_vars = {
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "REDIS_URL": "redis://localhost:6379",
        "SCRAPING_RATE_LIMIT": "10",
        "MAX_POSITIONS": "10",
        "MIN_CONFIDENCE": "0.7"
    }
    
    # Save original values
    for key in test_vars:
        original_vars[key] = os.environ.get(key)
    
    # Set test values
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, original_value in original_vars.items():
        if original_value is not None:
            os.environ[key] = original_value
        elif key in os.environ:
            del os.environ[key]


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = Mock()
    settings.openai_api_key = "test_openai_key"
    settings.anthropic_api_key = "test_anthropic_key"
    settings.redis_url = "redis://localhost:6379"
    settings.scraping_rate_limit = 10
    settings.max_positions = 10
    settings.min_confidence = 0.7
    return settings


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "web_scraping: marks tests as web scraping integration tests"
    )
    config.addinivalue_line(
        "markers", "llm_integration: marks tests as LLM service integration tests"
    )
    config.addinivalue_line(
        "markers", "rate_limiting: marks tests as rate limiting tests"
    )
    config.addinivalue_line(
        "markers", "cache_integration: marks tests as cache integration tests"
    )
    config.addinivalue_line(
        "markers", "error_handling: marks tests as error handling tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "real_api: marks tests that require real API calls"
    )
    config.addinivalue_line(
        "markers", "mock_only: marks tests that use only mocks"
    )
    config.addinivalue_line(
        "markers", "load_test: marks tests as load tests"
    )
    config.addinivalue_line(
        "markers", "network_simulation: marks tests that simulate network conditions"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    # Add markers based on test names
    for item in items:
        # Mark slow tests
        if "performance" in item.name or "load_test" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in item.name or "test_external" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark web scraping tests
        if "scraping" in item.name or "finviz" in item.name or "biztoc" in item.name:
            item.add_marker(pytest.mark.web_scraping)
        
        # Mark LLM integration tests
        if "llm" in item.name or "openai" in item.name or "anthropic" in item.name:
            item.add_marker(pytest.mark.llm_integration)
        
        # Mark rate limiting tests
        if "rate_limit" in item.name or "backoff" in item.name:
            item.add_marker(pytest.mark.rate_limiting)
        
        # Mark cache integration tests
        if "cache" in item.name or "redis" in item.name:
            item.add_marker(pytest.mark.cache_integration)
        
        # Mark error handling tests
        if "error" in item.name or "fallback" in item.name or "degradation" in item.name:
            item.add_marker(pytest.mark.error_handling)
        
        # Mark performance tests
        if "performance" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.performance)
        
        # Mark real API tests
        if "real_api" in item.name:
            item.add_marker(pytest.mark.real_api)
        
        # Mark mock-only tests
        if "mock" in item.name and "real_api" not in item.name:
            item.add_marker(pytest.mark.mock_only)
        
        # Mark load tests
        if "load" in item.name:
            item.add_marker(pytest.mark.load_test)
        
        # Mark network simulation tests
        if "network" in item.name or "timeout" in item.name:
            item.add_marker(pytest.mark.network_simulation)


# Fixtures for real API testing (when enabled)
@pytest.fixture
def real_redis_client():
    """Create a real Redis client for integration testing"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        yield client
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def real_openai_client():
    """Create a real OpenAI client for integration testing"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "test_openai_key":
        pytest.skip("Real OpenAI API key not available")
    
    import openai
    client = openai.AsyncOpenAI(api_key=api_key)
    yield client


@pytest.fixture
def real_anthropic_client():
    """Create a real Anthropic client for integration testing"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "test_anthropic_key":
        pytest.skip("Real Anthropic API key not available")
    
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key)
    yield client


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test"""
    yield
    
    # Clean up any test files created
    import shutil
    from pathlib import Path
    
    test_files = [
        "tests/integration/external_tests.log",
        "tests/integration/external_test_report.html",
        "htmlcov"
    ]
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)


# Performance monitoring fixtures
@pytest.fixture
def performance_monitor():
    """Monitor test performance"""
    import time
    import psutil
    
    start_time = time.time()
    process = psutil.Process()
    start_memory = process.memory_info().rss
    
    yield {
        "start_time": start_time,
        "start_memory": start_memory,
        "process": process
    }
    
    end_time = time.time()
    end_memory = process.memory_info().rss
    
    duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    if duration > 5.0:  # Warn for slow tests
        print(f"\nWarning: Test took {duration:.2f} seconds")
    
    if memory_delta > 50 * 1024 * 1024:  # Warn for high memory usage (50MB)
        print(f"\nWarning: Test used {memory_delta / 1024 / 1024:.2f} MB of memory")


# Async context manager for test isolation
@pytest.fixture
async def isolated_test_context():
    """Provide isolated test context for async tests"""
    # Setup isolation
    original_cwd = os.getcwd()
    
    try:
        yield
    finally:
        # Cleanup isolation
        os.chdir(original_cwd)
        
        # Cancel any remaining tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        for task in tasks:
            task.cancel()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)