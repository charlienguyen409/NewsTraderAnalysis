# Performance Testing Guide

## Executive Summary

This guide provides comprehensive instructions for performance testing the Market News Analysis Agent. The performance test suite evaluates system behavior under various load conditions, identifies bottlenecks, and provides optimization recommendations.

## Testing Strategy

### Test Pyramid Approach

```
     ┌─────────────────┐
     │   Stress Tests  │  ← System Breaking Points
     └─────────────────┘
    ┌───────────────────┐
    │ Integration Tests │   ← End-to-End Workflows  
    └───────────────────┘
   ┌─────────────────────┐
   │  Component Tests    │    ← API, WebSocket, Database
   └─────────────────────┘
  ┌───────────────────────┐
  │   Unit Performance    │     ← Individual Functions
  └───────────────────────┘
```

### Performance Testing Levels

1. **Unit Performance**: Individual function and method performance
2. **Component Tests**: API endpoints, WebSocket connections, database queries
3. **Integration Tests**: Complete workflow performance under load
4. **Stress Tests**: System limits and breaking point identification

## Performance Targets and SLAs

### Response Time Targets

| Component | Metric | Target | Threshold |
|-----------|--------|--------|-----------|
| API Endpoints | P95 Response Time | < 500ms | < 1000ms |
| API Endpoints | P99 Response Time | < 1000ms | < 2000ms |
| WebSocket | Connection Time | < 100ms | < 500ms |
| WebSocket | Message Latency | < 100ms | < 300ms |
| Database | Query Time P95 | < 200ms | < 500ms |
| Analysis | 10 Articles | < 30s | < 60s |

### Throughput Targets

| Component | Metric | Target | Minimum |
|-----------|--------|--------|---------|
| API | Requests/Second | 100+ | 50+ |
| WebSocket | Messages/Second | 1000+ | 500+ |
| Database | Queries/Second | 300+ | 150+ |
| System | Concurrent Users | 50+ | 25+ |

### Resource Utilization Targets

| Resource | Normal Load | Peak Load | Critical |
|----------|-------------|-----------|----------|
| CPU Usage | < 60% | < 80% | < 95% |
| Memory Usage | < 1GB | < 2GB | < 4GB |
| Disk I/O | < 50MB/s | < 100MB/s | < 200MB/s |
| Network | < 10MB/s | < 50MB/s | < 100MB/s |

## Test Execution Procedures

### Pre-Test Checklist

- [ ] Backend services are running and healthy
- [ ] Database connections are accessible
- [ ] Test environment is isolated from production
- [ ] System resources are monitored
- [ ] Test data is prepared
- [ ] Baseline metrics are collected

### Test Execution Steps

#### 1. Environment Preparation

```bash
# Start backend services
cd backend/
uvicorn app.main:app --reload --port 8000

# Verify health
curl http://localhost:8000/health

# Check database connectivity
psql -h localhost -U postgres -d market_analysis_test -c "SELECT 1;"
redis-cli ping
```

#### 2. Baseline Performance Collection

```bash
# Collect baseline metrics
python -m performance.utils.metrics --baseline

# Run minimal load test
python run_all_tests.py --level basic --test-type api
```

#### 3. Progressive Load Testing

```bash
# Light load validation
python run_all_tests.py --level basic

# Standard production simulation
python run_all_tests.py --level standard

# Comprehensive testing
python run_all_tests.py --level comprehensive

# Full stress testing
python run_all_tests.py --level full
```

#### 4. Component-Specific Testing

```bash
# API performance testing
python -m api.endpoint_tests
python -m api.run_load_tests --scenario heavy

# WebSocket scalability testing
python -m websocket.websocket_tests

# Database benchmarking
python -m database.db_performance_tests

# Integration workflow testing
python -m integration.full_system_tests

# Stress and breaking point testing
python -m stress.stress_tests
```

### Test Monitoring

#### Real-Time Monitoring

Monitor these metrics during test execution:

```bash
# System resources
htop
iostat 1
vmstat 1

# Network activity
netstat -i
ss -tuln

# Application logs
tail -f backend/logs/application.log

# Database performance
# PostgreSQL
SELECT * FROM pg_stat_activity;
SELECT * FROM pg_stat_database;

# Redis
redis-cli info
redis-cli monitor
```

#### Performance Metrics Dashboard

Access real-time metrics through:

- **Application Metrics**: `http://localhost:8000/metrics` (if implemented)
- **System Metrics**: System monitoring tools (htop, iostat)
- **Database Metrics**: Database monitoring queries
- **Test Metrics**: Performance test suite output

## Test Scenarios and Use Cases

### Scenario 1: Normal Production Load

**Objective**: Validate system performance under typical production conditions

**Load Pattern**:
- 25 concurrent users
- 2-3 requests per user per minute
- Mixed API endpoints (70% reads, 30% writes)
- 5-10 concurrent WebSocket connections
- Test duration: 10 minutes

**Expected Results**:
- API P95 response time < 300ms
- Error rate < 1%
- CPU usage < 50%
- Memory usage < 1GB

**Test Command**:
```bash
python run_all_tests.py --level standard
```

### Scenario 2: Peak Load Simulation

**Objective**: Test system behavior during peak usage periods

**Load Pattern**:
- 50 concurrent users
- 5-8 requests per user per minute
- Heavy analysis requests (multiple tickers)
- 20-30 concurrent WebSocket connections
- Test duration: 15 minutes

**Expected Results**:
- API P95 response time < 500ms
- Error rate < 5%
- CPU usage < 80%
- Memory usage < 2GB

**Test Command**:
```bash
python run_all_tests.py --level comprehensive
```

### Scenario 3: Stress Testing

**Objective**: Identify system breaking points and failure modes

**Load Pattern**:
- Progressive load from 10 to 100+ users
- Aggressive request rates
- Large payload testing
- Connection flood testing
- Extended duration testing

**Expected Outcomes**:
- Identify maximum user capacity
- Determine failure modes
- Measure recovery time
- Validate error handling

**Test Command**:
```bash
python run_all_tests.py --level full --test-type stress
```

### Scenario 4: Endurance Testing

**Objective**: Test system stability over extended periods

**Load Pattern**:
- Moderate constant load (30 users)
- Continuous operation for 2+ hours
- Memory leak detection
- Resource cleanup validation

**Test Command**:
```bash
python -m integration.full_system_tests --duration 7200  # 2 hours
```

## Performance Analysis and Interpretation

### Key Performance Indicators (KPIs)

#### Response Time Analysis

```
Response Time Distribution:
├── P50 (Median): Should be < 200ms
├── P95: Should be < 500ms  
├── P99: Should be < 1000ms
└── Max: Outliers should be investigated
```

#### Throughput Analysis

- **Requests per Second (RPS)**: Measure of system capacity
- **Messages per Second**: WebSocket performance indicator
- **Queries per Second (QPS)**: Database performance metric
- **Workflows per Minute**: End-to-end system throughput

#### Error Rate Analysis

```
Error Rate Categories:
├── < 1%: Excellent
├── 1-5%: Acceptable  
├── 5-15%: Warning
└── > 15%: Critical
```

#### Resource Utilization Analysis

- **CPU Usage**: Should remain < 80% under peak load
- **Memory Usage**: Monitor for memory leaks and excessive consumption
- **I/O Usage**: Check for disk and network bottlenecks
- **Connection Usage**: Monitor database and WebSocket connections

### Performance Bottleneck Identification

#### Common Bottleneck Patterns

1. **Database Bottlenecks**
   - Symptoms: High query response times, connection pool exhaustion
   - Investigation: Analyze slow query logs, check indexes
   - Solutions: Query optimization, index creation, connection pool tuning

2. **Memory Bottlenecks**
   - Symptoms: High memory usage, garbage collection pauses
   - Investigation: Memory profiling, heap analysis
   - Solutions: Memory optimization, garbage collection tuning

3. **CPU Bottlenecks**
   - Symptoms: High CPU usage, request queuing
   - Investigation: CPU profiling, thread analysis
   - Solutions: Algorithm optimization, horizontal scaling

4. **Network Bottlenecks**
   - Symptoms: High network latency, connection timeouts
   - Investigation: Network monitoring, bandwidth analysis
   - Solutions: Network optimization, CDN implementation

### Performance Trend Analysis

#### Regression Detection

Monitor these trends over time:
- Response time degradation
- Throughput reduction
- Error rate increases
- Resource usage growth

#### Performance Baselines

Establish baselines for:
- Clean system startup performance
- Typical production load performance
- Peak load performance
- Recovery performance after failures

## Optimization Recommendations

### API Performance Optimization

#### Response Time Optimization

1. **Caching Implementation**
   ```python
   # Implement Redis caching for frequent queries
   @cache(expire=300)  # 5-minute cache
   def get_market_summary():
       # Expensive operation
       pass
   ```

2. **Database Query Optimization**
   ```sql
   -- Add indexes for common query patterns
   CREATE INDEX idx_articles_ticker_time ON articles(ticker, scraped_at);
   CREATE INDEX idx_analyses_sentiment ON analyses(sentiment_score);
   ```

3. **Async Processing**
   ```python
   # Implement background task processing
   @background_task
   async def process_analysis_request(request_data):
       # Heavy processing in background
       pass
   ```

#### Throughput Optimization

1. **Connection Pooling**
   ```python
   # Optimize database connection pool
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

2. **Request Rate Limiting**
   ```python
   # Implement rate limiting per user
   @rate_limit("100/minute")
   async def api_endpoint():
       pass
   ```

### WebSocket Performance Optimization

1. **Connection Management**
   ```python
   # Implement proper connection cleanup
   class WebSocketManager:
       def __init__(self):
           self.connections = {}
           self.cleanup_interval = 300  # 5 minutes
   ```

2. **Message Broadcasting Optimization**
   ```python
   # Batch message broadcasting
   async def broadcast_to_subscribers(message, subscriber_ids):
       tasks = []
       for subscriber_id in subscriber_ids:
           task = asyncio.create_task(send_message(subscriber_id, message))
           tasks.append(task)
       await asyncio.gather(*tasks)
   ```

### Database Performance Optimization

#### PostgreSQL Optimization

1. **Index Optimization**
   ```sql
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM articles WHERE ticker = 'AAPL';
   
   -- Create covering indexes
   CREATE INDEX idx_articles_covering ON articles(ticker, scraped_at) 
   INCLUDE (title, content);
   ```

2. **Connection Pool Tuning**
   ```python
   # Optimal pool configuration
   SQLALCHEMY_ENGINE_OPTIONS = {
       "pool_size": 20,
       "max_overflow": 30,
       "pool_timeout": 30,
       "pool_recycle": 3600,
       "pool_pre_ping": True
   }
   ```

#### Redis Optimization

1. **Memory Optimization**
   ```python
   # Use appropriate data structures
   # Lists for queues
   redis.lpush("analysis_queue", json.dumps(task))
   
   # Hashes for objects
   redis.hset("user:123", {"name": "John", "email": "john@example.com"})
   
   # Sets for unique collections
   redis.sadd("active_sessions", session_id)
   ```

2. **Expiration Policies**
   ```python
   # Set appropriate TTL for cached data
   redis.setex("market_summary", 300, json.dumps(summary))  # 5 minutes
   redis.setex("user_session", 3600, session_data)  # 1 hour
   ```

### System Architecture Optimization

#### Horizontal Scaling

1. **Load Balancer Configuration**
   ```nginx
   upstream backend {
       server localhost:8000;
       server localhost:8001;
       server localhost:8002;
   }
   
   server {
       location / {
           proxy_pass http://backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Database Read Replicas**
   ```python
   # Separate read and write operations
   class DatabaseManager:
       def __init__(self):
           self.write_engine = create_engine(PRIMARY_DB_URL)
           self.read_engine = create_engine(REPLICA_DB_URL)
   ```

#### Monitoring and Alerting

1. **Performance Monitoring**
   ```python
   # Implement custom metrics
   @monitor_performance
   async def api_endpoint():
       with Timer() as timer:
           result = await process_request()
       
       metrics.record("api.response_time", timer.elapsed)
       return result
   ```

2. **Health Checks**
   ```python
   @app.get("/health")
   async def health_check():
       checks = {
           "database": await check_database_health(),
           "redis": await check_redis_health(),
           "external_apis": await check_external_apis()
       }
       
       if all(checks.values()):
           return {"status": "healthy", "checks": checks}
       else:
           raise HTTPException(500, {"status": "unhealthy", "checks": checks})
   ```

## Continuous Performance Testing

### CI/CD Integration

#### Automated Performance Tests

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r performance/requirements.txt
    
    - name: Start services
      run: |
        docker-compose up -d
        
    - name: Run performance tests
      run: |
        cd performance/
        python run_all_tests.py --level standard
    
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: performance-results
        path: performance/reports/
```

#### Performance Regression Detection

```python
# performance/regression_detector.py
class PerformanceRegressionDetector:
    def __init__(self):
        self.baseline_metrics = self.load_baseline()
    
    def detect_regressions(self, current_metrics):
        regressions = []
        
        for metric_name, current_value in current_metrics.items():
            baseline_value = self.baseline_metrics.get(metric_name)
            
            if baseline_value:
                regression_threshold = baseline_value * 1.2  # 20% regression
                
                if current_value > regression_threshold:
                    regressions.append({
                        "metric": metric_name,
                        "baseline": baseline_value,
                        "current": current_value,
                        "regression": (current_value - baseline_value) / baseline_value
                    })
        
        return regressions
```

### Performance Monitoring in Production

#### Key Metrics to Monitor

1. **Application Metrics**
   - Response times (P50, P95, P99)
   - Request throughput
   - Error rates
   - Active connections

2. **System Metrics**
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network traffic

3. **Business Metrics**
   - Analysis completion times
   - User session durations
   - Feature usage patterns

#### Alerting Thresholds

```python
ALERT_THRESHOLDS = {
    "api_response_time_p95": 1000,  # ms
    "error_rate": 5,  # percentage
    "cpu_usage": 85,  # percentage
    "memory_usage": 90,  # percentage
    "disk_usage": 85,  # percentage
    "active_connections": 80,  # percentage of pool
}
```

## Troubleshooting Performance Issues

### Common Performance Problems

#### Slow API Responses

**Symptoms**:
- High response times (> 1 second)
- Increasing response time over time
- User complaints about slow interface

**Investigation Steps**:
1. Check application logs for errors
2. Monitor database query performance
3. Analyze network latency
4. Review caching effectiveness

**Common Causes**:
- Slow database queries
- Missing database indexes
- Network latency
- Inefficient algorithms
- Memory pressure

**Solutions**:
- Optimize database queries
- Add appropriate indexes
- Implement caching
- Code optimization
- Memory management improvements

#### High Error Rates

**Symptoms**:
- HTTP 5xx errors
- Connection timeouts
- Service unavailable errors

**Investigation Steps**:
1. Review error logs
2. Check service health
3. Monitor resource usage
4. Analyze traffic patterns

**Common Causes**:
- Service overload
- Database connection exhaustion
- Memory leaks
- External service failures

**Solutions**:
- Implement rate limiting
- Increase connection pools
- Fix memory leaks
- Add circuit breakers

#### Memory Issues

**Symptoms**:
- High memory usage
- Out of memory errors
- Garbage collection pauses

**Investigation Steps**:
1. Memory profiling
2. Heap dump analysis
3. Monitor memory growth
4. Check for memory leaks

**Common Causes**:
- Memory leaks in code
- Large object retention
- Inefficient data structures
- Missing memory cleanup

**Solutions**:
- Fix memory leaks
- Optimize data structures
- Implement proper cleanup
- Tune garbage collection

### Performance Testing Best Practices

#### Test Environment Management

1. **Isolated Test Environment**
   - Separate from production
   - Consistent configuration
   - Clean state for each test

2. **Realistic Test Data**
   - Production-like data volumes
   - Representative data patterns
   - Proper data distribution

3. **Baseline Establishment**
   - Regular baseline collection
   - Version-controlled baselines
   - Trend analysis

#### Test Execution Best Practices

1. **Gradual Load Increase**
   - Start with light load
   - Progressive load increase
   - Monitor system behavior

2. **Sufficient Test Duration**
   - Allow system warm-up
   - Capture steady-state behavior
   - Identify memory leaks

3. **Comprehensive Monitoring**
   - Application metrics
   - System metrics
   - Business metrics

#### Results Analysis Best Practices

1. **Statistical Significance**
   - Multiple test runs
   - Statistical analysis
   - Confidence intervals

2. **Correlation Analysis**
   - Resource usage correlation
   - Performance pattern analysis
   - Root cause identification

3. **Actionable Insights**
   - Specific recommendations
   - Priority ranking
   - Implementation guidance

---

This performance testing guide provides a comprehensive framework for validating and optimizing the Market News Analysis Agent's performance. Regular performance testing and monitoring ensure the system meets user expectations and scales effectively with growing demand.