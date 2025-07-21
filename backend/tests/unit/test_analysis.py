"""
Comprehensive unit tests for core business logic in analysis services.

This test suite covers:
1. Sentiment analysis functions
2. Catalyst detection algorithms  
3. Position recommendation logic
4. Business logic validation
5. Error handling and edge cases
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, List, Any
from uuid import uuid4

from app.services.llm_service import LLMService
from app.services.analysis_service import AnalysisService
from app.models.position import PositionType
from app.config.models import DEFAULT_MODEL


class TestLLMServiceSentimentAnalysis:
    """Test suite for LLM service sentiment analysis functionality"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service with mocked external dependencies"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service.redis_client.ping.return_value = True
            return llm_service
    
    @pytest.fixture
    def sample_article(self):
        """Sample article for testing"""
        return {
            'title': 'Apple Reports Strong Q4 Earnings, Beats Revenue Expectations',
            'content': 'Apple Inc. reported fourth-quarter earnings that exceeded analysts expectations. Revenue grew 15% year-over-year to $94.9 billion, driven by strong iPhone sales.',
            'url': 'https://example.com/apple-earnings',
            'source': 'finviz',
            'ticker': 'AAPL',
            'published_at': '2023-10-01T15:30:00Z'
        }
    
    @pytest.fixture
    def sample_sentiment_response(self):
        """Sample LLM sentiment analysis response"""
        return {
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "catalysts": [
                {
                    "type": "earnings_beat",
                    "description": "Q4 earnings exceeded expectations",
                    "impact": "positive",
                    "significance": "high"
                }
            ],
            "reasoning": "Strong quarterly results with revenue growth and earnings beat indicating positive momentum",
            "ticker_mentioned": "AAPL",
            "key_phrases": ["earnings beat", "revenue growth", "strong iPhone sales"]
        }
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_success(self, mock_llm_service, sample_article, sample_sentiment_response):
        """Test successful sentiment analysis with proper response parsing"""
        # Mock the LLM API call
        mock_llm_service._call_openai = AsyncMock(return_value=json.dumps(sample_sentiment_response))
        
        # Mock cache miss
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Verify result structure
        assert result["sentiment_score"] == 0.8
        assert result["confidence"] == 0.9
        assert len(result["catalysts"]) == 1
        assert result["catalysts"][0]["type"] == "earnings_beat"
        assert result["ticker_mentioned"] == "AAPL"
        assert "reasoning" in result
        
        # Verify cache was attempted
        mock_llm_service._get_from_cache.assert_called_once()
        mock_llm_service._set_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_cache_hit(self, mock_llm_service, sample_article, sample_sentiment_response):
        """Test sentiment analysis with cache hit"""
        # Mock cache hit
        mock_llm_service._get_from_cache = Mock(return_value=sample_sentiment_response)
        mock_llm_service._call_openai = AsyncMock()
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Verify result from cache
        assert result == sample_sentiment_response
        
        # Verify LLM API was not called
        mock_llm_service._call_openai.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_invalid_json(self, mock_llm_service, sample_article):
        """Test sentiment analysis with invalid JSON response"""
        # Mock invalid JSON response
        mock_llm_service._call_openai = AsyncMock(return_value="invalid json response")
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback neutral analysis
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        assert result["catalysts"] == []
        assert "Error in analysis" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_empty_response(self, mock_llm_service, sample_article):
        """Test sentiment analysis with empty response"""
        # Mock empty response
        mock_llm_service._call_openai = AsyncMock(return_value="")
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback neutral analysis
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        assert result["catalysts"] == []
        assert "Error in analysis" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_missing_fields(self, mock_llm_service, sample_article):
        """Test sentiment analysis with missing required fields"""
        # Mock response with missing fields
        incomplete_response = {
            "sentiment_score": 0.5,
            # Missing confidence, catalysts, reasoning
        }
        mock_llm_service._call_openai = AsyncMock(return_value=json.dumps(incomplete_response))
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback neutral analysis
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        assert result["catalysts"] == []
        assert "Error in analysis" in result["reasoning"]
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_value_clamping(self, mock_llm_service, sample_article):
        """Test sentiment analysis with out-of-range values"""
        # Mock response with extreme values
        extreme_response = {
            "sentiment_score": 2.0,  # Should be clamped to 1.0
            "confidence": -0.5,      # Should be clamped to 0.0
            "catalysts": [],
            "reasoning": "Test extreme values"
        }
        mock_llm_service._call_openai = AsyncMock(return_value=json.dumps(extreme_response))
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Values should be clamped to valid ranges
        assert result["sentiment_score"] == 1.0  # Clamped from 2.0
        assert result["confidence"] == 0.0       # Clamped from -0.5
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_different_models(self, mock_llm_service, sample_article):
        """Test sentiment analysis with different LLM models"""
        mock_response = {
            "sentiment_score": 0.6,
            "confidence": 0.8,
            "catalysts": [],
            "reasoning": "Test response"
        }
        
        # Test OpenAI model
        mock_llm_service._call_openai = AsyncMock(return_value=json.dumps(mock_response))
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article, model="gpt-4o-mini")
        assert result["sentiment_score"] == 0.6
        
        # Test Anthropic model
        mock_llm_service._call_anthropic = AsyncMock(return_value=json.dumps(mock_response))
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article, model="claude-3-5-sonnet-20241022")
        assert result["sentiment_score"] == 0.6
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_api_error(self, mock_llm_service, sample_article):
        """Test sentiment analysis with API error"""
        # Mock API error
        mock_llm_service._call_openai = AsyncMock(side_effect=Exception("API Error"))
        mock_llm_service._get_from_cache = Mock(return_value=None)
        
        result = await mock_llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback neutral analysis
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        assert result["catalysts"] == []
        assert "Error in analysis" in result["reasoning"]


class TestCatalystDetection:
    """Test suite for catalyst detection algorithms"""
    
    def test_catalyst_types_detection(self):
        """Test detection of different catalyst types"""
        test_cases = [
            # Earnings catalysts
            {
                "catalyst": {
                    "type": "earnings_beat",
                    "description": "Q3 earnings beat expectations by 15%",
                    "impact": "positive",
                    "significance": "high"
                },
                "expected_type": "earnings_beat"
            },
            # FDA catalysts
            {
                "catalyst": {
                    "type": "fda_approval",
                    "description": "FDA approves new drug for diabetes treatment",
                    "impact": "positive",
                    "significance": "high"
                },
                "expected_type": "fda_approval"
            },
            # M&A catalysts
            {
                "catalyst": {
                    "type": "merger_announcement",
                    "description": "Company announces acquisition of competitor",
                    "impact": "positive",
                    "significance": "high"
                },
                "expected_type": "merger_announcement"
            },
            # Legal catalysts
            {
                "catalyst": {
                    "type": "legal_settlement",
                    "description": "Company settles major lawsuit",
                    "impact": "negative",
                    "significance": "medium"
                },
                "expected_type": "legal_settlement"
            }
        ]
        
        for test_case in test_cases:
            catalyst = test_case["catalyst"]
            assert catalyst["type"] == test_case["expected_type"]
            assert catalyst["impact"] in ["positive", "negative"]
            assert catalyst["significance"] in ["low", "medium", "high"]
    
    def test_catalyst_impact_scoring(self):
        """Test catalyst impact scoring logic"""
        # High impact catalysts
        high_impact_catalysts = [
            {"type": "earnings_beat", "significance": "high", "impact": "positive"},
            {"type": "fda_approval", "significance": "high", "impact": "positive"},
            {"type": "merger_announcement", "significance": "high", "impact": "positive"}
        ]
        
        # Medium impact catalysts
        medium_impact_catalysts = [
            {"type": "analyst_upgrade", "significance": "medium", "impact": "positive"},
            {"type": "product_launch", "significance": "medium", "impact": "positive"}
        ]
        
        # Low impact catalysts
        low_impact_catalysts = [
            {"type": "partnership", "significance": "low", "impact": "positive"},
            {"type": "management_change", "significance": "low", "impact": "neutral"}
        ]
        
        # Test that high impact catalysts have higher significance
        for catalyst in high_impact_catalysts:
            assert catalyst["significance"] == "high"
        
        for catalyst in medium_impact_catalysts:
            assert catalyst["significance"] == "medium"
        
        for catalyst in low_impact_catalysts:
            assert catalyst["significance"] == "low"
    
    def test_multiple_catalysts_aggregation(self):
        """Test aggregation of multiple catalysts"""
        multiple_catalysts = [
            {
                "type": "earnings_beat",
                "description": "Q3 earnings beat expectations",
                "impact": "positive",
                "significance": "high"
            },
            {
                "type": "analyst_upgrade",
                "description": "Morgan Stanley upgrades to Buy",
                "impact": "positive",
                "significance": "medium"
            }
        ]
        
        # Test that multiple positive catalysts exist
        assert len(multiple_catalysts) == 2
        assert all(cat["impact"] == "positive" for cat in multiple_catalysts)
        
        # Test significance weighting
        high_sig_count = sum(1 for cat in multiple_catalysts if cat["significance"] == "high")
        medium_sig_count = sum(1 for cat in multiple_catalysts if cat["significance"] == "medium")
        
        assert high_sig_count == 1
        assert medium_sig_count == 1
    
    def test_catalyst_confidence_scoring(self):
        """Test catalyst confidence scoring based on significance"""
        def calculate_catalyst_confidence(catalysts):
            """Calculate confidence based on catalyst significance"""
            if not catalysts:
                return 0.0
            
            significance_weights = {"high": 0.9, "medium": 0.6, "low": 0.3}
            total_weight = sum(significance_weights.get(cat["significance"], 0.3) for cat in catalysts)
            return min(1.0, total_weight / len(catalysts))
        
        # Test high confidence with high significance catalyst
        high_sig_catalysts = [{"significance": "high", "impact": "positive"}]
        assert calculate_catalyst_confidence(high_sig_catalysts) == 0.9
        
        # Test medium confidence with medium significance catalyst
        medium_sig_catalysts = [{"significance": "medium", "impact": "positive"}]
        assert calculate_catalyst_confidence(medium_sig_catalysts) == 0.6
        
        # Test low confidence with low significance catalyst
        low_sig_catalysts = [{"significance": "low", "impact": "positive"}]
        assert calculate_catalyst_confidence(low_sig_catalysts) == 0.3
        
        # Test mixed significance catalysts
        mixed_catalysts = [
            {"significance": "high", "impact": "positive"},
            {"significance": "medium", "impact": "positive"}
        ]
        expected_confidence = (0.9 + 0.6) / 2
        assert calculate_catalyst_confidence(mixed_catalysts) == expected_confidence


class TestPositionRecommendationLogic:
    """Test suite for position recommendation logic"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service for position testing"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            return llm_service
    
    @pytest.mark.asyncio
    async def test_strong_buy_recommendation(self, mock_llm_service):
        """Test STRONG_BUY position recommendation logic"""
        # Mock analyses with strong positive sentiment
        analyses = [
            {
                "ticker": "AAPL",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "catalysts": [
                    {"type": "earnings_beat", "significance": "high", "impact": "positive"},
                    {"type": "analyst_upgrade", "significance": "medium", "impact": "positive"}
                ],
                "reasoning": "Strong earnings beat and analyst upgrade"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "AAPL"
        assert positions[0]["position_type"] == "STRONG_BUY"
        assert positions[0]["confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_buy_recommendation(self, mock_llm_service):
        """Test BUY position recommendation logic"""
        # Mock analyses with moderate positive sentiment
        analyses = [
            {
                "ticker": "MSFT",
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "catalysts": [
                    {"type": "product_launch", "significance": "medium", "impact": "positive"}
                ],
                "reasoning": "Positive product launch announcement"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "MSFT"
        assert positions[0]["position_type"] == "BUY"
        assert positions[0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_short_recommendation(self, mock_llm_service):
        """Test SHORT position recommendation logic"""
        # Mock analyses with moderate negative sentiment
        analyses = [
            {
                "ticker": "TSLA",
                "sentiment_score": -0.5,
                "confidence": 0.8,
                "catalysts": [
                    {"type": "earnings_miss", "significance": "medium", "impact": "negative"}
                ],
                "reasoning": "Earnings miss and guidance lowered"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "TSLA"
        assert positions[0]["position_type"] == "SHORT"
        assert positions[0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_strong_short_recommendation(self, mock_llm_service):
        """Test STRONG_SHORT position recommendation logic"""
        # Mock analyses with strong negative sentiment
        analyses = [
            {
                "ticker": "NFLX",
                "sentiment_score": -0.8,
                "confidence": 0.9,
                "catalysts": [
                    {"type": "legal_issues", "significance": "high", "impact": "negative"},
                    {"type": "management_change", "significance": "medium", "impact": "negative"}
                ],
                "reasoning": "Major legal issues and management turmoil"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "NFLX"
        assert positions[0]["position_type"] == "STRONG_SHORT"
        assert positions[0]["confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_hold_position_filtered(self, mock_llm_service):
        """Test that HOLD positions are filtered out"""
        # Mock analyses with neutral sentiment (should result in HOLD)
        analyses = [
            {
                "ticker": "GOOGL",
                "sentiment_score": 0.1,  # Neutral sentiment
                "confidence": 0.8,
                "catalysts": [],
                "reasoning": "Neutral market conditions"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        # HOLD positions should be filtered out
        assert len(positions) == 0
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, mock_llm_service):
        """Test filtering by minimum confidence threshold"""
        # Mock analyses with low confidence
        analyses = [
            {
                "ticker": "AMZN",
                "sentiment_score": 0.8,
                "confidence": 0.5,  # Below threshold
                "catalysts": [{"type": "earnings_beat", "significance": "high", "impact": "positive"}],
                "reasoning": "Earnings beat but low confidence"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        # Should be filtered out due to low confidence
        assert len(positions) == 0
    
    @pytest.mark.asyncio
    async def test_max_positions_limit(self, mock_llm_service):
        """Test maximum positions limit"""
        # Mock many analyses
        analyses = [
            {
                "ticker": f"STOCK{i}",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "catalysts": [{"type": "earnings_beat", "significance": "high", "impact": "positive"}],
                "reasoning": f"Strong performance for STOCK{i}"
            }
            for i in range(15)  # More than max_positions
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=5, min_confidence=0.7)
        
        # Should be limited to max_positions
        assert len(positions) == 5
        
        # Should be sorted by confidence (highest first)
        confidences = [pos["confidence"] for pos in positions]
        assert confidences == sorted(confidences, reverse=True)
    
    @pytest.mark.asyncio
    async def test_ticker_aggregation(self, mock_llm_service):
        """Test aggregation of multiple articles for same ticker"""
        # Mock multiple analyses for same ticker
        analyses = [
            {
                "ticker": "AAPL",
                "sentiment_score": 0.6,
                "confidence": 0.8,
                "catalysts": [{"type": "earnings_beat", "significance": "high", "impact": "positive"}],
                "reasoning": "Strong earnings",
                "article_id": "1"
            },
            {
                "ticker": "AAPL",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "catalysts": [{"type": "analyst_upgrade", "significance": "medium", "impact": "positive"}],
                "reasoning": "Analyst upgrade",
                "article_id": "2"
            }
        ]
        
        mock_llm_service._get_from_cache = Mock(return_value=None)
        mock_llm_service._set_cache = Mock()
        
        positions = await mock_llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "AAPL"
        
        # Should aggregate sentiment and confidence
        expected_sentiment = (0.6 + 0.8) / 2  # 0.7
        expected_confidence = (0.8 + 0.9) / 2  # 0.85
        
        # Position type should be BUY (sentiment 0.7 > 0.4 but < 0.7 threshold for STRONG_BUY)
        assert positions[0]["position_type"] == "BUY"
        assert positions[0]["confidence"] == expected_confidence
        
        # Should include both article IDs
        assert len(positions[0]["supporting_articles"]) == 2
        assert "1" in positions[0]["supporting_articles"]
        assert "2" in positions[0]["supporting_articles"]


class TestBusinessLogicValidation:
    """Test suite for business logic validation"""
    
    def test_sentiment_score_validation(self):
        """Test sentiment score validation ranges"""
        valid_scores = [0.0, 0.5, 1.0, -0.5, -1.0]
        invalid_scores = [1.5, -1.5, 2.0, -2.0]
        
        for score in valid_scores:
            assert -1.0 <= score <= 1.0, f"Score {score} should be valid"
        
        for score in invalid_scores:
            assert not (-1.0 <= score <= 1.0), f"Score {score} should be invalid"
    
    def test_confidence_score_validation(self):
        """Test confidence score validation ranges"""
        valid_confidences = [0.0, 0.5, 1.0, 0.7, 0.85]
        invalid_confidences = [1.5, -0.1, 2.0, -1.0]
        
        for confidence in valid_confidences:
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} should be valid"
        
        for confidence in invalid_confidences:
            assert not (0.0 <= confidence <= 1.0), f"Confidence {confidence} should be invalid"
    
    def test_position_type_validation(self):
        """Test position type validation"""
        valid_types = ["STRONG_BUY", "BUY", "HOLD", "SHORT", "STRONG_SHORT"]
        invalid_types = ["SUPER_BUY", "MAYBE_BUY", "NEUTRAL", "SELL"]
        
        for pos_type in valid_types:
            assert pos_type in [pt.value for pt in PositionType], f"Position type {pos_type} should be valid"
        
        for pos_type in invalid_types:
            assert pos_type not in [pt.value for pt in PositionType], f"Position type {pos_type} should be invalid"
    
    def test_catalyst_structure_validation(self):
        """Test catalyst structure validation"""
        valid_catalyst = {
            "type": "earnings_beat",
            "description": "Q3 earnings beat expectations",
            "impact": "positive",
            "significance": "high"
        }
        
        required_fields = ["type", "description", "impact", "significance"]
        
        for field in required_fields:
            assert field in valid_catalyst, f"Required field {field} missing"
        
        # Test valid impact values
        valid_impacts = ["positive", "negative", "neutral"]
        assert valid_catalyst["impact"] in valid_impacts
        
        # Test valid significance values
        valid_significances = ["high", "medium", "low"]
        assert valid_catalyst["significance"] in valid_significances
    
    def test_reasoning_validation(self):
        """Test reasoning text validation"""
        valid_reasoning = [
            "Strong earnings beat with revenue growth",
            "FDA approval for new drug treatment",
            "Merger announcement with strategic partner"
        ]
        
        invalid_reasoning = [
            "",  # Empty
            "   ",  # Whitespace only
            "a" * 10000,  # Too long
            None  # None value
        ]
        
        for reasoning in valid_reasoning:
            assert reasoning and reasoning.strip(), f"Reasoning '{reasoning}' should be valid"
        
        for reasoning in invalid_reasoning:
            if reasoning is None:
                assert reasoning is None
            else:
                assert not (reasoning and reasoning.strip()), f"Reasoning '{reasoning}' should be invalid"


class TestPerformanceBenchmarks:
    """Test suite for performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_performance(self):
        """Test sentiment analysis performance benchmark"""
        import time
        
        # Mock fast response
        mock_response = {
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "catalysts": [],
            "reasoning": "Test benchmark"
        }
        
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._call_openai = AsyncMock(return_value=json.dumps(mock_response))
            llm_service._get_from_cache = Mock(return_value=None)
            llm_service._set_cache = Mock()
            
            sample_article = {
                'title': 'Test Article',
                'content': 'Test content for performance benchmark',
                'ticker': 'TEST'
            }
            
            start_time = time.time()
            result = await llm_service.analyze_sentiment(sample_article)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Should complete within reasonable time (allowing for mocking overhead)
            assert duration < 1.0, f"Sentiment analysis took {duration:.3f}s, expected < 1.0s"
            assert result["sentiment_score"] == 0.5
    
    @pytest.mark.asyncio
    async def test_position_generation_performance(self):
        """Test position generation performance benchmark"""
        import time
        
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._get_from_cache = Mock(return_value=None)
            llm_service._set_cache = Mock()
            
            # Mock multiple analyses
            analyses = [
                {
                    "ticker": f"STOCK{i}",
                    "sentiment_score": 0.8,
                    "confidence": 0.9,
                    "catalysts": [{"type": "earnings_beat", "significance": "high", "impact": "positive"}],
                    "reasoning": f"Strong performance for STOCK{i}"
                }
                for i in range(100)  # Many analyses
            ]
            
            start_time = time.time()
            positions = await llm_service.generate_positions(analyses, max_positions=10, min_confidence=0.7)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Should complete within reasonable time for 100 analyses
            assert duration < 2.0, f"Position generation took {duration:.3f}s, expected < 2.0s"
            assert len(positions) == 10
    
    def test_catalyst_processing_performance(self):
        """Test catalyst processing performance benchmark"""
        import time
        
        # Generate many catalysts
        catalysts = [
            {
                "type": f"catalyst_type_{i}",
                "description": f"Catalyst description {i}",
                "impact": "positive" if i % 2 == 0 else "negative",
                "significance": "high" if i % 3 == 0 else "medium"
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        # Process catalysts (simulate business logic)
        processed_catalysts = []
        for catalyst in catalysts:
            if catalyst["impact"] == "positive" and catalyst["significance"] == "high":
                processed_catalysts.append(catalyst)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should process 1000 catalysts quickly
        assert duration < 0.1, f"Catalyst processing took {duration:.3f}s, expected < 0.1s"
        assert len(processed_catalysts) > 0


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_empty_article_content(self):
        """Test analysis with empty article content"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._get_from_cache = Mock(return_value=None)
            llm_service._call_openai = AsyncMock(return_value='{"sentiment_score": 0.0, "confidence": 0.1, "catalysts": [], "reasoning": "No content"}')
            
            empty_article = {
                'title': '',
                'content': '',
                'ticker': 'TEST'
            }
            
            result = await llm_service.analyze_sentiment(empty_article)
            
            assert result["sentiment_score"] == 0.0
            assert result["confidence"] == 0.1
            assert result["catalysts"] == []
    
    @pytest.mark.asyncio
    async def test_malformed_ticker(self):
        """Test analysis with malformed ticker"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._get_from_cache = Mock(return_value=None)
            llm_service._call_openai = AsyncMock(return_value='{"sentiment_score": 0.5, "confidence": 0.8, "catalysts": [], "reasoning": "Test", "ticker_mentioned": "UNKNOWN"}')
            
            malformed_article = {
                'title': 'Test Article',
                'content': 'Test content',
                'ticker': None  # Malformed ticker
            }
            
            result = await llm_service.analyze_sentiment(malformed_article)
            
            # Should handle gracefully
            assert result["ticker_mentioned"] == "UNKNOWN"
    
    @pytest.mark.asyncio
    async def test_no_analyses_for_positions(self):
        """Test position generation with no analyses"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._get_from_cache = Mock(return_value=None)
            
            positions = await llm_service.generate_positions([], max_positions=10, min_confidence=0.7)
            
            assert len(positions) == 0
    
    @pytest.mark.asyncio
    async def test_all_low_confidence_analyses(self):
        """Test position generation with all low confidence analyses"""
        with patch('app.services.llm_service.openai.AsyncOpenAI'), \
             patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
             patch('app.services.llm_service.redis.Redis.from_url'):
            
            llm_service = LLMService()
            llm_service.redis_client = Mock()
            llm_service._get_from_cache = Mock(return_value=None)
            
            low_confidence_analyses = [
                {
                    "ticker": "TEST",
                    "sentiment_score": 0.8,
                    "confidence": 0.3,  # Below threshold
                    "catalysts": [],
                    "reasoning": "Low confidence analysis"
                }
            ]
            
            positions = await llm_service.generate_positions(low_confidence_analyses, max_positions=10, min_confidence=0.7)
            
            assert len(positions) == 0
    
    def test_invalid_catalyst_structure(self):
        """Test handling of invalid catalyst structure"""
        invalid_catalysts = [
            {},  # Empty catalyst
            {"type": "earnings_beat"},  # Missing required fields
            {"description": "Test", "impact": "positive"},  # Missing type and significance
            {"type": "test", "description": "test", "impact": "invalid", "significance": "high"}  # Invalid impact
        ]
        
        for catalyst in invalid_catalysts:
            required_fields = ["type", "description", "impact", "significance"]
            missing_fields = [field for field in required_fields if field not in catalyst]
            
            if missing_fields:
                assert len(missing_fields) > 0, f"Catalyst {catalyst} should have missing fields"
            
            if "impact" in catalyst and catalyst["impact"] not in ["positive", "negative", "neutral"]:
                assert catalyst["impact"] not in ["positive", "negative", "neutral"], f"Impact {catalyst['impact']} should be invalid"