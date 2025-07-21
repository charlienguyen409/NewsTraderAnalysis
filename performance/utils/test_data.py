"""
Test data generation utilities for performance testing
"""
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from faker import Faker

fake = Faker()


class TestDataGenerator:
    """Generate realistic test data for performance testing"""
    
    def __init__(self):
        self.tickers = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD", 
            "INTC", "CRM", "NFLX", "ADBE", "PYPL", "SHOP", "SQ", "ROKU",
            "ZM", "TWLO", "DOCU", "OKTA", "SNOW", "PLTR", "BB", "GME",
            "AMC", "SPCE", "NIO", "XPEV", "LI", "BABA", "JD", "PDD"
        ]
        
        self.sources = [
            "finviz.com", "biztoc.com", "yahoo.com", "marketwatch.com",
            "reuters.com", "bloomberg.com", "cnbc.com", "seekingalpha.com"
        ]
        
        self.catalysts = [
            "earnings_beat", "earnings_miss", "fda_approval", "fda_rejection",
            "merger_announcement", "acquisition", "partnership", "product_launch",
            "management_change", "legal_issue", "analyst_upgrade", "analyst_downgrade",
            "revenue_guidance", "stock_split", "dividend_announcement"
        ]
    
    def generate_article(self, ticker: str = None) -> Dict[str, Any]:
        """Generate a realistic article for testing"""
        if not ticker:
            ticker = random.choice(self.tickers)
            
        return {
            "id": str(uuid.uuid4()),
            "title": f"{ticker} {fake.sentence(nb_words=8)}",
            "content": fake.text(max_nb_chars=2000),
            "source": random.choice(self.sources),
            "url": fake.url(),
            "ticker": ticker,
            "scraped_at": datetime.now(timezone.utc) - timedelta(
                hours=random.randint(0, 48)
            ),
            "published_at": datetime.now(timezone.utc) - timedelta(
                hours=random.randint(0, 72)
            )
        }
    
    def generate_articles(self, count: int, ticker: str = None) -> List[Dict[str, Any]]:
        """Generate multiple articles"""
        return [self.generate_article(ticker) for _ in range(count)]
    
    def generate_analysis_request(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Generate an analysis request for testing"""
        if not tickers:
            tickers = random.sample(self.tickers, random.randint(1, 5))
        
        return {
            "tickers": tickers,
            "llm_model": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-3-opus"]),
            "sources": random.sample(self.sources, random.randint(1, 3)),
            "include_content": random.choice([True, False]),
            "max_articles_per_ticker": random.randint(5, 20)
        }
    
    def generate_analysis_result(self, ticker: str) -> Dict[str, Any]:
        """Generate a realistic analysis result"""
        sentiment_score = random.uniform(-1.0, 1.0)
        confidence = random.uniform(0.5, 1.0)
        
        return {
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "catalysts": random.sample(self.catalysts, random.randint(0, 3)),
            "reasoning": fake.paragraph(nb_sentences=5),
            "articles_analyzed": random.randint(1, 20),
            "created_at": datetime.now(timezone.utc)
        }
    
    def generate_position(self, ticker: str) -> Dict[str, Any]:
        """Generate a position recommendation"""
        position_types = ["STRONG_BUY", "BUY", "HOLD", "SHORT", "STRONG_SHORT"]
        
        return {
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "position_type": random.choice(position_types),
            "confidence": random.uniform(0.6, 1.0),
            "reasoning": fake.paragraph(nb_sentences=3),
            "target_price": random.uniform(50.0, 500.0),
            "risk_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "created_at": datetime.now(timezone.utc)
        }
    
    def generate_websocket_message(self, session_id: str = None) -> Dict[str, Any]:
        """Generate a WebSocket message for testing"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        message_types = [
            "analysis_started", "article_scraped", "article_analyzed",
            "position_generated", "analysis_completed", "error", "progress_update"
        ]
        
        message_type = random.choice(message_types)
        
        base_message = {
            "type": message_type,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if message_type == "progress_update":
            base_message.update({
                "progress": random.randint(0, 100),
                "current_step": fake.sentence(nb_words=4),
                "total_steps": random.randint(5, 20)
            })
        elif message_type == "article_scraped":
            base_message.update({
                "ticker": random.choice(self.tickers),
                "articles_count": random.randint(1, 50)
            })
        elif message_type == "error":
            base_message.update({
                "error_message": fake.sentence(),
                "error_code": random.choice(["SCRAPING_ERROR", "LLM_ERROR", "DB_ERROR"])
            })
        
        return base_message
    
    def generate_bulk_test_data(self, articles_count: int = 1000, 
                              analyses_count: int = 500) -> Dict[str, List[Dict[str, Any]]]:
        """Generate bulk test data for performance testing"""
        print(f"Generating {articles_count} articles and {analyses_count} analyses...")
        
        # Generate articles
        articles = []
        for i in range(articles_count):
            if i % 100 == 0:
                print(f"Generated {i} articles...")
            articles.append(self.generate_article())
        
        # Generate analyses
        analyses = []
        for i in range(analyses_count):
            if i % 100 == 0:
                print(f"Generated {i} analyses...")
            ticker = random.choice(self.tickers)
            analyses.append(self.generate_analysis_result(ticker))
        
        # Generate positions
        positions = []
        for ticker in self.tickers:
            for _ in range(random.randint(1, 3)):
                positions.append(self.generate_position(ticker))
        
        return {
            "articles": articles,
            "analyses": analyses,
            "positions": positions
        }


# Singleton instance
test_data_generator = TestDataGenerator()