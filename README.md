# Market Analysis Dashboard

AI-powered financial news analysis and trading recommendations using React frontend and FastAPI backend.

## Features

- **Real-time News Scraping**: Automatically scrapes financial news from FinViz and BizToc
- **AI-Powered Analysis**: Uses OpenAI GPT and Anthropic Claude for sentiment analysis and catalyst detection
- **Trading Recommendations**: Generates BUY/SHORT positions with confidence scores and detailed reasoning
- **Modern UI**: Clean, responsive dashboard with real-time updates via WebSockets
- **Production Ready**: Docker support with PostgreSQL, Redis, and comprehensive error handling

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API documentation
- **PostgreSQL**: Robust relational database with JSONB support for LLM responses
- **Redis**: High-performance caching and session storage
- **SQLAlchemy**: Python SQL toolkit and ORM
- **OpenAI/Anthropic**: AI APIs for sentiment analysis and news filtering

### Frontend  
- **React 18**: Latest React with hooks and modern patterns
- **TypeScript**: Type-safe development experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **React Query**: Powerful data fetching and caching
- **WebSockets**: Real-time updates during analysis

### Infrastructure
- **Docker**: Containerized deployment with multi-stage builds
- **Docker Compose**: Local development and production orchestration
- **Nginx**: Reverse proxy and static file serving in production

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- Anthropic API key (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NewsTraderAnalysis
   ```

2. **Set up environment variables**
   ```bash
   # Copy the main environment file
   cp .env.example .env
   
   # Copy backend environment file
   cp backend/.env.example backend/.env
   
   # Copy frontend environment file
   cp frontend/.env.example frontend/.env
   
   # Edit .env files with your actual API keys and configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   cd docker
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (without Docker)

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Set up database
   export DATABASE_URL="postgresql://user:pass@localhost/market_analysis"
   
   # Run server
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/market_analysis
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
SECRET_KEY=your-secret-key
MAX_POSITIONS=10
MIN_CONFIDENCE=0.7
SCRAPING_RATE_LIMIT=10
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## API Endpoints

### Articles
- `GET /api/v1/articles` - List articles with filtering
- `GET /api/v1/articles/{id}` - Get specific article
- `PATCH /api/v1/articles/{id}` - Update article

### Positions  
- `GET /api/v1/positions` - List trading positions
- `GET /api/v1/positions/{id}` - Get specific position
- `GET /api/v1/positions/session/{session_id}` - Get positions by analysis session

### Analysis
- `POST /api/v1/analysis/start` - Start new market analysis
- `GET /api/v1/analysis/status/{session_id}` - Get analysis status

### WebSocket
- `WS /ws` - Real-time updates for analysis progress

## Usage

1. **Configure Settings**: Set your preferred LLM model, position limits, and confidence thresholds
2. **Start Analysis**: Click "Analyze Market" to begin scraping and analysis
3. **Monitor Progress**: Watch real-time updates in the activity log
4. **Review Results**: Examine generated positions with confidence scores and reasoning
5. **Browse Articles**: Search and filter scraped news articles

## Analysis Process

1. **News Scraping**: Fetches latest headlines from FinViz and BizToc
2. **Relevance Filtering**: AI filters headlines for trading relevance  
3. **Content Extraction**: Scrapes full article content for selected news
4. **Sentiment Analysis**: AI analyzes each article for sentiment and catalysts
5. **Position Generation**: Combines analyses to generate trading recommendations
6. **Real-time Updates**: WebSocket broadcasts progress to connected clients

## Position Types

- **STRONG_BUY**: Sentiment > 0.7, multiple positive catalysts
- **BUY**: Sentiment > 0.4, at least one positive catalyst
- **HOLD**: Sentiment -0.2 to 0.4 (not displayed)
- **SHORT**: Sentiment < -0.4, negative catalysts
- **STRONG_SHORT**: Sentiment < -0.7, multiple negative catalysts

## Production Deployment

1. **Prepare environment**
   ```bash
   cp .env.example .env.prod
   # Configure production values
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up SSL certificates** (recommended)
   - Configure nginx with SSL certificates
   - Update environment variables for HTTPS

## Development

### Backend Development
- Use SQLAlchemy migrations for database changes
- Follow FastAPI best practices for API design
- Add comprehensive logging for debugging
- Mock external services in tests

### Frontend Development  
- Use TypeScript for type safety
- Follow React best practices and hooks patterns
- Implement error boundaries for graceful failures
- Add loading states for all async operations

### Testing

The project includes comprehensive testing across all layers:

#### Unit Tests
```bash
# Backend unit tests
cd backend
pytest tests/unit/ -v

# Frontend unit tests
cd frontend
npm test

# Run with coverage
cd backend
pytest tests/unit/ --cov=app --cov-report=html

cd frontend
npm run test:coverage
```

#### Integration Tests
```bash
# Backend integration tests (requires Docker)
cd backend
python tests/integration/run_integration_tests.py

# Frontend integration tests
cd frontend
npm run test:integration

# Run specific integration test
cd backend
python tests/integration/run_integration_tests.py -k TestCompleteAnalysisWorkflows
```

#### End-to-End Tests
```bash
# E2E tests with Playwright (requires running application)
cd e2e
npm test

# Run specific E2E test
npx playwright test market-analysis-trigger.spec.ts

# Run with browser UI
npx playwright test --ui

# Run in headed mode for debugging
npx playwright test --headed
```

#### Performance Tests
```bash
# Full performance test suite
cd performance
python run_all_tests.py --level comprehensive

# API load testing only
python -m api.run_load_tests --scenario medium

# WebSocket scalability tests
python -m websocket.websocket_tests

# Database performance benchmarks
python -m database.db_performance_tests
```

#### Quick Test Commands
```bash
# Run all tests (requires Docker and running application)
./scripts/run-all-tests.sh

# Run unit tests only
./scripts/run-unit-tests.sh

# Run tests with coverage report
./scripts/run-tests-with-coverage.sh

# Run CI test pipeline
./scripts/run-ci-tests.sh
```

#### Test Coverage Targets
- **Overall Coverage**: ≥80%
- **Critical Paths**: ≥85%
- **API Endpoints**: ≥90%
- **React Components**: ≥80%

For detailed testing instructions, see the [Testing Guide](docs/testing-guide.md).

## Architecture

### Database Schema
- **Articles**: Scraped news with metadata and processing status
- **Analyses**: AI sentiment analysis results with LLM responses
- **Positions**: Trading recommendations with supporting evidence

### Services
- **ScraperService**: Web scraping with rate limiting and error handling
- **LLMService**: AI integration with retry logic and response parsing  
- **AnalysisService**: Orchestrates the complete analysis pipeline
- **WebSocketManager**: Real-time communication with frontend clients

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Documentation

### Comprehensive Documentation
- [Testing Guide](docs/testing-guide.md) - Complete testing instructions and best practices
- [Architecture Documentation](docs/architecture.md) - System design and component overview
- [API Documentation](docs/api-documentation.md) - Detailed API reference with examples
- [Test Coverage](docs/test-coverage.md) - Coverage metrics and improvement plans

### Setup and Configuration
- [Environment Setup](backend/.env.example) - Backend environment configuration
- [Frontend Configuration](frontend/.env.example) - Frontend environment setup
- [Docker Configuration](.env.example) - Docker Compose environment setup

### Testing Documentation
- [Backend Testing](backend/tests/integration/README.md) - Backend integration testing
- [Frontend Testing](frontend/src/tests/integration/README.md) - Frontend integration testing
- [E2E Testing](e2e/TESTING_GUIDE.md) - End-to-end testing guide
- [Performance Testing](performance/README.md) - Performance and load testing

## License

MIT License - see LICENSE file for details