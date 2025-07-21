"""
Stress testing and breaking point identification
Tests system limits and identifies failure thresholds
"""
import asyncio
import time
import json
import psutil
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx
import websockets
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator
from utils.metrics import performance_collector, PerformanceMonitor


@dataclass
class StressTestPoint:
    """Single point in stress test progression"""
    load_level: int  # e.g., number of users, requests per second
    timestamp: datetime
    response_time_p95: float
    error_rate: float
    cpu_usage: float
    memory_usage_mb: float
    throughput: float
    active_connections: int
    system_stable: bool
    breaking_point_reached: bool = False


@dataclass
class StressTestResult:
    """Result of a stress test"""
    test_name: str
    test_type: str  # "user_load", "request_rate", "connection_flood", etc.
    start_time: datetime
    end_time: datetime
    test_points: List[StressTestPoint]
    breaking_point: Optional[StressTestPoint]
    max_stable_load: int
    peak_throughput: float
    failure_mode: str
    recovery_time: Optional[float]
    recommendations: List[str]


class StressTester:
    """Comprehensive stress testing to find system breaking points"""
    
    def __init__(self):
        self.api_base_url = config.API_BASE_URL
        self.ws_base_url = config.WS_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
        self.http_client = None
        self.performance_monitor = None
        self.system_monitor_running = False
        self.system_metrics = []
        
    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.performance_monitor = PerformanceMonitor(performance_collector, interval=1.0)
        await self.performance_monitor.start()
        
        # Start system monitoring
        self.system_monitor_running = True
        self.system_monitor_thread = threading.Thread(target=self._monitor_system_resources)
        self.system_monitor_thread.daemon = True
        self.system_monitor_thread.start()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.system_monitor_running = False
        if self.performance_monitor:
            await self.performance_monitor.stop()
        if self.http_client:
            await self.http_client.aclose()
    
    def _monitor_system_resources(self):
        """Monitor system resources in background thread"""
        while self.system_monitor_running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                self.system_metrics.append({
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_mb": memory.used / (1024 * 1024),
                    "available_memory_mb": memory.available / (1024 * 1024)
                })
                
                # Keep only recent metrics (last 300 points = 5 minutes)
                if len(self.system_metrics) > 300:
                    self.system_metrics = self.system_metrics[-300:]
                    
            except Exception as e:
                print(f"Error monitoring system resources: {e}")
            
            time.sleep(1)
    
    def _get_current_system_metrics(self) -> Dict[str, float]:
        """Get current system resource usage"""
        if not self.system_metrics:
            return {"cpu_percent": 0, "memory_mb": 0}
        
        recent_metrics = self.system_metrics[-5:]  # Last 5 seconds
        
        return {
            "cpu_percent": statistics.mean([m["cpu_percent"] for m in recent_metrics]),
            "memory_mb": statistics.mean([m["memory_mb"] for m in recent_metrics]),
            "memory_percent": statistics.mean([m["memory_percent"] for m in recent_metrics])
        }
    
    async def progressive_user_load_test(self, 
                                       start_users: int = 5,
                                       max_users: int = 200,
                                       increment: int = 5,
                                       step_duration: int = 30) -> StressTestResult:
        """Progressively increase user load until breaking point"""
        
        print(f"Progressive user load test: {start_users} to {max_users} users, +{increment} every {step_duration}s")
        
        start_time = datetime.now(timezone.utc)
        test_points = []
        breaking_point = None
        max_stable_load = start_users
        peak_throughput = 0
        
        current_users = start_users
        consecutive_failures = 0
        
        while current_users <= max_users:
            print(f"\n{'='*50}")
            print(f"TESTING {current_users} CONCURRENT USERS")
            print(f"{'='*50}")
            
            step_start = time.time()
            
            # Run load test for this user level
            try:
                result = await self._run_user_load_step(current_users, step_duration)
                
                system_metrics = self._get_current_system_metrics()
                
                test_point = StressTestPoint(
                    load_level=current_users,
                    timestamp=datetime.now(timezone.utc),
                    response_time_p95=result["response_time_p95"],
                    error_rate=result["error_rate"],
                    cpu_usage=system_metrics["cpu_percent"],
                    memory_usage_mb=system_metrics["memory_mb"],
                    throughput=result["throughput"],
                    active_connections=result["active_connections"],
                    system_stable=result["system_stable"]
                )
                
                test_points.append(test_point)
                
                print(f"Results: P95={result['response_time_p95']:.2f}ms, "
                      f"Error={result['error_rate']:.1f}%, "
                      f"Throughput={result['throughput']:.2f}req/s, "
                      f"CPU={system_metrics['cpu_percent']:.1f}%, "
                      f"Memory={system_metrics['memory_mb']:.0f}MB")
                
                # Check if system is stable
                if result["system_stable"]:
                    max_stable_load = current_users
                    peak_throughput = max(peak_throughput, result["throughput"])
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    print(f"⚠️  System instability detected (failure #{consecutive_failures})")
                
                # Breaking point detection criteria
                breaking_point_detected = (
                    result["error_rate"] > 25 or  # High error rate
                    result["response_time_p95"] > 5000 or  # Very slow responses
                    system_metrics["cpu_percent"] > 95 or  # CPU exhaustion
                    system_metrics["memory_percent"] > 95 or  # Memory exhaustion
                    consecutive_failures >= 2  # Multiple consecutive failures
                )
                
                if breaking_point_detected:
                    test_point.breaking_point_reached = True
                    breaking_point = test_point
                    print(f"🔥 BREAKING POINT REACHED at {current_users} users!")
                    
                    # Determine failure mode
                    if result["error_rate"] > 25:
                        failure_mode = "high_error_rate"
                    elif result["response_time_p95"] > 5000:
                        failure_mode = "response_timeout"
                    elif system_metrics["cpu_percent"] > 95:
                        failure_mode = "cpu_exhaustion"
                    elif system_metrics["memory_percent"] > 95:
                        failure_mode = "memory_exhaustion"
                    else:
                        failure_mode = "system_instability"
                    
                    break
                
            except Exception as e:
                print(f"❌ Test failed at {current_users} users: {str(e)}")
                
                # Create failure test point
                system_metrics = self._get_current_system_metrics()
                test_point = StressTestPoint(
                    load_level=current_users,
                    timestamp=datetime.now(timezone.utc),
                    response_time_p95=0,
                    error_rate=100,
                    cpu_usage=system_metrics["cpu_percent"],
                    memory_usage_mb=system_metrics["memory_mb"],
                    throughput=0,
                    active_connections=0,
                    system_stable=False,
                    breaking_point_reached=True
                )
                
                test_points.append(test_point)
                breaking_point = test_point
                failure_mode = "system_crash"
                break
            
            # Move to next user level
            current_users += increment
            
            # Wait before next step (if not at breaking point)
            if current_users <= max_users:
                await asyncio.sleep(5)  # Brief recovery time
        
        end_time = datetime.now(timezone.utc)
        
        # Generate recommendations
        recommendations = self._generate_load_recommendations(test_points, breaking_point)
        
        return StressTestResult(
            test_name="Progressive User Load Test",
            test_type="user_load",
            start_time=start_time,
            end_time=end_time,
            test_points=test_points,
            breaking_point=breaking_point,
            max_stable_load=max_stable_load,
            peak_throughput=peak_throughput,
            failure_mode=failure_mode if breaking_point else "no_failure",
            recovery_time=None,
            recommendations=recommendations
        )
    
    async def _run_user_load_step(self, num_users: int, duration: int) -> Dict[str, Any]:
        """Run a single user load test step"""
        
        response_times = []
        error_count = 0
        total_requests = 0
        active_connections = 0
        
        start_time = time.time()
        end_time = start_time + duration
        
        # Create user tasks
        user_tasks = []
        for user_id in range(num_users):
            task = asyncio.create_task(
                self._simulate_user_activity(f"stress_user_{user_id}", end_time)
            )
            user_tasks.append(task)
        
        # Let users run for the specified duration
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # Collect results
        for result in user_results:
            if isinstance(result, dict):
                response_times.extend(result["response_times"])
                error_count += result["errors"]
                total_requests += result["requests"]
                if result["connected"]:
                    active_connections += 1
            else:
                error_count += 1  # Task exception counts as error
        
        actual_duration = time.time() - start_time
        
        # Calculate metrics
        if response_times:
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        else:
            p95_response_time = 0
        
        error_rate = (error_count / max(total_requests, 1)) * 100
        throughput = total_requests / actual_duration if actual_duration > 0 else 0
        
        # Determine system stability
        system_stable = (
            error_rate < 15 and  # Less than 15% errors
            p95_response_time < 2000 and  # Less than 2 second response time
            active_connections >= num_users * 0.8  # At least 80% users connected
        )
        
        return {
            "response_time_p95": p95_response_time,
            "error_rate": error_rate,
            "throughput": throughput,
            "active_connections": active_connections,
            "system_stable": system_stable,
            "total_requests": total_requests
        }
    
    async def _simulate_user_activity(self, user_id: str, end_time: float) -> Dict[str, Any]:
        """Simulate realistic user activity for stress testing"""
        
        response_times = []
        error_count = 0
        request_count = 0
        connected = False
        
        try:
            # Try to establish connection
            websocket_url = f"{self.ws_base_url}/ws?client_id={user_id}"
            
            async with websockets.connect(websocket_url, timeout=5) as websocket:
                connected = True
                
                while time.time() < end_time:
                    try:
                        # Make API request
                        request_start = time.time()
                        
                        # Random API calls
                        endpoint = random.choice([
                            "/health",
                            "/api/v1/articles/?limit=10",
                            "/api/v1/positions/",
                            "/api/v1/analysis/market-summary"
                        ])
                        
                        response = await self.http_client.get(f"{self.api_base_url}{endpoint}")
                        request_end = time.time()
                        
                        response_time = (request_end - request_start) * 1000
                        response_times.append(response_time)
                        request_count += 1
                        
                        if response.status_code >= 400:
                            error_count += 1
                        
                        # Send WebSocket message occasionally
                        if request_count % 3 == 0:
                            message = {"type": "ping", "timestamp": time.time()}
                            await websocket.send(json.dumps(message))
                        
                        # Brief pause between requests
                        await asyncio.sleep(random.uniform(0.1, 0.5))
                        
                    except Exception as e:
                        error_count += 1
                        request_count += 1
                        
                        # If too many errors, break
                        if error_count > 10:
                            break
        
        except Exception as e:
            # Connection failed
            error_count += 1
            request_count += 1
        
        return {
            "response_times": response_times,
            "errors": error_count,
            "requests": request_count,
            "connected": connected
        }
    
    async def connection_flood_test(self, 
                                  max_connections: int = 500,
                                  connection_rate: float = 10.0) -> StressTestResult:
        """Test system with rapid connection creation (connection flood)"""
        
        print(f"Connection flood test: up to {max_connections} connections at {connection_rate}/sec")
        
        start_time = datetime.now(timezone.utc)
        test_points = []
        breaking_point = None
        
        connections = []
        connection_errors = 0
        connection_times = []
        
        connection_interval = 1.0 / connection_rate
        
        for i in range(max_connections):
            conn_start = time.time()
            
            try:
                # Attempt WebSocket connection
                websocket_url = f"{self.ws_base_url}/ws?client_id=flood_test_{i}"
                websocket = await websockets.connect(websocket_url, timeout=2)
                connections.append(websocket)
                
                conn_end = time.time()
                connection_time = (conn_end - conn_start) * 1000
                connection_times.append(connection_time)
                
                # Record test point every 50 connections
                if (i + 1) % 50 == 0:
                    system_metrics = self._get_current_system_metrics()
                    
                    avg_conn_time = statistics.mean(connection_times[-50:])
                    recent_errors = sum(1 for j in range(max(0, i-49), i+1) if j >= len(connections))
                    error_rate = (recent_errors / 50) * 100
                    
                    test_point = StressTestPoint(
                        load_level=i + 1,
                        timestamp=datetime.now(timezone.utc),
                        response_time_p95=avg_conn_time,
                        error_rate=error_rate,
                        cpu_usage=system_metrics["cpu_percent"],
                        memory_usage_mb=system_metrics["memory_mb"],
                        throughput=len(connections) / ((time.time() - start_time.timestamp()) / 60),  # connections per minute
                        active_connections=len(connections),
                        system_stable=(error_rate < 10 and avg_conn_time < 1000)
                    )
                    
                    test_points.append(test_point)
                    
                    print(f"Connections: {len(connections)}, "
                          f"Avg time: {avg_conn_time:.2f}ms, "
                          f"Errors: {error_rate:.1f}%, "
                          f"CPU: {system_metrics['cpu_percent']:.1f}%")
                    
                    # Check breaking point
                    if (error_rate > 25 or 
                        avg_conn_time > 5000 or 
                        system_metrics["cpu_percent"] > 95):
                        
                        test_point.breaking_point_reached = True
                        breaking_point = test_point
                        print(f"🔥 Connection flood breaking point at {len(connections)} connections!")
                        break
                
            except Exception as e:
                connection_errors += 1
                
                # If connection errors spike, we've hit the breaking point
                if connection_errors > 20:
                    system_metrics = self._get_current_system_metrics()
                    
                    breaking_point = StressTestPoint(
                        load_level=i + 1,
                        timestamp=datetime.now(timezone.utc),
                        response_time_p95=0,
                        error_rate=100,
                        cpu_usage=system_metrics["cpu_percent"],
                        memory_usage_mb=system_metrics["memory_mb"],
                        throughput=0,
                        active_connections=len(connections),
                        system_stable=False,
                        breaking_point_reached=True
                    )
                    
                    test_points.append(breaking_point)
                    print(f"🔥 Connection flood breaking point due to connection failures!")
                    break
            
            # Wait before next connection
            await asyncio.sleep(connection_interval)
        
        # Close all connections
        for websocket in connections:
            try:
                await websocket.close()
            except:
                pass
        
        end_time = datetime.now(timezone.utc)
        
        max_stable_connections = len(connections) if not breaking_point else breaking_point.active_connections
        
        return StressTestResult(
            test_name="Connection Flood Test",
            test_type="connection_flood",
            start_time=start_time,
            end_time=end_time,
            test_points=test_points,
            breaking_point=breaking_point,
            max_stable_load=max_stable_connections,
            peak_throughput=max_stable_connections,
            failure_mode="connection_exhaustion" if breaking_point else "no_failure",
            recovery_time=None,
            recommendations=self._generate_connection_recommendations(test_points, breaking_point)
        )
    
    async def memory_exhaustion_test(self, 
                                   payload_size_mb: float = 1.0,
                                   max_requests: int = 1000) -> StressTestResult:
        """Test system memory limits with large payloads"""
        
        print(f"Memory exhaustion test: {payload_size_mb}MB payloads, up to {max_requests} requests")
        
        start_time = datetime.now(timezone.utc)
        test_points = []
        breaking_point = None
        
        # Generate large test data
        large_articles = []
        for i in range(max_requests):
            article = test_data_generator.generate_article()
            # Increase content size to reach target payload size
            content_size = int(payload_size_mb * 1024 * 1024 / len(article["content"])) + 1
            article["content"] = article["content"] * content_size
            large_articles.append(article)
        
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        for i in range(0, max_requests, 10):  # Test in batches of 10
            batch_start = time.time()
            batch_responses = []
            batch_errors = 0
            
            # Send batch of large requests
            tasks = []
            for j in range(min(10, max_requests - i)):
                request_data = {
                    "tickers": ["TEST"],
                    "test_articles": [large_articles[i + j]]
                }
                
                task = asyncio.create_task(
                    self._send_large_request(request_data)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, tuple):
                    response_time, success = result
                    batch_responses.append(response_time)
                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        batch_errors += 1
                else:
                    failed_requests += 1
                    batch_errors += 1
            
            response_times.extend(batch_responses)
            
            # Record test point
            system_metrics = self._get_current_system_metrics()
            
            avg_response = statistics.mean(batch_responses) if batch_responses else 0
            error_rate = (batch_errors / 10) * 100
            
            test_point = StressTestPoint(
                load_level=i + 10,
                timestamp=datetime.now(timezone.utc),
                response_time_p95=avg_response,
                error_rate=error_rate,
                cpu_usage=system_metrics["cpu_percent"],
                memory_usage_mb=system_metrics["memory_mb"],
                throughput=successful_requests / (time.time() - start_time.timestamp()),
                active_connections=1,  # Single connection test
                system_stable=(error_rate < 20 and avg_response < 10000)
            )
            
            test_points.append(test_point)
            
            print(f"Requests: {i+10}, "
                  f"Memory: {system_metrics['memory_mb']:.0f}MB, "
                  f"Errors: {error_rate:.1f}%, "
                  f"Response: {avg_response:.2f}ms")
            
            # Check for memory exhaustion breaking point
            if (system_metrics["memory_percent"] > 90 or 
                error_rate > 50 or 
                avg_response > 30000):
                
                test_point.breaking_point_reached = True
                breaking_point = test_point
                print(f"🔥 Memory exhaustion breaking point!")
                break
            
            await asyncio.sleep(1)  # Brief pause between batches
        
        end_time = datetime.now(timezone.utc)
        
        return StressTestResult(
            test_name="Memory Exhaustion Test",
            test_type="memory_exhaustion",
            start_time=start_time,
            end_time=end_time,
            test_points=test_points,
            breaking_point=breaking_point,
            max_stable_load=successful_requests,
            peak_throughput=successful_requests / (end_time - start_time).total_seconds(),
            failure_mode="memory_exhaustion" if breaking_point else "no_failure",
            recovery_time=None,
            recommendations=self._generate_memory_recommendations(test_points, breaking_point)
        )
    
    async def _send_large_request(self, request_data: Dict[str, Any]) -> Tuple[float, bool]:
        """Send a large request and measure response time"""
        
        start_time = time.time()
        
        try:
            response = await self.http_client.post(
                f"{self.api_base_url}/api/v1/analysis/start",
                json=request_data,
                timeout=30
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return response_time, (200 <= response.status_code < 400)
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time, False
    
    def _generate_load_recommendations(self, test_points: List[StressTestPoint], 
                                     breaking_point: Optional[StressTestPoint]) -> List[str]:
        """Generate recommendations based on load test results"""
        
        recommendations = []
        
        if breaking_point:
            if breaking_point.cpu_usage > 90:
                recommendations.append("Consider horizontal scaling or upgrading CPU resources")
                recommendations.append("Implement connection pooling and request queuing")
            
            if breaking_point.memory_usage_mb > 1500:  # > 1.5GB
                recommendations.append("Optimize memory usage in application code")
                recommendations.append("Implement response caching to reduce memory pressure")
            
            if breaking_point.error_rate > 25:
                recommendations.append("Implement circuit breakers for external services")
                recommendations.append("Add request rate limiting per user")
            
            if breaking_point.response_time_p95 > 2000:
                recommendations.append("Optimize database queries and add indexes")
                recommendations.append("Implement async processing for heavy operations")
        
        stable_points = [p for p in test_points if p.system_stable]
        if stable_points:
            max_stable = max(stable_points, key=lambda p: p.load_level)
            recommendations.append(f"Safe operating capacity: {max_stable.load_level} concurrent users")
            recommendations.append(f"Recommended limit: {int(max_stable.load_level * 0.8)} users (80% of capacity)")
        
        return recommendations
    
    def _generate_connection_recommendations(self, test_points: List[StressTestPoint], 
                                           breaking_point: Optional[StressTestPoint]) -> List[str]:
        """Generate recommendations for connection-related issues"""
        
        recommendations = []
        
        if breaking_point:
            recommendations.append("Implement connection rate limiting")
            recommendations.append("Configure appropriate WebSocket timeout settings")
            recommendations.append("Monitor and limit concurrent connections per IP")
            recommendations.append("Consider using a WebSocket proxy/load balancer")
        
        return recommendations
    
    def _generate_memory_recommendations(self, test_points: List[StressTestPoint], 
                                       breaking_point: Optional[StressTestPoint]) -> List[str]:
        """Generate recommendations for memory-related issues"""
        
        recommendations = []
        
        if breaking_point:
            recommendations.append("Implement request payload size limits")
            recommendations.append("Add memory monitoring and alerts")
            recommendations.append("Consider streaming large payloads instead of loading into memory")
            recommendations.append("Implement garbage collection optimization")
        
        return recommendations
    
    def print_stress_result(self, result: StressTestResult):
        """Print detailed stress test results"""
        
        print(f"\n{'='*80}")
        print(f"STRESS TEST RESULT: {result.test_name}")
        print(f"{'='*80}")
        
        print(f"Test Type: {result.test_type}")
        print(f"Duration: {(result.end_time - result.start_time).total_seconds():.2f} seconds")
        print(f"Max Stable Load: {result.max_stable_load}")
        print(f"Peak Throughput: {result.peak_throughput:.2f}")
        
        if result.breaking_point:
            print(f"\n🔥 BREAKING POINT DETECTED:")
            bp = result.breaking_point
            print(f"  Load Level: {bp.load_level}")
            print(f"  Error Rate: {bp.error_rate:.2f}%")
            print(f"  Response Time P95: {bp.response_time_p95:.2f}ms")
            print(f"  CPU Usage: {bp.cpu_usage:.1f}%")
            print(f"  Memory Usage: {bp.memory_usage_mb:.0f}MB")
            print(f"  Failure Mode: {result.failure_mode}")
        else:
            print(f"\n✅ No breaking point reached within test limits")
        
        print(f"\n📊 TEST PROGRESSION:")
        print(f"{'Load':<8} {'P95 (ms)':<10} {'Errors %':<10} {'CPU %':<8} {'Memory MB':<12} {'Stable':<8}")
        print(f"{'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*12} {'-'*8}")
        
        for point in result.test_points[-10:]:  # Show last 10 points
            stable_icon = "✅" if point.system_stable else "❌"
            print(f"{point.load_level:<8} {point.response_time_p95:<10.1f} "
                  f"{point.error_rate:<10.1f} {point.cpu_usage:<8.1f} "
                  f"{point.memory_usage_mb:<12.0f} {stable_icon:<8}")
        
        if result.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")


# Import random for user simulation
import random


async def run_comprehensive_stress_tests():
    """Run all stress tests to identify system breaking points"""
    
    print("🚀 Starting comprehensive stress testing...")
    
    async with StressTester() as tester:
        all_results = []
        
        # Test 1: Progressive user load
        print(f"\n{'='*80}")
        print("STRESS TEST 1: PROGRESSIVE USER LOAD")
        print(f"{'='*80}")
        
        user_load_result = await tester.progressive_user_load_test(
            start_users=5, max_users=100, increment=5, step_duration=20
        )
        all_results.append(user_load_result)
        tester.print_stress_result(user_load_result)
        
        await asyncio.sleep(60)  # Recovery time
        
        # Test 2: Connection flood
        print(f"\n{'='*80}")
        print("STRESS TEST 2: CONNECTION FLOOD")
        print(f"{'='*80}")
        
        connection_flood_result = await tester.connection_flood_test(
            max_connections=200, connection_rate=5.0
        )
        all_results.append(connection_flood_result)
        tester.print_stress_result(connection_flood_result)
        
        await asyncio.sleep(60)  # Recovery time
        
        # Test 3: Memory exhaustion (reduced for safety)
        print(f"\n{'='*80}")
        print("STRESS TEST 3: MEMORY EXHAUSTION")
        print(f"{'='*80}")
        
        memory_test_result = await tester.memory_exhaustion_test(
            payload_size_mb=0.5, max_requests=100  # Reduced for safety
        )
        all_results.append(memory_test_result)
        tester.print_stress_result(memory_test_result)
        
        # Export results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"stress_test_results_{timestamp}.json"
        
        # Convert to JSON
        json_results = []
        for result in all_results:
            json_result = {
                "test_name": result.test_name,
                "test_type": result.test_type,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "max_stable_load": result.max_stable_load,
                "peak_throughput": result.peak_throughput,
                "failure_mode": result.failure_mode,
                "breaking_point": {
                    "load_level": result.breaking_point.load_level,
                    "error_rate": result.breaking_point.error_rate,
                    "response_time_p95": result.breaking_point.response_time_p95,
                    "cpu_usage": result.breaking_point.cpu_usage,
                    "memory_usage_mb": result.breaking_point.memory_usage_mb
                } if result.breaking_point else None,
                "recommendations": result.recommendations,
                "test_points": [
                    {
                        "load_level": p.load_level,
                        "timestamp": p.timestamp.isoformat(),
                        "response_time_p95": p.response_time_p95,
                        "error_rate": p.error_rate,
                        "cpu_usage": p.cpu_usage,
                        "memory_usage_mb": p.memory_usage_mb,
                        "throughput": p.throughput,
                        "system_stable": p.system_stable
                    }
                    for p in result.test_points
                ]
            }
            json_results.append(json_result)
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Stress test results exported to: {results_file}")
        
        # Summary
        print(f"\n{'='*80}")
        print("STRESS TEST SUMMARY")
        print(f"{'='*80}")
        
        for result in all_results:
            print(f"\n{result.test_name}:")
            print(f"  Max Stable Load: {result.max_stable_load}")
            print(f"  Failure Mode: {result.failure_mode}")
            if result.breaking_point:
                print(f"  Breaking Point: {result.breaking_point.load_level} {result.test_type}")
        
        return all_results


if __name__ == "__main__":
    asyncio.run(run_comprehensive_stress_tests())