# System Architecture Documentation

## Overview

The Market News Analysis Agent is a full-stack application that scrapes financial news, analyzes sentiment using AI, and generates trading recommendations. This document provides a comprehensive overview of the system architecture, component interactions, and design decisions.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [WebSocket Architecture](#websocket-architecture)
- [Service Layer](#service-layer)
- [Frontend Architecture](#frontend-architecture)
- [Testing Architecture](#testing-architecture)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Clean Architecture Implementation](#clean-architecture-implementation)

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │    │    Backend      │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Web Browser   │    │   PostgreSQL    │    │  OpenAI API     │
│   (Chrome, etc) │    │   Redis Cache   │    │  FinViz, BizToc │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Tailwind CSS for styling
- React Query for data fetching
- React Router for navigation
- WebSocket for real-time updates

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy ORM with async support
- PostgreSQL for persistent storage
- Redis for caching and session management
- WebSocket for real-time communication

**External Services:**
- OpenAI GPT-4 for sentiment analysis
- Anthropic Claude (optional)
- FinViz for financial news scraping
- BizToc for additional news sources

**Infrastructure:**
- Docker for containerization
- Docker Compose for development
- Nginx for reverse proxy (production)

## Component Architecture

### Backend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │     API     │  │  WebSocket  │  │   Schemas   │             │
│  │  Endpoints  │  │   Manager   │  │ (Pydantic)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│           │               │               │                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Service Layer                             │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │  │   Analysis   │ │   Scraper    │ │     LLM      │       │ │
│  │  │   Service    │ │   Service    │ │   Service    │       │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │  │  Activity    │ │    CRUD      │ │    Cache     │       │ │
│  │  │   Service    │ │   Service    │ │   Service    │       │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │               │               │                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Data Layer                               │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │  │   Models     │ │  Database    │ │    Redis     │       │ │
│  │  │ (SQLAlchemy) │ │ Connection   │ │  Connection  │       │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Pages    │  │ Components  │  │    Hooks    │             │
│  │             │  │             │  │  (Custom)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│           │               │               │                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    State Management                         │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │  │ React Query  │ │  Context API │ │  Local State │       │ │
│  │  │   (Server)   │ │   (Global)   │ │ (Component)  │       │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │               │               │                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Communication Layer                         │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │  │   HTTP API   │ │  WebSocket   │ │  Local       │       │ │
│  │  │   Client     │ │   Client     │ │  Storage     │       │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Articles     │     │    Analyses     │     │   Positions     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (UUID)       │────►│ id (UUID)       │────►│ id (UUID)       │
│ ticker (str)    │     │ article_id (FK) │     │ session_id (str)│
│ title (str)     │     │ session_id (str)│     │ ticker (str)    │
│ url (str)       │     │ sentiment_score │     │ position_type   │
│ content (text)  │     │ confidence      │     │ confidence      │
│ source (str)    │     │ catalysts (JSON)│     │ reasoning (text)│
│ scraped_at      │     │ llm_response    │     │ target_price    │
│ processed_at    │     │ created_at      │     │ created_at      │
│ status (enum)   │     │ updated_at      │     │ updated_at      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         │               ┌─────────────────┐             │
         └──────────────►│ Activity Logs   │◄────────────┘
                         ├─────────────────┤
                         │ id (UUID)       │
                         │ session_id (str)│
                         │ action (str)    │
                         │ details (JSON)  │
                         │ timestamp       │
                         │ level (enum)    │
                         └─────────────────┘
```

### Database Tables

#### Articles Table
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    content TEXT,
    source VARCHAR(50) NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_articles_ticker ON articles(ticker);
CREATE INDEX idx_articles_scraped_at ON articles(scraped_at);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_source ON articles(source);
```

#### Analyses Table
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    sentiment_score DECIMAL(4,3),
    confidence DECIMAL(4,3),
    catalysts JSONB,
    llm_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_analyses_session_id ON analyses(session_id);
CREATE INDEX idx_analyses_article_id ON analyses(article_id);
CREATE INDEX idx_analyses_sentiment_score ON analyses(sentiment_score);
```

#### Positions Table
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    position_type VARCHAR(20) NOT NULL,
    confidence DECIMAL(4,3) NOT NULL,
    reasoning TEXT NOT NULL,
    target_price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_positions_session_id ON positions(session_id);
CREATE INDEX idx_positions_ticker ON positions(ticker);
CREATE INDEX idx_positions_confidence ON positions(confidence);
CREATE INDEX idx_positions_created_at ON positions(created_at);
```

#### Activity Logs Table
```sql
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    level VARCHAR(20) DEFAULT 'INFO',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_activity_logs_session_id ON activity_logs(session_id);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX idx_activity_logs_level ON activity_logs(level);
```

## API Design

### RESTful Endpoints

#### Analysis Endpoints
```
POST   /api/v1/analysis/start          # Start new analysis
GET    /api/v1/analysis/status/{id}    # Get analysis status
DELETE /api/v1/analysis/{id}           # Cancel analysis
```

#### Articles Endpoints
```
GET    /api/v1/articles                # List articles with filtering
GET    /api/v1/articles/{id}           # Get specific article
PATCH  /api/v1/articles/{id}           # Update article
DELETE /api/v1/articles/{id}           # Delete article
```

#### Positions Endpoints
```
GET    /api/v1/positions               # List all positions
GET    /api/v1/positions/{id}          # Get specific position
GET    /api/v1/positions/session/{id}  # Get positions by session
DELETE /api/v1/positions/{id}          # Delete position
```

#### Activity Logs Endpoints
```
GET    /api/v1/activity-logs           # List activity logs
GET    /api/v1/activity-logs/session/{id}  # Get logs by session
```

### Request/Response Examples

#### Start Analysis Request
```json
{
  "max_positions": 5,
  "min_confidence": 0.7,
  "analysis_type": "headlines",
  "llm_model": "gpt-4",
  "sources": ["finviz", "biztoc"]
}
```

#### Start Analysis Response
```json
{
  "session_id": "analysis_20241201_143022_abc123",
  "message": "Analysis started successfully",
  "status": "started",
  "estimated_duration": 180
}
```

#### Analysis Status Response
```json
{
  "session_id": "analysis_20241201_143022_abc123",
  "status": "in_progress",
  "progress": 65,
  "current_step": "analyzing_sentiment",
  "articles_processed": 13,
  "positions_generated": 2,
  "started_at": "2024-12-01T14:30:22Z",
  "estimated_completion": "2024-12-01T14:33:22Z"
}
```

## WebSocket Architecture

### Connection Management

```python
# WebSocket connection lifecycle
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)
```

### Message Types

```typescript
// WebSocket message types
interface WebSocketMessage {
  type: 'analysis_progress' | 'analysis_complete' | 'analysis_error' | 'activity_log';
  data: any;
  timestamp: string;
  session_id?: string;
}

interface AnalysisProgressMessage {
  type: 'analysis_progress';
  data: {
    session_id: string;
    status: string;
    progress: number;
    current_step: string;
    articles_processed: number;
    positions_generated: number;
  };
}

interface ActivityLogMessage {
  type: 'activity_log';
  data: {
    session_id: string;
    action: string;
    details: any;
    level: 'INFO' | 'WARNING' | 'ERROR';
  };
}
```

## Service Layer

### Analysis Service

```python
class AnalysisService:
    def __init__(self, db: AsyncSession, websocket_manager: ConnectionManager):
        self.db = db
        self.websocket_manager = websocket_manager
        self.scraper_service = ScraperService()
        self.llm_service = LLMService()
        self.activity_service = ActivityLogService(db)
    
    async def analyze_market(self, request: AnalysisRequest) -> AnalysisResponse:
        session_id = self._generate_session_id()
        
        try:
            # 1. Scrape headlines
            await self._update_progress(session_id, "scraping", 10)
            headlines = await self.scraper_service.scrape_headlines(request.sources)
            
            # 2. Filter relevant headlines
            await self._update_progress(session_id, "filtering", 25)
            relevant_headlines = await self.llm_service.filter_headlines(headlines)
            
            # 3. Scrape full articles
            await self._update_progress(session_id, "scraping_articles", 40)
            articles = await self.scraper_service.scrape_articles(relevant_headlines)
            
            # 4. Analyze sentiment
            await self._update_progress(session_id, "analyzing", 70)
            analyses = await self.llm_service.analyze_articles(articles)
            
            # 5. Generate positions
            await self._update_progress(session_id, "generating_positions", 90)
            positions = await self._generate_positions(analyses, request)
            
            # 6. Complete
            await self._update_progress(session_id, "completed", 100)
            
            return AnalysisResponse(
                session_id=session_id,
                positions=positions,
                articles_processed=len(articles),
                message="Analysis completed successfully"
            )
            
        except Exception as e:
            await self._handle_error(session_id, e)
            raise
```

### Scraper Service

```python
class ScraperService:
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=10)
        self.session = aiohttp.ClientSession()
    
    async def scrape_headlines(self, sources: List[str]) -> List[Article]:
        headlines = []
        
        for source in sources:
            await self.rate_limiter.wait()
            
            if source == "finviz":
                headlines.extend(await self._scrape_finviz())
            elif source == "biztoc":
                headlines.extend(await self._scrape_biztoc())
        
        return headlines
    
    async def _scrape_finviz(self) -> List[Article]:
        # Implementation for FinViz scraping
        pass
    
    async def _scrape_biztoc(self) -> List[Article]:
        # Implementation for BizToc scraping
        pass
```

### LLM Service

```python
class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self.anthropic_client = AsyncAnthropic()
    
    async def analyze_sentiment(
        self, 
        article: Article, 
        model: str = "gpt-4"
    ) -> SentimentAnalysis:
        prompt = self._build_sentiment_prompt(article)
        
        if model.startswith("gpt"):
            response = await self._call_openai(prompt, model)
        elif model.startswith("claude"):
            response = await self._call_anthropic(prompt, model)
        
        return self._parse_sentiment_response(response)
    
    def _build_sentiment_prompt(self, article: Article) -> str:
        return f"""
        Analyze the sentiment and trading catalysts in this financial news article:
        
        Title: {article.title}
        Content: {article.content}
        
        Respond with JSON containing:
        - sentiment_score: float between -1 and 1
        - confidence: float between 0 and 1
        - catalysts: list of detected catalysts
        - reasoning: explanation of the analysis
        """
```

## Frontend Architecture

### Component Hierarchy

```
App
├── Layout
│   ├── Header
│   ├── Navigation
│   └── Footer
├── Router
│   ├── Dashboard
│   │   ├── MarketSummary
│   │   ├── AnalysisControls
│   │   └── ActivityLog
│   ├── Positions
│   │   ├── PositionsList
│   │   └── PositionCard
│   ├── Articles
│   │   ├── ArticlesList
│   │   ├── ArticleFilters
│   │   └── ArticleCard
│   └── Settings
│       ├── LLMSelector
│       └── AnalysisSettings
└── Providers
    ├── QueryClientProvider
    ├── WebSocketProvider
    └── ThemeProvider
```

### State Management

```typescript
// Global state management using Context API
interface AppState {
  user: User | null;
  settings: AppSettings;
  analysisStatus: AnalysisStatus | null;
  connectionState: 'connecting' | 'connected' | 'disconnected';
}

interface AppSettings {
  llmModel: 'gpt-4' | 'claude-3';
  maxPositions: number;
  minConfidence: number;
  analysisType: 'headlines' | 'full';
  sources: ('finviz' | 'biztoc')[];
}

// React Query for server state
const usePositions = (sessionId?: string) => {
  return useQuery({
    queryKey: ['positions', sessionId],
    queryFn: () => api.getPositions(sessionId),
    enabled: !!sessionId,
    refetchInterval: 30000
  });
};

const useAnalysisStatus = (sessionId: string) => {
  return useQuery({
    queryKey: ['analysis-status', sessionId],
    queryFn: () => api.getAnalysisStatus(sessionId),
    refetchInterval: 2000,
    enabled: !!sessionId
  });
};
```

### WebSocket Hook

```typescript
// Custom WebSocket hook
export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setConnectionState('connected');
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };
    
    ws.onclose = () => {
      setConnectionState('disconnected');
      setSocket(null);
    };
    
    ws.onerror = () => {
      setConnectionState('error');
    };
    
    return () => {
      ws.close();
    };
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, [socket]);

  return {
    connectionState,
    lastMessage,
    sendMessage,
    disconnect: () => socket?.close()
  };
};
```

## Testing Architecture

### Test Strategy Pyramid

```
     /\
    /  \     E2E Tests (Playwright)
   /____\    - User workflows
  /      \   - Cross-browser testing
 /        \  - Visual regression
/__________\

/            \
|             | Integration Tests
| Frontend    | - Component integration
| Integration | - API integration  
|             | - Real-time features
|_____________|

/              \
|               | Unit Tests
| Backend       | - Service layer
| Unit Tests    | - API endpoints
|               | - Database models
|_______________|

/                \
|                 | Unit Tests
| Frontend        | - Components
| Unit Tests      | - Hooks
|                 | - Utilities
|_________________|
```

### Test Environment Setup

```yaml
# Testing infrastructure
version: '3.8'
services:
  test-postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: test_market_analysis
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
  
  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
  
  test-backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://test_user:test_password@test-postgres:5432/test_market_analysis
      REDIS_URL: redis://test-redis:6379
      TESTING: true
    depends_on:
      - test-postgres
      - test-redis
```

## Security Architecture

### Authentication & Authorization

```python
# JWT token-based authentication
class SecurityService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    async def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    async def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")
```

### Input Validation

```python
# Pydantic models for input validation
class AnalysisRequest(BaseModel):
    max_positions: int = Field(ge=1, le=20, description="Maximum positions to generate")
    min_confidence: float = Field(ge=0.1, le=1.0, description="Minimum confidence threshold")
    analysis_type: AnalysisType = Field(description="Type of analysis to perform")
    llm_model: LLMModel = Field(description="LLM model to use")
    sources: List[NewsSource] = Field(min_items=1, description="News sources to scrape")
    
    @validator('sources')
    def validate_sources(cls, v):
        allowed_sources = ['finviz', 'biztoc']
        for source in v:
            if source not in allowed_sources:
                raise ValueError(f'Invalid source: {source}')
        return v
```

### Rate Limiting

```python
# Rate limiting middleware
class RateLimitMiddleware:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(429, "Rate limit exceeded")
        
        # Record request
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response
```

## Deployment Architecture

### Production Setup

```yaml
# Production Docker Compose
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      VITE_API_URL: https://api.marketanalysis.com
      VITE_WS_URL: wss://api.marketanalysis.com/ws

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/market_analysis
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: market_analysis
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### Scaling Considerations

```python
# Horizontal scaling with load balancer
class LoadBalancer:
    def __init__(self, backend_servers: List[str]):
        self.servers = backend_servers
        self.current = 0
    
    def get_next_server(self) -> str:
        server = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return server

# WebSocket scaling with Redis pub/sub
class WebSocketManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_connections = {}
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        # Broadcast to local connections
        await self._broadcast_local(session_id, message)
        
        # Publish to Redis for other instances
        await self.redis.publish(
            f"websocket:{session_id}", 
            json.dumps(message)
        )
```

## Clean Architecture Implementation

### Roadmap for Clean Architecture

#### Phase 1: Dependency Inversion
- Abstract external dependencies (LLM APIs, databases)
- Create interfaces for all external services
- Implement dependency injection container

#### Phase 2: Domain Layer Separation
- Extract business logic from service layer
- Create domain entities and value objects
- Implement domain services for business rules

#### Phase 3: Use Case Implementation
- Create use case classes for each business operation
- Implement command/query separation (CQRS)
- Add cross-cutting concerns (logging, validation)

#### Phase 4: Clean API Layer
- Implement controllers that only handle HTTP concerns
- Add presentation models separate from domain models
- Create API versioning strategy

### Clean Architecture Structure

```
backend/
├── domain/                 # Business entities and rules
│   ├── entities/
│   ├── value_objects/
│   └── services/
├── application/            # Use cases and application logic
│   ├── use_cases/
│   ├── interfaces/
│   └── services/
├── infrastructure/         # External concerns
│   ├── database/
│   ├── external_apis/
│   └── message_queues/
├── presentation/           # API layer
│   ├── controllers/
│   ├── dto/
│   └── middleware/
└── main.py                # Dependency injection setup
```

---

## Summary

This architecture documentation provides a comprehensive overview of the Market News Analysis Agent system. The architecture follows modern software engineering principles with clear separation of concerns, scalable design patterns, and comprehensive testing strategies.

Key architectural decisions:
- **Microservices-ready**: Service layer can be easily extracted into separate services
- **Event-driven**: WebSocket architecture supports real-time updates
- **Testable**: Clear separation enables comprehensive testing at all levels
- **Scalable**: Database design and caching strategy support horizontal scaling
- **Maintainable**: Clean architecture principles guide future development

For specific implementation details, refer to the individual service documentation and code comments.