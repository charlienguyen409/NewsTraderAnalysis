"""
WebSocket performance and scalability testing
"""
import asyncio
import websockets
import json
import time
import uuid
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator
from utils.metrics import performance_collector


@dataclass
class WebSocketMetric:
    """Single WebSocket performance metric"""
    connection_id: str
    message_type: str
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


@dataclass
class WebSocketTestResult:
    """Result of WebSocket performance test"""
    test_name: str
    total_connections: int
    successful_connections: int
    failed_connections: int
    total_messages_sent: int
    total_messages_received: int
    connection_time_stats: Dict[str, float]
    message_latency_stats: Dict[str, float]
    throughput_messages_per_second: float
    error_rate: float
    errors: List[str]
    test_duration: float


class WebSocketPerformanceTester:
    """Test WebSocket connections for performance and scalability"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.WS_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
        self.connections: List[websockets.WebSocketServerProtocol] = []
        self.metrics: List[WebSocketMetric] = []
        self.connection_times: List[float] = []
        self.message_latencies: List[float] = []
        self.errors: List[str] = []
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def connect_websocket(self, endpoint: str = "/ws", client_id: str = None) -> Tuple[Optional[websockets.WebSocketServerProtocol], float]:
        """Connect to WebSocket and measure connection time"""
        
        if not client_id:
            client_id = str(uuid.uuid4())
        
        url = f"{self.base_url}{endpoint}?client_id={client_id}"
        
        start_time = time.time()
        try:
            websocket = await websockets.connect(url, timeout=10)
            end_time = time.time()
            connection_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            self.connection_times.append(connection_time)
            return websocket, connection_time
            
        except Exception as e:
            end_time = time.time()
            connection_time = (end_time - start_time) * 1000
            self.errors.append(f"Connection failed: {str(e)}")
            return None, connection_time
    
    async def send_message_and_measure_latency(self, websocket: websockets.WebSocketServerProtocol, 
                                             message: Dict[str, Any], 
                                             connection_id: str) -> Optional[float]:
        """Send a message and measure round-trip latency"""
        
        # Add timestamp to message for latency calculation
        message["sent_at"] = time.time()
        
        try:
            start_time = time.time()
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Record metric
            metric = WebSocketMetric(
                connection_id=connection_id,
                message_type=message.get("type", "unknown"),
                latency_ms=latency
            )
            self.metrics.append(metric)
            self.message_latencies.append(latency)
            
            return latency
            
        except Exception as e:
            self.errors.append(f"Message send/receive failed: {str(e)}")
            return None
    
    async def test_connection_scalability(self, max_connections: int = 100, 
                                        connection_rate: float = 10.0) -> WebSocketTestResult:
        """Test WebSocket connection scalability"""
        
        print(f"Testing WebSocket connection scalability: {max_connections} connections at {connection_rate}/sec")
        
        start_time = time.time()
        successful_connections = 0
        failed_connections = 0
        active_connections = []
        
        # Connect at specified rate
        connection_interval = 1.0 / connection_rate
        
        for i in range(max_connections):
            client_id = f"test_client_{i}"
            
            websocket, connection_time = await self.connect_websocket(client_id=client_id)
            
            if websocket:
                successful_connections += 1
                active_connections.append((websocket, client_id))
                self.logger.info(f"Connection {i+1}/{max_connections} successful ({connection_time:.2f}ms)")
            else:
                failed_connections += 1
                self.logger.error(f"Connection {i+1}/{max_connections} failed")
            
            # Wait before next connection
            if i < max_connections - 1:
                await asyncio.sleep(connection_interval)
        
        # Keep connections alive for a short period
        await asyncio.sleep(5)
        
        # Test message sending on active connections
        messages_sent = 0
        messages_received = 0
        
        for websocket, client_id in active_connections[:min(10, len(active_connections))]:  # Test first 10 connections
            try:
                message = test_data_generator.generate_websocket_message()
                latency = await self.send_message_and_measure_latency(websocket, message, client_id)
                
                if latency is not None:
                    messages_sent += 1
                    messages_received += 1
                else:
                    messages_sent += 1
                    
            except Exception as e:
                self.errors.append(f"Message test failed for {client_id}: {str(e)}")
        
        # Close all connections
        for websocket, client_id in active_connections:
            try:
                await websocket.close()
            except:
                pass
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate statistics
        connection_stats = self._calculate_connection_stats()
        latency_stats = self._calculate_latency_stats()
        
        error_rate = (failed_connections / max_connections * 100) if max_connections > 0 else 0
        throughput = messages_received / test_duration if test_duration > 0 else 0
        
        return WebSocketTestResult(
            test_name="Connection Scalability",
            total_connections=max_connections,
            successful_connections=successful_connections,
            failed_connections=failed_connections,
            total_messages_sent=messages_sent,
            total_messages_received=messages_received,
            connection_time_stats=connection_stats,
            message_latency_stats=latency_stats,
            throughput_messages_per_second=throughput,
            error_rate=error_rate,
            errors=self.errors.copy(),
            test_duration=test_duration
        )
    
    async def test_message_throughput(self, num_connections: int = 10, 
                                    messages_per_connection: int = 100,
                                    concurrent_messages: int = 5) -> WebSocketTestResult:
        """Test WebSocket message throughput"""
        
        print(f"Testing WebSocket message throughput: {num_connections} connections, "
              f"{messages_per_connection} messages each, {concurrent_messages} concurrent")
        
        start_time = time.time()
        
        # Establish connections
        connections = []
        successful_connections = 0
        failed_connections = 0
        
        for i in range(num_connections):
            client_id = f"throughput_client_{i}"
            websocket, connection_time = await self.connect_websocket(client_id=client_id)
            
            if websocket:
                successful_connections += 1
                connections.append((websocket, client_id))
            else:
                failed_connections += 1
        
        if not connections:
            raise Exception("No successful connections established")
        
        # Send messages concurrently
        total_messages_sent = 0
        total_messages_received = 0
        
        # Create tasks for concurrent message sending
        tasks = []
        for websocket, client_id in connections:
            task = asyncio.create_task(
                self._send_messages_to_connection(
                    websocket, client_id, messages_per_connection, concurrent_messages
                )
            )
            tasks.append(task)
        
        # Wait for all message sending tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, tuple):
                sent, received = result
                total_messages_sent += sent
                total_messages_received += received
            else:
                self.errors.append(f"Message sending task failed: {str(result)}")
        
        # Close connections
        for websocket, client_id in connections:
            try:
                await websocket.close()
            except:
                pass
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate statistics
        connection_stats = self._calculate_connection_stats()
        latency_stats = self._calculate_latency_stats()
        
        error_rate = (failed_connections / num_connections * 100) if num_connections > 0 else 0
        throughput = total_messages_received / test_duration if test_duration > 0 else 0
        
        return WebSocketTestResult(
            test_name="Message Throughput",
            total_connections=num_connections,
            successful_connections=successful_connections,
            failed_connections=failed_connections,
            total_messages_sent=total_messages_sent,
            total_messages_received=total_messages_received,
            connection_time_stats=connection_stats,
            message_latency_stats=latency_stats,
            throughput_messages_per_second=throughput,
            error_rate=error_rate,
            errors=self.errors.copy(),
            test_duration=test_duration
        )
    
    async def test_concurrent_analysis_subscriptions(self, num_connections: int = 20,
                                                   analysis_sessions: int = 5) -> WebSocketTestResult:
        """Test concurrent analysis session subscriptions"""
        
        print(f"Testing concurrent analysis subscriptions: {num_connections} connections, "
              f"{analysis_sessions} analysis sessions")
        
        start_time = time.time()
        
        # Generate analysis session IDs
        session_ids = [str(uuid.uuid4()) for _ in range(analysis_sessions)]
        
        # Establish connections to analysis WebSocket endpoints
        connections = []
        successful_connections = 0
        failed_connections = 0
        
        for i in range(num_connections):
            session_id = session_ids[i % len(session_ids)]  # Distribute connections across sessions
            client_id = f"analysis_client_{i}"
            
            endpoint = f"/ws/analysis/{session_id}"
            websocket, connection_time = await self.connect_websocket(endpoint=endpoint, client_id=client_id)
            
            if websocket:
                successful_connections += 1
                connections.append((websocket, client_id, session_id))
            else:
                failed_connections += 1
        
        if not connections:
            raise Exception("No successful connections established")
        
        # Simulate analysis progress messages
        total_messages_sent = 0
        total_messages_received = 0
        
        # Send analysis progress messages to each connection
        for websocket, client_id, session_id in connections:
            try:
                # Send subscription confirmation message
                message = {
                    "type": "subscribe_session",
                    "session_id": session_id
                }
                
                latency = await self.send_message_and_measure_latency(websocket, message, client_id)
                
                if latency is not None:
                    total_messages_sent += 1
                    total_messages_received += 1
                else:
                    total_messages_sent += 1
                
                # Send a few progress update messages
                for progress in [25, 50, 75, 100]:
                    progress_message = {
                        "type": "progress_update",
                        "session_id": session_id,
                        "progress": progress,
                        "current_step": f"Processing step {progress}%"
                    }
                    
                    latency = await self.send_message_and_measure_latency(websocket, progress_message, client_id)
                    
                    if latency is not None:
                        total_messages_sent += 1
                        total_messages_received += 1
                    else:
                        total_messages_sent += 1
                    
                    await asyncio.sleep(0.1)  # Small delay between progress updates
                
            except Exception as e:
                self.errors.append(f"Analysis subscription test failed for {client_id}: {str(e)}")
        
        # Close connections
        for websocket, client_id, session_id in connections:
            try:
                await websocket.close()
            except:
                pass
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate statistics
        connection_stats = self._calculate_connection_stats()
        latency_stats = self._calculate_latency_stats()
        
        error_rate = (failed_connections / num_connections * 100) if num_connections > 0 else 0
        throughput = total_messages_received / test_duration if test_duration > 0 else 0
        
        return WebSocketTestResult(
            test_name="Concurrent Analysis Subscriptions",
            total_connections=num_connections,
            successful_connections=successful_connections,
            failed_connections=failed_connections,
            total_messages_sent=total_messages_sent,
            total_messages_received=total_messages_received,
            connection_time_stats=connection_stats,
            message_latency_stats=latency_stats,
            throughput_messages_per_second=throughput,
            error_rate=error_rate,
            errors=self.errors.copy(),
            test_duration=test_duration
        )
    
    async def _send_messages_to_connection(self, websocket: websockets.WebSocketServerProtocol,
                                         client_id: str, num_messages: int, 
                                         concurrent_messages: int) -> Tuple[int, int]:
        """Send multiple messages to a single connection"""
        
        messages_sent = 0
        messages_received = 0
        
        # Send messages in batches
        batch_size = concurrent_messages
        num_batches = (num_messages + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min((batch_num + 1) * batch_size, num_messages)
            batch_messages = batch_end - batch_start
            
            # Create tasks for this batch
            tasks = []
            for i in range(batch_messages):
                message = test_data_generator.generate_websocket_message()
                task = asyncio.create_task(
                    self.send_message_and_measure_latency(websocket, message, client_id)
                )
                tasks.append(task)
            
            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            for result in results:
                messages_sent += 1
                if not isinstance(result, Exception) and result is not None:
                    messages_received += 1
        
        return messages_sent, messages_received
    
    def _calculate_connection_stats(self) -> Dict[str, float]:
        """Calculate connection time statistics"""
        if not self.connection_times:
            return {}
        
        return {
            "mean": statistics.mean(self.connection_times),
            "median": statistics.median(self.connection_times),
            "min": min(self.connection_times),
            "max": max(self.connection_times),
            "p95": statistics.quantiles(self.connection_times, n=20)[18] if len(self.connection_times) >= 20 else max(self.connection_times),
            "std": statistics.stdev(self.connection_times) if len(self.connection_times) > 1 else 0
        }
    
    def _calculate_latency_stats(self) -> Dict[str, float]:
        """Calculate message latency statistics"""
        if not self.message_latencies:
            return {}
        
        return {
            "mean": statistics.mean(self.message_latencies),
            "median": statistics.median(self.message_latencies),
            "min": min(self.message_latencies),
            "max": max(self.message_latencies),
            "p95": statistics.quantiles(self.message_latencies, n=20)[18] if len(self.message_latencies) >= 20 else max(self.message_latencies),
            "p99": statistics.quantiles(self.message_latencies, n=100)[98] if len(self.message_latencies) >= 100 else max(self.message_latencies),
            "std": statistics.stdev(self.message_latencies) if len(self.message_latencies) > 1 else 0
        }
    
    def print_test_result(self, result: WebSocketTestResult):
        """Print detailed test results"""
        
        print(f"\n{'='*60}")
        print(f"WEBSOCKET TEST RESULT: {result.test_name}")
        print(f"{'='*60}")
        
        print(f"Test Duration: {result.test_duration:.2f} seconds")
        print(f"Total Connections: {result.total_connections}")
        print(f"Successful Connections: {result.successful_connections}")
        print(f"Failed Connections: {result.failed_connections}")
        print(f"Connection Success Rate: {(result.successful_connections/result.total_connections*100):.1f}%")
        
        print(f"\nMessage Statistics:")
        print(f"Messages Sent: {result.total_messages_sent}")
        print(f"Messages Received: {result.total_messages_received}")
        print(f"Message Success Rate: {(result.total_messages_received/result.total_messages_sent*100):.1f}%")
        print(f"Throughput: {result.throughput_messages_per_second:.2f} messages/second")
        
        if result.connection_time_stats:
            stats = result.connection_time_stats
            print(f"\nConnection Time Statistics:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  95th Percentile: {stats['p95']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
        
        if result.message_latency_stats:
            stats = result.message_latency_stats
            print(f"\nMessage Latency Statistics:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  95th Percentile: {stats['p95']:.2f}ms")
            print(f"  99th Percentile: {stats['p99']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
        
        print(f"\nError Rate: {result.error_rate:.2f}%")
        
        if result.errors:
            print(f"\nSample Errors (first 5):")
            for error in result.errors[:5]:
                print(f"  - {error}")
        
        # Target analysis
        print(f"\n{'='*60}")
        print("TARGET ANALYSIS")
        print(f"{'='*60}")
        
        if result.message_latency_stats:
            p95_latency = result.message_latency_stats['p95']
            if p95_latency <= targets.websocket_messages_per_second:
                print(f"✅ Message latency P95: {p95_latency:.2f}ms (target: {targets.websocket_messages_per_second}ms)")
            else:
                print(f"❌ Message latency P95: {p95_latency:.2f}ms (target: {targets.websocket_messages_per_second}ms)")
        
        if result.throughput_messages_per_second >= targets.websocket_messages_per_second:
            print(f"✅ Throughput: {result.throughput_messages_per_second:.2f} msg/s (target: {targets.websocket_messages_per_second} msg/s)")
        else:
            print(f"❌ Throughput: {result.throughput_messages_per_second:.2f} msg/s (target: {targets.websocket_messages_per_second} msg/s)")
        
        if result.successful_connections >= targets.max_websocket_connections:
            print(f"✅ Concurrent connections: {result.successful_connections} (target: {targets.max_websocket_connections})")
        else:
            print(f"❌ Concurrent connections: {result.successful_connections} (target: {targets.max_websocket_connections})")


async def run_websocket_performance_tests():
    """Run comprehensive WebSocket performance tests"""
    
    print("🚀 Starting comprehensive WebSocket performance testing...")
    
    tester = WebSocketPerformanceTester()
    results = []
    
    # Test scenarios
    test_scenarios = [
        ("test_connection_scalability", {"max_connections": 50, "connection_rate": 5.0}),
        ("test_connection_scalability", {"max_connections": 100, "connection_rate": 10.0}),
        ("test_message_throughput", {"num_connections": 10, "messages_per_connection": 50, "concurrent_messages": 5}),
        ("test_message_throughput", {"num_connections": 20, "messages_per_connection": 100, "concurrent_messages": 10}),
        ("test_concurrent_analysis_subscriptions", {"num_connections": 20, "analysis_sessions": 5}),
        ("test_concurrent_analysis_subscriptions", {"num_connections": 50, "analysis_sessions": 10}),
    ]
    
    for test_method, kwargs in test_scenarios:
        try:
            print(f"\n{'='*80}")
            print(f"RUNNING: {test_method.upper()} with {kwargs}")
            print(f"{'='*80}")
            
            method = getattr(tester, test_method)
            result = await method(**kwargs)
            
            tester.print_test_result(result)
            results.append(result)
            
            # Clear metrics for next test
            tester.metrics.clear()
            tester.connection_times.clear()
            tester.message_latencies.clear()
            tester.errors.clear()
            
            # Wait between tests
            print("\n⏳ Waiting 15 seconds before next test...")
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"❌ Test {test_method} failed: {str(e)}")
    
    # Export results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"websocket_performance_results_{timestamp}.json"
    
    json_results = []
    for result in results:
        json_results.append({
            "test_name": result.test_name,
            "total_connections": result.total_connections,
            "successful_connections": result.successful_connections,
            "failed_connections": result.failed_connections,
            "total_messages_sent": result.total_messages_sent,
            "total_messages_received": result.total_messages_received,
            "connection_time_stats": result.connection_time_stats,
            "message_latency_stats": result.message_latency_stats,
            "throughput_messages_per_second": result.throughput_messages_per_second,
            "error_rate": result.error_rate,
            "test_duration": result.test_duration,
            "errors_sample": result.errors[:10]  # Keep only first 10 errors
        })
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\n✅ WebSocket performance test results exported to: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_websocket_performance_tests())