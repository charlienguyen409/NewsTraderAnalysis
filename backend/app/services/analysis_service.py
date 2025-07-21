import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID
from sqlalchemy.orm import Session

from .scraper import NewsScraper
from .llm_service import LLMService
from .crud import article_crud, analysis_crud, position_crud, market_summary_crud
from .activity_log_service import ActivityLogService
from ..models.article import Article
from ..models.market_summary import AnalysisTypeEnum
from ..schemas.analysis_request import AnalysisRequest
from ..schemas.article import ArticleCreate
from ..schemas.analysis import AnalysisCreate
from ..schemas.position import PositionCreate
from ..schemas.market_summary import MarketSummaryCreate
from ..models.position import PositionType


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.activity_log = ActivityLogService(db)

    async def run_analysis(self, session_id: UUID, request: AnalysisRequest):
        """Run complete market analysis pipeline"""
        try:
            logging.info(f"Starting analysis session {session_id}")
            start_time = datetime.now()
            
            # Log analysis start
            self.activity_log.log_analysis_progress(
                "start_analysis",
                f"Starting market analysis session with {len(request.sources)} sources",
                session_id,
                {"sources": request.sources, "llm_model": request.llm_model}
            )
            
            # Step 1: Scrape news articles
            await self._broadcast_status(session_id, "scraping", "Scraping financial news sources...")
            articles = await self._scrape_news_sources(request.sources, session_id)
            
            if not articles:
                await self._broadcast_status(session_id, "error", "No articles found")
                self.activity_log.log_analysis_progress(
                    "error_no_articles",
                    "No articles found from any source",
                    session_id
                )
                return
            
            # Step 2: Filter relevant headlines using LLM
            await self._broadcast_status(session_id, "filtering", f"Filtering {len(articles)} headlines for relevance...")
            relevant_articles = await self._filter_relevant_headlines(articles, request.llm_model, session_id, max_headlines=100)
            
            # Step 3: Scrape full article content
            await self._broadcast_status(session_id, "content_scraping", f"Scraping content for {len(relevant_articles)} articles...")
            articles_with_content = await self._scrape_article_contents(relevant_articles, session_id)
            
            # Step 4: Store articles in database
            await self._broadcast_status(session_id, "storing", "Storing articles in database...")
            stored_articles = await self._store_articles(articles_with_content, session_id)
            
            # Step 5: Analyze sentiment for each article
            await self._broadcast_status(session_id, "analyzing", f"Analyzing sentiment for {len(stored_articles)} articles...")
            analyses = await self._analyze_articles(stored_articles, request.llm_model, session_id)
            
            # Step 6: Generate trading positions
            await self._broadcast_status(session_id, "generating", "Generating trading recommendations...")
            positions = await self._generate_positions(
                analyses, session_id, request.max_positions, request.min_confidence
            )
            
            # Step 7: Generate market summary
            await self._broadcast_status(session_id, "summarizing", "Generating daily market summary...")
            market_summary = await self._generate_market_summary(stored_articles, analyses, positions, request.llm_model, session_id, "full")
            
            # Step 8: Complete analysis
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log completion
            self.activity_log.log_analysis_progress(
                "complete_analysis",
                f"Analysis completed successfully in {duration:.2f}s",
                session_id,
                {
                    "positions_count": len(positions),
                    "articles_analyzed": len(stored_articles),
                    "duration": duration,
                    "articles_scraped": len(articles),
                    "articles_filtered": len(relevant_articles),
                    "market_summary_generated": True
                }
            )
            
            await self._broadcast_status(
                session_id, 
                "completed", 
                f"Analysis complete! Generated {len(positions)} positions from {len(stored_articles)} articles",
                {
                    "positions_count": len(positions),
                    "articles_analyzed": len(stored_articles),
                    "duration": duration
                }
            )
            
            logging.info(f"Analysis session {session_id} completed in {duration:.2f}s")
            
            return market_summary
            
        except Exception as e:
            logging.error(f"Error in analysis session {session_id}: {e}")
            await self._broadcast_status(session_id, "error", f"Analysis failed: {str(e)}")

    async def run_headline_analysis(self, session_id: UUID, request: AnalysisRequest):
        """Run headline-only analysis pipeline (no full article content scraping)"""
        try:
            logging.info(f"Starting headline analysis session {session_id}")
            start_time = datetime.now()
            
            # Log analysis start
            self.activity_log.log_analysis_progress(
                "start_headline_analysis",
                f"Starting headline-only analysis with {len(request.sources)} sources",
                session_id,
                {"sources": request.sources, "llm_model": request.llm_model, "analysis_type": "headlines"}
            )
            
            # Step 1: Scrape news headlines
            await self._broadcast_status(session_id, "scraping", "Scraping financial news headlines...")
            articles = await self._scrape_news_sources(request.sources, session_id)
            
            if not articles:
                await self._broadcast_status(session_id, "error", "No articles found")
                self.activity_log.log_analysis_progress(
                    "error_no_articles",
                    "No articles found from any source",
                    session_id
                )
                return
            
            # Step 2: Filter relevant headlines using LLM
            await self._broadcast_status(session_id, "filtering", f"Filtering {len(articles)} headlines for relevance...")
            relevant_articles = await self._filter_relevant_headlines(articles, request.llm_model, session_id, max_headlines=100)
            
            # Step 3: Store articles (with headlines only - no content scraping)
            await self._broadcast_status(session_id, "storing", "Storing headline data...")
            stored_articles = await self._store_articles(relevant_articles, session_id)
            
            # Step 4: Analyze headlines using LLM (no full content)
            await self._broadcast_status(session_id, "analyzing", f"Analyzing {len(stored_articles)} headlines...")
            analyses = await self._analyze_headlines_only(stored_articles, request.llm_model, session_id)
            
            # Step 5: Generate trading positions with headline indicator
            await self._broadcast_status(session_id, "generating", "Generating headline-based recommendations...")
            positions = await self._generate_headline_positions(
                analyses, session_id, request.max_positions, request.min_confidence
            )
            
            # Step 6: Generate market summary
            await self._broadcast_status(session_id, "summarizing", "Generating daily market summary...")
            market_summary = await self._generate_market_summary(stored_articles, analyses, positions, request.llm_model, session_id, "headlines")
            
            # Step 7: Complete analysis
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log completion
            self.activity_log.log_analysis_progress(
                "complete_headline_analysis",
                f"Headline analysis completed successfully in {duration:.2f}s",
                session_id,
                {
                    "positions_count": len(positions),
                    "headlines_analyzed": len(stored_articles),
                    "duration": duration,
                    "headlines_scraped": len(articles),
                    "headlines_filtered": len(relevant_articles),
                    "analysis_type": "headlines"
                }
            )
            
            await self._broadcast_status(
                session_id, 
                "completed", 
                f"Headline analysis complete! Generated {len(positions)} positions from {len(stored_articles)} headlines",
                {
                    "positions_count": len(positions),
                    "articles_analyzed": len(stored_articles),
                    "duration": duration,
                    "analysis_type": "headlines"
                }
            )
            
            logging.info(f"Headline analysis session {session_id} completed in {duration:.2f}s")
            
            return market_summary
            
        except Exception as e:
            logging.error(f"Error in headline analysis session {session_id}: {e}")
            await self._broadcast_status(session_id, "error", f"Headline analysis failed: {str(e)}")

    async def _scrape_news_sources(self, sources: List[str], session_id: UUID) -> List[Dict]:
        """Scrape news from specified sources using enhanced scraper"""
        all_articles = []
        
        async with NewsScraper() as scraper:
            # Use existing scraping methods
            tasks = []
            tasks.append(scraper.scrape_finviz())
            tasks.append(scraper.scrape_biztoc())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logging.error(f"Scraping failed: {str(result)}")
                    self.activity_log.log_error(
                        "scraping",
                        "scrape_sources",
                        result,
                        session_id=session_id
                    )
            
            # Log scraping results
            sources_found = {}
            for article in all_articles:
                source = article.get('source', 'unknown')
                sources_found[source] = sources_found.get(source, 0) + 1
            
            for source, count in sources_found.items():
                logging.info(f"Scraped {count} articles from {source}")
            
            # Remove any None or invalid articles
            all_articles = [article for article in all_articles if article and article.get('title')]
        
        return all_articles

    async def _filter_relevant_headlines(self, articles: List[Dict], model: str, session_id: UUID, max_headlines: int = 50) -> List[Dict]:
        """Filter headlines for trading relevance using LLM"""
        try:
            # First deduplicate articles by title similarity and date
            deduplicated_articles = self._deduplicate_articles(articles)
            
            selected_indices = await self.llm_service.analyze_headlines(deduplicated_articles, model, max_headlines, str(session_id))
            relevant_articles = []
            
            for selection in selected_indices:
                index = selection.get("index", 0) - 1  # Convert to 0-based
                if 0 <= index < len(deduplicated_articles):
                    article = deduplicated_articles[index].copy()
                    article["selection_reasoning"] = selection.get("reasoning", "")
                    relevant_articles.append(article)
            
            # Log headline filtering results
            selected_headlines = [
                {
                    "title": article.get("title", ""),
                    "reasoning": article.get("selection_reasoning", "")
                }
                for article in relevant_articles[:5]  # First 5 for logging
            ]
            
            self.activity_log.log_headline_filtering(
                len(deduplicated_articles),
                len(relevant_articles),
                session_id,
                selected_headlines=selected_headlines,
                reasoning=f"LLM selected {len(relevant_articles)} articles from {len(deduplicated_articles)} deduplicated articles (originally {len(articles)})"
            )
            
            return relevant_articles
            
        except Exception as e:
            logging.error(f"Error filtering headlines: {e}")
            self.activity_log.log_error(
                "analysis",
                "filter_headlines",
                e,
                context={"total_articles": len(articles), "model": model},
                session_id=session_id
            )
            # Fallback: return first 20 articles
            return articles[:20]

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Deduplicate articles by title similarity and date"""
        from datetime import datetime
        import difflib
        
        if not articles:
            return articles
        
        deduplicated = []
        seen_titles = []
        
        for article in articles:
            title = article.get('title', '').strip().lower()
            published_at = article.get('published_at')
            
            # Skip if no title
            if not title:
                continue
            
            # Check for similar titles (85% similarity threshold)
            is_duplicate = False
            for seen_title, seen_date in seen_titles:
                similarity = difflib.SequenceMatcher(None, title, seen_title).ratio()
                
                # If titles are very similar (85%+) and from same day, skip
                if similarity >= 0.85:
                    # Check if same day
                    if published_at and seen_date:
                        try:
                            if isinstance(published_at, str):
                                pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
                            else:
                                pub_date = published_at.date()
                            
                            if isinstance(seen_date, str):
                                seen_date_obj = datetime.fromisoformat(seen_date.replace('Z', '+00:00')).date()
                            else:
                                seen_date_obj = seen_date.date()
                            
                            if pub_date == seen_date_obj:
                                is_duplicate = True
                                break
                        except:
                            # If date parsing fails, still consider it duplicate if titles are very similar
                            is_duplicate = True
                            break
                    else:
                        # No date info, just use title similarity
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(article)
                seen_titles.append((title, published_at))
        
        duplicates_found = len(articles) - len(deduplicated)
        logging.info(f"Deduplicated {len(articles)} articles to {len(deduplicated)} unique articles")
        
        return deduplicated

    async def _scrape_article_contents(self, articles: List[Dict], session_id: UUID) -> List[Dict]:
        """Scrape full content for filtered articles"""
        async with NewsScraper() as scraper:
            tasks = [
                scraper.scrape_article_content(article["url"]) 
                for article in articles
            ]
            
            contents = await asyncio.gather(*tasks, return_exceptions=True)
            
            articles_with_content = []
            for i, (article, content) in enumerate(zip(articles, contents)):
                if isinstance(content, str) and content:
                    article["content"] = content
                    articles_with_content.append(article)
                else:
                    logging.warning(f"Failed to scrape content for: {article['url']}")
            
            return articles_with_content

    async def _store_articles(self, articles: List[Dict], session_id: UUID) -> List[Dict]:
        """Store articles in database"""
        stored_articles = []
        
        for article_data in articles:
            try:
                article_create = ArticleCreate(
                    url=article_data["url"],
                    title=article_data["title"],
                    content=article_data.get("content"),
                    source=article_data["source"],
                    ticker=article_data.get("ticker"),
                    published_at=article_data.get("published_at"),
                    article_metadata=article_data.get("article_metadata", {})
                )
                
                # Check if article already exists (by URL or by title+date)
                existing = self.db.query(Article).filter(Article.url == article_create.url).first()
                
                if not existing and article_create.title and article_create.published_at:
                    # Also check for similar title on same date
                    from datetime import datetime, timedelta
                    
                    # Get date range (same day)
                    if isinstance(article_create.published_at, str):
                        pub_date = datetime.fromisoformat(article_create.published_at.replace('Z', '+00:00'))
                    else:
                        pub_date = article_create.published_at
                    
                    start_date = pub_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=1)
                    
                    # Look for articles with similar titles on the same date
                    same_day_articles = self.db.query(Article).filter(
                        Article.published_at >= start_date,
                        Article.published_at < end_date,
                        Article.title.isnot(None)
                    ).all()
                    
                    # Check title similarity
                    import difflib
                    for same_day_article in same_day_articles:
                        if same_day_article.title:
                            similarity = difflib.SequenceMatcher(
                                None, 
                                article_create.title.lower().strip(), 
                                same_day_article.title.lower().strip()
                            ).ratio()
                            
                            if similarity >= 0.85:  # 85% similarity threshold
                                existing = same_day_article
                                break
                
                if existing:
                    # Log database article reuse
                    reuse_reason = "URL match" if existing.url == article_create.url else "Title similarity + same date"
                    self.activity_log.log_database_article_reuse(
                        article_url=existing.url,
                        article_title=existing.title or "No title",
                        reuse_reason=reuse_reason,
                        session_id=session_id
                    )
                    
                    stored_articles.append({
                        **article_data,
                        "article_id": existing.id
                    })
                else:
                    db_article = article_crud.create_article(self.db, article_create)
                    stored_articles.append({
                        **article_data,
                        "article_id": db_article.id
                    })
                    
            except Exception as e:
                logging.error(f"Error storing article {article_data.get('url', 'unknown')}: {e}")
                self.activity_log.log_error(
                    "database",
                    "store_article",
                    e,
                    context={"url": article_data.get('url', 'unknown')},
                    session_id=session_id
                )
        
        # Log storage results
        self.activity_log.log_analysis_progress(
            "store_articles",
            f"Stored {len(stored_articles)} articles in database",
            session_id,
            {"stored_count": len(stored_articles), "attempted_count": len(articles)}
        )
        
        return stored_articles

    async def _analyze_articles(self, articles: List[Dict], model: str, session_id: UUID) -> List[Dict]:
        """Analyze sentiment for each article"""
        analyses = []
        
        for i, article in enumerate(articles, 1):
            try:
                # Log real-time progress
                article_title = article.get("title", "Unknown Article")
                self.activity_log.log_task_progress(
                    task_name="Sentiment Analysis",
                    current_item=i,
                    total_items=len(articles),
                    item_identifier=f"{article.get('ticker', 'N/A')}: {article_title}",
                    session_id=session_id
                )
                
                sentiment_analysis = await self.llm_service.analyze_sentiment(article, model, str(session_id))
                
                # Log individual LLM analysis
                self.activity_log.log_llm_analysis(
                    model,
                    "sentiment_analysis",
                    article.get("title", ""),
                    session_id,
                    analysis_result=sentiment_analysis,
                    reasoning=sentiment_analysis.get("reasoning", "")
                )
                
                # Store analysis in database
                ticker_value = sentiment_analysis.get("ticker_mentioned") or article.get("ticker") or "UNKNOWN"
                analysis_create = AnalysisCreate(
                    article_id=article["article_id"],
                    ticker=ticker_value,
                    sentiment_score=sentiment_analysis["sentiment_score"],
                    confidence=sentiment_analysis["confidence"],
                    catalysts=sentiment_analysis.get("catalysts", []),
                    reasoning=sentiment_analysis["reasoning"],
                    llm_model=model,
                    raw_response=sentiment_analysis
                )
                
                db_analysis = analysis_crud.create_analysis(self.db, analysis_create)
                
                # Mark article as processed
                db_article = self.db.query(Article).filter(Article.id == article["article_id"]).first()
                if db_article:
                    db_article.is_processed = True
                    self.db.commit()
                
                analyses.append({
                    **sentiment_analysis,
                    "article_id": article["article_id"],
                    "analysis_id": db_analysis.id,
                    "ticker": analysis_create.ticker
                })
                
            except Exception as e:
                logging.error(f"Error analyzing article {article.get('article_id')}: {e}")
                self.activity_log.log_error(
                    "llm",
                    "sentiment_analysis",
                    e,
                    context={"article_id": article.get('article_id'), "model": model},
                    session_id=session_id
                )
        
        # Log analysis completion
        self.activity_log.log_analysis_progress(
            "complete_sentiment_analysis",
            f"Completed sentiment analysis for {len(analyses)} articles",
            session_id,
            {"successful_analyses": len(analyses), "attempted_analyses": len(articles)}
        )
        
        return analyses

    async def _generate_positions(
        self, 
        analyses: List[Dict], 
        session_id: UUID, 
        max_positions: int, 
        min_confidence: float
    ) -> List[Dict]:
        """Generate trading positions from analyses"""
        try:
            positions_data = await self.llm_service.generate_positions(
                analyses, max_positions, min_confidence
            )
            
            stored_positions = []
            for position_data in positions_data:
                try:
                    position_create = PositionCreate(
                        ticker=position_data["ticker"],
                        position_type=PositionType(position_data["position_type"]),
                        confidence=position_data["confidence"],
                        reasoning=position_data["reasoning"],
                        catalysts=position_data.get("catalysts", []),
                        supporting_articles=[str(article_id) for article_id in position_data.get("supporting_articles", [])],
                        analysis_session_id=session_id
                    )
                    
                    db_position = position_crud.create_position(self.db, position_create)
                    stored_positions.append(db_position)
                    
                    # Log each position generation
                    self.activity_log.log_position_generation(
                        position_data["ticker"],
                        position_data["position_type"],
                        position_data["confidence"],
                        session_id,
                        reasoning=position_data["reasoning"],
                        catalyst=position_data.get("catalysts", [None])[0] if position_data.get("catalysts") else None
                    )
                    
                except Exception as e:
                    logging.error(f"Error storing position for {position_data.get('ticker')}: {e}")
                    self.activity_log.log_error(
                        "database",
                        "store_position",
                        e,
                        context={"ticker": position_data.get('ticker')},
                        session_id=session_id
                    )
            
            # Log position generation completion
            self.activity_log.log_analysis_progress(
                "complete_position_generation",
                f"Generated {len(stored_positions)} trading positions",
                session_id,
                {
                    "positions_generated": len(stored_positions),
                    "positions_attempted": len(positions_data),
                    "max_positions": max_positions,
                    "min_confidence": min_confidence
                }
            )
            
            return stored_positions
            
        except Exception as e:
            logging.error(f"Error generating positions: {e}")
            self.activity_log.log_error(
                "llm",
                "generate_positions",
                e,
                context={"analyses_count": len(analyses)},
                session_id=session_id
            )
            return []

    async def _analyze_headlines_only(self, articles: List[Dict], model: str, session_id: UUID) -> List[Dict]:
        """Analyze sentiment based on headlines only (no full content)"""
        analyses = []
        
        for i, article in enumerate(articles, 1):
            try:
                # Log real-time progress
                article_title = article.get("title", "Unknown Article")
                self.activity_log.log_task_progress(
                    task_name="Headlines Sentiment Analysis",
                    current_item=i,
                    total_items=len(articles),
                    item_identifier=f"{article.get('ticker', 'N/A')}: {article_title}",
                    session_id=session_id
                )
                
                # Create a simplified article dict with just headline and metadata
                headline_article = {
                    'title': article.get('title', ''),
                    'source': article.get('source', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('published_at'),
                    'content': f"Headline: {article.get('title', '')}"  # Use headline as content
                }
                
                sentiment_analysis = await self.llm_service.analyze_sentiment(headline_article, model, str(session_id))
                
                # Log individual LLM analysis
                self.activity_log.log_llm_analysis(
                    model,
                    "headline_sentiment_analysis",
                    article.get("title", ""),
                    session_id,
                    analysis_result=sentiment_analysis,
                    reasoning=f"Headline-only analysis: {sentiment_analysis.get('reasoning', '')}"
                )
                
                # Store analysis in database with headline indicator
                ticker_value = sentiment_analysis.get("ticker_mentioned") or article.get("ticker") or "UNKNOWN"
                analysis_create = AnalysisCreate(
                    article_id=article["article_id"],
                    ticker=ticker_value,
                    sentiment_score=sentiment_analysis["sentiment_score"],
                    confidence=sentiment_analysis["confidence"],
                    catalysts=sentiment_analysis.get("catalysts", []),
                    reasoning=f"[HEADLINE ANALYSIS] {sentiment_analysis['reasoning']}",  # Add indicator
                    llm_model=model,
                    raw_response={
                        **sentiment_analysis,
                        "analysis_type": "headlines_only"
                    }
                )
                
                db_analysis = analysis_crud.create_analysis(self.db, analysis_create)
                
                # Mark article as processed
                db_article = self.db.query(Article).filter(Article.id == article["article_id"]).first()
                if db_article:
                    db_article.is_processed = True
                    self.db.commit()
                
                analyses.append({
                    **sentiment_analysis,
                    "article_id": article["article_id"],
                    "analysis_id": db_analysis.id,
                    "ticker": analysis_create.ticker,
                    "analysis_type": "headlines_only"
                })
                
            except Exception as e:
                logging.error(f"Error analyzing headline {article.get('article_id')}: {e}")
                self.activity_log.log_error(
                    "llm",
                    "headline_sentiment_analysis",
                    e,
                    context={"article_id": article.get('article_id'), "model": model},
                    session_id=session_id
                )
        
        # Log analysis completion
        self.activity_log.log_analysis_progress(
            "complete_headline_sentiment_analysis",
            f"Completed headline sentiment analysis for {len(analyses)} articles",
            session_id,
            {"successful_analyses": len(analyses), "attempted_analyses": len(articles), "analysis_type": "headlines"}
        )
        
        return analyses

    async def _generate_headline_positions(
        self, 
        analyses: List[Dict], 
        session_id: UUID, 
        max_positions: int, 
        min_confidence: float
    ) -> List[Dict]:
        """Generate trading positions from headline analyses with special indicators"""
        try:
            positions_data = await self.llm_service.generate_positions(
                analyses, max_positions, min_confidence
            )
            
            stored_positions = []
            for position_data in positions_data:
                try:
                    # Add headline indicator to reasoning
                    headline_reasoning = f"[HEADLINE-BASED RECOMMENDATION] {position_data['reasoning']}"
                    
                    position_create = PositionCreate(
                        ticker=position_data["ticker"],
                        position_type=PositionType(position_data["position_type"]),
                        confidence=position_data["confidence"],
                        reasoning=headline_reasoning,  # Modified reasoning with indicator
                        catalysts=position_data.get("catalysts", []),
                        supporting_articles=[str(article_id) for article_id in position_data.get("supporting_articles", [])],
                        analysis_session_id=session_id
                    )
                    
                    db_position = position_crud.create_position(self.db, position_create)
                    stored_positions.append(db_position)
                    
                    # Log each position generation with headline indicator
                    self.activity_log.log_position_generation(
                        position_data["ticker"],
                        position_data["position_type"],
                        position_data["confidence"],
                        session_id,
                        reasoning=f"Headline-based: {position_data['reasoning']}",
                        catalyst=position_data.get("catalysts", [None])[0] if position_data.get("catalysts") else None
                    )
                    
                except Exception as e:
                    logging.error(f"Error storing headline position for {position_data.get('ticker')}: {e}")
                    self.activity_log.log_error(
                        "database",
                        "store_headline_position",
                        e,
                        context={"ticker": position_data.get('ticker')},
                        session_id=session_id
                    )
            
            # Log position generation completion
            self.activity_log.log_analysis_progress(
                "complete_headline_position_generation",
                f"Generated {len(stored_positions)} headline-based trading positions",
                session_id,
                {
                    "positions_generated": len(stored_positions),
                    "positions_attempted": len(positions_data),
                    "max_positions": max_positions,
                    "min_confidence": min_confidence,
                    "analysis_type": "headlines"
                }
            )
            
            return stored_positions
            
        except Exception as e:
            logging.error(f"Error generating headline positions: {e}")
            self.activity_log.log_error(
                "llm",
                "generate_headline_positions",
                e,
                context={"analyses_count": len(analyses)},
                session_id=session_id
            )
            return []

    async def _generate_market_summary(self, articles: List[Dict], analyses: List[Dict], positions: List, llm_model: str, session_id: UUID, analysis_type: str = "full") -> Dict:
        """Generate market summary using LLM and store in database"""
        try:
            # Convert stored positions to dict format for LLM
            positions_data = []
            for position in positions:
                if hasattr(position, '__dict__'):
                    positions_data.append({
                        'ticker': position.ticker,
                        'position_type': position.position_type.value if hasattr(position.position_type, 'value') else str(position.position_type),
                        'confidence': position.confidence,
                        'reasoning': position.reasoning
                    })
                else:
                    positions_data.append(position)
            
            # Log market summary generation
            self.activity_log.log_analysis_progress(
                "generate_market_summary",
                f"Generating daily market summary from {len(articles)} articles and {len(analyses)} analyses",
                session_id,
                {
                    "articles_count": len(articles),
                    "analyses_count": len(analyses),
                    "positions_count": len(positions_data),
                    "model": llm_model,
                    "analysis_type": analysis_type
                }
            )
            
            # Generate summary using LLM
            summary = await self.llm_service.generate_market_summary(
                articles, analyses, positions_data, llm_model, str(session_id)
            )
            
            # Prepare data sources metadata
            data_sources = {
                "articles_count": len(articles),
                "analyses_count": len(analyses),
                "positions_count": len(positions_data)
            }
            
            # Store market summary in database
            summary_create = MarketSummaryCreate(
                session_id=session_id,
                summary_data=summary,
                analysis_type=AnalysisTypeEnum.FULL if analysis_type == "full" else AnalysisTypeEnum.HEADLINES,
                model_used=llm_model,
                data_sources=data_sources
            )
            
            db_summary = market_summary_crud.create_market_summary(self.db, summary_create)
            
            # Log market summary storage
            self.activity_log.log_analysis_progress(
                "store_market_summary",
                f"Market summary stored in database with ID {db_summary.id}",
                session_id,
                {
                    "summary_id": str(db_summary.id),
                    "analysis_type": analysis_type,
                    "model": llm_model,
                    "data_sources": data_sources
                }
            )
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating/storing market summary: {e}")
            self.activity_log.log_error(
                "llm",
                "generate_market_summary",
                e,
                context={"model": llm_model, "analysis_type": analysis_type},
                session_id=session_id
            )
            return {
                "error": str(e),
                "summary": "Unable to generate market summary due to technical issues."
            }

    async def _broadcast_status(self, session_id: UUID, status: str, message: str, data: Dict = None):
        """Broadcast analysis status via WebSocket"""
        from ..core.websocket import websocket_manager
        
        try:
            await websocket_manager.broadcast_analysis_status(session_id, status, message, data)
        except Exception as e:
            logging.error(f"Error broadcasting status: {e}")
        
        # Also log for debugging
        logging.info(f"Session {session_id} - {status}: {message}")
        if data:
            logging.info(f"Session {session_id} - Data: {data}")

    def get_analysis_status(self, session_id: UUID) -> Dict:
        """Get current status of analysis session"""
        positions = position_crud.get_positions_by_session(self.db, session_id)
        
        if positions:
            return {
                "session_id": session_id,
                "status": "completed",
                "positions_count": len(positions),
                "created_at": positions[0].created_at if positions else None
            }
        else:
            return {
                "session_id": session_id,
                "status": "processing",
                "positions_count": 0,
                "created_at": None
            }