# Integration Tests for Market Analysis API

This directory contains comprehensive integration tests for the complete API workflows of the Market Analysis application.

## Overview

The integration tests cover:

- **Complete Analysis Workflows** - End-to-end testing from analysis trigger to position generation
- **API Integration** - Testing all API endpoints with realistic data flows
- **Service Integration** - Testing interactions between LLM, scraping, cache, and database services
- **WebSocket Integration** - Real-time communication testing
- **Error Handling** - Cross-service error propagation and recovery
- **Performance** - Long-running operations and resource usage
- **Database Transactions** - Transaction integrity and rollback scenarios

## Test Structure

### Test Classes

1. **TestCompleteAnalysisWorkflows**
   - `test_complete_analysis_workflow_success` - Full analysis pipeline
   - `test_headline_analysis_workflow_success` - Headlines-only analysis
   - `test_analysis_workflow_with_no_articles` - Error handling for empty results

2. **TestAPIIntegrationWithRealisticDataFlows**
   - `test_articles_api_with_filtering_and_pagination` - Articles endpoint testing
   - `test_positions_api_with_session_filtering` - Positions endpoint testing
   - `test_market_summary_api_with_real_data` - Market summary with dependencies
   - `test_activity_logs_api_with_filtering` - Activity logs endpoint testing

3. **TestServiceIntegration**
   - `test_llm_service_integration_with_analysis_service` - LLM ↔ Analysis service
   - `test_cache_service_integration` - Redis cache integration
   - `test_database_service_integration` - Database relationships and constraints

4. **TestWebSocketIntegration**
   - `test_websocket_connection_and_subscription` - WebSocket connection lifecycle
   - `test_websocket_analysis_updates` - Real-time analysis updates
   - `test_websocket_error_handling` - WebSocket error scenarios
   - `test_websocket_concurrent_connections` - Multiple concurrent connections

5. **TestErrorHandlingIntegration**
   - `test_llm_service_error_propagation` - LLM service error handling
   - `test_database_error_handling` - Database constraint violations
   - `test_timeout_handling` - Operation timeout scenarios
   - `test_fallback_mechanisms` - Service fallback behavior

6. **TestPerformanceIntegration**
   - `test_concurrent_analysis_sessions` - Multiple concurrent analyses
   - `test_large_dataset_handling` - Large dataset processing
   - `test_memory_usage_monitoring` - Memory usage optimization

7. **TestDatabaseTransactionIntegration**
   - `test_transaction_rollback_on_error` - Transaction rollback scenarios
   - `test_concurrent_transaction_handling` - Concurrent database access
   - `test_foreign_key_constraint_handling` - Relationship integrity

## Running the Tests

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- All dependencies from `requirements.txt`

### Quick Start

```bash
# Run all integration tests
python tests/integration/run_integration_tests.py

# Run specific test class
python tests/integration/run_integration_tests.py -k TestCompleteAnalysisWorkflows

# Run specific test method
python tests/integration/run_integration_tests.py -k test_complete_analysis_workflow_success

# Run with coverage
python tests/integration/run_integration_tests.py --coverage

# List all available tests
python tests/integration/run_integration_tests.py --list-tests
```

### Using Docker Compose

```bash
# Start test environment
docker-compose -f tests/integration/docker-compose.test.yml up -d

# Run tests in container
docker-compose -f tests/integration/docker-compose.test.yml run test-runner

# Clean up
docker-compose -f tests/integration/docker-compose.test.yml down -v
```

### Manual Setup

```bash
# Start test databases
docker run -d --name test_postgres_integration -p 5433:5432 \
  -e POSTGRES_DB=test_market_analysis \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_password \
  postgres:15-alpine

docker run -d --name test_redis_integration -p 6380:6379 \
  redis:7-alpine

# Run tests
cd backend
python -m pytest tests/integration/test_workflows.py -v
```

## Test Environment

### Docker Containers

The integration tests use isolated Docker containers:

- **PostgreSQL** (port 5433) - Test database
- **Redis** (port 6380) - Test cache
- **Test Runner** - Containerized test execution

### Environment Variables

```bash
DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_market_analysis
REDIS_URL=redis://localhost:6380
TESTING=true
```

### Test Data

Each test uses:
- Isolated database session with transaction rollback
- Mocked external services (LLM APIs, web scraping)
- Realistic test data generators
- Performance monitoring fixtures

## Coverage Analysis

### Running Coverage Analysis

```bash
# Generate coverage report
python tests/integration/test_coverage.py

# Quick coverage check
python tests/integration/test_coverage.py --quick
```

### Coverage Targets

- **Overall Coverage**: ≥80%
- **Critical Paths**: ≥80%
- **API Endpoints**: ≥90%
- **Service Layer**: ≥85%

### Coverage Reports

Generated reports include:
- HTML coverage report (`htmlcov/index.html`)
- JSON coverage data (`coverage.json`)
- Terminal coverage summary
- Critical path analysis

## Test Fixtures

### Database Fixtures

- `integration_db_session` - Isolated database session
- `test_engine` - Test database engine
- `postgres_container` - PostgreSQL Docker container

### Mock Fixtures

- `mock_external_services` - Mock web scraping and HTTP requests
- `mock_llm_services` - Mock OpenAI and Anthropic APIs
- `integration_test_data` - Comprehensive test data sets

### Performance Fixtures

- `performance_monitor` - Resource usage monitoring
- `websocket_test_client` - WebSocket connection management
- `database_isolation` - Test isolation verification

## Best Practices

### Test Design

1. **Isolation** - Each test runs in isolated environment
2. **Mocking** - External services are mocked consistently
3. **Cleanup** - Automatic cleanup of containers and data
4. **Monitoring** - Performance and resource usage tracking

### Error Testing

1. **Propagation** - Verify errors propagate correctly
2. **Fallbacks** - Test fallback mechanisms
3. **Recovery** - Test system recovery from errors
4. **Logging** - Verify error logging and context

### Performance Testing

1. **Concurrency** - Test concurrent operations
2. **Scalability** - Test with large datasets
3. **Memory** - Monitor memory usage
4. **Timeouts** - Test timeout handling

## Troubleshooting

### Common Issues

1. **Docker not available**
   ```bash
   # Install Docker and ensure it's running
   docker info
   ```

2. **Port conflicts**
   ```bash
   # Check for port usage
   netstat -tulpn | grep :5433
   netstat -tulpn | grep :6380
   ```

3. **Container cleanup**
   ```bash
   # Clean up test containers
   docker container stop test_postgres_integration test_redis_integration
   docker container rm test_postgres_integration test_redis_integration
   ```

4. **Test timeouts**
   ```bash
   # Increase timeout in conftest.py
   # Check Docker resource limits
   ```

### Debug Mode

```bash
# Run with verbose output
python tests/integration/run_integration_tests.py -v

# Run single test with debugging
python -m pytest tests/integration/test_workflows.py::TestCompleteAnalysisWorkflows::test_complete_analysis_workflow_success -v -s
```

### Logs and Debugging

- Test logs are available in the terminal output
- Docker container logs: `docker logs test_postgres_integration`
- Coverage reports provide detailed execution analysis
- Performance metrics are logged for each test

## Continuous Integration

### GitHub Actions

The integration tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration-tests:
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
      redis:
        image: redis:7-alpine
        ports:
          - 6380:6379
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest-cov docker psutil
      - name: Run integration tests
        run: |
          cd backend
          python -m pytest tests/integration/test_workflows.py --cov=app --cov-report=xml
```

### Local Development

```bash
# Run tests before committing
python tests/integration/run_integration_tests.py --coverage

# Verify coverage meets requirements
python tests/integration/test_coverage.py

# Run specific test categories during development
python tests/integration/run_integration_tests.py -k TestAPIIntegration
```

## Contributing

When adding new integration tests:

1. **Follow Naming** - Use descriptive test names
2. **Add Documentation** - Document test purpose and coverage
3. **Mock Externals** - Mock all external dependencies
4. **Test Cleanup** - Ensure proper cleanup in fixtures
5. **Performance** - Consider performance implications
6. **Coverage** - Maintain coverage targets

### Example Test Structure

```python
def test_new_feature_integration(self, integration_client, integration_db_session, mock_external_services):
    \"\"\"Test new feature integration with description\"\"\"
    
    # Arrange
    test_data = create_test_data()
    mock_external_services["llm"].configure_response(test_response)
    
    # Act
    response = integration_client.post("/api/v1/new-feature", json=test_data)
    
    # Assert
    assert response.status_code == 200
    verify_database_state(integration_db_session)
    verify_external_calls(mock_external_services)
```

## Related Documentation

- [Backend Testing Requirements](../../docs/backend-testing-requirements.md)
- [Testing Environment Setup](../../docs/testing-environment.md)
- [API Documentation](../../docs/api-documentation.md)
- [Service Architecture](../../docs/service-architecture.md)