# API Documentation with Test Examples

## Overview

This document provides comprehensive API documentation for the Market News Analysis Agent, including detailed request/response examples, error handling, and test scenarios for each endpoint.

## Table of Contents

- [Base URLs and Authentication](#base-urls-and-authentication)
- [Analysis Endpoints](#analysis-endpoints)
- [Articles Endpoints](#articles-endpoints)
- [Positions Endpoints](#positions-endpoints)
- [Activity Logs Endpoints](#activity-logs-endpoints)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Testing Examples](#testing-examples)

## Base URLs and Authentication

### Base URLs
- **Development**: `http://localhost:8000`
- **Production**: `https://api.marketanalysis.com`

### Authentication
Currently, the API does not require authentication, but this will be added in future versions.

### API Versioning
All endpoints are versioned and prefixed with `/api/v1/`.

## Analysis Endpoints

### Start Analysis

Initiates a new market analysis session.

#### Request
```http
POST /api/v1/analysis/start
Content-Type: application/json

{
  "max_positions": 5,
  "min_confidence": 0.7,
  "analysis_type": "headlines",
  "llm_model": "gpt-4",
  "sources": ["finviz", "biztoc"]
}
```

#### Request Schema
```typescript
interface AnalysisRequest {
  max_positions: number;      // 1-20, default: 10
  min_confidence: number;     // 0.1-1.0, default: 0.7
  analysis_type: "headlines" | "full";  // default: "headlines"
  llm_model: "gpt-4" | "gpt-3.5-turbo" | "claude-3";
  sources: ("finviz" | "biztoc")[];  // default: ["finviz", "biztoc"]
}
```

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "analysis_20241201_143022_abc123",
  "message": "Analysis started successfully",
  "status": "started",
  "estimated_duration": 180
}
```

#### Error Responses
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "max_positions must be between 1 and 20"
}
```

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "loc": ["body", "min_confidence"],
      "msg": "ensure this value is greater than or equal to 0.1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

#### Test Examples

##### Unit Test Example
```python
# tests/unit/test_analysis_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

@patch('app.api.routes.analysis.AnalysisService')
def test_start_analysis_success(mock_analysis_service, client: TestClient):
    # Arrange
    mock_analysis_service.return_value.analyze_market = AsyncMock(
        return_value={
            "session_id": "test-session-123",
            "message": "Analysis started successfully",
            "status": "started",
            "estimated_duration": 180
        }
    )
    
    request_data = {
        "max_positions": 5,
        "min_confidence": 0.7,
        "analysis_type": "headlines",
        "llm_model": "gpt-4",
        "sources": ["finviz"]
    }
    
    # Act
    response = client.post("/api/v1/analysis/start", json=request_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
    assert data["status"] == "started"
    mock_analysis_service.return_value.analyze_market.assert_called_once()

def test_start_analysis_invalid_max_positions(client: TestClient):
    # Arrange
    request_data = {
        "max_positions": 25,  # Invalid: > 20
        "min_confidence": 0.7,
        "analysis_type": "headlines",
        "llm_model": "gpt-4"
    }
    
    # Act
    response = client.post("/api/v1/analysis/start", json=request_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "max_positions" in str(data["detail"])
```

##### Integration Test Example
```python
# tests/integration/test_analysis_workflows.py
import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_analysis_workflow(
    integration_client: AsyncClient,
    mock_external_services,
    integration_test_data
):
    # Arrange
    analysis_request = {
        "max_positions": 3,
        "min_confidence": 0.8,
        "analysis_type": "headlines",
        "llm_model": "gpt-4",
        "sources": ["finviz"]
    }
    
    mock_external_services["scraper"].configure_response(
        integration_test_data["sample_headlines"]
    )
    mock_external_services["llm"].configure_response(
        integration_test_data["sample_analysis"]
    )
    
    # Act - Start analysis
    response = await integration_client.post(
        "/api/v1/analysis/start",
        json=analysis_request
    )
    
    # Assert initial response
    assert response.status_code == 200
    session_data = response.json()
    session_id = session_data["session_id"]
    
    # Wait for completion
    await wait_for_analysis_completion(integration_client, session_id)
    
    # Verify positions were generated
    positions_response = await integration_client.get(
        f"/api/v1/positions/session/{session_id}"
    )
    assert positions_response.status_code == 200
    positions = positions_response.json()
    assert len(positions) > 0
    assert all(p["confidence"] >= 0.8 for p in positions)
```

##### E2E Test Example
```typescript
// e2e/tests/analysis-api.spec.ts
import { test, expect } from '@playwright/test';

test('should start analysis via API and WebSocket', async ({ page }) => {
  // Mock API response
  await page.route('/api/v1/analysis/start', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        session_id: 'test-session-123',
        message: 'Analysis started successfully',
        status: 'started',
        estimated_duration: 180
      })
    });
  });

  // Navigate to page
  await page.goto('/');
  
  // Start analysis
  await page.click('[data-testid="start-analysis"]');
  
  // Verify API call was made
  const apiCall = await page.waitForRequest('/api/v1/analysis/start');
  const requestData = apiCall.postDataJSON();
  expect(requestData.max_positions).toBe(5);
  expect(requestData.analysis_type).toBe('headlines');
  
  // Verify UI updates
  await expect(page.locator('[data-testid="analysis-status"]')).toContainText('started');
});
```

### Get Analysis Status

Retrieves the current status of an analysis session.

#### Request
```http
GET /api/v1/analysis/status/{session_id}
```

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "analysis_20241201_143022_abc123",
  "status": "in_progress",
  "progress": 65,
  "current_step": "analyzing_sentiment",
  "articles_processed": 13,
  "positions_generated": 2,
  "started_at": "2024-12-01T14:30:22Z",
  "estimated_completion": "2024-12-01T14:33:22Z",
  "error_message": null
}
```

#### Response Schema
```typescript
interface AnalysisStatus {
  session_id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;  // 0-100
  current_step: string;
  articles_processed: number;
  positions_generated: number;
  started_at: string;  // ISO datetime
  completed_at?: string;  // ISO datetime
  estimated_completion?: string;  // ISO datetime
  error_message?: string;
}
```

#### Test Example
```python
def test_get_analysis_status_success(client: TestClient):
    # Arrange
    session_id = "test-session-123"
    
    with patch('app.services.analysis_service.AnalysisService.get_status') as mock_get_status:
        mock_get_status.return_value = {
            "session_id": session_id,
            "status": "completed",
            "progress": 100,
            "current_step": "finished",
            "articles_processed": 15,
            "positions_generated": 5,
            "started_at": "2024-12-01T14:30:22Z",
            "completed_at": "2024-12-01T14:33:45Z"
        }
        
        # Act
        response = client.get(f"/api/v1/analysis/status/{session_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["positions_generated"] == 5

def test_get_analysis_status_not_found(client: TestClient):
    # Act
    response = client.get("/api/v1/analysis/status/nonexistent-session")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
```

## Articles Endpoints

### List Articles

Retrieves a paginated list of articles with optional filtering.

#### Request
```http
GET /api/v1/articles?ticker=AAPL&source=finviz&limit=10&offset=0&sort=scraped_at&order=desc
```

#### Query Parameters
- `ticker` (string, optional): Filter by stock ticker
- `source` (string, optional): Filter by news source
- `limit` (integer, optional): Number of results (1-100, default: 20)
- `offset` (integer, optional): Pagination offset (default: 0)
- `sort` (string, optional): Sort field (default: "scraped_at")
- `order` (string, optional): Sort order "asc" or "desc" (default: "desc")

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "articles": [
    {
      "id": "article-uuid-123",
      "ticker": "AAPL",
      "title": "Apple Reports Strong Q4 Earnings",
      "url": "https://finviz.com/news/apple-earnings",
      "content": "Apple Inc. reported stronger than expected...",
      "source": "finviz",
      "scraped_at": "2024-12-01T14:25:00Z",
      "processed_at": "2024-12-01T14:26:15Z",
      "status": "processed"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### Test Example
```python
def test_list_articles_with_filters(client: TestClient):
    # Arrange
    with patch('app.services.crud.get_articles') as mock_get_articles:
        mock_articles = [
            {
                "id": "article-1",
                "ticker": "AAPL",
                "title": "Apple News",
                "source": "finviz",
                "scraped_at": "2024-12-01T14:25:00Z"
            }
        ]
        mock_get_articles.return_value = (mock_articles, 1)
        
        # Act
        response = client.get("/api/v1/articles?ticker=AAPL&limit=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
        assert data["articles"][0]["ticker"] == "AAPL"
        assert data["total"] == 1
        assert data["limit"] == 5
        
        # Verify service called with correct parameters
        mock_get_articles.assert_called_once_with(
            db=mock.ANY,
            ticker="AAPL",
            source=None,
            limit=5,
            offset=0,
            sort="scraped_at",
            order="desc"
        )
```

### Get Single Article

Retrieves a specific article by ID.

#### Request
```http
GET /api/v1/articles/{article_id}
```

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "article-uuid-123",
  "ticker": "AAPL",
  "title": "Apple Reports Strong Q4 Earnings",
  "url": "https://finviz.com/news/apple-earnings",
  "content": "Full article content here...",
  "source": "finviz",
  "scraped_at": "2024-12-01T14:25:00Z",
  "processed_at": "2024-12-01T14:26:15Z",
  "status": "processed",
  "sentiment_analysis": {
    "sentiment_score": 0.75,
    "confidence": 0.89,
    "catalysts": ["earnings_beat", "positive_guidance"]
  }
}
```

## Positions Endpoints

### List Positions

Retrieves trading positions with optional filtering.

#### Request
```http
GET /api/v1/positions?session_id=analysis_123&ticker=AAPL&position_type=BUY
```

#### Query Parameters
- `session_id` (string, optional): Filter by analysis session
- `ticker` (string, optional): Filter by stock ticker
- `position_type` (string, optional): Filter by position type
- `min_confidence` (float, optional): Minimum confidence threshold
- `limit` (integer, optional): Number of results (default: 20)
- `offset` (integer, optional): Pagination offset (default: 0)

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "positions": [
    {
      "id": "position-uuid-456",
      "session_id": "analysis_20241201_143022_abc123",
      "ticker": "AAPL",
      "position_type": "BUY",
      "confidence": 0.85,
      "reasoning": "Strong earnings beat with positive guidance for Q1",
      "target_price": 195.50,
      "created_at": "2024-12-01T14:33:45Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Test Example
```python
def test_list_positions_by_session(client: TestClient):
    # Arrange
    session_id = "test-session-123"
    
    with patch('app.services.crud.get_positions') as mock_get_positions:
        mock_positions = [
            {
                "id": "position-1",
                "session_id": session_id,
                "ticker": "AAPL",
                "position_type": "BUY",
                "confidence": 0.85,
                "reasoning": "Strong earnings",
                "created_at": "2024-12-01T14:33:45Z"
            }
        ]
        mock_get_positions.return_value = (mock_positions, 1)
        
        # Act
        response = client.get(f"/api/v1/positions?session_id={session_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["positions"]) == 1
        assert data["positions"][0]["session_id"] == session_id
        assert data["positions"][0]["confidence"] == 0.85
```

### Get Positions by Session

Retrieves all positions for a specific analysis session.

#### Request
```http
GET /api/v1/positions/session/{session_id}
```

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "id": "position-uuid-456",
    "session_id": "analysis_20241201_143022_abc123",
    "ticker": "AAPL",
    "position_type": "BUY",
    "confidence": 0.85,
    "reasoning": "Strong earnings beat with positive guidance",
    "target_price": 195.50,
    "created_at": "2024-12-01T14:33:45Z"
  },
  {
    "id": "position-uuid-789",
    "session_id": "analysis_20241201_143022_abc123",
    "ticker": "TSLA",
    "position_type": "SHORT",
    "confidence": 0.72,
    "reasoning": "Production concerns and regulatory issues",
    "target_price": 180.00,
    "created_at": "2024-12-01T14:33:50Z"
  }
]
```

## Activity Logs Endpoints

### List Activity Logs

Retrieves activity logs with optional filtering.

#### Request
```http
GET /api/v1/activity-logs?session_id=analysis_123&level=INFO&limit=50
```

#### Query Parameters
- `session_id` (string, optional): Filter by analysis session
- `level` (string, optional): Filter by log level (INFO, WARNING, ERROR)
- `action` (string, optional): Filter by action type
- `limit` (integer, optional): Number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

#### Success Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "logs": [
    {
      "id": "log-uuid-101",
      "session_id": "analysis_20241201_143022_abc123",
      "action": "analysis_started",
      "details": {
        "max_positions": 5,
        "min_confidence": 0.7,
        "sources": ["finviz", "biztoc"]
      },
      "level": "INFO",
      "timestamp": "2024-12-01T14:30:22Z"
    },
    {
      "id": "log-uuid-102",
      "session_id": "analysis_20241201_143022_abc123",
      "action": "headlines_scraped",
      "details": {
        "source": "finviz",
        "headlines_count": 25
      },
      "level": "INFO",
      "timestamp": "2024-12-01T14:30:45Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

## WebSocket API

### Connection Endpoint
```
ws://localhost:8000/ws
```

### Message Types

#### Subscribe to Analysis Session
```json
{
  "type": "subscribe",
  "session_id": "analysis_20241201_143022_abc123"
}
```

#### Analysis Progress Update
```json
{
  "type": "analysis_progress",
  "data": {
    "session_id": "analysis_20241201_143022_abc123",
    "status": "in_progress",
    "progress": 65,
    "current_step": "analyzing_sentiment",
    "articles_processed": 13,
    "positions_generated": 2
  },
  "timestamp": "2024-12-01T14:32:15Z"
}
```

#### Analysis Complete
```json
{
  "type": "analysis_complete",
  "data": {
    "session_id": "analysis_20241201_143022_abc123",
    "status": "completed",
    "positions_count": 5,
    "articles_processed": 25,
    "duration_seconds": 183
  },
  "timestamp": "2024-12-01T14:33:45Z"
}
```

#### Activity Log Update
```json
{
  "type": "activity_log",
  "data": {
    "session_id": "analysis_20241201_143022_abc123",
    "action": "position_generated",
    "details": {
      "ticker": "AAPL",
      "position_type": "BUY",
      "confidence": 0.85
    },
    "level": "INFO"
  },
  "timestamp": "2024-12-01T14:33:30Z"
}
```

#### Error Message
```json
{
  "type": "analysis_error",
  "data": {
    "session_id": "analysis_20241201_143022_abc123",
    "error": "LLM service temporarily unavailable",
    "error_code": "LLM_SERVICE_ERROR",
    "retry_after": 60
  },
  "timestamp": "2024-12-01T14:31:30Z"
}
```

### WebSocket Test Example

```python
# tests/integration/test_websocket.py
import pytest
import websockets
import json
import asyncio

@pytest.mark.asyncio
async def test_websocket_analysis_updates():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to session
        subscribe_message = {
            "type": "subscribe",
            "session_id": "test-session-123"
        }
        await websocket.send(json.dumps(subscribe_message))
        
        # Start analysis via HTTP API
        session_id = await start_test_analysis()
        
        # Listen for WebSocket updates
        messages = []
        timeout = 30  # seconds
        
        try:
            while len(messages) < 3:  # Expect at least 3 updates
                message = await asyncio.wait_for(
                    websocket.recv(), 
                    timeout=timeout
                )
                messages.append(json.loads(message))
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for WebSocket messages")
        
        # Verify message progression
        assert messages[0]["type"] == "analysis_progress"
        assert messages[0]["data"]["status"] in ["started", "in_progress"]
        
        assert messages[-1]["type"] in ["analysis_complete", "analysis_progress"]
        if messages[-1]["type"] == "analysis_complete":
            assert messages[-1]["data"]["status"] == "completed"
```

## Error Handling

### Standard Error Response Format

All API errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-12-01T14:30:22Z",
  "path": "/api/v1/analysis/start",
  "request_id": "req-uuid-456"
}
```

### HTTP Status Codes

| Status Code | Description | When Used |
|-------------|-------------|-----------|
| 200 | OK | Successful GET, PATCH |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid request data |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service down |

### Error Code Reference

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `SESSION_NOT_FOUND` | Analysis session doesn't exist |
| `ANALYSIS_IN_PROGRESS` | Session already running |
| `LLM_SERVICE_ERROR` | LLM API unavailable |
| `SCRAPER_SERVICE_ERROR` | Web scraping failed |
| `DATABASE_ERROR` | Database operation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

### Error Handling Test Examples

```python
def test_error_handling_invalid_session_id(client: TestClient):
    # Act
    response = client.get("/api/v1/analysis/status/invalid-session-id")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "SESSION_NOT_FOUND"
    assert "session" in data["detail"].lower()

def test_error_handling_validation_error(client: TestClient):
    # Arrange
    invalid_request = {
        "max_positions": 0,  # Invalid: must be >= 1
        "min_confidence": 1.5,  # Invalid: must be <= 1.0
        "analysis_type": "invalid_type"  # Invalid enum value
    }
    
    # Act
    response = client.post("/api/v1/analysis/start", json=invalid_request)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) >= 3  # Should have errors for all invalid fields

@patch('app.services.llm_service.LLMService.analyze_sentiment')
def test_error_handling_llm_service_error(mock_llm_service, client: TestClient):
    # Arrange
    mock_llm_service.side_effect = Exception("LLM service unavailable")
    
    # Act
    response = client.post("/api/v1/analysis/start", json={
        "max_positions": 5,
        "min_confidence": 0.7,
        "analysis_type": "headlines",
        "llm_model": "gpt-4"
    })
    
    # Assert
    assert response.status_code == 503
    data = response.json()
    assert data["error_code"] == "LLM_SERVICE_ERROR"
```

## Rate Limiting

### Rate Limits
- **Analysis endpoints**: 10 requests per minute per IP
- **General endpoints**: 60 requests per minute per IP
- **WebSocket connections**: 5 concurrent connections per IP

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1638360000
```

### Rate Limit Test Example

```python
def test_rate_limiting(client: TestClient):
    # Make requests up to the limit
    for i in range(60):
        response = client.get("/api/v1/articles")
        assert response.status_code == 200
        
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    # Next request should be rate limited
    response = client.get("/api/v1/articles")
    assert response.status_code == 429
    data = response.json()
    assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
```

## Testing Examples

### Postman Collection

```json
{
  "info": {
    "name": "Market Analysis API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Start Analysis",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"max_positions\": 5,\n  \"min_confidence\": 0.7,\n  \"analysis_type\": \"headlines\",\n  \"llm_model\": \"gpt-4\",\n  \"sources\": [\"finviz\"]\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/analysis/start",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "analysis", "start"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    }
  ]
}
```

### cURL Examples

```bash
# Start analysis
curl -X POST "http://localhost:8000/api/v1/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "max_positions": 5,
    "min_confidence": 0.7,
    "analysis_type": "headlines",
    "llm_model": "gpt-4",
    "sources": ["finviz"]
  }'

# Get analysis status
curl "http://localhost:8000/api/v1/analysis/status/analysis_20241201_143022_abc123"

# List articles with filtering
curl "http://localhost:8000/api/v1/articles?ticker=AAPL&limit=5"

# Get positions by session
curl "http://localhost:8000/api/v1/positions/session/analysis_20241201_143022_abc123"
```

### JavaScript/TypeScript Examples

```typescript
// TypeScript API client
class MarketAnalysisAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async startAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/analysis/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getAnalysisStatus(sessionId: string): Promise<AnalysisStatus> {
    const response = await fetch(`${this.baseURL}/api/v1/analysis/status/${sessionId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getPositionsBySession(sessionId: string): Promise<Position[]> {
    const response = await fetch(`${this.baseURL}/api/v1/positions/session/${sessionId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  connectWebSocket(onMessage: (message: WebSocketMessage) => void): WebSocket {
    const ws = new WebSocket(`${this.baseURL.replace('http', 'ws')}/ws`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      onMessage(message);
    };

    return ws;
  }
}

// Usage example
const api = new MarketAnalysisAPI();

// Start analysis
const analysisResponse = await api.startAnalysis({
  max_positions: 5,
  min_confidence: 0.7,
  analysis_type: 'headlines',
  llm_model: 'gpt-4',
  sources: ['finviz']
});

// Connect to WebSocket for real-time updates
const ws = api.connectWebSocket((message) => {
  console.log('Received message:', message);
});

// Subscribe to session updates
ws.send(JSON.stringify({
  type: 'subscribe',
  session_id: analysisResponse.session_id
}));
```

---

## Summary

This API documentation provides comprehensive information for integrating with the Market News Analysis Agent API, including:

- **Complete endpoint documentation** with request/response examples
- **WebSocket API** for real-time updates
- **Error handling** with consistent error formats
- **Testing examples** at unit, integration, and E2E levels
- **Rate limiting** information and best practices
- **Code examples** in multiple languages

For additional help or questions about the API, refer to the [Testing Guide](testing-guide.md) and [Architecture Documentation](architecture.md).