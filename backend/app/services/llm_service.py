import openai
import anthropic
import json
import logging
import hashlib
import redis
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..config.models import get_model_config, DEFAULT_MODEL


class LLMService:
    def __init__(self):
        # Validate API keys on initialization
        if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
            logging.warning("OpenAI API key not configured. OpenAI models will not work.")
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your-anthropic-api-key-here":
            logging.warning("Anthropic API key not configured. Anthropic models will not work.")
            
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        # Initialize Redis cache
        try:
            self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logging.info("LLM cache connected to Redis")
        except Exception as e:
            logging.warning(f"Failed to connect to Redis cache: {e}. LLM caching disabled.")
            self.redis_client = None

    def _generate_cache_key(self, content: str, model: str, analysis_type: str) -> str:
        """Generate a unique cache key for LLM analysis"""
        # Create hash of content + model + analysis type
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        return f"llm_cache:{analysis_type}:{model}:{content_hash}"
    
    def _get_from_cache(self, cache_key: str, session_id: Optional[str] = None) -> Optional[Dict]:
        """Get cached LLM result"""
        if not self.redis_client:
            return None
        
        try:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                result = json.loads(cached_result)
                logging.info(f"LLM cache hit: {cache_key}")
                
                # Log cache hit to activity log if session provided
                if session_id:
                    try:
                        from ..core.database import get_db
                        from .activity_log_service import ActivityLogService
                        from uuid import UUID
                        
                        db = next(get_db())
                        activity_log = ActivityLogService(db)
                        
                        # Extract cache type from key
                        cache_parts = cache_key.split(":")
                        cache_type = cache_parts[1] if len(cache_parts) > 1 else "unknown"
                        model = cache_parts[2] if len(cache_parts) > 2 else "unknown"
                        
                        activity_log.log_cache_hit(
                            cache_type=cache_type,
                            model=model,
                            content_identifier=cache_key.split(":")[-1][:16],
                            session_id=UUID(session_id)
                        )
                    except Exception:
                        pass  # Don't fail if activity logging fails
                
                return result
        except Exception as e:
            logging.warning(f"Cache read error: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, result: Dict, ttl_hours: int = 24) -> None:
        """Cache LLM result"""
        if not self.redis_client:
            return
        
        try:
            # Cache for 24 hours by default
            ttl_seconds = ttl_hours * 3600
            self.redis_client.setex(
                cache_key, 
                ttl_seconds, 
                json.dumps(result, default=str)
            )
            logging.info(f"LLM result cached: {cache_key} (TTL: {ttl_hours}h)")
        except Exception as e:
            logging.warning(f"Cache write error: {e}")
    
    def _generate_headlines_content_hash(self, headlines: List[Dict], max_headlines: int) -> str:
        """Generate consistent hash for headlines analysis"""
        # Sort headlines by title to ensure consistent hashing regardless of order
        sorted_headlines = sorted(headlines, key=lambda x: x.get('title', ''))
        
        # Create content string from headlines + max_headlines
        content_parts = []
        for headline in sorted_headlines:
            content_parts.append(f"{headline.get('title', '')}|{headline.get('source', '')}")
        
        content_string = f"max_headlines:{max_headlines}|headlines:" + "|".join(content_parts)
        return content_string

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_headlines(self, headlines: List[Dict], model: str = DEFAULT_MODEL, max_headlines: int = 50, session_id: Optional[str] = None) -> List[Dict]:
        """Filter headlines to find the most relevant ones for trading analysis"""
        
        # Check cache first
        content_hash = self._generate_headlines_content_hash(headlines, max_headlines)
        cache_key = self._generate_cache_key(content_hash, model, "headlines")
        
        cached_result = self._get_from_cache(cache_key, session_id)
        if cached_result:
            return cached_result.get("selected_headlines", [])
        
        # Log cache miss
        if session_id:
            try:
                from ..core.database import get_db
                from .activity_log_service import ActivityLogService
                from uuid import UUID
                
                db = next(get_db())
                activity_log = ActivityLogService(db)
                activity_log.log_cache_miss(
                    cache_type="headlines",
                    model=model,
                    content_identifier=f"{len(headlines)} headlines",
                    session_id=UUID(session_id)
                )
            except Exception:
                pass  # Don't fail if activity logging fails
        
        headlines_text = "\n".join([
            f"{i+1}. {h['title']} (Source: {h['source']})"
            for i, h in enumerate(headlines)
        ])

        prompt = f"""You are a financial news analyst tasked with identifying the most relevant headlines for trading decisions.

From the following headlines, select the TOP {max_headlines} most relevant for generating trading recommendations. Focus on:

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
            
            # Cache the result
            self._set_cache(cache_key, result, ttl_hours=24)
            
            return result.get("selected_headlines", [])
            
        except Exception as e:
            logging.error(f"Error analyzing headlines: {e}")
            # Fallback: return first 20 headlines
            return [{"index": i+1, "reasoning": "Fallback selection"} for i in range(min(20, len(headlines)))]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_sentiment(self, article: Dict, model: str = DEFAULT_MODEL, session_id: Optional[str] = None) -> Dict:
        """Analyze sentiment and extract trading signals from an article"""
        
        content_preview = article.get('content', article.get('title', ''))[:2000]
        ticker = article.get('ticker', 'UNKNOWN')
        
        # Check cache first - use title + content preview for hashing
        cache_content = f"title:{article.get('title', '')}|content:{content_preview}|ticker:{ticker}"
        cache_key = self._generate_cache_key(cache_content, model, "sentiment")
        
        cached_result = self._get_from_cache(cache_key, session_id)
        if cached_result:
            return cached_result
        
        # Log cache miss
        if session_id:
            try:
                from ..core.database import get_db
                from .activity_log_service import ActivityLogService
                from uuid import UUID
                
                db = next(get_db())
                activity_log = ActivityLogService(db)
                activity_log.log_cache_miss(
                    cache_type="sentiment",
                    model=model,
                    content_identifier=f"{ticker}: {article.get('title', '')[:30]}...",
                    session_id=UUID(session_id)
                )
            except Exception:
                pass  # Don't fail if activity logging fails

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

            # Validate response before parsing
            if not response or response.strip() == "":
                raise ValueError("Empty response from LLM API")
            
            logging.debug(f"LLM response length: {len(response)}")
            logging.debug(f"LLM response preview: {response[:200]}...")
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON response from LLM: {response[:500]}...")
                raise ValueError(f"Invalid JSON response: {str(e)}")
            
            # Validate response structure
            required_fields = ["sentiment_score", "confidence", "catalysts", "reasoning"]
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid response structure")
            
            # Clamp values to valid ranges
            result["sentiment_score"] = max(-1.0, min(1.0, result["sentiment_score"]))
            result["confidence"] = max(0.0, min(1.0, result["confidence"]))
            
            # Cache the result
            self._set_cache(cache_key, result, ttl_hours=24)
            
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
        
        # Check cache first - create hash from analyses + parameters
        analysis_data = {
            'analyses': sorted(analyses, key=lambda x: x.get('ticker', '')),
            'max_positions': max_positions,
            'min_confidence': min_confidence
        }
        cache_content = json.dumps(analysis_data, sort_keys=True, default=str)
        cache_key = self._generate_cache_key(cache_content, "position_generation", "positions")
        
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result.get("positions", [])
        
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
        final_positions = positions[:max_positions]
        
        # Cache the result
        result = {"positions": final_positions}
        self._set_cache(cache_key, result, ttl_hours=24)
        
        return final_positions

    async def generate_market_summary(
        self, 
        articles: List[Dict], 
        analyses: List[Dict], 
        positions: List[Dict], 
        model: str = DEFAULT_MODEL,
        session_id: Optional[str] = None
    ) -> Dict:
        """Generate a comprehensive market summary from all analysis data"""
        
        # Check cache first
        summary_data = {
            'articles_count': len(articles),
            'analyses_count': len(analyses), 
            'positions_count': len(positions),
            'articles_sample': [a.get('title', '')[:100] for a in articles[:10]],
            'analyses_sample': [(a.get('ticker', ''), a.get('sentiment_score', 0)) for a in analyses[:10]],
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        cache_content = json.dumps(summary_data, sort_keys=True, default=str)
        cache_key = self._generate_cache_key(cache_content, model, "market_summary")
        
        cached_result = self._get_from_cache(cache_key, session_id)
        if cached_result:
            return cached_result
        
        # Log cache miss
        if session_id:
            try:
                from ..core.database import get_db
                from .activity_log_service import ActivityLogService
                from uuid import UUID
                
                db = next(get_db())
                activity_log = ActivityLogService(db)
                activity_log.log_cache_miss(
                    cache_type="market_summary",
                    model=model,
                    content_identifier=f"Daily summary {datetime.now().strftime('%Y-%m-%d')}",
                    session_id=UUID(session_id)
                )
            except Exception:
                pass

        # Prepare data for summary
        top_articles = articles[:15]  # Top 15 most recent articles
        sentiment_scores = [a.get('sentiment_score', 0) for a in analyses]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # Group analyses by ticker
        ticker_sentiments = {}
        for analysis in analyses:
            ticker = analysis.get('ticker', 'UNKNOWN')
            if ticker != 'UNKNOWN':
                if ticker not in ticker_sentiments:
                    ticker_sentiments[ticker] = []
                ticker_sentiments[ticker].append({
                    'sentiment': analysis.get('sentiment_score', 0),
                    'confidence': analysis.get('confidence', 0),
                    'catalysts': analysis.get('catalysts', [])
                })

        # Aggregate ticker data
        ticker_summary = {}
        for ticker, analyses_list in ticker_sentiments.items():
            avg_sent = sum(a['sentiment'] for a in analyses_list) / len(analyses_list)
            avg_conf = sum(a['confidence'] for a in analyses_list) / len(analyses_list)
            all_catalysts = []
            for a in analyses_list:
                all_catalysts.extend(a['catalysts'])
            
            ticker_summary[ticker] = {
                'sentiment': avg_sent,
                'confidence': avg_conf,
                'mention_count': len(analyses_list),
                'catalysts': all_catalysts[:5]  # Top 5 catalysts
            }

        # Sort tickers by sentiment and confidence
        top_bullish = sorted(ticker_summary.items(), 
                           key=lambda x: (x[1]['sentiment'], x[1]['confidence']), 
                           reverse=True)[:5]
        top_bearish = sorted(ticker_summary.items(), 
                           key=lambda x: (x[1]['sentiment'], -x[1]['confidence']))[:5]

        prompt = f"""You are a professional financial market analyst. Generate a comprehensive daily market summary based on the following data from {len(articles)} news articles and {len(analyses)} AI analyses.

**MARKET DATA OVERVIEW:**
- Total Articles Analyzed: {len(articles)}
- Average Market Sentiment: {avg_sentiment:.2f} (scale: -1 to +1)
- Number of Unique Stocks: {len(ticker_summary)}
- Trading Positions Generated: {len(positions)}

**TOP HEADLINES TODAY:**
{chr(10).join([f"• {article.get('title', 'N/A')}" for article in top_articles[:10]])}

**MOST BULLISH STOCKS (Top 5):**
{chr(10).join([f"• {ticker}: {data['sentiment']:.2f} sentiment, {data['mention_count']} mentions" for ticker, data in top_bullish])}

**MOST BEARISH STOCKS (Top 5):**
{chr(10).join([f"• {ticker}: {data['sentiment']:.2f} sentiment, {data['mention_count']} mentions" for ticker, data in top_bearish])}

**TRADING POSITIONS RECOMMENDED:**
{chr(10).join([f"• {pos.get('ticker', 'N/A')}: {pos.get('position_type', 'N/A')} (confidence: {pos.get('confidence', 0):.2f})" for pos in positions[:8]])}

Generate a comprehensive market summary with the following sections:

1. **Overall Market Sentiment**: Brief assessment of today's market mood
2. **Key Market Themes**: 3-4 dominant themes driving today's news
3. **Stocks to Watch**: Top 5-8 stocks with reasoning for why they're important today
4. **Notable Catalysts**: Most significant events/news that could move markets
5. **Risk Factors**: Any concerns or negative developments to monitor

Keep the summary professional, concise but informative (400-600 words total). Focus on actionable insights for traders and investors.

Return your response in JSON format:

{{
    "overall_sentiment": "Brief market mood assessment",
    "sentiment_score": 0.15,  // Overall sentiment score (-1 to +1)
    "key_themes": [
        "Theme 1 description",
        "Theme 2 description", 
        "Theme 3 description"
    ],
    "stocks_to_watch": [
        {{
            "ticker": "AAPL",
            "reason": "Why this stock is important today",
            "sentiment": "bullish|bearish|neutral",
            "confidence": 0.85
        }}
    ],
    "notable_catalysts": [
        {{
            "type": "earnings|fda|merger|etc",
            "description": "Description of the catalyst",
            "impact": "positive|negative",
            "affected_stocks": ["AAPL", "MSFT"]
        }}
    ],
    "risk_factors": [
        "Risk factor 1",
        "Risk factor 2"
    ],
    "summary": "2-3 paragraph executive summary of today's market landscape"
}}"""

        try:
            model_config = get_model_config(model)
            if model_config.provider == "openai":
                response = await self._call_openai(prompt, model, temperature=0.3)
            elif model_config.provider == "anthropic":
                response = await self._call_anthropic(prompt, model, temperature=0.3)
            else:
                raise ValueError(f"Unsupported provider for model {model}: {model_config.provider}")

            result = json.loads(response)
            
            # Add metadata
            result['generated_at'] = datetime.now(timezone.utc).isoformat()
            result['model_used'] = model
            result['data_sources'] = {
                'articles_analyzed': len(articles),
                'sentiment_analyses': len(analyses),
                'positions_generated': len(positions),
                'unique_tickers': len(ticker_summary)
            }
            
            # Cache the result for 2 hours (market summaries can be shorter lived)
            self._set_cache(cache_key, result, ttl_hours=2)
            
            return result
            
        except Exception as e:
            logging.error(f"Error generating market summary: {e}")
            error_msg = str(e)
            
            # Check for specific API key issues
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                error_msg = "API authentication failed. Please check your API keys."
                summary_text = f"Unable to generate AI-powered market summary due to API authentication issues. Please verify your OpenAI/Anthropic API keys are configured correctly."
            elif "expecting value" in error_msg.lower():
                error_msg = "Empty response from AI model"
                summary_text = f"AI model returned an empty response. This may indicate API quota exhaustion or model unavailability."
            else:
                summary_text = f"Analysis encountered an error: {error_msg}"
            
            # Generate basic summary from available data without LLM
            basic_summary = self._generate_basic_market_summary(
                articles, analyses, positions, ticker_summary if 'ticker_summary' in locals() else {}, avg_sentiment
            )
            
            # Return informative fallback summary with basic analysis
            return {
                "overall_sentiment": basic_summary["overall_sentiment"],
                "sentiment_score": avg_sentiment,
                "key_themes": basic_summary["key_themes"],
                "stocks_to_watch": basic_summary["stocks_to_watch"],
                "notable_catalysts": basic_summary["notable_catalysts"],
                "risk_factors": basic_summary["risk_factors"],
                "summary": f"{summary_text} However, basic analysis from {len(articles)} articles and {len(analyses)} analyses is available below.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_used": f"{model} (fallback)",
                "data_sources": {
                    "articles_analyzed": len(articles),
                    "sentiment_analyses": len(analyses), 
                    "positions_generated": len(positions),
                    "unique_tickers": len(ticker_summary) if 'ticker_summary' in locals() else 0
                },
                "error": error_msg
            }

    def _generate_basic_market_summary(self, articles: List[Dict], analyses: List[Dict], positions: List[Dict], ticker_summary: Dict, avg_sentiment: float) -> Dict:
        """Generate a basic market summary without LLM when APIs are unavailable"""
        
        # Basic sentiment assessment
        if avg_sentiment > 0.3:
            sentiment_desc = "Generally positive market sentiment detected"
        elif avg_sentiment < -0.3:
            sentiment_desc = "Generally negative market sentiment detected"
        else:
            sentiment_desc = "Mixed market sentiment with neutral overall tone"
        
        # Top articles by source
        source_counts = {}
        for article in articles[:10]:
            source = article.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Key themes based on data patterns
        themes = []
        if len(analyses) > 0:
            themes.append(f"Analyzed sentiment across {len(set(a.get('ticker', 'N/A') for a in analyses))} different stocks")
        if len(articles) > 20:
            themes.append("High volume of financial news indicates active market conditions")
        if source_counts:
            top_source = max(source_counts.keys(), key=lambda x: source_counts[x])
            themes.append(f"Primary news source: {top_source.upper()} ({source_counts[top_source]} articles)")
        
        # Stocks to watch - top by sentiment and confidence
        stocks_to_watch = []
        for ticker, data in list(ticker_summary.items())[:5]:
            if ticker != 'UNKNOWN':
                sentiment_label = "bullish" if data['sentiment'] > 0.2 else "bearish" if data['sentiment'] < -0.2 else "neutral"
                stocks_to_watch.append({
                    "ticker": ticker,
                    "reason": f"Mentioned in {data['mention_count']} articles with {data['confidence']:.1%} average confidence",
                    "sentiment": sentiment_label,
                    "confidence": data['confidence']
                })
        
        # Notable catalysts from analysis data
        catalysts = []
        catalyst_types = set()
        for analysis in analyses[:20]:
            for catalyst in analysis.get('catalysts', []):
                if catalyst.get('type') not in catalyst_types:
                    catalysts.append({
                        "type": catalyst.get('type', 'market_event'),
                        "description": catalyst.get('description', 'Market-moving event detected'),
                        "impact": catalyst.get('impact', 'neutral'),
                        "affected_stocks": [analysis.get('ticker', 'N/A')]
                    })
                    catalyst_types.add(catalyst.get('type'))
                    if len(catalysts) >= 3:
                        break
        
        # Basic risk factors
        risk_factors = []
        if avg_sentiment < -0.1:
            risk_factors.append("Overall negative sentiment may indicate market uncertainty")
        if len(positions) > 0:
            short_positions = [p for p in positions if p.get('position_type', '').endswith('SHORT')]
            if len(short_positions) > len(positions) * 0.3:
                risk_factors.append("High proportion of short positions suggests bearish outlook")
        if not risk_factors:
            risk_factors.append("Standard market risks apply - monitor for volatility")
        
        return {
            "overall_sentiment": sentiment_desc,
            "key_themes": themes[:3] if themes else ["Limited market data available"],
            "stocks_to_watch": stocks_to_watch,
            "notable_catalysts": catalysts,
            "risk_factors": risk_factors
        }

    async def _call_openai(self, prompt: str, model: str, temperature: float = 0.1) -> str:
        """Call OpenAI API"""
        # Check API key configuration first
        if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here":
            raise Exception("OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.")
        
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
            content = response.choices[0].message.content
            if not content or content.strip() == "":
                raise Exception("OpenAI API returned empty response")
            return content
        except Exception as e:
            # Check for authentication errors
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str or "401" in error_str:
                error_msg = f"OpenAI API authentication failed. Please check your OPENAI_API_KEY in .env file. Error: {str(e)}"
            else:
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
        # Check API key configuration first
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your-anthropic-api-key-here":
            raise Exception("Anthropic API key not configured. Please set ANTHROPIC_API_KEY in your .env file.")
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nPlease respond with valid JSON only."}
                ]
            )
            content = response.content[0].text
            if not content or content.strip() == "":
                raise Exception("Anthropic API returned empty response")
            return content
        except Exception as e:
            # Check for authentication errors
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str or "401" in error_str or "unauthorized" in error_str:
                error_msg = f"Anthropic API authentication failed. Please check your ANTHROPIC_API_KEY in .env file. Error: {str(e)}"
            else:
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

    # Cache management methods
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"cache_enabled": False}
        
        try:
            info = self.redis_client.info()
            
            # Get LLM cache keys
            llm_keys = self.redis_client.keys("llm_cache:*")
            
            # Group by analysis type
            cache_stats = {
                "cache_enabled": True,
                "total_keys": len(llm_keys),
                "headline_cache_count": len([k for k in llm_keys if ":headlines:" in k]),
                "sentiment_cache_count": len([k for k in llm_keys if ":sentiment:" in k]),
                "position_cache_count": len([k for k in llm_keys if ":positions:" in k]),
                "memory_used": info.get("used_memory_human", "Unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
            
            # Calculate hit rate
            total_requests = cache_stats["hits"] + cache_stats["misses"]
            if total_requests > 0:
                cache_stats["hit_rate"] = round((cache_stats["hits"] / total_requests) * 100, 2)
            else:
                cache_stats["hit_rate"] = 0
            
            return cache_stats
            
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return {"cache_enabled": True, "error": str(e)}
    
    def clear_cache(self, cache_type: Optional[str] = None) -> Dict[str, int]:
        """Clear LLM cache"""
        if not self.redis_client:
            return {"deleted": 0}
        
        try:
            if cache_type:
                # Clear specific cache type
                pattern = f"llm_cache:{cache_type}:*"
                keys = self.redis_client.keys(pattern)
            else:
                # Clear all LLM cache
                keys = self.redis_client.keys("llm_cache:*")
            
            deleted_count = 0
            if keys:
                deleted_count = self.redis_client.delete(*keys)
            
            logging.info(f"Cleared {deleted_count} LLM cache entries (type: {cache_type or 'all'})")
            return {"deleted": deleted_count}
            
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")
            return {"deleted": 0, "error": str(e)}