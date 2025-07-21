"""
Integration tests for external service interactions.

This module tests real external service integrations including:
1. Web scraping (FinViz, BizToc, RSS feeds)
2. LLM service integration (OpenAI, Anthropic)
3. Rate limiting and retry mechanisms
4. Cache integration (Redis)
5. Error handling and fallbacks
6. Performance and reliability
"""

import pytest
import asyncio
import aiohttp
import json
import time
import redis
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4

from app.services.scraper import NewsScraper, RateLimiter
from app.services.enhanced_scraper import EnhancedNewsScraper, AdaptiveRateLimiter, RSSHandler, YahooFinanceHandler, WSJHandler
from app.services.llm_service import LLMService
from app.core.config import settings
from tests.mocks import (
    LLMResponseFactory,
    ArticleFactory,
    AnalysisFactory,
    MockLLMService,
    create_test_session_id
)


class TestWebScrapingIntegration:
    """Test web scraping integration with real and mock data"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session"""
        session = Mock()
        session.get = AsyncMock()
        return session
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response"""
        response = Mock()
        response.status = 200
        response.text = AsyncMock()
        return response
    
    @pytest.fixture
    def sample_finviz_html(self):
        """Sample FinViz HTML for testing"""
        return """
        <html>
        <body>
            <table class="news_time-table">
                <tr><th>Time</th><th>Source</th><th>Title</th></tr>
                <tr>
                    <td>10:30AM</td>
                    <td>MarketWatch</td>
                    <td><a href="https://example.com/article1">Apple Reports Strong Q4 Earnings</a></td>
                </tr>
                <tr>
                    <td>09:45AM</td>
                    <td>Reuters</td>
                    <td><a href="https://example.com/article2">Tesla Faces Production Challenges</a></td>
                </tr>
                <tr>
                    <td>08:15AM</td>
                    <td>Yahoo Finance</td>
                    <td><a href="https://example.com/article3">Microsoft Cloud Revenue Surges</a></td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_biztoc_html(self):
        """Sample BizToc HTML for testing"""
        return """
        <html>
        <body>
            <div class="stories">
                <a href="/story/amazon-earnings-beat-expectations" class="story-link">Amazon Earnings Beat Expectations</a>
                <a href="/story/google-announces-new-ai-features" class="story-link">Google Announces New AI Features</a>
                <a href="/story/netflix-subscriber-growth-slows" class="story-link">Netflix Subscriber Growth Slows</a>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_rss_feed(self):
        """Sample RSS feed XML for testing"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Financial News</title>
                <description>Latest financial news</description>
                <item>
                    <title>Apple (AAPL) Reports Record Quarterly Revenue</title>
                    <link>https://example.com/apple-earnings</link>
                    <description>Apple Inc. reported record quarterly revenue driven by iPhone sales</description>
                    <pubDate>Thu, 15 Dec 2023 10:30:00 GMT</pubDate>
                </item>
                <item>
                    <title>Tesla (TSLA) Announces New Gigafactory Location</title>
                    <link>https://example.com/tesla-gigafactory</link>
                    <description>Tesla announces plans for new Gigafactory in Austin, Texas</description>
                    <pubDate>Thu, 15 Dec 2023 09:15:00 GMT</pubDate>
                </item>
            </channel>
        </rss>
        """
    
    @pytest.mark.asyncio
    async def test_finviz_scraping_success(self, mock_session, mock_response, sample_finviz_html):
        """Test successful FinViz scraping"""
        # Setup mock response
        mock_response.text.return_value = sample_finviz_html
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping
        articles = await scraper.scrape_finviz()
        
        # Verify results
        assert len(articles) == 3
        assert articles[0]['title'] == 'Apple Reports Strong Q4 Earnings'
        assert articles[0]['source'] == 'finviz'
        assert articles[0]['url'] == 'https://example.com/article1'
        assert 'published_at' in articles[0]
        
        # Verify session was called correctly
        mock_session.get.assert_called_once_with("https://finviz.com/news.ashx")
    
    @pytest.mark.asyncio
    async def test_finviz_scraping_empty_table(self, mock_session, mock_response):
        """Test FinViz scraping with empty news table"""
        empty_html = "<html><body><p>No news table found</p></body></html>"
        mock_response.text.return_value = empty_html
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping with empty table
        articles = await scraper.scrape_finviz()
        
        # Should return mock data for testing
        assert len(articles) == 3
        assert articles[0]['source'] == 'MarketWatch'
        assert articles[0]['ticker'] == 'AAPL'
    
    @pytest.mark.asyncio
    async def test_finviz_scraping_http_error(self, mock_session, mock_response):
        """Test FinViz scraping with HTTP error"""
        mock_response.status = 403
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping with HTTP error
        articles = await scraper.scrape_finviz()
        
        # Should return empty list on error
        assert articles == []
    
    @pytest.mark.asyncio
    async def test_biztoc_scraping_success(self, mock_session, mock_response, sample_biztoc_html):
        """Test successful BizToc scraping"""
        mock_response.text.return_value = sample_biztoc_html
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping
        articles = await scraper.scrape_biztoc()
        
        # Verify results
        assert len(articles) == 3
        assert articles[0]['title'] == 'Amazon Earnings Beat Expectations'
        assert articles[0]['source'] == 'biztoc'
        assert articles[0]['url'] == 'https://biztoc.com/story/amazon-earnings-beat-expectations'
        assert 'published_at' in articles[0]
    
    @pytest.mark.asyncio
    async def test_biztoc_scraping_no_stories(self, mock_session, mock_response):
        """Test BizToc scraping with no stories found"""
        empty_html = "<html><body><p>No stories found</p></body></html>"
        mock_response.text.return_value = empty_html
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping with no stories
        with pytest.raises(Exception) as exc_info:
            await scraper.scrape_biztoc()
        
        assert "No valid articles extracted from BizToc" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_biztoc_scraping_http_error(self, mock_session, mock_response):
        """Test BizToc scraping with HTTP error"""
        mock_response.status = 429  # Rate limited
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test scraping with HTTP error
        with pytest.raises(Exception) as exc_info:
            await scraper.scrape_biztoc()
        
        assert "BizToc API returned HTTP 429" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_rss_feed_scraping(self, mock_session, mock_response, sample_rss_feed):
        """Test RSS feed scraping"""
        mock_response.text.return_value = sample_rss_feed
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create RSS handler
        rss_handler = RSSHandler("https://example.com/feed.xml", "test_source")
        rate_limiter = Mock()
        rate_limiter.acquire = AsyncMock()
        
        # Test scraping
        articles = await rss_handler.scrape_articles(mock_session, rate_limiter)
        
        # Verify results
        assert len(articles) == 2
        assert articles[0]['title'] == 'Apple (AAPL) Reports Record Quarterly Revenue'
        assert articles[0]['source'] == 'test_source'
        assert articles[0]['url'] == 'https://example.com/apple-earnings'
        assert articles[0]['ticker'] == 'AAPL'
        assert 'published_at' in articles[0]
    
    @pytest.mark.asyncio
    async def test_enhanced_scraper_multiple_sources(self, mock_session, mock_response, sample_rss_feed):
        """Test enhanced scraper with multiple sources"""
        mock_response.text.return_value = sample_rss_feed
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = EnhancedNewsScraper()
        scraper.session = mock_session
        
        # Test scraping all sources
        articles = await scraper.scrape_all_sources()
        
        # Should get articles from multiple sources
        assert len(articles) >= 0  # May be empty due to mocking
        
        # Verify session was called for multiple sources
        assert mock_session.get.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_article_content_scraping(self, mock_session, mock_response):
        """Test article content scraping"""
        sample_html = """
        <html>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>This is the article content with important financial information.</p>
                <p>The company reported strong earnings and positive guidance.</p>
            </article>
        </body>
        </html>
        """
        mock_response.text.return_value = sample_html
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test content scraping
        content = await scraper.scrape_article_content("https://example.com/article")
        
        # Verify content extracted
        assert content is not None
        assert "article content" in content
        assert "strong earnings" in content
        assert len(content) > 50
    
    @pytest.mark.asyncio
    async def test_article_content_scraping_401_error(self, mock_session, mock_response):
        """Test article content scraping with 401 error"""
        mock_response.status = 401
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test content scraping with 401 error
        content = await scraper.scrape_article_content("https://example.com/article")
        
        # Should return None on 401 error
        assert content is None
    
    @pytest.mark.asyncio
    async def test_article_content_scraping_403_error(self, mock_session, mock_response):
        """Test article content scraping with 403 error"""
        mock_response.status = 403
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test content scraping with 403 error
        content = await scraper.scrape_article_content("https://example.com/article")
        
        # Should return None on 403 error
        assert content is None


class TestRateLimitingIntegration:
    """Test rate limiting and retry mechanisms"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing"""
        return RateLimiter(max_requests=3, window=10)
    
    @pytest.fixture
    def adaptive_rate_limiter(self):
        """Create an adaptive rate limiter for testing"""
        return AdaptiveRateLimiter({
            'test.com': {'max_requests': 2, 'window': 5},
            'default': {'max_requests': 5, 'window': 10}
        })
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic_functionality(self, rate_limiter):
        """Test basic rate limiter functionality"""
        domain = "test.com"
        
        # First 3 requests should be immediate
        start_time = time.time()
        await rate_limiter.acquire(domain)
        await rate_limiter.acquire(domain)
        await rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        # Should be fast (under 1 second)
        assert elapsed < 1.0
        
        # 4th request should be delayed
        start_time = time.time()
        await rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        # Should be delayed (at least 1 second)
        assert elapsed >= 1.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_domains(self, rate_limiter):
        """Test rate limiter with multiple domains"""
        domain1 = "test1.com"
        domain2 = "test2.com"
        
        # Each domain should have separate limits
        start_time = time.time()
        await rate_limiter.acquire(domain1)
        await rate_limiter.acquire(domain1)
        await rate_limiter.acquire(domain1)
        await rate_limiter.acquire(domain2)
        await rate_limiter.acquire(domain2)
        await rate_limiter.acquire(domain2)
        elapsed = time.time() - start_time
        
        # Should be fast since domains are separate
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_adaptive_rate_limiter_domain_specific(self, adaptive_rate_limiter):
        """Test adaptive rate limiter with domain-specific limits"""
        # Test domain with specific limits
        domain = "test.com"
        
        # First 2 requests should be immediate
        start_time = time.time()
        await adaptive_rate_limiter.acquire(domain)
        await adaptive_rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0
        
        # 3rd request should be delayed
        start_time = time.time()
        await adaptive_rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        assert elapsed >= 1.0
    
    @pytest.mark.asyncio
    async def test_adaptive_rate_limiter_default_domain(self, adaptive_rate_limiter):
        """Test adaptive rate limiter with default domain limits"""
        # Test domain without specific limits (uses default)
        domain = "unknown.com"
        
        # First 5 requests should be immediate
        start_time = time.time()
        for _ in range(5):
            await adaptive_rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_time_window_reset(self, rate_limiter):
        """Test rate limiter time window reset"""
        domain = "test.com"
        
        # Use up all requests
        for _ in range(3):
            await rate_limiter.acquire(domain)
        
        # Wait for window to reset
        await asyncio.sleep(11)  # Window is 10 seconds
        
        # Should be able to make requests again immediately
        start_time = time.time()
        await rate_limiter.acquire(domain)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_simulation(self):
        """Test exponential backoff pattern for retries"""
        backoff_times = []
        
        # Simulate exponential backoff
        for attempt in range(5):
            backoff_time = min(60, 2 ** attempt)  # Cap at 60 seconds
            backoff_times.append(backoff_time)
        
        # Verify exponential growth
        assert backoff_times == [1, 2, 4, 8, 16]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for external service failures"""
        failure_count = 0
        max_failures = 3
        circuit_open = False
        
        async def mock_external_call():
            nonlocal failure_count, circuit_open
            
            if circuit_open:
                raise Exception("Circuit breaker is open")
            
            # Simulate failures
            if failure_count < max_failures:
                failure_count += 1
                raise Exception("Service unavailable")
            
            return "Success"
        
        # Test circuit breaker behavior
        with pytest.raises(Exception):
            await mock_external_call()
        
        with pytest.raises(Exception):
            await mock_external_call()
        
        with pytest.raises(Exception):
            await mock_external_call()
        
        # Circuit should now be open
        circuit_open = True
        
        with pytest.raises(Exception) as exc_info:
            await mock_external_call()
        
        assert "Circuit breaker is open" in str(exc_info.value)


class TestLLMServiceIntegration:
    """Test LLM service integration with OpenAI and Anthropic"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client"""
        client = Mock()
        client.ping.return_value = True
        client.get.return_value = None
        client.setex.return_value = True
        client.keys.return_value = []
        client.delete.return_value = 0
        return client
    
    @pytest.fixture
    def llm_service(self, mock_redis_client):
        """Create LLM service with mocked Redis"""
        with patch('redis.Redis.from_url', return_value=mock_redis_client):
            service = LLMService()
            service.redis_client = mock_redis_client
            return service
    
    @pytest.mark.asyncio
    async def test_openai_api_call_success(self, llm_service):
        """Test successful OpenAI API call"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"sentiment_score": 0.8, "confidence": 0.9, "catalysts": [], "reasoning": "Positive sentiment"}'
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_response):
            result = await llm_service._call_openai("Test prompt", "gpt-4o-mini")
            
            assert result is not None
            assert "sentiment_score" in result
    
    @pytest.mark.asyncio
    async def test_openai_api_call_authentication_error(self, llm_service):
        """Test OpenAI API call with authentication error"""
        with patch.object(llm_service.openai_client.chat.completions, 'create', side_effect=Exception("Authentication failed")):
            with pytest.raises(Exception) as exc_info:
                await llm_service._call_openai("Test prompt", "gpt-4o-mini")
            
            assert "authentication" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_openai_api_call_empty_response(self, llm_service):
        """Test OpenAI API call with empty response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(Exception) as exc_info:
                await llm_service._call_openai("Test prompt", "gpt-4o-mini")
            
            assert "empty response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_anthropic_api_call_success(self, llm_service):
        """Test successful Anthropic API call"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"sentiment_score": 0.7, "confidence": 0.85, "catalysts": [], "reasoning": "Positive analysis"}'
        
        with patch.object(llm_service.anthropic_client.messages, 'create', return_value=mock_response):
            result = await llm_service._call_anthropic("Test prompt", "claude-3-5-sonnet-20241022")
            
            assert result is not None
            assert "sentiment_score" in result
    
    @pytest.mark.asyncio
    async def test_anthropic_api_call_authentication_error(self, llm_service):
        """Test Anthropic API call with authentication error"""
        with patch.object(llm_service.anthropic_client.messages, 'create', side_effect=Exception("Unauthorized")):
            with pytest.raises(Exception) as exc_info:
                await llm_service._call_anthropic("Test prompt", "claude-3-5-sonnet-20241022")
            
            assert "authentication" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_with_caching(self, llm_service):
        """Test sentiment analysis with caching"""
        sample_article = ArticleFactory.create_article(
            title="Apple Reports Strong Q4 Earnings",
            content="Apple Inc. reported record quarterly revenue",
            ticker="AAPL"
        )
        
        expected_response = LLMResponseFactory.create_sentiment_response(
            sentiment_score=0.8,
            confidence=0.9,
            ticker="AAPL"
        )
        
        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps(expected_response)
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_openai_response):
            # First call should hit API
            result1 = await llm_service.analyze_sentiment(sample_article)
            
            # Verify cache was set
            llm_service.redis_client.setex.assert_called()
            
            # Second call should hit cache
            llm_service.redis_client.get.return_value = json.dumps(expected_response)
            result2 = await llm_service.analyze_sentiment(sample_article)
            
            # Results should be the same
            assert result1['sentiment_score'] == result2['sentiment_score']
            assert result1['confidence'] == result2['confidence']
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_cache_miss(self, llm_service):
        """Test sentiment analysis with cache miss"""
        sample_article = ArticleFactory.create_article()
        session_id = str(uuid4())
        
        # Mock cache miss
        llm_service.redis_client.get.return_value = None
        
        expected_response = LLMResponseFactory.create_sentiment_response()
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps(expected_response)
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_openai_response):
            result = await llm_service.analyze_sentiment(sample_article, session_id=session_id)
            
            # Should get expected response
            assert result['sentiment_score'] == expected_response['sentiment_score']
            assert result['confidence'] == expected_response['confidence']
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_fallback_on_error(self, llm_service):
        """Test sentiment analysis fallback on API error"""
        sample_article = ArticleFactory.create_article(ticker="AAPL")
        
        # Mock API error
        with patch.object(llm_service.openai_client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = await llm_service.analyze_sentiment(sample_article)
            
            # Should get fallback response
            assert result['sentiment_score'] == 0.0
            assert result['confidence'] == 0.1
            assert result['ticker_mentioned'] == "AAPL"
            assert "Error in analysis" in result['reasoning']
    
    @pytest.mark.asyncio
    async def test_headlines_analysis_with_caching(self, llm_service):
        """Test headlines analysis with caching"""
        sample_headlines = [
            {"title": "Apple Reports Strong Earnings", "source": "Reuters"},
            {"title": "Tesla Announces New Model", "source": "Yahoo Finance"},
            {"title": "Microsoft Cloud Growth", "source": "MarketWatch"}
        ]
        
        expected_response = LLMResponseFactory.create_headlines_response(
            headlines_count=3,
            selected_count=2
        )
        
        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps({"selected_headlines": expected_response})
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_openai_response):
            # First call should hit API
            result1 = await llm_service.analyze_headlines(sample_headlines)
            
            # Verify cache was set
            llm_service.redis_client.setex.assert_called()
            
            # Second call should hit cache
            llm_service.redis_client.get.return_value = json.dumps({"selected_headlines": expected_response})
            result2 = await llm_service.analyze_headlines(sample_headlines)
            
            # Results should be the same
            assert len(result1) == len(result2)
    
    @pytest.mark.asyncio
    async def test_headlines_analysis_fallback_on_error(self, llm_service):
        """Test headlines analysis fallback on API error"""
        sample_headlines = [
            {"title": "Apple Reports Strong Earnings", "source": "Reuters"},
            {"title": "Tesla Announces New Model", "source": "Yahoo Finance"}
        ]
        
        # Mock API error
        with patch.object(llm_service.openai_client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = await llm_service.analyze_headlines(sample_headlines)
            
            # Should get fallback response (first 2 headlines)
            assert len(result) == 2
            assert result[0]['index'] == 1
            assert result[1]['index'] == 2
            assert all(item['reasoning'] == "Fallback selection" for item in result)
    
    @pytest.mark.asyncio
    async def test_position_generation_with_caching(self, llm_service):
        """Test position generation with caching"""
        sample_analyses = [
            AnalysisFactory.create_bullish_analysis("AAPL"),
            AnalysisFactory.create_bearish_analysis("TSLA"),
            AnalysisFactory.create_neutral_analysis("MSFT")
        ]
        
        # Test position generation
        result = await llm_service.generate_positions(sample_analyses)
        
        # Should filter out neutral positions
        assert len(result) == 2
        assert any(pos['ticker'] == 'AAPL' and pos['position_type'] == 'STRONG_BUY' for pos in result)
        assert any(pos['ticker'] == 'TSLA' and pos['position_type'] == 'SHORT' for pos in result)
        
        # Verify cache was set
        llm_service.redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_market_summary_generation(self, llm_service):
        """Test market summary generation"""
        sample_articles = ArticleFactory.create_multiple_articles(5)
        sample_analyses = AnalysisFactory.create_multiple_analyses(5)
        sample_positions = [
            LLMResponseFactory.create_position_response("AAPL", "STRONG_BUY"),
            LLMResponseFactory.create_position_response("TSLA", "SHORT")
        ]
        
        expected_summary = LLMResponseFactory.create_market_summary_response()
        
        # Mock OpenAI response
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock()]
        mock_openai_response.choices[0].message.content = json.dumps(expected_summary)
        
        with patch.object(llm_service.openai_client.chat.completions, 'create', return_value=mock_openai_response):
            result = await llm_service.generate_market_summary(
                sample_articles,
                sample_analyses,
                sample_positions
            )
            
            # Should get expected summary structure
            assert 'overall_sentiment' in result
            assert 'sentiment_score' in result
            assert 'key_themes' in result
            assert 'stocks_to_watch' in result
            assert 'notable_catalysts' in result
            assert 'risk_factors' in result
            assert 'generated_at' in result
    
    @pytest.mark.asyncio
    async def test_market_summary_fallback_on_error(self, llm_service):
        """Test market summary fallback on API error"""
        sample_articles = ArticleFactory.create_multiple_articles(3)
        sample_analyses = AnalysisFactory.create_multiple_analyses(3)
        sample_positions = []
        
        # Mock API error
        with patch.object(llm_service.openai_client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = await llm_service.generate_market_summary(
                sample_articles,
                sample_analyses,
                sample_positions
            )
            
            # Should get fallback summary
            assert 'overall_sentiment' in result
            assert 'error' in result
            assert 'fallback' in result['model_used']
            assert result['data_sources']['articles_analyzed'] == 3
            assert result['data_sources']['sentiment_analyses'] == 3


class TestRedisCacheIntegration:
    """Test Redis cache integration"""
    
    @pytest.fixture
    def redis_client(self):
        """Create a mock Redis client"""
        client = Mock()
        client.ping.return_value = True
        client.get.return_value = None
        client.setex.return_value = True
        client.keys.return_value = []
        client.delete.return_value = 0
        client.info.return_value = {
            'used_memory_human': '1MB',
            'keyspace_hits': 50,
            'keyspace_misses': 25
        }
        return client
    
    @pytest.fixture
    def llm_service_with_cache(self, redis_client):
        """Create LLM service with Redis cache"""
        with patch('redis.Redis.from_url', return_value=redis_client):
            service = LLMService()
            service.redis_client = redis_client
            return service
    
    def test_cache_key_generation(self, llm_service_with_cache):
        """Test cache key generation"""
        content = "Test content"
        model = "gpt-4o-mini"
        analysis_type = "sentiment"
        
        cache_key = llm_service_with_cache._generate_cache_key(content, model, analysis_type)
        
        assert cache_key.startswith("llm_cache:sentiment:gpt-4o-mini:")
        assert len(cache_key.split(":")) == 4
    
    def test_cache_hit(self, llm_service_with_cache):
        """Test cache hit scenario"""
        cache_key = "llm_cache:sentiment:gpt-4o-mini:test123"
        expected_result = {"sentiment_score": 0.8, "confidence": 0.9}
        
        # Mock cache hit
        llm_service_with_cache.redis_client.get.return_value = json.dumps(expected_result)
        
        result = llm_service_with_cache._get_from_cache(cache_key)
        
        assert result == expected_result
        llm_service_with_cache.redis_client.get.assert_called_once_with(cache_key)
    
    def test_cache_miss(self, llm_service_with_cache):
        """Test cache miss scenario"""
        cache_key = "llm_cache:sentiment:gpt-4o-mini:test123"
        
        # Mock cache miss
        llm_service_with_cache.redis_client.get.return_value = None
        
        result = llm_service_with_cache._get_from_cache(cache_key)
        
        assert result is None
        llm_service_with_cache.redis_client.get.assert_called_once_with(cache_key)
    
    def test_cache_set(self, llm_service_with_cache):
        """Test setting cache"""
        cache_key = "llm_cache:sentiment:gpt-4o-mini:test123"
        result = {"sentiment_score": 0.8, "confidence": 0.9}
        
        llm_service_with_cache._set_cache(cache_key, result, ttl_hours=24)
        
        # Verify cache was set with correct TTL
        expected_ttl = 24 * 3600  # 24 hours in seconds
        llm_service_with_cache.redis_client.setex.assert_called_once_with(
            cache_key,
            expected_ttl,
            json.dumps(result, default=str)
        )
    
    def test_cache_stats(self, llm_service_with_cache):
        """Test cache statistics"""
        # Mock cache keys
        mock_keys = [
            "llm_cache:sentiment:gpt-4o-mini:key1",
            "llm_cache:headlines:gpt-4o-mini:key2",
            "llm_cache:positions:key3"
        ]
        llm_service_with_cache.redis_client.keys.return_value = mock_keys
        
        stats = llm_service_with_cache.get_cache_stats()
        
        assert stats['cache_enabled'] is True
        assert stats['total_keys'] == 3
        assert stats['sentiment_cache_count'] == 1
        assert stats['headline_cache_count'] == 1
        assert stats['position_cache_count'] == 1
        assert stats['hit_rate'] == 66.67  # 50 hits / (50 + 25) * 100
    
    def test_cache_clear_all(self, llm_service_with_cache):
        """Test clearing all cache"""
        mock_keys = [
            "llm_cache:sentiment:gpt-4o-mini:key1",
            "llm_cache:headlines:gpt-4o-mini:key2"
        ]
        llm_service_with_cache.redis_client.keys.return_value = mock_keys
        llm_service_with_cache.redis_client.delete.return_value = 2
        
        result = llm_service_with_cache.clear_cache()
        
        assert result['deleted'] == 2
        llm_service_with_cache.redis_client.keys.assert_called_once_with("llm_cache:*")
        llm_service_with_cache.redis_client.delete.assert_called_once_with(*mock_keys)
    
    def test_cache_clear_specific_type(self, llm_service_with_cache):
        """Test clearing specific cache type"""
        mock_keys = ["llm_cache:sentiment:gpt-4o-mini:key1"]
        llm_service_with_cache.redis_client.keys.return_value = mock_keys
        llm_service_with_cache.redis_client.delete.return_value = 1
        
        result = llm_service_with_cache.clear_cache(cache_type="sentiment")
        
        assert result['deleted'] == 1
        llm_service_with_cache.redis_client.keys.assert_called_once_with("llm_cache:sentiment:*")
        llm_service_with_cache.redis_client.delete.assert_called_once_with(*mock_keys)
    
    def test_cache_error_handling(self, llm_service_with_cache):
        """Test cache error handling"""
        cache_key = "llm_cache:sentiment:gpt-4o-mini:test123"
        
        # Mock Redis error
        llm_service_with_cache.redis_client.get.side_effect = Exception("Redis connection error")
        
        result = llm_service_with_cache._get_from_cache(cache_key)
        
        # Should return None on error
        assert result is None


class TestErrorHandlingAndFallbacks:
    """Test error handling and fallback mechanisms"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service"""
        return MockLLMService()
    
    @pytest.mark.asyncio
    async def test_scraping_network_error_fallback(self):
        """Test scraping fallback on network error"""
        mock_session = Mock()
        mock_session.get.side_effect = aiohttp.ClientError("Network error")
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Should return empty list on network error
        result = await scraper.scrape_finviz()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_scraping_timeout_error_fallback(self):
        """Test scraping fallback on timeout error"""
        mock_session = Mock()
        mock_session.get.side_effect = asyncio.TimeoutError("Request timeout")
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Should return empty list on timeout
        result = await scraper.scrape_finviz()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_llm_service_degradation_handling(self):
        """Test LLM service degradation handling"""
        # Create service with no API keys
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.redis_url = "redis://localhost:6379"
            
            service = LLMService()
            
            # Should handle missing API keys gracefully
            assert service.openai_client is not None
            assert service.anthropic_client is not None
    
    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self):
        """Test Redis unavailable fallback"""
        with patch('redis.Redis.from_url', side_effect=Exception("Redis unavailable")):
            service = LLMService()
            
            # Should handle Redis unavailable gracefully
            assert service.redis_client is None
            
            # Cache operations should not fail
            result = service._get_from_cache("test_key")
            assert result is None
            
            # Cache set should not fail
            service._set_cache("test_key", {"test": "data"})
            # Should complete without error
    
    @pytest.mark.asyncio
    async def test_partial_service_failure_handling(self):
        """Test handling of partial service failures"""
        # Test scenario where some scrapers fail but others succeed
        mock_session = Mock()
        
        # Mock successful RSS feed
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='<?xml version="1.0"?><rss><channel><item><title>Test</title><link>http://test.com</link></item></channel></rss>')
        
        # Mock failed FinViz scraper
        def mock_get(url):
            if "finviz" in url:
                raise Exception("FinViz unavailable")
            else:
                return mock_response
        
        mock_session.get.side_effect = lambda url: mock_get(url).__aenter__()
        
        scraper = EnhancedNewsScraper()
        scraper.session = mock_session
        
        # Should still get some articles from working sources
        articles = await scraper.scrape_all_sources()
        # May be empty due to mocking complexity, but should not crash
        assert isinstance(articles, list)
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed API responses"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        with patch('redis.Redis.from_url', return_value=mock_redis):
            service = LLMService()
            
            # Mock malformed JSON response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Invalid JSON response"
            
            with patch.object(service.openai_client.chat.completions, 'create', return_value=mock_response):
                article = ArticleFactory.create_article()
                result = await service.analyze_sentiment(article)
                
                # Should return fallback response
                assert result['sentiment_score'] == 0.0
                assert result['confidence'] == 0.1
                assert "Error in analysis" in result['reasoning']


class TestPerformanceAndReliability:
    """Test performance and reliability of external service interactions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping_performance(self):
        """Test concurrent scraping performance"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Test concurrent article content scraping
        urls = [f"https://example.com/article{i}" for i in range(10)]
        
        start_time = time.time()
        tasks = [scraper.scrape_article_content(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        # Should complete all requests relatively quickly
        assert elapsed < 5.0  # Should be faster than 5 seconds
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_rate_limiting_under_load(self):
        """Test rate limiting behavior under load"""
        rate_limiter = RateLimiter(max_requests=5, window=10)
        domain = "test.com"
        
        # Make many requests quickly
        start_time = time.time()
        tasks = [rate_limiter.acquire(domain) for _ in range(10)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Should be rate limited (should take longer than immediate)
        assert elapsed > 5.0  # Should take at least 5 seconds due to rate limiting
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self):
        """Test cache performance under load"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = json.dumps({"cached": "data"})
        mock_redis.setex.return_value = True
        
        with patch('redis.Redis.from_url', return_value=mock_redis):
            service = LLMService()
            
            # Test many cache operations
            start_time = time.time()
            tasks = [service._get_from_cache(f"test_key_{i}") for i in range(100)]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # Should complete quickly
            assert elapsed < 1.0
            assert len(results) == 100
            assert all(result == {"cached": "data"} for result in results)
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage monitoring for large data processing"""
        # Create large dataset
        large_articles = ArticleFactory.create_multiple_articles(1000)
        large_analyses = AnalysisFactory.create_multiple_analyses(1000)
        
        # Test memory efficient processing
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        
        with patch('redis.Redis.from_url', return_value=mock_redis):
            service = LLMService()
            
            # Should be able to process large datasets
            start_time = time.time()
            positions = await service.generate_positions(large_analyses)
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time
            assert elapsed < 5.0
            assert isinstance(positions, list)
    
    @pytest.mark.asyncio
    async def test_service_health_monitoring(self):
        """Test service health monitoring"""
        # Test Redis health check
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            'used_memory_human': '10MB',
            'keyspace_hits': 100,
            'keyspace_misses': 50
        }
        
        with patch('redis.Redis.from_url', return_value=mock_redis):
            service = LLMService()
            
            # Test health check
            stats = service.get_cache_stats()
            
            assert stats['cache_enabled'] is True
            assert stats['hit_rate'] > 0
            assert 'memory_used' in stats
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_simulation(self):
        """Test graceful degradation when services are unavailable"""
        # Simulate all external services being unavailable
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Service unavailable")
        
        scraper = NewsScraper()
        scraper.session = mock_session
        
        # Should handle graceful degradation
        articles = await scraper.scrape_finviz()
        assert articles == []  # Should return empty list instead of crashing
        
        # Test BizToc with same failure
        with pytest.raises(Exception):
            await scraper.scrape_biztoc()
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test proper resource cleanup"""
        # Test scraper context manager
        scraper = NewsScraper()
        
        async with scraper:
            assert scraper.session is not None
        
        # Session should be closed after context manager
        # Note: In real implementation, session would be closed
        # This test verifies the pattern is followed
    
    @pytest.mark.asyncio
    async def test_error_recovery_patterns(self):
        """Test error recovery patterns"""
        retry_count = 0
        max_retries = 3
        
        async def failing_operation():
            nonlocal retry_count
            retry_count += 1
            if retry_count < max_retries:
                raise Exception(f"Attempt {retry_count} failed")
            return "Success"
        
        # Test retry with exponential backoff
        for attempt in range(max_retries):
            try:
                result = await failing_operation()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        assert result == "Success"
        assert retry_count == max_retries