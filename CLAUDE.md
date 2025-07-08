# Market News Analysis Agent

## Project Overview
This is a full-stack market analysis application that scrapes financial news and generates trading recommendations using AI sentiment analysis.

## Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI + PostgreSQL + Redis
- **AI**: OpenAI GPT or Claude API for sentiment and all AI analysis
- **Deployment**: Docker + Docker Compose

## Project Structure
```
/frontend - React application with market dashboard
/backend - FastAPI server with analysis engine
/docker - Docker configuration files
/.github - CI/CD workflows
```

## Key Features to Implement
1. On-demand market analysis triggered by user button click
2. Web scraping from FinViz and BizToc with proper rate limiting
3. LLM-based catalyst detection (no keyword matching)
4. PostgreSQL database for persistent storage
5. Real-time WebSocket updates for analysis progress
6. Article browser with search and filtering
7. Activity log showing agent actions

## Development Guidelines

### API Design
- RESTful endpoints for CRUD operations
- WebSocket for real-time updates during analysis
- Proper error handling with meaningful status codes
- Request validation using Pydantic models

### Database Schema
- Use UUID primary keys for all tables
- Add proper indexes for ticker, timestamp, and full-text search
- Store LLM analysis results as JSONB
- Implement soft deletes where appropriate

### Web Scraping Best Practices
- Respect robots.txt
- Implement exponential backoff for retries
- Use rate limiting (10 requests per minute per domain)
- Add proper User-Agent headers
- Handle dynamic content with Selenium when needed
- Cache scraped content for 24 hours

### LLM Integration
- Use structured prompts for consistent output
- Request JSON responses for easier parsing
- Implement retry logic with exponential backoff
- Log all LLM interactions for debugging
- Use temperature 0.1-0.2 for consistent analysis

### Frontend Requirements
- Mobile-responsive design
- Loading states for all async operations
- Error boundaries for graceful failure handling
- Optimistic UI updates where appropriate
- Dark mode support

### Testing Strategy
- Unit tests for utility functions
- Integration tests for API endpoints
- Mock external services (scraping, LLM) in tests
- Use pytest for backend, Jest for frontend

## Create Configuration Environment File 

### Environment Variables
```
# Backend
DATABASE_URL=postgresql://user:pass@localhost/market_analysis
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
MAX_POSITIONS=10
MIN_CONFIDENCE=0.7

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Docker Setup
- Use multi-stage builds for smaller images
- Include health checks for all services
- Use volumes for PostgreSQL data persistence
- Set resource limits for containers

## Analysis Logic

### Position Recommendations
- STRONG_BUY: sentiment > 0.7, multiple positive catalysts
- BUY: sentiment > 0.4, at least one positive catalyst  
- HOLD: sentiment -0.2 to 0.4
- SHORT: sentiment < -0.4, negative catalysts
- STRONG_SHORT: sentiment < -0.7, multiple negative catalysts

### Catalyst Types to Detect
- Earnings (beats/misses)
- FDA approvals/rejections
- M&A activity
- Major partnerships
- Legal issues
- Management changes
- Product launches
- Think outside the box

## Error Handling
- Log all errors with context
- Return user-friendly error messages
- Implement circuit breakers for external services
- Add monitoring and alerting

## Performance Considerations
- Implement database connection pooling
- Use Redis for caching frequent queries
- Batch LLM requests when possible
- Implement pagination for large result sets
- Use async/await throughout the stack

## Security
- Validate all user inputs
- Use parameterized queries
- Implement rate limiting on API endpoints
- Add CORS configuration
- Use environment variables for secrets

## Commit Conventions
Use conventional commits:
- feat: new feature
- fix: bug fix
- docs: documentation
- style: formatting
- refactor: code restructuring
- test: adding tests
- chore: maintenance

## When Working on This Project
1. Always run tests before committing
2. Update documentation as you code
3. Follow the existing code style
4. Add meaningful commit messages
