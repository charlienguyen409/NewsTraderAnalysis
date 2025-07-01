import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Protocol
import time
import logging
import random
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from uuid import UUID

from ..core.config import settings


class SiteHandler(ABC):
    """Abstract base class for site-specific scraping handlers"""
    
    @abstractmethod
    async def scrape_articles(self, session: aiohttp.ClientSession, rate_limiter) -> List[Dict]:
        pass
    
    @abstractmethod
    async def scrape_content(self, session: aiohttp.ClientSession, url: str, rate_limiter) -> Optional[str]:
        pass


class RSSHandler(SiteHandler):
    """Handler for RSS feed scraping - most reliable approach"""
    
    def __init__(self, feed_url: str, source_name: str):
        self.feed_url = feed_url
        self.source_name = source_name
    
    async def scrape_articles(self, session: aiohttp.ClientSession, rate_limiter) -> List[Dict]:
        domain = urlparse(self.feed_url).netloc
        await rate_limiter.acquire(domain)
        
        try:
            async with session.get(self.feed_url) as response:
                if response.status != 200:
                    logging.error(f"RSS feed {self.feed_url} returned status {response.status}")
                    return []
                
                feed_content = await response.text()
                feed = feedparser.parse(feed_content)
                
                articles = []
                for entry in feed.entries[:20]:  # Limit to 20 articles
                    try:
                        published_at = datetime.now(timezone.utc)
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        
                        articles.append({
                            'url': entry.link,
                            'title': entry.title,
                            'source': self.source_name,
                            'published_at': published_at,
                            'summary': getattr(entry, 'summary', ''),
                            'ticker': self._extract_ticker_from_title(entry.title)
                        })
                    except Exception as e:
                        logging.warning(f"Error processing RSS entry: {e}")
                        continue
                
                return articles
                
        except Exception as e:
            logging.error(f"Error scraping RSS feed {self.feed_url}: {e}")
            return []
    
    async def scrape_content(self, session: aiohttp.ClientSession, url: str, rate_limiter) -> Optional[str]:
        # For RSS feeds, we often have summary content already
        # This method can be used for full article content if needed
        return None
    
    def _extract_ticker_from_title(self, title: str) -> Optional[str]:
        import re
        patterns = [
            r'\(([A-Z]{1,5})\)',  # (AAPL)
            r'\b([A-Z]{2,5}):\s',  # TSLA: 
            r'\$([A-Z]{1,5})\b',   # $MSFT
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        return None


class YahooFinanceHandler(SiteHandler):
    """Specialized handler for Yahoo Finance with enhanced headers"""
    
    async def scrape_articles(self, session: aiohttp.ClientSession, rate_limiter) -> List[Dict]:
        # Use RSS feed for Yahoo Finance - more reliable
        rss_handler = RSSHandler(
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "yahoo_finance"
        )
        return await rss_handler.scrape_articles(session, rate_limiter)
    
    async def scrape_content(self, session: aiohttp.ClientSession, url: str, rate_limiter) -> Optional[str]:
        domain = urlparse(url).netloc
        await rate_limiter.acquire(domain)
        
        try:
            # Add random delay to appear more human-like
            await asyncio.sleep(random.uniform(1, 3))
            
            async with session.get(url) as response:
                if response.status != 200:
                    logging.warning(f"Yahoo Finance returned status {response.status} for {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "aside"]):
                    element.decompose()
                
                # Yahoo Finance specific selectors
                selectors = [
                    '[data-module="ArticleBody"]',
                    '.article-wrap',
                    '.caas-body',
                    '.story-body',
                    '.article-content',
                    'main article'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text(strip=True)
                        if len(content) > 100:
                            return self._clean_content(content)
                
                return None
                
        except Exception as e:
            logging.error(f"Error scraping Yahoo Finance content from {url}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        # Limit content length
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        return content


class WSJHandler(SiteHandler):
    """Handler for WSJ - uses RSS feeds to avoid paywall and bot detection"""
    
    async def scrape_articles(self, session: aiohttp.ClientSession, rate_limiter) -> List[Dict]:
        # WSJ RSS feeds
        feeds = [
            ("https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "wsj_markets"),
            ("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "wsj_business")
        ]
        
        all_articles = []
        for feed_url, source_name in feeds:
            rss_handler = RSSHandler(feed_url, source_name)
            articles = await rss_handler.scrape_articles(session, rate_limiter)
            all_articles.extend(articles)
        
        return all_articles
    
    async def scrape_content(self, session: aiohttp.ClientSession, url: str, rate_limiter) -> Optional[str]:
        # WSJ has strong paywall and bot detection
        # For now, return None and rely on RSS summaries
        logging.info(f"Skipping WSJ content scraping for {url} - using RSS summary instead")
        return None


class EnhancedNewsScraper:
    """Enhanced news scraper with site-specific handlers and better anti-bot measures"""
    
    def __init__(self, activity_log_service=None, session_id: Optional[UUID] = None):
        self.rate_limiter = self._create_adaptive_rate_limiter()
        self.session = None
        self.activity_log = activity_log_service
        self.session_id = session_id
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Initialize site handlers
        self.handlers = {
            'yahoo_finance': YahooFinanceHandler(),
            'wsj': WSJHandler(),
            'reuters_rss': RSSHandler("http://feeds.reuters.com/reuters/businessNews", "reuters"),
            'marketwatch_rss': RSSHandler("http://feeds.marketwatch.com/marketwatch/marketpulse/", "marketwatch"),
            'cnbc_rss': RSSHandler("https://www.cnbc.com/id/100003114/device/rss/rss.html", "cnbc"),
            'finviz': self  # Keep existing FinViz scraper
        }
    
    def _create_adaptive_rate_limiter(self):
        """Create rate limiter with different limits per domain"""
        return AdaptiveRateLimiter({
            'finance.yahoo.com': {'max_requests': 5, 'window': 60},
            'wsj.com': {'max_requests': 2, 'window': 60},
            'reuters.com': {'max_requests': 8, 'window': 60},
            'marketwatch.com': {'max_requests': 8, 'window': 60},
            'default': {'max_requests': 10, 'window': 60}
        })
    
    async def __aenter__(self):
        # Rotate user agent
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(
                limit=50,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            ),
            # Fix for Yahoo Finance header length issue
            max_line_size=32760,
            max_field_size=32760
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_all_sources(self) -> List[Dict]:
        """Scrape articles from all configured sources"""
        all_articles = []
        
        # Use RSS feeds and site-specific handlers
        for source_name, handler in self.handlers.items():
            try:
                # Log scraping start
                if self.activity_log and self.session_id:
                    self.activity_log.log_scraping_start(source_name, self.session_id)
                
                if source_name == 'finviz':
                    # Use existing FinViz scraper
                    articles = await self.scrape_finviz()
                else:
                    articles = await handler.scrape_articles(self.session, self.rate_limiter)
                
                logging.info(f"Scraped {len(articles)} articles from {source_name}")
                
                # Log successful scraping with headlines
                if self.activity_log and self.session_id:
                    headlines = [article.get('title', '') for article in articles]
                    self.activity_log.log_scraping_success(
                        source_name, 
                        len(articles), 
                        self.session_id,
                        headlines=headlines
                    )
                
                all_articles.extend(articles)
                
                # Add delay between sources
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logging.error(f"Error scraping {source_name}: {e}")
                
                # Log scraping error
                if self.activity_log and self.session_id:
                    self.activity_log.log_scraping_error(
                        source_name, 
                        e, 
                        session_id=self.session_id
                    )
                continue
        
        return all_articles
    
    async def scrape_article_content(self, url: str) -> Optional[str]:
        """Scrape content using appropriate handler based on URL domain"""
        domain = urlparse(url).netloc.lower()
        
        try:
            # Determine appropriate handler
            if 'yahoo.com' in domain:
                handler = self.handlers['yahoo_finance']
                content = await handler.scrape_content(self.session, url, self.rate_limiter)
            elif 'wsj.com' in domain:
                handler = self.handlers['wsj']
                content = await handler.scrape_content(self.session, url, self.rate_limiter)
            else:
                # Use generic content scraping
                content = await self._generic_content_scraping(url)
            
            # Log content scraping result
            if self.activity_log and self.session_id:
                success = content is not None
                content_length = len(content) if content else 0
                error = None if success else "No content found"
                
                self.activity_log.log_content_scraping(
                    url, success, self.session_id, content_length, error
                )
            
            return content
            
        except Exception as e:
            # Log content scraping error
            if self.activity_log and self.session_id:
                self.activity_log.log_content_scraping(
                    url, False, self.session_id, error=str(e)
                )
            return None
    
    async def _generic_content_scraping(self, url: str) -> Optional[str]:
        """Generic content scraping for sites without specific handlers"""
        domain = urlparse(url).netloc
        await self.rate_limiter.acquire(domain)
        
        try:
            # Add human-like delay
            await asyncio.sleep(random.uniform(1, 3))
            
            async with self.session.get(url) as response:
                if response.status == 401:
                    logging.warning(f"Access denied (401) for {url} - site blocks automated requests")
                    return None
                elif response.status == 403:
                    logging.warning(f"Forbidden (403) for {url} - bot detection active")
                    return None
                elif response.status != 200:
                    logging.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "aside", "header"]):
                    element.decompose()
                
                # Enhanced content selectors
                selectors = [
                    'article', '.article-content', '.story-content',
                    '.post-content', '.entry-content', 'main',
                    '[data-module="ArticleBody"]', '.article-body',
                    '.content', '.text', '.article-text',
                    '[class*="article"]', '[class*="story"]', '[class*="content"]',
                    '[role="article"]'
                ]
                
                for selector in selectors:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text(strip=True)
                        if len(content) > 100:
                            return self._clean_content(content)
                
                return None
                
        except Exception as e:
            logging.error(f"Error in generic content scraping for {url}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and format scraped content"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        return content
    
    # Keep existing FinViz scraper method
    async def scrape_finviz(self) -> List[Dict]:
        url = "https://finviz.com/news.ashx"
        domain = urlparse(url).netloc
        
        await self.rate_limiter.acquire(domain)
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logging.error(f"FinViz returned status {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                articles = []
                news_table = (
                    soup.find('table', {'class': 'news_time-table'}) or
                    soup.find('table', {'class': 'fullview-news-outer'}) or
                    soup.find('table', {'class': lambda x: x and 'news' in x.lower()})
                )
                
                if not news_table:
                    logging.warning("Could not find news table on FinViz - using RSS fallback")
                    # Fallback to FinViz RSS if available
                    return []
                
                for row in news_table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        time_cell = cells[0]
                        source_cell = cells[1]
                        title_cell = cells[2]
                        
                        link = title_cell.find('a')
                        if link and link.get('href'):
                            article_url = link['href']
                            if not article_url.startswith('http'):
                                article_url = urljoin(url, article_url)
                            
                            articles.append({
                                'url': article_url,
                                'title': link.text.strip(),
                                'source': 'finviz',
                                'published_at': self._parse_finviz_time(time_cell.text.strip()),
                                'metadata': {
                                    'source_site': source_cell.text.strip() if source_cell else None
                                }
                            })
                
                return articles[:20]
                
        except Exception as e:
            logging.error(f"Error scraping FinViz: {e}")
            return []
    
    def _parse_finviz_time(self, time_str: str) -> datetime:
        try:
            if 'AM' in time_str or 'PM' in time_str:
                return datetime.strptime(time_str, "%I:%M%p").replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day,
                    tzinfo=timezone.utc
                )
            else:
                return datetime.now(timezone.utc)
        except:
            return datetime.now(timezone.utc)


class AdaptiveRateLimiter:
    """Rate limiter with different limits per domain"""
    
    def __init__(self, domain_limits: Dict[str, Dict[str, int]]):
        self.domain_limits = domain_limits
        self.requests = {}
    
    async def acquire(self, domain: str):
        # Get limits for this domain or use default
        limits = self.domain_limits.get(domain, self.domain_limits['default'])
        max_requests = limits['max_requests']
        window = limits['window']
        
        now = time.time()
        if domain not in self.requests:
            self.requests[domain] = []
        
        # Clean old requests
        self.requests[domain] = [
            req_time for req_time in self.requests[domain] 
            if now - req_time < window
        ]
        
        # Check if we need to wait
        if len(self.requests[domain]) >= max_requests:
            sleep_time = window - (now - self.requests[domain][0]) + random.uniform(1, 3)
            logging.info(f"Rate limiting {domain}: waiting {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        
        self.requests[domain].append(now)