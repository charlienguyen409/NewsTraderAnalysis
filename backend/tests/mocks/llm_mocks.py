"""
Mock factories for LLM service responses and external API calls.

This module provides reusable mock objects for:
1. LLM API responses (OpenAI, Anthropic)
2. Sentiment analysis results
3. Catalyst detection results
4. Position recommendation results
5. Market summary responses
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock


class LLMResponseFactory:
    """Factory for creating mock LLM responses"""
    
    @staticmethod
    def create_sentiment_response(
        sentiment_score: float = 0.5,
        confidence: float = 0.8,
        catalysts: Optional[List[Dict]] = None,
        reasoning: str = "Mock sentiment analysis",
        ticker: str = "AAPL"
    ) -> Dict[str, Any]:
        """Create a mock sentiment analysis response"""
        if catalysts is None:
            catalysts = [
                {
                    "type": "earnings_beat",
                    "description": "Strong quarterly earnings",
                    "impact": "positive",
                    "significance": "high"
                }
            ]
        
        return {
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "catalysts": catalysts,
            "reasoning": reasoning,
            "ticker_mentioned": ticker,
            "key_phrases": ["earnings", "growth", "revenue"]
        }
    
    @staticmethod
    def create_headlines_response(
        headlines_count: int = 10,
        selected_count: int = 5
    ) -> List[Dict[str, Any]]:
        """Create a mock headlines filtering response"""
        return [
            {
                "index": i + 1,
                "reasoning": f"Headline {i+1} is relevant for trading due to market impact"
            }
            for i in range(min(selected_count, headlines_count))
        ]
    
    @staticmethod
    def create_position_response(
        ticker: str = "AAPL",
        position_type: str = "STRONG_BUY",
        confidence: float = 0.9,
        catalysts: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Create a mock position recommendation response"""
        if catalysts is None:
            catalysts = [
                {
                    "type": "earnings_beat",
                    "description": "Strong quarterly performance",
                    "impact": "positive",
                    "significance": "high"
                }
            ]
        
        return {
            "ticker": ticker,
            "position_type": position_type,
            "confidence": confidence,
            "reasoning": f"Strong {position_type.lower()} signal based on positive catalysts",
            "catalysts": catalysts,
            "supporting_articles": ["article_1", "article_2"]
        }
    
    @staticmethod
    def create_market_summary_response(
        sentiment_score: float = 0.2,
        stocks_count: int = 5
    ) -> Dict[str, Any]:
        """Create a mock market summary response"""
        return {
            "overall_sentiment": "Generally positive market sentiment with selective opportunities",
            "sentiment_score": sentiment_score,
            "key_themes": [
                "Earnings season showing mixed results",
                "Technology sector outperforming",
                "Interest rate concerns persist"
            ],
            "stocks_to_watch": [
                {
                    "ticker": f"STOCK{i}",
                    "reason": f"Strong performance indicators for STOCK{i}",
                    "sentiment": "bullish" if i % 2 == 0 else "bearish",
                    "confidence": 0.8
                }
                for i in range(stocks_count)
            ],
            "notable_catalysts": [
                {
                    "type": "earnings",
                    "description": "Several companies reporting strong earnings",
                    "impact": "positive",
                    "affected_stocks": ["AAPL", "MSFT", "GOOGL"]
                }
            ],
            "risk_factors": [
                "Market volatility due to economic uncertainty",
                "Potential interest rate changes"
            ],
            "summary": "Markets showing resilience with selective opportunities in technology and healthcare sectors.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_used": "gpt-4o-mini",
            "data_sources": {
                "articles_analyzed": 100,
                "sentiment_analyses": 80,
                "positions_generated": 10,
                "unique_tickers": 25
            }
        }
    
    @staticmethod
    def create_error_response(error_message: str = "API Error") -> Dict[str, Any]:
        """Create a mock error response"""
        return {
            "sentiment_score": 0.0,
            "confidence": 0.1,
            "catalysts": [],
            "reasoning": f"Error in analysis: {error_message}",
            "ticker_mentioned": "UNKNOWN",
            "key_phrases": []
        }


class CatalystFactory:
    """Factory for creating mock catalyst data"""
    
    CATALYST_TYPES = [
        "earnings_beat", "earnings_miss", "fda_approval", "fda_rejection",
        "merger_announcement", "partnership", "legal_settlement", "legal_issues",
        "analyst_upgrade", "analyst_downgrade", "product_launch", "management_change"
    ]
    
    IMPACT_TYPES = ["positive", "negative", "neutral"]
    SIGNIFICANCE_LEVELS = ["high", "medium", "low"]
    
    @staticmethod
    def create_catalyst(
        catalyst_type: Optional[str] = None,
        impact: Optional[str] = None,
        significance: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a mock catalyst"""
        if catalyst_type is None:
            catalyst_type = random.choice(CatalystFactory.CATALYST_TYPES)
        
        if impact is None:
            impact = random.choice(CatalystFactory.IMPACT_TYPES)
        
        if significance is None:
            significance = random.choice(CatalystFactory.SIGNIFICANCE_LEVELS)
        
        if description is None:
            description = f"Mock {catalyst_type.replace('_', ' ')} catalyst"
        
        return {
            "type": catalyst_type,
            "description": description,
            "impact": impact,
            "significance": significance
        }
    
    @staticmethod
    def create_earnings_beat_catalyst() -> Dict[str, Any]:
        """Create a mock earnings beat catalyst"""
        return CatalystFactory.create_catalyst(
            catalyst_type="earnings_beat",
            impact="positive",
            significance="high",
            description="Company reports earnings that exceeded analyst expectations"
        )
    
    @staticmethod
    def create_fda_approval_catalyst() -> Dict[str, Any]:
        """Create a mock FDA approval catalyst"""
        return CatalystFactory.create_catalyst(
            catalyst_type="fda_approval",
            impact="positive",
            significance="high",
            description="FDA approves new drug treatment"
        )
    
    @staticmethod
    def create_legal_issues_catalyst() -> Dict[str, Any]:
        """Create a mock legal issues catalyst"""
        return CatalystFactory.create_catalyst(
            catalyst_type="legal_issues",
            impact="negative",
            significance="medium",
            description="Company faces new legal challenges"
        )
    
    @staticmethod
    def create_multiple_catalysts(count: int = 3) -> List[Dict[str, Any]]:
        """Create multiple mock catalysts"""
        return [CatalystFactory.create_catalyst() for _ in range(count)]


class ArticleFactory:
    """Factory for creating mock article data"""
    
    SAMPLE_TITLES = [
        "Apple Reports Strong Q4 Earnings, Beats Revenue Expectations",
        "Microsoft Announces Cloud Partnership with Major Enterprise Client",
        "Tesla Faces Production Challenges, Lowers Guidance",
        "Amazon FDA Approval for New Healthcare Device",
        "Google Settles Antitrust Lawsuit for $2.8 Billion",
        "Meta Launches New VR Platform, Stock Surges",
        "Netflix Subscriber Growth Slows, Shares Drop",
        "Salesforce CEO Steps Down, Interim Leadership Announced"
    ]
    
    SAMPLE_SOURCES = ["finviz", "biztoc", "yahoo", "reuters", "bloomberg"]
    
    @staticmethod
    def create_article(
        title: Optional[str] = None,
        content: Optional[str] = None,
        ticker: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        published_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a mock article"""
        if title is None:
            title = random.choice(ArticleFactory.SAMPLE_TITLES)
        
        if content is None:
            content = f"Mock article content for {title}. This is a detailed analysis of the market impact and business implications."
        
        if ticker is None:
            ticker = random.choice(["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX"])
        
        if source is None:
            source = random.choice(ArticleFactory.SAMPLE_SOURCES)
        
        if url is None:
            url = f"https://example.com/article-{hash(title) % 10000}"
        
        if published_at is None:
            published_at = datetime.now(timezone.utc).isoformat()
        
        return {
            "title": title,
            "content": content,
            "ticker": ticker,
            "source": source,
            "url": url,
            "published_at": published_at,
            "article_metadata": {}
        }
    
    @staticmethod
    def create_multiple_articles(count: int = 10) -> List[Dict[str, Any]]:
        """Create multiple mock articles"""
        return [ArticleFactory.create_article() for _ in range(count)]


class AnalysisFactory:
    """Factory for creating mock analysis data"""
    
    @staticmethod
    def create_analysis(
        ticker: str = "AAPL",
        sentiment_score: float = 0.5,
        confidence: float = 0.8,
        catalysts: Optional[List[Dict]] = None,
        reasoning: str = "Mock analysis reasoning",
        article_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a mock analysis"""
        if catalysts is None:
            catalysts = [CatalystFactory.create_catalyst()]
        
        if article_id is None:
            article_id = f"article_{hash(ticker) % 1000}"
        
        return {
            "ticker": ticker,
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "catalysts": catalysts,
            "reasoning": reasoning,
            "article_id": article_id,
            "analysis_id": f"analysis_{hash(ticker) % 1000}"
        }
    
    @staticmethod
    def create_bullish_analysis(ticker: str = "AAPL") -> Dict[str, Any]:
        """Create a mock bullish analysis"""
        return AnalysisFactory.create_analysis(
            ticker=ticker,
            sentiment_score=0.8,
            confidence=0.9,
            catalysts=[CatalystFactory.create_earnings_beat_catalyst()],
            reasoning="Strong positive sentiment due to earnings beat and positive guidance"
        )
    
    @staticmethod
    def create_bearish_analysis(ticker: str = "TSLA") -> Dict[str, Any]:
        """Create a mock bearish analysis"""
        return AnalysisFactory.create_analysis(
            ticker=ticker,
            sentiment_score=-0.6,
            confidence=0.8,
            catalysts=[CatalystFactory.create_legal_issues_catalyst()],
            reasoning="Negative sentiment due to legal challenges and production issues"
        )
    
    @staticmethod
    def create_neutral_analysis(ticker: str = "MSFT") -> Dict[str, Any]:
        """Create a mock neutral analysis"""
        return AnalysisFactory.create_analysis(
            ticker=ticker,
            sentiment_score=0.1,
            confidence=0.6,
            catalysts=[],
            reasoning="Neutral sentiment with no significant catalysts"
        )
    
    @staticmethod
    def create_multiple_analyses(count: int = 10) -> List[Dict[str, Any]]:
        """Create multiple mock analyses"""
        return [AnalysisFactory.create_analysis() for _ in range(count)]


class MockLLMService:
    """Mock LLM service for testing"""
    
    def __init__(self):
        self.redis_client = Mock()
        self.openai_client = Mock()
        self.anthropic_client = Mock()
        
        # Set up default mock responses
        self.redis_client.ping.return_value = True
        self.redis_client.get.return_value = None
        self.redis_client.setex.return_value = True
        
    def setup_sentiment_analysis_mock(self, response: Dict[str, Any]):
        """Set up mock for sentiment analysis"""
        self.analyze_sentiment = AsyncMock(return_value=response)
    
    def setup_headlines_analysis_mock(self, response: List[Dict[str, Any]]):
        """Set up mock for headlines analysis"""
        self.analyze_headlines = AsyncMock(return_value=response)
    
    def setup_position_generation_mock(self, response: List[Dict[str, Any]]):
        """Set up mock for position generation"""
        self.generate_positions = AsyncMock(return_value=response)
    
    def setup_market_summary_mock(self, response: Dict[str, Any]):
        """Set up mock for market summary"""
        self.generate_market_summary = AsyncMock(return_value=response)
    
    def setup_cache_mock(self, cache_hits: Dict[str, Any] = None):
        """Set up mock for cache operations"""
        if cache_hits:
            self.redis_client.get.side_effect = lambda key: json.dumps(cache_hits.get(key)) if key in cache_hits else None
        else:
            self.redis_client.get.return_value = None


class TestDatasets:
    """Predefined datasets for testing"""
    
    @staticmethod
    def get_earnings_season_dataset() -> Dict[str, Any]:
        """Get a dataset simulating earnings season"""
        return {
            "articles": [
                ArticleFactory.create_article(
                    title="Apple Reports Record Q4 Earnings",
                    ticker="AAPL",
                    content="Apple Inc. announced record quarterly earnings with revenue of $117.2 billion, beating analyst expectations."
                ),
                ArticleFactory.create_article(
                    title="Microsoft Cloud Growth Drives Strong Quarter",
                    ticker="MSFT",
                    content="Microsoft reported strong quarterly results driven by Azure cloud growth and Office 365 adoption."
                ),
                ArticleFactory.create_article(
                    title="Tesla Misses Delivery Targets, Stock Falls",
                    ticker="TSLA",
                    content="Tesla reported quarterly deliveries below expectations, citing supply chain challenges."
                )
            ],
            "analyses": [
                AnalysisFactory.create_bullish_analysis("AAPL"),
                AnalysisFactory.create_bullish_analysis("MSFT"),
                AnalysisFactory.create_bearish_analysis("TSLA")
            ],
            "expected_positions": [
                {"ticker": "AAPL", "position_type": "STRONG_BUY", "confidence": 0.9},
                {"ticker": "MSFT", "position_type": "BUY", "confidence": 0.8},
                {"ticker": "TSLA", "position_type": "SHORT", "confidence": 0.8}
            ]
        }
    
    @staticmethod
    def get_fda_approval_dataset() -> Dict[str, Any]:
        """Get a dataset simulating FDA approval news"""
        return {
            "articles": [
                ArticleFactory.create_article(
                    title="BioTech Company Receives FDA Approval for New Drug",
                    ticker="BIOTECH",
                    content="The FDA has approved the company's new treatment for diabetes, marking a major milestone."
                )
            ],
            "analyses": [
                AnalysisFactory.create_analysis(
                    ticker="BIOTECH",
                    sentiment_score=0.9,
                    confidence=0.95,
                    catalysts=[CatalystFactory.create_fda_approval_catalyst()],
                    reasoning="FDA approval is a major positive catalyst for biotech companies"
                )
            ],
            "expected_positions": [
                {"ticker": "BIOTECH", "position_type": "STRONG_BUY", "confidence": 0.95}
            ]
        }
    
    @staticmethod
    def get_mixed_sentiment_dataset() -> Dict[str, Any]:
        """Get a dataset with mixed sentiment signals"""
        return {
            "articles": ArticleFactory.create_multiple_articles(20),
            "analyses": [
                AnalysisFactory.create_bullish_analysis("AAPL"),
                AnalysisFactory.create_bearish_analysis("TSLA"),
                AnalysisFactory.create_neutral_analysis("MSFT"),
                AnalysisFactory.create_bullish_analysis("GOOGL"),
                AnalysisFactory.create_bearish_analysis("META")
            ],
            "expected_positions": [
                {"ticker": "AAPL", "position_type": "STRONG_BUY"},
                {"ticker": "GOOGL", "position_type": "STRONG_BUY"},
                {"ticker": "TSLA", "position_type": "SHORT"},
                {"ticker": "META", "position_type": "SHORT"}
                # MSFT should be filtered out due to neutral sentiment
            ]
        }


# Utility functions for test setup
def create_mock_llm_service_with_responses(
    sentiment_responses: List[Dict[str, Any]] = None,
    position_responses: List[Dict[str, Any]] = None,
    market_summary_response: Dict[str, Any] = None
) -> MockLLMService:
    """Create a mock LLM service with predefined responses"""
    mock_service = MockLLMService()
    
    if sentiment_responses:
        mock_service.analyze_sentiment = AsyncMock(side_effect=sentiment_responses)
    
    if position_responses:
        mock_service.generate_positions = AsyncMock(return_value=position_responses)
    
    if market_summary_response:
        mock_service.generate_market_summary = AsyncMock(return_value=market_summary_response)
    
    return mock_service


def create_test_session_id() -> str:
    """Create a test session ID"""
    from uuid import uuid4
    return str(uuid4())


# Constants for testing
TEST_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "NVDA"]
TEST_MODELS = ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-20241022"]
TEST_CONFIDENCE_THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9]
TEST_SENTIMENT_RANGES = [
    (-1.0, -0.7),  # Strong negative
    (-0.7, -0.4),  # Moderate negative
    (-0.4, 0.4),   # Neutral
    (0.4, 0.7),    # Moderate positive
    (0.7, 1.0)     # Strong positive
]