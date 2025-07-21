"""
Database performance benchmarks and query testing
"""
import asyncio
import time
import statistics
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import asyncpg
import aioredis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator


@dataclass
class QueryPerformanceResult:
    """Result of a database query performance test"""
    query_name: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    total_operations: int
    successful_operations: int
    failed_operations: int
    execution_times: List[float]
    average_time: float
    median_time: float
    p95_time: float
    p99_time: float
    min_time: float
    max_time: float
    operations_per_second: float
    error_rate: float
    errors: List[str]
    test_duration: float


@dataclass
class DatabasePerformanceResult:
    """Overall database performance test result"""
    test_name: str
    postgres_results: List[QueryPerformanceResult]
    redis_results: List[QueryPerformanceResult]
    connection_pool_stats: Dict[str, Any]
    concurrent_connection_test: Dict[str, Any]
    test_duration: float


class DatabasePerformanceTester:
    """Test database performance with various query patterns and loads"""
    
    def __init__(self):
        self.postgres_url = config.TEST_DATABASE_URL
        self.redis_url = config.TEST_REDIS_URL
        self.engine = None
        self.Session = None
        self.redis_pool = None
        
    async def __aenter__(self):
        # Setup PostgreSQL connection pool
        self.engine = create_engine(
            self.postgres_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # Setup Redis connection pool
        self.redis_pool = aioredis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.engine:
            self.engine.dispose()
        if self.redis_pool:
            await self.redis_pool.disconnect()
    
    async def test_postgres_query_performance(self, query: str, query_name: str,
                                            query_type: str = "SELECT",
                                            num_operations: int = 100,
                                            concurrent_operations: int = 5,
                                            parameters: List[Dict] = None) -> QueryPerformanceResult:
        """Test PostgreSQL query performance"""
        
        print(f"Testing PostgreSQL query: {query_name} ({num_operations} operations, {concurrent_operations} concurrent)")
        
        execution_times = []
        errors = []
        successful_operations = 0
        failed_operations = 0
        
        start_time = time.time()
        
        # Create connection pool for concurrent testing
        pool = await asyncpg.create_pool(
            self.postgres_url,
            min_size=concurrent_operations,
            max_size=concurrent_operations * 2,
            command_timeout=30
        )
        
        try:
            # Create batches of concurrent operations
            batch_size = concurrent_operations
            num_batches = (num_operations + batch_size - 1) // batch_size
            
            for batch_num in range(num_batches):
                batch_start = batch_num * batch_size
                batch_end = min((batch_num + 1) * batch_size, num_operations)
                batch_operations = batch_end - batch_start
                
                # Create tasks for this batch
                tasks = []
                for i in range(batch_operations):
                    operation_index = batch_start + i
                    params = parameters[operation_index] if parameters and operation_index < len(parameters) else None
                    
                    task = asyncio.create_task(
                        self._execute_postgres_query(pool, query, params)
                    )
                    tasks.append(task)
                
                # Wait for all tasks in this batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        failed_operations += 1
                        errors.append(str(result))
                    else:
                        execution_time, success = result
                        execution_times.append(execution_time)
                        
                        if success:
                            successful_operations += 1
                        else:
                            failed_operations += 1
                
                # Small delay between batches
                if batch_num < num_batches - 1:
                    await asyncio.sleep(0.01)
        
        finally:
            await pool.close()
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate statistics
        if execution_times:
            average_time = statistics.mean(execution_times)
            median_time = statistics.median(execution_times)
            p95_time = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times)
            p99_time = statistics.quantiles(execution_times, n=100)[98] if len(execution_times) >= 100 else max(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
        else:
            average_time = median_time = p95_time = p99_time = min_time = max_time = 0
        
        operations_per_second = num_operations / test_duration if test_duration > 0 else 0
        error_rate = (failed_operations / num_operations * 100) if num_operations > 0 else 0
        
        return QueryPerformanceResult(
            query_name=query_name,
            query_type=query_type,
            total_operations=num_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            execution_times=execution_times,
            average_time=average_time,
            median_time=median_time,
            p95_time=p95_time,
            p99_time=p99_time,
            min_time=min_time,
            max_time=max_time,
            operations_per_second=operations_per_second,
            error_rate=error_rate,
            errors=errors[:10],  # Keep only first 10 errors
            test_duration=test_duration
        )
    
    async def _execute_postgres_query(self, pool: asyncpg.Pool, query: str, 
                                     parameters: Dict = None) -> Tuple[float, bool]:
        """Execute a single PostgreSQL query and measure execution time"""
        
        start_time = time.time()
        
        try:
            async with pool.acquire() as connection:
                if parameters:
                    await connection.execute(query, *parameters.values())
                else:
                    await connection.execute(query)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            return execution_time, True
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            return execution_time, False
    
    async def test_redis_performance(self, operation_type: str, key_pattern: str = "test_key_{i}",
                                   num_operations: int = 1000, 
                                   concurrent_operations: int = 10,
                                   value_size: int = 1024) -> QueryPerformanceResult:
        """Test Redis performance for different operations"""
        
        print(f"Testing Redis {operation_type}: {num_operations} operations, {concurrent_operations} concurrent")
        
        execution_times = []
        errors = []
        successful_operations = 0
        failed_operations = 0
        
        start_time = time.time()
        
        # Create Redis connections
        redis_connections = []
        for _ in range(concurrent_operations):
            redis = aioredis.Redis(connection_pool=self.redis_pool)
            redis_connections.append(redis)
        
        try:
            # Generate test data
            test_value = "x" * value_size
            
            # Create batches of concurrent operations
            batch_size = concurrent_operations
            num_batches = (num_operations + batch_size - 1) // batch_size
            
            for batch_num in range(num_batches):
                batch_start = batch_num * batch_size
                batch_end = min((batch_num + 1) * batch_size, num_operations)
                batch_operations = batch_end - batch_start
                
                # Create tasks for this batch
                tasks = []
                for i in range(batch_operations):
                    operation_index = batch_start + i
                    redis_conn = redis_connections[i % len(redis_connections)]
                    key = key_pattern.format(i=operation_index)
                    
                    task = asyncio.create_task(
                        self._execute_redis_operation(redis_conn, operation_type, key, test_value)
                    )
                    tasks.append(task)
                
                # Wait for all tasks in this batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        failed_operations += 1
                        errors.append(str(result))
                    else:
                        execution_time, success = result
                        execution_times.append(execution_time)
                        
                        if success:
                            successful_operations += 1
                        else:
                            failed_operations += 1
                
                # Small delay between batches
                if batch_num < num_batches - 1:
                    await asyncio.sleep(0.001)
        
        finally:
            # Clean up Redis connections
            for redis_conn in redis_connections:
                await redis_conn.close()
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate statistics
        if execution_times:
            average_time = statistics.mean(execution_times)
            median_time = statistics.median(execution_times)
            p95_time = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times)
            p99_time = statistics.quantiles(execution_times, n=100)[98] if len(execution_times) >= 100 else max(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
        else:
            average_time = median_time = p95_time = p99_time = min_time = max_time = 0
        
        operations_per_second = num_operations / test_duration if test_duration > 0 else 0
        error_rate = (failed_operations / num_operations * 100) if num_operations > 0 else 0
        
        return QueryPerformanceResult(
            query_name=f"Redis {operation_type}",
            query_type=operation_type,
            total_operations=num_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            execution_times=execution_times,
            average_time=average_time,
            median_time=median_time,
            p95_time=p95_time,
            p99_time=p99_time,
            min_time=min_time,
            max_time=max_time,
            operations_per_second=operations_per_second,
            error_rate=error_rate,
            errors=errors[:10],
            test_duration=test_duration
        )
    
    async def _execute_redis_operation(self, redis_conn: aioredis.Redis, operation_type: str,
                                     key: str, value: str) -> Tuple[float, bool]:
        """Execute a single Redis operation and measure execution time"""
        
        start_time = time.time()
        
        try:
            if operation_type.upper() == "SET":
                await redis_conn.set(key, value)
            elif operation_type.upper() == "GET":
                await redis_conn.get(key)
            elif operation_type.upper() == "DEL":
                await redis_conn.delete(key)
            elif operation_type.upper() == "INCR":
                await redis_conn.incr(key)
            elif operation_type.upper() == "LPUSH":
                await redis_conn.lpush(key, value)
            elif operation_type.upper() == "RPOP":
                await redis_conn.rpop(key)
            else:
                raise ValueError(f"Unsupported Redis operation: {operation_type}")
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            return execution_time, True
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            return execution_time, False
    
    async def test_concurrent_connections(self, max_connections: int = 50) -> Dict[str, Any]:
        """Test database performance under concurrent connections"""
        
        print(f"Testing concurrent database connections: {max_connections} connections")
        
        start_time = time.time()
        
        # Test PostgreSQL concurrent connections
        postgres_connections = []
        postgres_successful = 0
        postgres_failed = 0
        postgres_connection_times = []
        
        for i in range(max_connections):
            conn_start = time.time()
            try:
                conn = await asyncpg.connect(self.postgres_url)
                postgres_connections.append(conn)
                postgres_successful += 1
                
                conn_end = time.time()
                postgres_connection_times.append((conn_end - conn_start) * 1000)
                
            except Exception as e:
                postgres_failed += 1
        
        # Test simple query on all connections
        postgres_query_times = []
        if postgres_connections:
            query_tasks = []
            for conn in postgres_connections:
                task = asyncio.create_task(self._test_simple_query(conn))
                query_tasks.append(task)
            
            query_results = await asyncio.gather(*query_tasks, return_exceptions=True)
            
            for result in query_results:
                if not isinstance(result, Exception):
                    postgres_query_times.append(result)
        
        # Close PostgreSQL connections
        for conn in postgres_connections:
            try:
                await conn.close()
            except:
                pass
        
        # Test Redis concurrent connections
        redis_connections = []
        redis_successful = 0
        redis_failed = 0
        redis_connection_times = []
        
        for i in range(max_connections):
            conn_start = time.time()
            try:
                redis_conn = aioredis.Redis(connection_pool=self.redis_pool)
                await redis_conn.ping()  # Test connection
                redis_connections.append(redis_conn)
                redis_successful += 1
                
                conn_end = time.time()
                redis_connection_times.append((conn_end - conn_start) * 1000)
                
            except Exception as e:
                redis_failed += 1
        
        # Test simple Redis operations on all connections
        redis_operation_times = []
        if redis_connections:
            operation_tasks = []
            for i, redis_conn in enumerate(redis_connections):
                task = asyncio.create_task(self._test_simple_redis_operation(redis_conn, f"test_{i}"))
                operation_tasks.append(task)
            
            operation_results = await asyncio.gather(*operation_tasks, return_exceptions=True)
            
            for result in operation_results:
                if not isinstance(result, Exception):
                    redis_operation_times.append(result)
        
        # Close Redis connections
        for redis_conn in redis_connections:
            try:
                await redis_conn.close()
            except:
                pass
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        return {
            "test_duration": test_duration,
            "max_connections_tested": max_connections,
            "postgres": {
                "successful_connections": postgres_successful,
                "failed_connections": postgres_failed,
                "connection_times": {
                    "mean": statistics.mean(postgres_connection_times) if postgres_connection_times else 0,
                    "max": max(postgres_connection_times) if postgres_connection_times else 0,
                    "min": min(postgres_connection_times) if postgres_connection_times else 0
                },
                "query_times": {
                    "mean": statistics.mean(postgres_query_times) if postgres_query_times else 0,
                    "max": max(postgres_query_times) if postgres_query_times else 0,
                    "min": min(postgres_query_times) if postgres_query_times else 0
                }
            },
            "redis": {
                "successful_connections": redis_successful,
                "failed_connections": redis_failed,
                "connection_times": {
                    "mean": statistics.mean(redis_connection_times) if redis_connection_times else 0,
                    "max": max(redis_connection_times) if redis_connection_times else 0,
                    "min": min(redis_connection_times) if redis_connection_times else 0
                },
                "operation_times": {
                    "mean": statistics.mean(redis_operation_times) if redis_operation_times else 0,
                    "max": max(redis_operation_times) if redis_operation_times else 0,
                    "min": min(redis_operation_times) if redis_operation_times else 0
                }
            }
        }
    
    async def _test_simple_query(self, conn: asyncpg.Connection) -> float:
        """Execute a simple query and return execution time"""
        start_time = time.time()
        await conn.execute("SELECT 1")
        end_time = time.time()
        return (end_time - start_time) * 1000
    
    async def _test_simple_redis_operation(self, redis_conn: aioredis.Redis, key: str) -> float:
        """Execute a simple Redis operation and return execution time"""
        start_time = time.time()
        await redis_conn.set(key, "test_value")
        await redis_conn.get(key)
        end_time = time.time()
        return (end_time - start_time) * 1000
    
    def print_query_result(self, result: QueryPerformanceResult):
        """Print detailed query performance results"""
        
        print(f"\n{'='*60}")
        print(f"QUERY PERFORMANCE RESULT: {result.query_name}")
        print(f"{'='*60}")
        
        print(f"Query Type: {result.query_type}")
        print(f"Total Operations: {result.total_operations}")
        print(f"Successful: {result.successful_operations}")
        print(f"Failed: {result.failed_operations}")
        print(f"Success Rate: {(result.successful_operations/result.total_operations*100):.1f}%")
        print(f"Test Duration: {result.test_duration:.2f} seconds")
        print(f"Operations per Second: {result.operations_per_second:.2f}")
        
        print(f"\nExecution Time Statistics:")
        print(f"  Mean: {result.average_time:.2f}ms")
        print(f"  Median: {result.median_time:.2f}ms")
        print(f"  95th Percentile: {result.p95_time:.2f}ms")
        print(f"  99th Percentile: {result.p99_time:.2f}ms")
        print(f"  Min: {result.min_time:.2f}ms")
        print(f"  Max: {result.max_time:.2f}ms")
        
        print(f"\nError Rate: {result.error_rate:.2f}%")
        
        if result.errors:
            print(f"\nSample Errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        # Target analysis
        print(f"\n{'='*60}")
        print("TARGET ANALYSIS")
        print(f"{'='*60}")
        
        if result.p95_time <= targets.db_query_time_95th:
            print(f"✅ 95th percentile query time: {result.p95_time:.2f}ms (target: {targets.db_query_time_95th}ms)")
        else:
            print(f"❌ 95th percentile query time: {result.p95_time:.2f}ms (target: {targets.db_query_time_95th}ms)")
        
        if result.error_rate <= 1.0:  # 1% error rate threshold
            print(f"✅ Error rate: {result.error_rate:.2f}% (threshold: 1%)")
        else:
            print(f"❌ Error rate: {result.error_rate:.2f}% (threshold: 1%)")


async def run_database_performance_tests():
    """Run comprehensive database performance tests"""
    
    print("🚀 Starting comprehensive database performance testing...")
    
    async with DatabasePerformanceTester() as tester:
        postgres_results = []
        redis_results = []
        
        # PostgreSQL Query Tests
        print(f"\n{'='*80}")
        print("POSTGRESQL PERFORMANCE TESTS")
        print(f"{'='*80}")
        
        # Basic SELECT queries
        select_queries = [
            ("SELECT 1", "Simple SELECT", "SELECT", 1000, 10),
            ("SELECT COUNT(*) FROM articles", "Count Articles", "SELECT", 100, 5),
            ("SELECT * FROM articles LIMIT 10", "Select Articles Limit", "SELECT", 200, 8),
            ("SELECT * FROM articles WHERE ticker = 'AAPL' ORDER BY scraped_at DESC LIMIT 20", "Ticker Filter", "SELECT", 150, 6),
            ("SELECT COUNT(*) FROM analyses WHERE sentiment_score > 0.5", "Sentiment Filter", "SELECT", 100, 5),
            ("SELECT a.*, ar.title FROM analyses a JOIN articles ar ON a.article_id = ar.id LIMIT 50", "Join Query", "SELECT", 50, 3),
        ]
        
        for query, name, query_type, num_ops, concurrent in select_queries:
            try:
                result = await tester.test_postgres_query_performance(
                    query, name, query_type, num_ops, concurrent
                )
                postgres_results.append(result)
                tester.print_query_result(result)
                
                await asyncio.sleep(2)  # Brief pause between tests
                
            except Exception as e:
                print(f"❌ Failed to test {name}: {str(e)}")
        
        # Redis Performance Tests
        print(f"\n{'='*80}")
        print("REDIS PERFORMANCE TESTS")
        print(f"{'='*80}")
        
        redis_operations = [
            ("SET", "Redis SET Operations", 2000, 20, 1024),
            ("GET", "Redis GET Operations", 2000, 20, 1024),
            ("INCR", "Redis INCR Operations", 1000, 15, 0),
            ("LPUSH", "Redis LPUSH Operations", 1000, 15, 512),
            ("RPOP", "Redis RPOP Operations", 1000, 15, 0),
        ]
        
        for operation, name, num_ops, concurrent, value_size in redis_operations:
            try:
                result = await tester.test_redis_performance(
                    operation, "perf_test_key_{i}", num_ops, concurrent, value_size
                )
                redis_results.append(result)
                tester.print_query_result(result)
                
                await asyncio.sleep(2)  # Brief pause between tests
                
            except Exception as e:
                print(f"❌ Failed to test {name}: {str(e)}")
        
        # Concurrent Connection Test
        print(f"\n{'='*80}")
        print("CONCURRENT CONNECTION TESTS")
        print(f"{'='*80}")
        
        concurrent_test_results = await tester.test_concurrent_connections(max_connections=50)
        
        print(f"Concurrent Connection Test Results:")
        print(f"  PostgreSQL: {concurrent_test_results['postgres']['successful_connections']}/50 successful connections")
        print(f"  Redis: {concurrent_test_results['redis']['successful_connections']}/50 successful connections")
        print(f"  Test Duration: {concurrent_test_results['test_duration']:.2f} seconds")
        
        # Export results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"database_performance_results_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {
            "test_timestamp": timestamp,
            "postgres_results": [],
            "redis_results": [],
            "concurrent_connection_test": concurrent_test_results
        }
        
        for result in postgres_results:
            json_results["postgres_results"].append({
                "query_name": result.query_name,
                "query_type": result.query_type,
                "total_operations": result.total_operations,
                "successful_operations": result.successful_operations,
                "failed_operations": result.failed_operations,
                "average_time": result.average_time,
                "median_time": result.median_time,
                "p95_time": result.p95_time,
                "p99_time": result.p99_time,
                "min_time": result.min_time,
                "max_time": result.max_time,
                "operations_per_second": result.operations_per_second,
                "error_rate": result.error_rate,
                "test_duration": result.test_duration,
                "errors_sample": result.errors
            })
        
        for result in redis_results:
            json_results["redis_results"].append({
                "query_name": result.query_name,
                "query_type": result.query_type,
                "total_operations": result.total_operations,
                "successful_operations": result.successful_operations,
                "failed_operations": result.failed_operations,
                "average_time": result.average_time,
                "median_time": result.median_time,
                "p95_time": result.p95_time,
                "p99_time": result.p99_time,
                "min_time": result.min_time,
                "max_time": result.max_time,
                "operations_per_second": result.operations_per_second,
                "error_rate": result.error_rate,
                "test_duration": result.test_duration,
                "errors_sample": result.errors
            })
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Database performance test results exported to: {results_file}")
        
        # Print overall summary
        print(f"\n{'='*80}")
        print("OVERALL DATABASE PERFORMANCE SUMMARY")
        print(f"{'='*80}")
        
        total_postgres_tests = len(postgres_results)
        postgres_targets_met = sum(1 for r in postgres_results if r.p95_time <= targets.db_query_time_95th)
        
        total_redis_tests = len(redis_results)
        redis_targets_met = sum(1 for r in redis_results if r.p95_time <= targets.db_query_time_95th)
        
        print(f"PostgreSQL: {postgres_targets_met}/{total_postgres_tests} tests met performance targets")
        print(f"Redis: {redis_targets_met}/{total_redis_tests} tests met performance targets")
        
        return {
            "postgres_results": postgres_results,
            "redis_results": redis_results,
            "concurrent_connection_test": concurrent_test_results
        }


if __name__ == "__main__":
    asyncio.run(run_database_performance_tests())