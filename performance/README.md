# Performance Test Suite for Market News Analysis Agent

## Overview

This comprehensive performance test suite evaluates all aspects of the Market News Analysis Agent system under various load conditions. The suite includes API load testing, WebSocket scalability testing, database performance benchmarking, full system integration testing, and stress testing to identify breaking points.

## Test Architecture

```
performance/
├── api/                    # API load testing with Locust
├── websocket/             # WebSocket scalability tests
├── database/              # Database performance benchmarks
├── integration/           # Full system integration tests
├── stress/                # Stress testing and breaking point identification
├── reports/               # Performance monitoring and reporting
├── utils/                 # Shared utilities and test data generation
├── config.py              # Configuration and performance targets
├── requirements.txt       # Performance testing dependencies
└── run_all_tests.py       # Master test runner
```

## Performance Targets

The test suite validates the following performance targets:

- **API Response Time**: < 500ms for 95% of requests
- **Analysis Completion**: < 30 seconds for 10 articles
- **WebSocket Message Latency**: < 100ms
- **Database Queries**: < 200ms for complex queries
- **Concurrent Users**: Support 50+ simultaneous users
- **Memory Usage**: < 2GB under normal load

## Quick Start

### Prerequisites

1. **Backend Running**: Ensure the FastAPI backend is running on `http://localhost:8000`
2. **Database Accessible**: PostgreSQL and Redis should be accessible
3. **Dependencies**: Install performance testing dependencies

```bash
cd performance/
pip install -r requirements.txt
```

### Running All Tests

```bash
# Run comprehensive performance test suite
python run_all_tests.py --level comprehensive

# Run specific test type only
python run_all_tests.py --test-type api

# Run with different levels
python run_all_tests.py --level basic     # Quick validation
python run_all_tests.py --level standard  # Standard testing
python run_all_tests.py --level full      # Full comprehensive testing
```

### Running Individual Test Modules

```bash
# API Performance Tests
python -m api.endpoint_tests
python -m api.run_load_tests --scenario medium

# WebSocket Performance Tests
python -m websocket.websocket_tests

# Database Performance Tests
python -m database.db_performance_tests

# Integration Tests
python -m integration.full_system_tests

# Stress Tests
python -m stress.stress_tests

# Generate Performance Report
python -m reports.dashboard
```

## Test Modules

### 1. API Load Testing (`api/`)

**Locust-based Load Testing**
- Multiple user simulation patterns
- Progressive load testing
- Endpoint-specific performance validation
- Concurrent request handling

**Key Files:**
- `locustfile.py` - Locust test definitions with realistic user behavior
- `endpoint_tests.py` - Individual endpoint performance testing
- `run_load_tests.py` - Test runner with multiple scenarios

**Test Scenarios:**
- Light Load: 10 users, 60 seconds
- Medium Load: 25 users, 180 seconds  
- Heavy Load: 50 users, 300 seconds
- Stress Test: 100 users, 600 seconds

### 2. WebSocket Scalability (`websocket/`)

**Connection and Message Performance**
- Connection scalability testing (up to 100+ connections)
- Message throughput and latency measurement
- Concurrent analysis session subscriptions
- Connection flood testing

**Key Metrics:**
- Connection establishment time
- Message round-trip latency
- Maximum concurrent connections
- Message throughput (messages/second)

### 3. Database Performance (`database/`)

**Query Performance Benchmarking**
- PostgreSQL query performance testing
- Redis operation benchmarking
- Concurrent connection testing
- Connection pool optimization validation

**Test Categories:**
- Simple SELECT queries
- Complex JOIN operations
- Filtered queries with indexes
- Redis cache operations
- Connection pool stress testing

### 4. Integration Testing (`integration/`)

**Full System Workflow Testing**
- End-to-end analysis workflow performance
- Concurrent user simulation
- Real-time WebSocket message flow
- System scalability validation

**Workflow Testing:**
1. WebSocket connection establishment
2. Analysis request via API
3. Real-time progress monitoring
4. Completion verification
5. Resource cleanup

### 5. Stress Testing (`stress/`)

**Breaking Point Identification**
- Progressive user load until failure
- Connection flood testing
- Memory exhaustion testing
- System recovery validation

**Breaking Point Categories:**
- User load limits
- Connection limits
- Memory pressure points
- CPU exhaustion thresholds

## Performance Monitoring

### Real-time Metrics Collection

The test suite collects comprehensive metrics during execution:

- **Response Times**: Mean, median, P95, P99 percentiles
- **Throughput**: Requests/second, messages/second
- **Error Rates**: HTTP errors, connection failures
- **System Resources**: CPU usage, memory consumption
- **Connection Stats**: Active connections, connection times

### Automated Reporting

Performance reports are automatically generated with:

- **Executive Summary**: High-level performance overview
- **Detailed Metrics**: Per-component performance analysis
- **Trend Analysis**: Performance over time
- **Target Validation**: Comparison against performance targets
- **Optimization Recommendations**: Actionable improvement suggestions

## Configuration

### Performance Targets (`config.py`)

```python
class PerformanceTargets:
    api_response_time_95th: float = 500.0  # ms
    api_response_time_99th: float = 1000.0  # ms
    api_requests_per_second: float = 100.0
    websocket_messages_per_second: float = 1000.0
    max_concurrent_users: int = 50
    max_websocket_connections: int = 100
    db_query_time_95th: float = 200.0  # ms
    max_memory_usage_mb: float = 2048.0
    analysis_time_10_articles: float = 30.0  # seconds
```

### Test Scenarios (`config.py`)

Predefined test scenarios with different load characteristics:

- **Light Load**: Basic functionality validation
- **Medium Load**: Typical production load simulation
- **Heavy Load**: Peak usage simulation
- **Stress Test**: System limit identification

## Results and Reporting

### Output Files

Performance tests generate various output files:

```
reports/
├── performance_report_YYYYMMDD_HHMMSS.html    # Comprehensive HTML report
├── locust_report_YYYYMMDD_HHMMSS.html         # Locust load test report
├── endpoint_test_YYYYMMDD_HHMMSS.json         # API endpoint results
├── websocket_performance_YYYYMMDD_HHMMSS.json # WebSocket test results
├── database_performance_YYYYMMDD_HHMMSS.json  # Database benchmark results
├── full_system_performance_YYYYMMDD_HHMMSS.json # Integration test results
├── stress_test_results_YYYYMMDD_HHMMSS.json   # Stress test results
└── charts/                                     # Performance visualization charts
    ├── response_time_trend.png
    ├── resource_usage.png
    └── throughput_comparison.png
```

### HTML Dashboard

The comprehensive HTML report includes:

- **Executive Summary**: Key performance indicators
- **Component Analysis**: Detailed breakdown by system component
- **Trend Visualization**: Performance charts and graphs
- **Target Validation**: Performance target achievement status
- **Recommendations**: Specific optimization suggestions

## Optimization Recommendations

Based on test results, the suite provides specific optimization recommendations:

### API Performance
- Implement response caching for frequently accessed endpoints
- Optimize database queries with proper indexing
- Add request rate limiting per user
- Implement connection pooling

### Database Optimization
- Add indexes on ticker and timestamp columns
- Optimize query execution plans
- Implement query result caching
- Configure connection pool sizing

### WebSocket Scalability
- Implement connection rate limiting
- Optimize message broadcasting
- Add proper connection cleanup
- Consider WebSocket proxy/load balancer

### System Scalability
- Implement horizontal scaling with load balancer
- Optimize memory usage in analysis service
- Add circuit breakers for external services
- Implement async processing for heavy operations

## Troubleshooting

### Common Issues

**Backend Connection Failures**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if needed
cd backend/
uvicorn app.main:app --reload
```

**Database Connection Issues**
```bash
# Check PostgreSQL connection
psql -h localhost -U postgres -d market_analysis_test

# Check Redis connection
redis-cli ping
```

**Missing Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt

# Install specific packages
pip install locust httpx websockets asyncpg aioredis matplotlib seaborn
```

### Performance Test Debugging

**Enable Verbose Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Reduce Test Scale for Debugging**
```python
# In config.py, reduce test parameters
MAX_USERS = 5
TEST_DURATION = 30
```

**Check System Resources**
```bash
# Monitor system resources during tests
htop
iostat 1
```

## Contributing

### Adding New Performance Tests

1. **Create Test Module**: Add new test file in appropriate directory
2. **Follow Patterns**: Use existing test patterns and utilities
3. **Update Configuration**: Add new test parameters to `config.py`
4. **Integrate with Runner**: Add test to `run_all_tests.py`
5. **Document Results**: Ensure proper metrics collection and reporting

### Test Data Generation

Use the provided test data generator:

```python
from utils.test_data import test_data_generator

# Generate test articles
articles = test_data_generator.generate_articles(count=100)

# Generate analysis requests
request = test_data_generator.generate_analysis_request()

# Generate WebSocket messages
message = test_data_generator.generate_websocket_message()
```

### Performance Metrics

Collect performance metrics using the metrics utility:

```python
from utils.metrics import performance_collector

# Record response time
performance_collector.record_response_time(
    url="/api/endpoint",
    method="GET", 
    response_time=245.5,
    status_code=200
)

# Record custom metric
performance_collector.record_custom_metric(
    name="analysis_completion_time",
    value=28.3,
    unit="seconds"
)
```

## License

This performance test suite is part of the Market News Analysis Agent project and follows the same licensing terms.

## Support

For questions or issues with the performance test suite:

1. Check the troubleshooting section above
2. Review test logs and error messages
3. Ensure all prerequisites are met
4. Contact the development team with specific error details

---

**Note**: Performance testing can be resource-intensive. Run comprehensive tests during off-peak hours and monitor system resources to avoid impacting other services.