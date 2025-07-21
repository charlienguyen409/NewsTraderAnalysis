"""
Additional mock factories for external service testing.

This module provides comprehensive mock objects for:
1. Web scraping responses (HTML, RSS, JSON)
2. Rate limiting scenarios
3. Network error simulations
4. Cache behavior mocking
5. API response variations
"""

import json
import asyncio
import aiohttp
import time
import random
from typing import Dict, List, Any, Optional, Union, Callable
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(Enum):
    """Service availability statuses"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class NetworkError(Enum):
    """Network error types"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    DNS_ERROR = "dns_error"
    SSL_ERROR = "ssl_error"
    HTTP_ERROR = "http_error"


@dataclass
class MockServiceConfig:
    """Configuration for mock service behavior"""
    status: ServiceStatus = ServiceStatus.AVAILABLE
    response_delay: float = 0.1
    error_rate: float = 0.0
    rate_limit_requests: int = 10
    rate_limit_window: int = 60
    cache_enabled: bool = True


class MockHTMLResponseFactory:
    """Factory for creating mock HTML responses"""
    
    @staticmethod
    def create_finviz_response(articles_count: int = 10) -> str:
        """Create a mock FinViz news page response"""
        articles_html = ""
        for i in range(articles_count):
            time_str = f"{9 + i}:30AM" if i < 3 else f"{10 + i - 3}:15AM"
            source = random.choice(["MarketWatch", "Reuters", "Yahoo Finance", "Bloomberg"])
            title = f"Stock News Article {i + 1} - Market Update"
            url = f"https://example.com/article{i + 1}"
            
            articles_html += f"""
            <tr>
                <td>{time_str}</td>
                <td>{source}</td>
                <td><a href="{url}">{title}</a></td>
            </tr>
            """
        
        return f"""
        <html>
        <head><title>FinViz News</title></head>
        <body>
            <table class="news_time-table">
                <tr>
                    <th>Time</th>
                    <th>Source</th>
                    <th>Title</th>
                </tr>
                {articles_html}
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def create_biztoc_response(articles_count: int = 15) -> str:
        """Create a mock BizToc page response"""
        articles_html = ""
        for i in range(articles_count):
            title = f"Business News Story {i + 1}"
            url = f"/story/business-news-story-{i + 1}"
            
            articles_html += f"""
            <a href="{url}" class="story-link">{title}</a>
            """
        
        return f"""
        <html>
        <head><title>BizToc</title></head>
        <body>
            <div class="stories">
                {articles_html}
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def create_article_content_response(
        title: str = "Sample Article",
        content: str = None,
        has_paywall: bool = False
    ) -> str:
        """Create a mock article content response"""
        if content is None:
            content = f"""
            This is a sample article about {title}.
            
            The article contains important financial information and market analysis.
            It discusses recent developments in the stock market and provides insights
            for investors and traders.
            
            Key points include:
            - Market performance analysis
            - Company earnings reports
            - Economic indicators
            - Investment recommendations
            """
        
        paywall_html = """
        <div class="paywall">
            <p>This content is available to subscribers only.</p>
            <button>Subscribe Now</button>
        </div>
        """ if has_paywall else ""
        
        return f"""
        <html>
        <head><title>{title}</title></head>
        <body>
            <article>
                <h1>{title}</h1>
                <div class="article-content">
                    {content}
                </div>
                {paywall_html}
            </article>
        </body>
        </html>
        """
    
    @staticmethod
    def create_empty_response() -> str:
        """Create an empty HTML response"""
        return """
        <html>
        <head><title>Empty Page</title></head>
        <body>
            <p>No content available</p>
        </body>
        </html>
        """
    
    @staticmethod
    def create_error_response(status_code: int = 500) -> str:
        """Create an error HTML response"""
        return f"""
        <html>
        <head><title>Error {status_code}</title></head>
        <body>
            <h1>Error {status_code}</h1>
            <p>An error occurred while processing your request.</p>
        </body>
        </html>
        """


class MockRSSResponseFactory:
    """Factory for creating mock RSS feed responses"""
    
    @staticmethod
    def create_rss_feed(
        articles_count: int = 20,
        feed_title: str = "Financial News Feed",
        feed_description: str = "Latest financial news and market updates"
    ) -> str:
        """Create a mock RSS feed response"""
        items_xml = ""
        for i in range(articles_count):
            title = f"Financial News Article {i + 1}"
            link = f"https://example.com/article{i + 1}"
            description = f"Description for article {i + 1} about financial markets"
            pub_date = (datetime.now(timezone.utc) - timedelta(hours=i)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            
            items_xml += f"""
            <item>
                <title>{title}</title>
                <link>{link}</link>
                <description>{description}</description>
                <pubDate>{pub_date}</pubDate>
                <guid>{link}</guid>
            </item>
            """
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>{feed_title}</title>
                <description>{feed_description}</description>
                <link>https://example.com</link>
                <language>en-us</language>
                <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
                {items_xml}
            </channel>
        </rss>
        """
    
    @staticmethod
    def create_reuters_feed() -> str:
        """Create a mock Reuters RSS feed"""
        return MockRSSResponseFactory.create_rss_feed(
            articles_count=15,
            feed_title="Reuters Business News",
            feed_description="Latest business and financial news from Reuters"
        )
    
    @staticmethod
    def create_yahoo_finance_feed() -> str:
        """Create a mock Yahoo Finance RSS feed"""
        return MockRSSResponseFactory.create_rss_feed(
            articles_count=25,
            feed_title="Yahoo Finance News",
            feed_description="Financial news and market analysis from Yahoo Finance"
        )
    
    @staticmethod
    def create_marketwatch_feed() -> str:
        """Create a mock MarketWatch RSS feed"""
        return MockRSSResponseFactory.create_rss_feed(
            articles_count=20,
            feed_title="MarketWatch News",
            feed_description="Market news and analysis from MarketWatch"
        )
    
    @staticmethod
    def create_invalid_rss() -> str:
        """Create an invalid RSS feed response"""
        return """
        <html>
        <body>
            <p>This is not a valid RSS feed</p>
        </body>
        </html>
        """


class MockAPIResponseFactory:
    """Factory for creating mock API responses"""
    
    @staticmethod
    def create_openai_response(
        content: str,
        model: str = "gpt-4o-mini",
        usage_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Create a mock OpenAI API response"""
        return {
            "id": f"chatcmpl-{random.randint(100000, 999999)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": usage_tokens // 2,
                "completion_tokens": usage_tokens // 2,
                "total_tokens": usage_tokens
            }
        }
    
    @staticmethod
    def create_anthropic_response(
        content: str,
        model: str = "claude-3-5-sonnet-20241022",
        usage_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Create a mock Anthropic API response"""
        return {
            "id": f"msg_{random.randint(100000, 999999)}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": usage_tokens // 2,
                "output_tokens": usage_tokens // 2
            }
        }
    
    @staticmethod
    def create_openai_error_response(
        error_type: str = "rate_limit_exceeded",
        error_message: str = "Rate limit exceeded"
    ) -> Dict[str, Any]:
        """Create a mock OpenAI error response"""
        return {
            "error": {
                "message": error_message,
                "type": error_type,
                "param": None,
                "code": None
            }
        }
    
    @staticmethod
    def create_anthropic_error_response(
        error_type: str = "rate_limit_error",
        error_message: str = "Rate limit exceeded"
    ) -> Dict[str, Any]:
        """Create a mock Anthropic error response"""
        return {
            "type": "error",
            "error": {
                "type": error_type,
                "message": error_message
            }
        }


class MockNetworkConditions:
    """Mock network conditions for testing"""
    
    @staticmethod
    async def simulate_network_delay(delay: float = 0.1):
        """Simulate network delay"""
        await asyncio.sleep(delay)
    
    @staticmethod
    async def simulate_timeout():
        """Simulate a timeout error"""
        await asyncio.sleep(30)  # Long delay to simulate timeout
        raise asyncio.TimeoutError("Request timed out")
    
    @staticmethod
    def simulate_connection_error():
        """Simulate a connection error"""
        raise aiohttp.ClientConnectionError("Connection failed")
    
    @staticmethod
    def simulate_dns_error():
        """Simulate a DNS resolution error"""
        raise aiohttp.ClientError("DNS resolution failed")
    
    @staticmethod
    def simulate_ssl_error():
        """Simulate an SSL error"""
        raise aiohttp.ClientSSLError("SSL certificate verification failed")
    
    @staticmethod
    def simulate_http_error(status_code: int = 500):
        """Simulate an HTTP error response"""
        response = Mock()
        response.status = status_code
        response.reason = "Internal Server Error"
        return response


class MockRateLimiter:
    """Mock rate limiter for testing"""
    
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
        self.enabled = True
    
    async def acquire(self, domain: str):
        """Mock rate limiter acquire method"""
        if not self.enabled:
            return
        
        now = time.time()
        if domain not in self.requests:
            self.requests[domain] = []
        
        # Clean old requests
        self.requests[domain] = [
            req_time for req_time in self.requests[domain]
            if now - req_time < self.window
        ]
        
        # Check if rate limited
        if len(self.requests[domain]) >= self.max_requests:
            raise Exception(f"Rate limit exceeded for {domain}")
        
        self.requests[domain].append(now)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable rate limiting"""
        self.enabled = enabled
    
    def get_request_count(self, domain: str) -> int:
        """Get current request count for domain"""
        return len(self.requests.get(domain, []))


class MockCacheService:
    """Mock cache service for testing"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.cache = {}
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Mock cache get method"""
        if not self.enabled:
            return None
        
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Mock cache set method"""
        if not self.enabled:
            return
        
        self.cache[key] = value
    
    async def delete(self, key: str):
        """Mock cache delete method"""
        if key in self.cache:
            del self.cache[key]
    
    async def clear(self):
        """Mock cache clear method"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "enabled": self.enabled,
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class MockExternalService:
    """Mock external service for comprehensive testing"""
    
    def __init__(self, config: MockServiceConfig = None):
        self.config = config or MockServiceConfig()
        self.call_count = 0
        self.error_count = 0
        self.last_call_time = None
        self.response_history = []
    
    async def make_request(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock external service request"""
        self.call_count += 1
        self.last_call_time = time.time()
        
        # Simulate response delay
        if self.config.response_delay > 0:
            await asyncio.sleep(self.config.response_delay)
        
        # Simulate service status
        if self.config.status == ServiceStatus.UNAVAILABLE:
            self.error_count += 1
            raise Exception("Service unavailable")
        
        # Simulate error rate
        if random.random() < self.config.error_rate:
            self.error_count += 1
            raise Exception("Random service error")
        
        # Simulate rate limiting
        if self.config.status == ServiceStatus.RATE_LIMITED:
            raise Exception("Rate limit exceeded")
        
        # Return mock response
        response = {
            "url": url,
            "status": "success",
            "data": f"Mock response for {url}",
            "timestamp": time.time()
        }
        
        self.response_history.append(response)
        return response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        success_rate = ((self.call_count - self.error_count) / self.call_count * 100) if self.call_count > 0 else 0
        
        return {
            "call_count": self.call_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "last_call_time": self.last_call_time,
            "status": self.config.status.value
        }
    
    def reset_metrics(self):
        """Reset service metrics"""
        self.call_count = 0
        self.error_count = 0
        self.last_call_time = None
        self.response_history.clear()


class MockSessionFactory:
    """Factory for creating mock aiohttp sessions"""
    
    @staticmethod
    def create_session(
        response_factory: Callable = None,
        status_code: int = 200,
        response_delay: float = 0.1,
        should_raise: Exception = None
    ) -> Mock:
        """Create a mock aiohttp session"""
        session = Mock()
        
        async def mock_get(url, **kwargs):
            if response_delay > 0:
                await asyncio.sleep(response_delay)
            
            if should_raise:
                raise should_raise
            
            response = Mock()
            response.status = status_code
            
            if response_factory:
                response.text = AsyncMock(return_value=response_factory())
            else:
                response.text = AsyncMock(return_value="Mock response")
            
            return response
        
        session.get.return_value.__aenter__ = mock_get
        session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        return session
    
    @staticmethod
    def create_failing_session(error_type: NetworkError = NetworkError.CONNECTION_ERROR) -> Mock:
        """Create a session that always fails"""
        session = Mock()
        
        if error_type == NetworkError.TIMEOUT:
            session.get.side_effect = asyncio.TimeoutError("Request timeout")
        elif error_type == NetworkError.CONNECTION_ERROR:
            session.get.side_effect = aiohttp.ClientConnectionError("Connection failed")
        elif error_type == NetworkError.DNS_ERROR:
            session.get.side_effect = aiohttp.ClientError("DNS resolution failed")
        elif error_type == NetworkError.SSL_ERROR:
            session.get.side_effect = aiohttp.ClientSSLError("SSL verification failed")
        else:
            session.get.side_effect = Exception("Generic error")
        
        return session


class MockRedisFactory:
    """Factory for creating mock Redis clients"""
    
    @staticmethod
    def create_redis_client(
        available: bool = True,
        hit_rate: float = 0.8,
        memory_usage: str = "10MB"
    ) -> Mock:
        """Create a mock Redis client"""
        client = Mock()
        
        if not available:
            client.ping.side_effect = Exception("Redis unavailable")
            return client
        
        client.ping.return_value = True
        client.get.return_value = None
        client.setex.return_value = True
        client.keys.return_value = []
        client.delete.return_value = 0
        
        # Mock info for statistics
        total_requests = 100
        hits = int(total_requests * hit_rate)
        misses = total_requests - hits
        
        client.info.return_value = {
            "used_memory_human": memory_usage,
            "keyspace_hits": hits,
            "keyspace_misses": misses
        }
        
        return client
    
    @staticmethod
    def create_cache_with_data(cache_data: Dict[str, Any]) -> Mock:
        """Create a Redis client with pre-populated cache data"""
        client = Mock()
        client.ping.return_value = True
        
        def mock_get(key):
            if key in cache_data:
                return json.dumps(cache_data[key])
            return None
        
        client.get.side_effect = mock_get
        client.setex.return_value = True
        client.keys.return_value = list(cache_data.keys())
        client.delete.return_value = len(cache_data)
        
        return client


class MockScenarioBuilder:
    """Builder for creating complex test scenarios"""
    
    def __init__(self):
        self.services = {}
        self.network_conditions = {}
        self.cache_config = {}
        self.rate_limit_config = {}
    
    def add_service(self, name: str, config: MockServiceConfig) -> 'MockScenarioBuilder':
        """Add a service to the scenario"""
        self.services[name] = MockExternalService(config)
        return self
    
    def set_network_conditions(self, conditions: Dict[str, Any]) -> 'MockScenarioBuilder':
        """Set network conditions for the scenario"""
        self.network_conditions = conditions
        return self
    
    def set_cache_config(self, config: Dict[str, Any]) -> 'MockScenarioBuilder':
        """Set cache configuration for the scenario"""
        self.cache_config = config
        return self
    
    def set_rate_limit_config(self, config: Dict[str, Any]) -> 'MockScenarioBuilder':
        """Set rate limiting configuration for the scenario"""
        self.rate_limit_config = config
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the complete test scenario"""
        return {
            "services": self.services,
            "network_conditions": self.network_conditions,
            "cache_config": self.cache_config,
            "rate_limit_config": self.rate_limit_config
        }


# Pre-built scenarios for common testing situations
class MockScenarios:
    """Pre-built test scenarios"""
    
    @staticmethod
    def healthy_services() -> Dict[str, Any]:
        """Scenario with all services healthy"""
        return MockScenarioBuilder() \
            .add_service("finviz", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .add_service("biztoc", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .add_service("openai", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .add_service("anthropic", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .set_cache_config({"enabled": True, "hit_rate": 0.8}) \
            .set_rate_limit_config({"enabled": True, "strict": False}) \
            .build()
    
    @staticmethod
    def degraded_services() -> Dict[str, Any]:
        """Scenario with some services degraded"""
        return MockScenarioBuilder() \
            .add_service("finviz", MockServiceConfig(status=ServiceStatus.DEGRADED, error_rate=0.3)) \
            .add_service("biztoc", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .add_service("openai", MockServiceConfig(status=ServiceStatus.DEGRADED, response_delay=2.0)) \
            .add_service("anthropic", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .set_cache_config({"enabled": True, "hit_rate": 0.5}) \
            .set_rate_limit_config({"enabled": True, "strict": True}) \
            .build()
    
    @staticmethod
    def services_down() -> Dict[str, Any]:
        """Scenario with critical services down"""
        return MockScenarioBuilder() \
            .add_service("finviz", MockServiceConfig(status=ServiceStatus.UNAVAILABLE)) \
            .add_service("biztoc", MockServiceConfig(status=ServiceStatus.UNAVAILABLE)) \
            .add_service("openai", MockServiceConfig(status=ServiceStatus.UNAVAILABLE)) \
            .add_service("anthropic", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .set_cache_config({"enabled": False}) \
            .set_rate_limit_config({"enabled": True, "strict": True}) \
            .build()
    
    @staticmethod
    def rate_limited_services() -> Dict[str, Any]:
        """Scenario with services being rate limited"""
        return MockScenarioBuilder() \
            .add_service("finviz", MockServiceConfig(status=ServiceStatus.RATE_LIMITED)) \
            .add_service("biztoc", MockServiceConfig(status=ServiceStatus.RATE_LIMITED)) \
            .add_service("openai", MockServiceConfig(status=ServiceStatus.RATE_LIMITED)) \
            .add_service("anthropic", MockServiceConfig(status=ServiceStatus.AVAILABLE)) \
            .set_cache_config({"enabled": True, "hit_rate": 0.9}) \
            .set_rate_limit_config({"enabled": True, "strict": True}) \
            .build()


# Utility functions for test setup
def create_mock_environment(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create a complete mock environment from a scenario"""
    return {
        "session": MockSessionFactory.create_session(),
        "redis": MockRedisFactory.create_redis_client(),
        "rate_limiter": MockRateLimiter(),
        "cache": MockCacheService(),
        "services": scenario["services"],
        "config": scenario
    }


def simulate_load_test(
    service: MockExternalService,
    concurrent_requests: int = 100,
    duration: float = 10.0
) -> Dict[str, Any]:
    """Simulate a load test on a mock service"""
    async def load_test():
        start_time = time.time()
        tasks = []
        
        while time.time() - start_time < duration:
            if len(tasks) < concurrent_requests:
                task = asyncio.create_task(service.make_request(f"https://example.com/{len(tasks)}"))
                tasks.append(task)
            
            # Clean up completed tasks
            tasks = [task for task in tasks if not task.done()]
            await asyncio.sleep(0.01)
        
        # Wait for remaining tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return service.get_metrics()
    
    return asyncio.run(load_test())