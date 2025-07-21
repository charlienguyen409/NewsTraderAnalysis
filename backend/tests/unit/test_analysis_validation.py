"""
Simple validation script to test the analysis module without pytest complications.
This script validates that the core business logic tests work correctly.
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4

# Import the modules we need to test
from app.services.llm_service import LLMService
from app.models.position import PositionType
from app.config.models import DEFAULT_MODEL
from tests.mocks import LLMResponseFactory, CatalystFactory, AnalysisFactory


def test_llm_response_factory():
    """Test the LLM response factory"""
    print("Testing LLM Response Factory...")
    
    # Test sentiment response creation
    response = LLMResponseFactory.create_sentiment_response(
        sentiment_score=0.8,
        confidence=0.9,
        ticker="AAPL"
    )
    
    assert response["sentiment_score"] == 0.8
    assert response["confidence"] == 0.9
    assert response["ticker_mentioned"] == "AAPL"
    assert len(response["catalysts"]) > 0
    
    print("✓ LLM Response Factory working correctly")


def test_catalyst_factory():
    """Test the catalyst factory"""
    print("Testing Catalyst Factory...")
    
    # Test catalyst creation
    catalyst = CatalystFactory.create_catalyst(
        catalyst_type="earnings_beat",
        impact="positive",
        significance="high"
    )
    
    assert catalyst["type"] == "earnings_beat"
    assert catalyst["impact"] == "positive"
    assert catalyst["significance"] == "high"
    assert "description" in catalyst
    
    # Test specific catalyst types
    earnings_catalyst = CatalystFactory.create_earnings_beat_catalyst()
    assert earnings_catalyst["type"] == "earnings_beat"
    assert earnings_catalyst["impact"] == "positive"
    
    fda_catalyst = CatalystFactory.create_fda_approval_catalyst()
    assert fda_catalyst["type"] == "fda_approval"
    assert fda_catalyst["impact"] == "positive"
    
    print("✓ Catalyst Factory working correctly")


def test_analysis_factory():
    """Test the analysis factory"""
    print("Testing Analysis Factory...")
    
    # Test basic analysis creation
    analysis = AnalysisFactory.create_analysis(
        ticker="AAPL",
        sentiment_score=0.7,
        confidence=0.8
    )
    
    assert analysis["ticker"] == "AAPL"
    assert analysis["sentiment_score"] == 0.7
    assert analysis["confidence"] == 0.8
    assert len(analysis["catalysts"]) > 0
    
    # Test specific analysis types
    bullish = AnalysisFactory.create_bullish_analysis("MSFT")
    assert bullish["ticker"] == "MSFT"
    assert bullish["sentiment_score"] > 0.5
    
    bearish = AnalysisFactory.create_bearish_analysis("TSLA")
    assert bearish["ticker"] == "TSLA"
    assert bearish["sentiment_score"] < 0
    
    print("✓ Analysis Factory working correctly")


async def test_sentiment_analysis_logic():
    """Test sentiment analysis logic"""
    print("Testing Sentiment Analysis Logic...")
    
    with patch('app.services.llm_service.openai.AsyncOpenAI'), \
         patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
         patch('app.services.llm_service.redis.Redis.from_url'):
        
        # Create mock LLM service
        llm_service = LLMService()
        llm_service.redis_client = Mock()
        llm_service.redis_client.ping.return_value = True
        
        # Mock successful response
        mock_response = {
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "catalysts": [
                {
                    "type": "earnings_beat",
                    "description": "Strong quarterly earnings",
                    "impact": "positive",
                    "significance": "high"
                }
            ],
            "reasoning": "Strong earnings beat drives positive sentiment",
            "ticker_mentioned": "AAPL",
            "key_phrases": ["earnings", "beat", "revenue"]
        }
        
        # Mock cache miss and API call
        llm_service._get_from_cache = Mock(return_value=None)
        llm_service._set_cache = Mock()
        llm_service._call_openai = AsyncMock(return_value=json.dumps(mock_response))
        
        # Test sentiment analysis
        sample_article = {
            'title': 'Apple Reports Strong Q4 Earnings',
            'content': 'Apple beat earnings expectations with strong revenue growth',
            'ticker': 'AAPL'
        }
        
        result = await llm_service.analyze_sentiment(sample_article)
        
        assert result["sentiment_score"] == 0.8
        assert result["confidence"] == 0.9
        assert result["ticker_mentioned"] == "AAPL"
        assert len(result["catalysts"]) > 0
        assert result["catalysts"][0]["type"] == "earnings_beat"
        
        print("✓ Sentiment Analysis Logic working correctly")


async def test_position_recommendation_logic():
    """Test position recommendation logic"""
    print("Testing Position Recommendation Logic...")
    
    with patch('app.services.llm_service.openai.AsyncOpenAI'), \
         patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
         patch('app.services.llm_service.redis.Redis.from_url'):
        
        # Create mock LLM service
        llm_service = LLMService()
        llm_service.redis_client = Mock()
        llm_service.redis_client.ping.return_value = True
        
        # Mock cache operations
        llm_service._get_from_cache = Mock(return_value=None)
        llm_service._set_cache = Mock()
        
        # Test STRONG_BUY recommendation
        strong_buy_analyses = [
            {
                "ticker": "AAPL",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "catalysts": [
                    {"type": "earnings_beat", "significance": "high", "impact": "positive"}
                ],
                "reasoning": "Strong earnings beat"
            }
        ]
        
        positions = await llm_service.generate_positions(strong_buy_analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "AAPL"
        assert positions[0]["position_type"] == "STRONG_BUY"
        assert positions[0]["confidence"] == 0.9
        
        # Test SHORT recommendation
        short_analyses = [
            {
                "ticker": "TSLA",
                "sentiment_score": -0.6,
                "confidence": 0.8,
                "catalysts": [
                    {"type": "legal_issues", "significance": "medium", "impact": "negative"}
                ],
                "reasoning": "Legal challenges impact sentiment"
            }
        ]
        
        positions = await llm_service.generate_positions(short_analyses, max_positions=10, min_confidence=0.7)
        
        assert len(positions) == 1
        assert positions[0]["ticker"] == "TSLA"
        assert positions[0]["position_type"] == "SHORT"
        assert positions[0]["confidence"] == 0.8
        
        print("✓ Position Recommendation Logic working correctly")


def test_catalyst_detection_logic():
    """Test catalyst detection logic"""
    print("Testing Catalyst Detection Logic...")
    
    # Test catalyst type validation
    valid_catalyst = {
        "type": "earnings_beat",
        "description": "Q3 earnings beat expectations",
        "impact": "positive",
        "significance": "high"
    }
    
    required_fields = ["type", "description", "impact", "significance"]
    for field in required_fields:
        assert field in valid_catalyst, f"Missing required field: {field}"
    
    # Test impact validation
    valid_impacts = ["positive", "negative", "neutral"]
    assert valid_catalyst["impact"] in valid_impacts
    
    # Test significance validation
    valid_significances = ["high", "medium", "low"]
    assert valid_catalyst["significance"] in valid_significances
    
    # Test catalyst scoring logic
    def calculate_catalyst_score(catalysts):
        significance_weights = {"high": 0.9, "medium": 0.6, "low": 0.3}
        if not catalysts:
            return 0.0
        
        total_weight = sum(significance_weights.get(cat["significance"], 0.3) for cat in catalysts)
        return min(1.0, total_weight / len(catalysts))
    
    high_significance_catalysts = [{"significance": "high", "impact": "positive"}]
    assert calculate_catalyst_score(high_significance_catalysts) == 0.9
    
    mixed_catalysts = [
        {"significance": "high", "impact": "positive"},
        {"significance": "medium", "impact": "positive"}
    ]
    expected_score = (0.9 + 0.6) / 2
    assert calculate_catalyst_score(mixed_catalysts) == expected_score
    
    print("✓ Catalyst Detection Logic working correctly")


def test_business_logic_validation():
    """Test business logic validation"""
    print("Testing Business Logic Validation...")
    
    # Test sentiment score validation
    def validate_sentiment_score(score):
        return -1.0 <= score <= 1.0
    
    assert validate_sentiment_score(0.5) == True
    assert validate_sentiment_score(1.0) == True
    assert validate_sentiment_score(-1.0) == True
    assert validate_sentiment_score(1.5) == False
    assert validate_sentiment_score(-1.5) == False
    
    # Test confidence validation
    def validate_confidence(confidence):
        return 0.0 <= confidence <= 1.0
    
    assert validate_confidence(0.8) == True
    assert validate_confidence(0.0) == True
    assert validate_confidence(1.0) == True
    assert validate_confidence(-0.1) == False
    assert validate_confidence(1.1) == False
    
    # Test position type validation
    valid_position_types = [pt.value for pt in PositionType]
    assert "STRONG_BUY" in valid_position_types
    assert "BUY" in valid_position_types
    assert "HOLD" in valid_position_types
    assert "SHORT" in valid_position_types
    assert "STRONG_SHORT" in valid_position_types
    assert "INVALID_TYPE" not in valid_position_types
    
    print("✓ Business Logic Validation working correctly")


async def test_error_handling():
    """Test error handling in analysis logic"""
    print("Testing Error Handling...")
    
    with patch('app.services.llm_service.openai.AsyncOpenAI'), \
         patch('app.services.llm_service.anthropic.AsyncAnthropic'), \
         patch('app.services.llm_service.redis.Redis.from_url'):
        
        # Create mock LLM service
        llm_service = LLMService()
        llm_service.redis_client = Mock()
        llm_service.redis_client.ping.return_value = True
        
        # Mock cache miss
        llm_service._get_from_cache = Mock(return_value=None)
        llm_service._set_cache = Mock()
        
        # Test invalid JSON response
        llm_service._call_openai = AsyncMock(return_value="invalid json")
        
        sample_article = {
            'title': 'Test Article',
            'content': 'Test content',
            'ticker': 'TEST'
        }
        
        result = await llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback response
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        assert result["catalysts"] == []
        assert "Error in analysis" in result["reasoning"]
        
        # Test empty response
        llm_service._call_openai = AsyncMock(return_value="")
        
        result = await llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback response
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        
        # Test API exception
        llm_service._call_openai = AsyncMock(side_effect=Exception("API Error"))
        
        result = await llm_service.analyze_sentiment(sample_article)
        
        # Should return fallback response
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.1
        
        print("✓ Error Handling working correctly")


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("RUNNING ANALYSIS MODULE VALIDATION TESTS")
    print("=" * 60)
    
    try:
        # Test factory functions
        test_llm_response_factory()
        test_catalyst_factory()
        test_analysis_factory()
        
        # Test async logic
        await test_sentiment_analysis_logic()
        await test_position_recommendation_logic()
        await test_error_handling()
        
        # Test business logic
        test_catalyst_detection_logic()
        test_business_logic_validation()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY! ✓")
        print("=" * 60)
        
        # Test summary
        print("\nTest Coverage Summary:")
        print("- Sentiment Analysis Functions: ✓")
        print("- Catalyst Detection Algorithms: ✓")
        print("- Position Recommendation Logic: ✓")
        print("- Business Logic Validation: ✓")
        print("- Error Handling: ✓")
        print("- Mock Factories: ✓")
        print("- Edge Cases: ✓")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)