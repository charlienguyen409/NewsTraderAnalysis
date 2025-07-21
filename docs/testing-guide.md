# Comprehensive Testing Guide

## Overview

This guide provides detailed instructions for running, writing, and maintaining tests for the Market News Analysis Agent. The testing strategy includes unit tests, integration tests, end-to-end tests, and performance tests to ensure system reliability and quality.

## Table of Contents

- [Testing Architecture](#testing-architecture)
- [Setting Up Test Environment](#setting-up-test-environment)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Test Data Management](#test-data-management)
- [CI/CD Testing](#cicd-testing)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Testing Architecture

### Test Pyramid

```
    /\
   /  \
  /E2E \    <- End-to-End Tests (Few, High Value)
 /______\
/        \
| Integration|  <- Integration Tests (Some, Critical Paths)
|___________|
/            \
|    Unit      | <- Unit Tests (Many, Fast, Isolated)
|______________|
```

### Test Types Overview

1. **Unit Tests** - Test individual functions, components, and classes in isolation
2. **Integration Tests** - Test interactions between components and services
3. **End-to-End Tests** - Test complete user workflows across the entire system
4. **Performance Tests** - Test system performance, load, and scalability

### Test Coverage Targets

- **Overall Coverage**: ≥80%
- **Critical Business Logic**: ≥85%
- **API Endpoints**: ≥90%
- **React Components**: ≥80%
- **Service Layer**: ≥85%

## Setting Up Test Environment

### Prerequisites

1. **Docker and Docker Compose** - For isolated test databases
2. **Node.js 18+** - For frontend tests
3. **Python 3.11+** - For backend tests
4. **Playwright** - For E2E tests

### Quick Setup

```bash
# Clone and setup
git clone <repository-url>
cd NewsTraderAnalysis

# Install backend dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Install frontend dependencies
cd ../frontend
npm install

# Install E2E test dependencies
cd ../e2e
npm install
npx playwright install

# Install performance test dependencies
cd ../performance
pip install -r requirements.txt
```

### Environment Variables for Testing

Create test environment files:

```bash
# Backend test environment
cat > backend/.env.test << EOF
DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_market_analysis
REDIS_URL=redis://localhost:6380
OPENAI_API_KEY=test-key-not-real
ANTHROPIC_API_KEY=test-key-not-real
TESTING=true
LOG_LEVEL=DEBUG
EOF

# Frontend test environment
cat > frontend/.env.test << EOF
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws
NODE_ENV=test
EOF
```

## Unit Testing

### Backend Unit Tests

#### Running Backend Unit Tests

```bash
cd backend

# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_analysis.py -v

# Run specific test function
pytest tests/unit/test_analysis.py::test_sentiment_analysis -v

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html --cov-report=term

# Run with coverage and open report
pytest tests/unit/ --cov=app --cov-report=html && open htmlcov/index.html
```

#### Writing Backend Unit Tests

**Testing Service Layer:**

```python
# tests/unit/test_analysis_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.analysis_service import AnalysisService
from app.schemas.analysis_request import AnalysisRequest

class TestAnalysisService:
    @pytest.fixture
    def analysis_service(self, mock_db_session):
        return AnalysisService(mock_db_session)
    
    @pytest.fixture
    def sample_analysis_request(self):
        return AnalysisRequest(
            max_positions=5,
            min_confidence=0.7,
            analysis_type="headlines",
            llm_model="gpt-4"
        )
    
    @patch('app.services.analysis_service.LLMService')
    @patch('app.services.analysis_service.ScraperService')
    async def test_analyze_market_success(
        self, 
        mock_scraper, 
        mock_llm, 
        analysis_service, 
        sample_analysis_request
    ):
        # Arrange
        mock_scraper.return_value.scrape_headlines.return_value = [
            {"title": "Apple beats earnings", "ticker": "AAPL", "source": "finviz"}
        ]
        mock_llm.return_value.analyze_sentiment.return_value = {
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "catalysts": ["earnings_beat"]
        }
        
        # Act
        result = await analysis_service.analyze_market(sample_analysis_request)
        
        # Assert
        assert result.session_id is not None
        assert len(result.positions) >= 0
        mock_scraper.return_value.scrape_headlines.assert_called_once()
        mock_llm.return_value.analyze_sentiment.assert_called()
```

**Testing API Endpoints:**

```python
# tests/unit/test_analysis_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

class TestAnalysisAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('app.api.routes.analysis.AnalysisService')
    def test_start_analysis_success(self, mock_analysis_service, client):
        # Arrange
        mock_analysis_service.return_value.analyze_market = AsyncMock(
            return_value={"session_id": "test-123", "message": "Analysis started"}
        )
        
        # Act
        response = client.post("/api/v1/analysis/start", json={
            "max_positions": 5,
            "min_confidence": 0.7,
            "analysis_type": "headlines",
            "llm_model": "gpt-4"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-123"
        assert "message" in data
```

### Frontend Unit Tests

#### Running Frontend Unit Tests

```bash
cd frontend

# Run all unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- PositionCard.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"
```

#### Writing Frontend Unit Tests

**Testing React Components:**

```typescript
// src/components/__tests__/PositionCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PositionCard from '../PositionCard';
import { Position } from '../../types';

const mockPosition: Position = {
  id: 'test-1',
  ticker: 'AAPL',
  position_type: 'BUY',
  confidence: 0.85,
  reasoning: 'Strong earnings beat with positive guidance',
  session_id: 'session-123',
  created_at: '2024-01-01T00:00:00Z'
};

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('PositionCard', () => {
  it('should render position information correctly', () => {
    renderWithQueryClient(<PositionCard position={mockPosition} />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText(/Strong earnings beat/)).toBeInTheDocument();
  });
  
  it('should handle click events', () => {
    const onClickMock = jest.fn();
    renderWithQueryClient(
      <PositionCard position={mockPosition} onClick={onClickMock} />
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(onClickMock).toHaveBeenCalledWith(mockPosition);
  });
});
```

**Testing Custom Hooks:**

```typescript
// src/lib/__tests__/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  send(data: string) {
    // Mock implementation
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }
}

global.WebSocket = MockWebSocket as any;

describe('useWebSocket', () => {
  it('should connect to WebSocket and handle messages', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws'));
    
    await act(async () => {
      // Wait for connection
    });
    
    expect(result.current.connectionState).toBe('Connected');
    
    // Test sending message
    act(() => {
      result.current.sendMessage({ type: 'subscribe', session_id: 'test-123' });
    });
    
    // Test cleanup
    act(() => {
      result.current.disconnect();
    });
    
    expect(result.current.connectionState).toBe('Disconnected');
  });
});
```

## Integration Testing

### Backend Integration Tests

#### Running Backend Integration Tests

```bash
cd backend

# Run all integration tests (starts Docker containers)
python tests/integration/run_integration_tests.py

# Run specific test class
python tests/integration/run_integration_tests.py -k TestCompleteAnalysisWorkflows

# Run with coverage
python tests/integration/run_integration_tests.py --coverage

# Use Docker Compose for tests
docker-compose -f tests/integration/docker-compose.test.yml up --abort-on-container-exit
```

#### Writing Backend Integration Tests

```python
# tests/integration/test_workflows.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from app.services.analysis_service import AnalysisService
from app.schemas.analysis_request import AnalysisRequest

class TestCompleteAnalysisWorkflows:
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow_success(
        self,
        integration_client,
        integration_db_session: AsyncSession,
        mock_external_services,
        integration_test_data
    ):
        """Test complete analysis workflow from request to position generation"""
        
        # Arrange
        analysis_request = AnalysisRequest(
            max_positions=5,
            min_confidence=0.7,
            analysis_type="full",
            llm_model="gpt-4"
        )
        
        # Configure mock responses
        mock_external_services["scraper"].configure_headlines_response(
            integration_test_data["sample_headlines"]
        )
        mock_external_services["llm"].configure_analysis_response(
            integration_test_data["sample_analysis"]
        )
        
        # Act
        response = integration_client.post(
            "/api/v1/analysis/start",
            json=analysis_request.dict()
        )
        
        # Assert initial response
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session_id"]
        
        # Wait for analysis completion
        await self._wait_for_analysis_completion(integration_client, session_id)
        
        # Verify positions were created
        positions_response = integration_client.get(
            f"/api/v1/positions/session/{session_id}"
        )
        assert positions_response.status_code == 200
        positions = positions_response.json()
        
        assert len(positions) > 0
        for position in positions:
            assert position["confidence"] >= 0.7
            assert position["position_type"] in ["BUY", "SHORT", "STRONG_BUY", "STRONG_SHORT"]
        
        # Verify database state
        await self._verify_database_consistency(integration_db_session, session_id)
    
    async def _wait_for_analysis_completion(self, client, session_id: str, timeout: int = 30):
        """Wait for analysis to complete with timeout"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status_response = client.get(f"/api/v1/analysis/status/{session_id}")
            status_data = status_response.json()
            
            if status_data["status"] in ["completed", "failed"]:
                return status_data
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Analysis did not complete within {timeout} seconds")
            
            await asyncio.sleep(1)
```

### Frontend Integration Tests

#### Running Frontend Integration Tests

```bash
cd frontend

# Run all integration tests
npm run test:integration

# Run specific integration test
npm test -- analysisWorkflow.test.tsx

# Run with coverage
npm run test:coverage -- --testPathPattern=integration
```

#### Writing Frontend Integration Tests

```typescript
// src/tests/integration/analysisWorkflow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';
import { mockHandlers, MockWebSocket } from '../mocks';

const renderApp = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Analysis Workflow Integration', () => {
  beforeEach(() => {
    mockHandlers.reset();
    MockWebSocket.reset();
  });

  it('should complete full analysis workflow', async () => {
    const user = userEvent.setup();
    renderApp();
    
    // 1. Navigate to Dashboard
    await waitFor(() => {
      expect(screen.getByText('Market Analysis Dashboard')).toBeInTheDocument();
    });
    
    // 2. Configure analysis settings
    const settingsButton = screen.getByText('Settings');
    await user.click(settingsButton);
    
    const maxPositionsInput = screen.getByLabelText('Max Positions');
    await user.clear(maxPositionsInput);
    await user.type(maxPositionsInput, '5');
    
    const saveButton = screen.getByText('Save');
    await user.click(saveButton);
    
    // 3. Start analysis
    const analyzeButton = screen.getByText('Analyze Market');
    await user.click(analyzeButton);
    
    // 4. Verify loading state
    expect(screen.getByText('Analysis in progress...')).toBeInTheDocument();
    
    // 5. Simulate WebSocket updates
    MockWebSocket.simulateMessage({
      type: 'analysis_progress',
      data: { status: 'scraping', progress: 25 }
    });
    
    await waitFor(() => {
      expect(screen.getByText('Scraping financial news...')).toBeInTheDocument();
    });
    
    // 6. Complete analysis
    MockWebSocket.simulateMessage({
      type: 'analysis_complete',
      data: { session_id: 'test-session-123', positions_count: 3 }
    });
    
    // 7. Verify results
    await waitFor(() => {
      expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
      expect(screen.getByText('3 positions generated')).toBeInTheDocument();
    });
    
    // 8. Navigate to positions
    const positionsLink = screen.getByText('View Positions');
    await user.click(positionsLink);
    
    await waitFor(() => {
      expect(screen.getByText('Trading Positions')).toBeInTheDocument();
      const positionCards = screen.getAllByTestId('position-card');
      expect(positionCards).toHaveLength(3);
    });
  });
});
```

## End-to-End Testing

### Running E2E Tests

```bash
cd e2e

# Run all E2E tests
npm test

# Run specific test
npx playwright test market-analysis-trigger.spec.ts

# Run with browser UI for debugging
npx playwright test --ui

# Run in headed mode
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium

# Generate test report
npx playwright show-report
```

### Writing E2E Tests

```typescript
// e2e/tests/market-analysis-trigger.spec.ts
import { test, expect } from '@playwright/test';
import { 
  navigateAndWait, 
  waitForElement, 
  mockApiResponse,
  generateTestArticles 
} from '../utils/test-helpers';

test.describe('Market Analysis Trigger', () => {
  test.beforeEach(async ({ page }) => {
    // Setup mock responses
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      session_id: 'test-session-123',
      message: 'Analysis started successfully'
    });
    
    await navigateAndWait(page, '/');
  });

  test('should trigger analysis and display progress', async ({ page }) => {
    // Start analysis
    const analyzeButton = await waitForElement(page, '[data-testid="start-analysis"]');
    await analyzeButton.click();
    
    // Verify loading state
    await expect(page.locator('[data-testid="analysis-status"]')).toContainText('Starting');
    
    // Simulate progress updates via WebSocket
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'analysis_progress',
          data: { status: 'scraping', progress: 25 }
        }));
      };
    });
    
    // Verify progress update
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    await expect(page.locator('[data-testid="analysis-status"]')).toContainText('Scraping');
    
    // Complete analysis
    await page.evaluate(() => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'analysis_complete',
          data: { session_id: 'test-session-123', positions_count: 5 }
        }));
      };
    });
    
    // Verify completion
    await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible();
    await expect(page.locator('[data-testid="positions-count"]')).toContainText('5');
  });

  test('should handle analysis errors gracefully', async ({ page }) => {
    // Mock error response
    await mockApiResponse(page, /\/api\/v1\/analysis\/start/, {
      error: 'LLM service unavailable'
    }, 500);
    
    // Try to start analysis
    const analyzeButton = await waitForElement(page, '[data-testid="start-analysis"]');
    await analyzeButton.click();
    
    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Analysis failed');
    
    // Verify button is re-enabled
    await expect(analyzeButton).toBeEnabled();
  });
});
```

## Performance Testing

### Running Performance Tests

```bash
cd performance

# Run comprehensive performance test suite
python run_all_tests.py --level comprehensive

# Run specific performance tests
python -m api.run_load_tests --scenario medium
python -m websocket.websocket_tests
python -m database.db_performance_tests

# Generate performance report
python -m reports.dashboard
```

For detailed performance testing information, see the [Performance Testing Guide](../performance/README.md).

## Test Data Management

### Backend Test Data

```python
# tests/fixtures/test_data.py
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

class TestDataFactory:
    @staticmethod
    def create_test_article(
        ticker: str = "AAPL",
        title: str = "Test Article",
        sentiment_score: float = 0.5,
        source: str = "finviz"
    ) -> Dict[str, Any]:
        return {
            "id": f"article-{random.randint(1000, 9999)}",
            "ticker": ticker,
            "title": title,
            "url": f"https://example.com/article-{random.randint(1, 1000)}",
            "content": f"Test content for {title}",
            "sentiment_score": sentiment_score,
            "source": source,
            "scraped_at": datetime.utcnow().isoformat(),
            "processed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def create_test_position(
        ticker: str = "AAPL",
        position_type: str = "BUY",
        confidence: float = 0.8
    ) -> Dict[str, Any]:
        return {
            "id": f"position-{random.randint(1000, 9999)}",
            "ticker": ticker,
            "position_type": position_type,
            "confidence": confidence,
            "reasoning": f"Test reasoning for {ticker} {position_type}",
            "session_id": f"session-{random.randint(100, 999)}",
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def create_test_analysis_request(
        max_positions: int = 5,
        min_confidence: float = 0.7,
        analysis_type: str = "headlines",
        llm_model: str = "gpt-4"
    ) -> Dict[str, Any]:
        return {
            "max_positions": max_positions,
            "min_confidence": min_confidence,
            "analysis_type": analysis_type,
            "llm_model": llm_model
        }
```

### Frontend Test Data

```typescript
// src/tests/mocks/testData.ts
import { Article, Position, AnalysisStatus } from '../../types';

export const mockArticles: Article[] = [
  {
    id: 'article-1',
    ticker: 'AAPL',
    title: 'Apple Reports Strong Q4 Earnings',
    url: 'https://example.com/apple-earnings',
    content: 'Apple exceeded expectations...',
    sentiment_score: 0.85,
    source: 'finviz',
    scraped_at: '2024-01-01T10:00:00Z',
    processed_at: '2024-01-01T10:05:00Z'
  },
  // ... more mock data
];

export const mockPositions: Position[] = [
  {
    id: 'position-1',
    ticker: 'AAPL',
    position_type: 'BUY',
    confidence: 0.85,
    reasoning: 'Strong earnings beat with positive guidance',
    session_id: 'session-123',
    created_at: '2024-01-01T10:00:00Z'
  },
  // ... more mock data
];

export const createMockAnalysisStatus = (
  status: string = 'completed'
): AnalysisStatus => ({
  session_id: 'session-123',
  status,
  progress: status === 'completed' ? 100 : 50,
  current_step: status === 'completed' ? 'finished' : 'analyzing',
  articles_processed: 10,
  positions_generated: 5,
  started_at: '2024-01-01T10:00:00Z',
  completed_at: status === 'completed' ? '2024-01-01T10:30:00Z' : null
});
```

## CI/CD Testing

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_market_analysis
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6380:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest-cov
    
    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit/ --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm run test:coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    needs: [backend-unit-tests, frontend-tests]
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_market_analysis
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5433:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6380:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest-cov docker psutil
    
    - name: Run integration tests
      run: |
        cd backend
        python tests/integration/run_integration_tests.py --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Start services
      run: |
        docker-compose -f docker/docker-compose.yml up -d
        # Wait for services to be ready
        sleep 30
    
    - name: Install E2E dependencies
      run: |
        cd e2e
        npm ci
        npx playwright install --with-deps
    
    - name: Run E2E tests
      run: |
        cd e2e
        npm test
    
    - name: Upload E2E artifacts
      uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: playwright-report
        path: e2e/playwright-report/
```

## Troubleshooting

### Common Issues

#### Test Database Connection Issues

```bash
# Check if test database is running
docker ps | grep postgres

# Start test database manually
docker run -d --name test_postgres \
  -p 5433:5432 \
  -e POSTGRES_DB=test_market_analysis \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_password \
  postgres:15-alpine

# Check connection
psql -h localhost -p 5433 -U test_user -d test_market_analysis
```

#### Frontend Test Failures

```bash
# Clear Jest cache
cd frontend
npx jest --clearCache

# Update snapshots
npm test -- --updateSnapshot

# Run tests with verbose output
npm test -- --verbose --no-coverage
```

#### Mock Service Issues

```bash
# Reset all mocks in test
beforeEach(() => {
  jest.clearAllMocks();
  MockWebSocket.reset();
  mockHandlers.reset();
});
```

### Debug Mode

#### Backend Debug Mode

```bash
# Run tests with debugger
cd backend
python -m pytest tests/unit/test_analysis.py::test_specific_function -s -vv --pdb

# Run with logging
python -m pytest tests/unit/ -s --log-cli-level=DEBUG
```

#### Frontend Debug Mode

```bash
# Run tests with debug output
cd frontend
npm test -- --verbose --watchAll=false

# Debug specific test
npm test -- PositionCard.test.tsx --verbose --no-coverage
```

#### E2E Debug Mode

```bash
# Run E2E tests in headed mode
cd e2e
npx playwright test --headed

# Run with inspector
npx playwright test --debug

# Take screenshots on failure
npx playwright test --screenshot=only-on-failure
```

## Best Practices

### Writing Effective Tests

1. **Test Behavior, Not Implementation**
   - Focus on what the system should do, not how it does it
   - Test user interactions and expected outcomes

2. **Use Descriptive Test Names**
   ```python
   # Good
   def test_analysis_service_generates_positions_when_confidence_above_threshold():
   
   # Bad  
   def test_analysis():
   ```

3. **Follow AAA Pattern**
   ```python
   def test_example():
       # Arrange
       setup_test_data()
       
       # Act
       result = perform_action()
       
       # Assert
       assert result == expected_outcome
   ```

4. **Mock External Dependencies**
   - Mock HTTP requests, database calls, file operations
   - Use consistent mock data across tests

5. **Test Edge Cases**
   - Empty inputs, null values, extreme values
   - Network failures, timeout scenarios
   - Invalid user inputs

### Test Maintenance

1. **Keep Tests Simple**
   - One assertion per test when possible
   - Avoid complex test setup

2. **Use Page Object Pattern for E2E Tests**
   ```typescript
   // e2e/pages/DashboardPage.ts
   export class DashboardPage {
     constructor(private page: Page) {}
     
     async startAnalysis() {
       await this.page.click('[data-testid="start-analysis"]');
     }
     
     async waitForAnalysisComplete() {
       await this.page.waitForSelector('[data-testid="analysis-complete"]');
     }
   }
   ```

3. **Regular Test Review**
   - Remove obsolete tests
   - Update tests when features change
   - Refactor duplicated test code

4. **Monitor Test Performance**
   - Keep test suites fast
   - Parallelize when possible
   - Use appropriate test levels

### Coverage Guidelines

1. **Focus on Critical Paths**
   - Prioritize business logic over boilerplate
   - Ensure error paths are tested

2. **Don't Chase 100% Coverage**
   - Aim for meaningful coverage
   - Consider complexity and risk

3. **Use Coverage Tools Effectively**
   ```bash
   # Generate coverage report with branch coverage
   pytest --cov=app --cov-branch --cov-report=html
   
   # Exclude test files from coverage
   pytest --cov=app --cov-report=html --cov-config=.coveragerc
   ```

4. **Review Coverage Reports**
   - Identify untested code paths
   - Focus on low-coverage, high-risk areas

---

## Summary

This comprehensive testing guide provides everything you need to effectively test the Market News Analysis Agent. Remember:

- **Start with unit tests** for fast feedback
- **Add integration tests** for critical workflows  
- **Use E2E tests** for user journey validation
- **Include performance tests** for scalability
- **Maintain tests** as the codebase evolves

For specific questions or issues, refer to the troubleshooting section or consult the individual test documentation in each module.