import openai
import anthropic
import json
import logging
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..config.models import get_model_config, DEFAULT_MODEL


class LLMService:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_headlines(self, headlines: List[Dict], model: str = DEFAULT_MODEL) -> List[Dict]:
        """Filter headlines to find the most relevant ones for trading analysis"""
        
        headlines_text = "\n".join([
            f"{i+1}. {h['title']} (Source: {h['source']})"
            for i, h in enumerate(headlines)
        ])

        prompt = f"""You are a financial news analyst tasked with identifying the most relevant headlines for trading decisions.

From the following headlines, select the TOP 20 most relevant for generating trading recommendations. Focus on:

1. **Earnings and Financial Results**: Earnings beats/misses, revenue surprises, guidance changes
2. **Corporate Actions**: M&A, IPOs, spin-offs, share buybacks, dividends
3. **FDA/Regulatory Approvals**: Drug approvals, clinical trial results, regulatory decisions
4. **Major Partnerships**: Strategic alliances, joint ventures, major contracts
5. **Leadership Changes**: CEO/CFO changes, board appointments
6. **Product Launches**: New product announcements, market expansions
7. **Legal Issues**: Lawsuits, settlements, regulatory investigations
8. **Market-Moving Events**: Economic data, sector-specific news
9. **Analyst Actions**: Upgrades, downgrades, price target changes
10. **Unexpected Catalysts**: Unusual events that could significantly impact stock prices

IGNORE general market commentary, routine corporate updates, and non-actionable news.

Headlines:
{headlines_text}

Return a JSON array with the indices (1-based) of the selected headlines, along with reasoning:

{{
    "selected_headlines": [
        {{
            "index": 1,
            "reasoning": "Brief explanation of why this headline is relevant for trading"
        }}
    ]
}}"""

        try:
            model_config = get_model_config(model)
            if model_config.provider == "openai":
                response = await self._call_openai(prompt, model, temperature=0.1)
            elif model_config.provider == "anthropic":
                response = await self._call_anthropic(prompt, model, temperature=0.1)
            else:
                raise ValueError(f"Unsupported provider for model {model}: {model_config.provider}")

            result = json.loads(response)
            return result.get("selected_headlines", [])
            
        except Exception as e:
            logging.error(f"Error analyzing headlines: {e}")
            # Fallback: return first 20 headlines
            return [{"index": i+1, "reasoning": "Fallback selection"} for i in range(min(20, len(headlines)))]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_sentiment(self, article: Dict, model: str = DEFAULT_MODEL) -> Dict:
        """Analyze sentiment and extract trading signals from an article"""
        
        content_preview = article.get('content', article.get('title', ''))[:2000]
        ticker = article.get('ticker', 'UNKNOWN')

        prompt = f"""You are an expert financial analyst specializing in news sentiment analysis for trading decisions.

Analyze the following news article and provide a comprehensive trading analysis:

**Title**: {article.get('title', 'N/A')}
**Ticker**: {ticker}
**Content Preview**: {content_preview}

Your analysis should include:

1. **Sentiment Score** (-1.0 to 1.0): Where -1.0 is extremely bearish, 0 is neutral, 1.0 is extremely bullish
2. **Confidence Level** (0.0 to 1.0): How confident you are in your analysis
3. **Key Catalysts**: Specific events or factors that could drive price movement
4. **Trading Reasoning**: Detailed explanation of why this news supports a particular trading position

**Catalyst Types to Look For**:
- Earnings beats/misses and guidance changes
- FDA approvals/rejections and clinical trial results
- M&A activity and strategic partnerships
- Legal developments and regulatory changes
- Management changes and corporate restructuring
- Product launches and market expansion
- Analyst upgrades/downgrades
- Unexpected positive/negative developments

Return your analysis in JSON format:

{{
    "sentiment_score": -0.8,
    "confidence": 0.9,
    "catalysts": [
        {{
            "type": "earnings_miss",
            "description": "Q3 earnings missed expectations by 15%",
            "impact": "negative",
            "significance": "high"
        }}
    ],
    "reasoning": "Detailed explanation of your analysis and trading rationale",
    "ticker_mentioned": "AAPL",
    "key_phrases": ["earnings miss", "guidance lowered", "revenue decline"]
}}"""

        try:
            model_config = get_model_config(model)
            if model_config.provider == "openai":
                response = await self._call_openai(prompt, model, temperature=0.2)
            elif model_config.provider == "anthropic":
                response = await self._call_anthropic(prompt, model, temperature=0.2)
            else:
                raise ValueError(f"Unsupported provider for model {model}: {model_config.provider}")

            result = json.loads(response)
            
            # Validate response structure
            required_fields = ["sentiment_score", "confidence", "catalysts", "reasoning"]
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid response structure")
            
            # Clamp values to valid ranges
            result["sentiment_score"] = max(-1.0, min(1.0, result["sentiment_score"]))
            result["confidence"] = max(0.0, min(1.0, result["confidence"]))
            
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            # Fallback neutral analysis
            return {
                "sentiment_score": 0.0,
                "confidence": 0.1,
                "catalysts": [],
                "reasoning": f"Error in analysis: {str(e)}",
                "ticker_mentioned": ticker,
                "key_phrases": []
            }

    async def generate_positions(self, analyses: List[Dict], max_positions: int = 10, min_confidence: float = 0.7) -> List[Dict]:
        """Generate trading positions based on sentiment analyses"""
        
        # Group analyses by ticker
        ticker_analyses = {}
        for analysis in analyses:
            ticker = analysis.get('ticker', 'UNKNOWN')
            if ticker not in ticker_analyses:
                ticker_analyses[ticker] = []
            ticker_analyses[ticker].append(analysis)

        positions = []
        
        for ticker, ticker_analysis_list in ticker_analyses.items():
            # Aggregate sentiment for this ticker
            total_sentiment = sum(a['sentiment_score'] for a in ticker_analysis_list)
            avg_sentiment = total_sentiment / len(ticker_analysis_list)
            avg_confidence = sum(a['confidence'] for a in ticker_analysis_list) / len(ticker_analysis_list)
            
            # Skip if confidence is too low
            if avg_confidence < min_confidence:
                continue
            
            # Determine position type based on sentiment
            if avg_sentiment > 0.7:
                position_type = "STRONG_BUY"
            elif avg_sentiment > 0.4:
                position_type = "BUY"
            elif avg_sentiment < -0.7:
                position_type = "STRONG_SHORT"
            elif avg_sentiment < -0.4:
                position_type = "SHORT"
            else:
                position_type = "HOLD"
            
            # Skip HOLD positions
            if position_type == "HOLD":
                continue
            
            # Combine catalysts and reasoning
            all_catalysts = []
            reasoning_parts = []
            
            for analysis in ticker_analysis_list:
                all_catalysts.extend(analysis.get('catalysts', []))
                reasoning_parts.append(analysis.get('reasoning', ''))
            
            combined_reasoning = f"Based on {len(ticker_analysis_list)} article(s): " + " | ".join(reasoning_parts)
            
            positions.append({
                'ticker': ticker,
                'position_type': position_type,
                'confidence': avg_confidence,
                'reasoning': combined_reasoning,
                'catalysts': all_catalysts,
                'supporting_articles': [a.get('article_id') for a in ticker_analysis_list if a.get('article_id')]
            })
        
        # Sort by confidence and limit to max_positions
        positions.sort(key=lambda x: x['confidence'], reverse=True)
        return positions[:max_positions]

    async def _call_openai(self, prompt: str, model: str, temperature: float = 0.1) -> str:
        """Call OpenAI API"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional financial analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}. Possible fixes: 1) Check API key validity, 2) Verify model '{model}' is available, 3) Check internet connection, 4) Verify account has sufficient credits"
            logging.error(error_msg)
            
            # Log to activity log if available
            try:
                from ..core.database import get_db
                from .activity_log_service import ActivityLogService
                
                db = next(get_db())
                activity_log = ActivityLogService(db)
                activity_log.log_llm_error(
                    model=model,
                    error=e,
                    prompt_type="openai_api_call"
                )
            except Exception:
                pass  # Don't fail if activity logging fails
                
            raise Exception(error_msg)

    async def _call_anthropic(self, prompt: str, model: str, temperature: float = 0.1) -> str:
        """Call Anthropic API"""
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nPlease respond with valid JSON only."}
                ]
            )
            return response.content[0].text
        except Exception as e:
            error_msg = f"Anthropic API error: {str(e)}. Possible fixes: 1) Check API key validity, 2) Verify model '{model}' is available, 3) Check internet connection, 4) Verify account has sufficient credits"
            logging.error(error_msg)
            
            # Log to activity log if available
            try:
                from ..core.database import get_db
                from .activity_log_service import ActivityLogService
                
                db = next(get_db())
                activity_log = ActivityLogService(db)
                activity_log.log_llm_error(
                    model=model,
                    error=e,
                    prompt_type="anthropic_api_call"
                )
            except Exception:
                pass  # Don't fail if activity logging fails
                
            raise Exception(error_msg)