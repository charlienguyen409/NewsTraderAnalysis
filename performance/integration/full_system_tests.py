"""
Full system integration performance tests
Tests complete analysis workflows under load
"""
import asyncio
import time
import json
import uuid
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import httpx
import websockets

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator
from utils.metrics import performance_collector, PerformanceMonitor


@dataclass
class AnalysisWorkflowResult:
    """Result of a complete analysis workflow test"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_duration: float  # seconds
    api_response_time: float  # milliseconds
    websocket_connection_time: float  # milliseconds
    analysis_completion_time: Optional[float]  # seconds
    messages_received: int
    final_status: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class SystemIntegrationResult:
    """Result of full system integration test"""
    test_name: str
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    workflow_results: List[AnalysisWorkflowResult]
    average_completion_time: float
    p95_completion_time: float
    api_response_stats: Dict[str, float]
    websocket_stats: Dict[str, float]
    concurrent_user_capacity: int
    system_throughput: float  # workflows per minute
    error_rate: float
    test_duration: float


class FullSystemPerformanceTester:
    """Test complete system performance with realistic workflows"""
    
    def __init__(self):
        self.api_base_url = config.API_BASE_URL
        self.ws_base_url = config.WS_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
        self.http_client = None
        self.performance_monitor = None
        
    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.performance_monitor = PerformanceMonitor(performance_collector, interval=2.0)
        await self.performance_monitor.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.performance_monitor:
            await self.performance_monitor.stop()
        if self.http_client:
            await self.http_client.aclose()
    
    async def run_complete_analysis_workflow(self, client_id: str = None) -> AnalysisWorkflowResult:
        """Run a complete analysis workflow from start to finish"""
        
        if not client_id:
            client_id = str(uuid.uuid4())
        
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        result = AnalysisWorkflowResult(
            session_id=session_id,
            start_time=start_time,
            end_time=None,
            total_duration=0.0,
            api_response_time=0.0,
            websocket_connection_time=0.0,
            analysis_completion_time=None,
            messages_received=0,
            final_status="unknown",
            success=False
        )
        
        try:
            # Step 1: Connect to WebSocket for real-time updates
            ws_start = time.time()
            websocket_url = f"{self.ws_base_url}/ws?client_id={client_id}"
            
            async with websockets.connect(websocket_url, timeout=10) as websocket:
                ws_end = time.time()
                result.websocket_connection_time = (ws_end - ws_start) * 1000
                
                # Step 2: Start analysis via API
                analysis_request = test_data_generator.generate_analysis_request()
                
                api_start = time.time()
                response = await self.http_client.post(
                    f"{self.api_base_url}/api/v1/analysis/start",
                    json=analysis_request
                )
                api_end = time.time()
                
                result.api_response_time = (api_end - api_start) * 1000
                
                if response.status_code != 200:
                    result.error_message = f"API request failed: {response.status_code}"
                    return result
                
                response_data = response.json()
                actual_session_id = response_data.get("session_id")
                
                if not actual_session_id:
                    result.error_message = "No session_id in API response"
                    return result
                
                result.session_id = actual_session_id
                
                # Step 3: Subscribe to analysis session via WebSocket
                subscription_message = {
                    "type": "subscribe_session",
                    "session_id": actual_session_id
                }
                
                await websocket.send(json.dumps(subscription_message))
                
                # Step 4: Monitor analysis progress via WebSocket
                analysis_start_time = time.time()
                analysis_completed = False
                timeout_duration = 120  # 2 minutes timeout
                
                while not analysis_completed:
                    try:
                        # Wait for WebSocket message with timeout
                        message = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=min(10, timeout_duration - (time.time() - analysis_start_time))
                        )
                        
                        result.messages_received += 1
                        
                        try:
                            message_data = json.loads(message)
                            message_type = message_data.get("type", "")
                            
                            if message_type == "analysis_completed":
                                analysis_completed = True
                                result.final_status = "completed"
                                result.success = True
                                
                            elif message_type == "error":
                                analysis_completed = True
                                result.final_status = "error"
                                result.error_message = message_data.get("message", "Unknown error")
                                
                        except json.JSONDecodeError:
                            # Ignore invalid JSON messages
                            pass
                        
                        # Check timeout
                        if time.time() - analysis_start_time > timeout_duration:
                            result.final_status = "timeout"
                            result.error_message = f"Analysis timeout after {timeout_duration}s"
                            break
                        
                    except asyncio.TimeoutError:
                        # Check if analysis is still running via API
                        status_response = await self.http_client.get(
                            f"{self.api_base_url}/api/v1/analysis/status/{actual_session_id}/"
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            api_status = status_data.get("status", "unknown")
                            
                            if api_status in ["completed", "failed", "error"]:
                                analysis_completed = True
                                result.final_status = api_status
                                result.success = (api_status == "completed")
                                
                                if api_status != "completed":
                                    result.error_message = status_data.get("error", f"Analysis {api_status}")
                        
                        # Check overall timeout
                        if time.time() - analysis_start_time > timeout_duration:
                            result.final_status = "timeout"
                            result.error_message = f"Analysis timeout after {timeout_duration}s"
                            break
                
                analysis_end_time = time.time()
                result.analysis_completion_time = analysis_end_time - analysis_start_time
                
        except Exception as e:
            result.error_message = f"Workflow failed: {str(e)}"
            result.final_status = "exception"
        
        finally:
            end_time = datetime.now(timezone.utc)
            result.end_time = end_time
            result.total_duration = (end_time - start_time).total_seconds()
        
        return result
    
    async def test_concurrent_analysis_workflows(self, num_concurrent_users: int = 10,
                                               workflows_per_user: int = 2) -> SystemIntegrationResult:
        """Test system performance with concurrent analysis workflows"""
        
        print(f"Testing concurrent analysis workflows: {num_concurrent_users} users, "
              f"{workflows_per_user} workflows each")
        
        start_time = time.time()
        workflow_results = []
        
        # Create tasks for concurrent users
        user_tasks = []
        for user_id in range(num_concurrent_users):
            client_id = f"perf_test_user_{user_id}"
            
            # Each user runs multiple workflows
            user_task = asyncio.create_task(
                self._run_user_workflows(client_id, workflows_per_user)
            )
            user_tasks.append(user_task)
        
        # Wait for all user tasks to complete
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        # Collect all workflow results
        for result in user_results:
            if isinstance(result, list):
                workflow_results.extend(result)
            else:
                print(f"User task failed: {result}")
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Analyze results
        total_workflows = len(workflow_results)
        successful_workflows = sum(1 for r in workflow_results if r.success)
        failed_workflows = total_workflows - successful_workflows
        
        if successful_workflows > 0:
            completion_times = [r.analysis_completion_time for r in workflow_results 
                             if r.success and r.analysis_completion_time is not None]
            
            if completion_times:
                average_completion_time = statistics.mean(completion_times)
                p95_completion_time = (statistics.quantiles(completion_times, n=20)[18] 
                                     if len(completion_times) >= 20 else max(completion_times))
            else:
                average_completion_time = 0
                p95_completion_time = 0
        else:
            average_completion_time = 0
            p95_completion_time = 0
        
        # API response time statistics
        api_response_times = [r.api_response_time for r in workflow_results if r.api_response_time > 0]
        api_response_stats = {}
        if api_response_times:
            api_response_stats = {
                "mean": statistics.mean(api_response_times),
                "median": statistics.median(api_response_times),
                "p95": (statistics.quantiles(api_response_times, n=20)[18] 
                       if len(api_response_times) >= 20 else max(api_response_times)),
                "max": max(api_response_times),
                "min": min(api_response_times)
            }
        
        # WebSocket connection statistics
        ws_connection_times = [r.websocket_connection_time for r in workflow_results if r.websocket_connection_time > 0]
        websocket_stats = {}
        if ws_connection_times:
            websocket_stats = {
                "mean": statistics.mean(ws_connection_times),
                "median": statistics.median(ws_connection_times),
                "p95": (statistics.quantiles(ws_connection_times, n=20)[18] 
                       if len(ws_connection_times) >= 20 else max(ws_connection_times)),
                "max": max(ws_connection_times),
                "min": min(ws_connection_times)
            }
        
        error_rate = (failed_workflows / total_workflows * 100) if total_workflows > 0 else 0
        system_throughput = (successful_workflows / test_duration * 60) if test_duration > 0 else 0  # workflows per minute
        
        return SystemIntegrationResult(
            test_name="Concurrent Analysis Workflows",
            total_workflows=total_workflows,
            successful_workflows=successful_workflows,
            failed_workflows=failed_workflows,
            workflow_results=workflow_results,
            average_completion_time=average_completion_time,
            p95_completion_time=p95_completion_time,
            api_response_stats=api_response_stats,
            websocket_stats=websocket_stats,
            concurrent_user_capacity=num_concurrent_users,
            system_throughput=system_throughput,
            error_rate=error_rate,
            test_duration=test_duration
        )
    
    async def _run_user_workflows(self, client_id: str, num_workflows: int) -> List[AnalysisWorkflowResult]:
        """Run multiple workflows for a single user"""
        
        results = []
        
        for workflow_num in range(num_workflows):
            try:
                workflow_result = await self.run_complete_analysis_workflow(client_id)
                results.append(workflow_result)
                
                # Small delay between workflows for the same user
                if workflow_num < num_workflows - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                # Create a failed workflow result
                failed_result = AnalysisWorkflowResult(
                    session_id="failed",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                    total_duration=0.0,
                    api_response_time=0.0,
                    websocket_connection_time=0.0,
                    analysis_completion_time=None,
                    messages_received=0,
                    final_status="exception",
                    success=False,
                    error_message=str(e)
                )
                results.append(failed_result)
        
        return results
    
    async def test_system_scalability(self, max_users: int = 50, 
                                    user_increment: int = 5) -> List[SystemIntegrationResult]:
        """Test system scalability by gradually increasing concurrent users"""
        
        print(f"Testing system scalability: incrementing from {user_increment} to {max_users} users")
        
        scalability_results = []
        
        for num_users in range(user_increment, max_users + 1, user_increment):
            print(f"\n{'='*60}")
            print(f"TESTING WITH {num_users} CONCURRENT USERS")
            print(f"{'='*60}")
            
            try:
                result = await self.test_concurrent_analysis_workflows(
                    num_concurrent_users=num_users,
                    workflows_per_user=1  # Single workflow per user for scalability test
                )
                
                scalability_results.append(result)
                self.print_integration_result(result)
                
                # Wait between scalability steps
                if num_users < max_users:
                    print(f"\n⏳ Waiting 30 seconds before testing {num_users + user_increment} users...")
                    await asyncio.sleep(30)
                
                # Stop if error rate gets too high
                if result.error_rate > 50:
                    print(f"\n⚠️  Stopping scalability test due to high error rate: {result.error_rate:.1f}%")
                    break
                    
            except Exception as e:
                print(f"❌ Scalability test failed at {num_users} users: {str(e)}")
                break
        
        return scalability_results
    
    async def test_sustained_load(self, num_users: int = 20, 
                                duration_minutes: int = 10) -> SystemIntegrationResult:
        """Test system performance under sustained load"""
        
        print(f"Testing sustained load: {num_users} users for {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        all_workflow_results = []
        
        while time.time() < end_time:
            # Run a batch of workflows
            batch_result = await self.test_concurrent_analysis_workflows(
                num_concurrent_users=num_users,
                workflows_per_user=1
            )
            
            all_workflow_results.extend(batch_result.workflow_results)
            
            print(f"Batch completed: {batch_result.successful_workflows}/{batch_result.total_workflows} successful, "
                  f"error rate: {batch_result.error_rate:.1f}%")
            
            # Wait before next batch
            remaining_time = end_time - time.time()
            if remaining_time > 60:  # If more than 1 minute remaining
                await asyncio.sleep(30)  # Wait 30 seconds between batches
            else:
                break
        
        final_duration = time.time() - start_time
        
        # Aggregate all results
        total_workflows = len(all_workflow_results)
        successful_workflows = sum(1 for r in all_workflow_results if r.success)
        failed_workflows = total_workflows - successful_workflows
        
        # Calculate statistics across all workflows
        completion_times = [r.analysis_completion_time for r in all_workflow_results 
                           if r.success and r.analysis_completion_time is not None]
        
        if completion_times:
            average_completion_time = statistics.mean(completion_times)
            p95_completion_time = (statistics.quantiles(completion_times, n=20)[18] 
                                 if len(completion_times) >= 20 else max(completion_times))
        else:
            average_completion_time = 0
            p95_completion_time = 0
        
        error_rate = (failed_workflows / total_workflows * 100) if total_workflows > 0 else 0
        system_throughput = (successful_workflows / final_duration * 60) if final_duration > 0 else 0
        
        return SystemIntegrationResult(
            test_name=f"Sustained Load ({duration_minutes} minutes)",
            total_workflows=total_workflows,
            successful_workflows=successful_workflows,
            failed_workflows=failed_workflows,
            workflow_results=all_workflow_results,
            average_completion_time=average_completion_time,
            p95_completion_time=p95_completion_time,
            api_response_stats={},  # Could be calculated if needed
            websocket_stats={},     # Could be calculated if needed
            concurrent_user_capacity=num_users,
            system_throughput=system_throughput,
            error_rate=error_rate,
            test_duration=final_duration
        )
    
    def print_integration_result(self, result: SystemIntegrationResult):
        """Print detailed integration test results"""
        
        print(f"\n{'='*60}")
        print(f"SYSTEM INTEGRATION RESULT: {result.test_name}")
        print(f"{'='*60}")
        
        print(f"Test Duration: {result.test_duration:.2f} seconds")
        print(f"Concurrent Users: {result.concurrent_user_capacity}")
        print(f"Total Workflows: {result.total_workflows}")
        print(f"Successful Workflows: {result.successful_workflows}")
        print(f"Failed Workflows: {result.failed_workflows}")
        print(f"Success Rate: {((result.successful_workflows/result.total_workflows)*100):.1f}%")
        print(f"Error Rate: {result.error_rate:.2f}%")
        print(f"System Throughput: {result.system_throughput:.2f} workflows/minute")
        
        print(f"\nAnalysis Completion Times:")
        print(f"  Average: {result.average_completion_time:.2f} seconds")
        print(f"  95th Percentile: {result.p95_completion_time:.2f} seconds")
        
        if result.api_response_stats:
            stats = result.api_response_stats
            print(f"\nAPI Response Times:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  95th Percentile: {stats['p95']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
        
        if result.websocket_stats:
            stats = result.websocket_stats
            print(f"\nWebSocket Connection Times:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  Median: {stats['median']:.2f}ms")
            print(f"  95th Percentile: {stats['p95']:.2f}ms")
            print(f"  Max: {stats['max']:.2f}ms")
        
        # Target analysis
        print(f"\n{'='*60}")
        print("TARGET ANALYSIS")
        print(f"{'='*60}")
        
        if result.p95_completion_time <= targets.analysis_time_10_articles:
            print(f"✅ Analysis completion P95: {result.p95_completion_time:.2f}s "
                  f"(target: {targets.analysis_time_10_articles}s)")
        else:
            print(f"❌ Analysis completion P95: {result.p95_completion_time:.2f}s "
                  f"(target: {targets.analysis_time_10_articles}s)")
        
        if result.concurrent_user_capacity >= targets.max_concurrent_users:
            print(f"✅ Concurrent users: {result.concurrent_user_capacity} "
                  f"(target: {targets.max_concurrent_users})")
        else:
            print(f"❌ Concurrent users: {result.concurrent_user_capacity} "
                  f"(target: {targets.max_concurrent_users})")
        
        if result.error_rate <= 5.0:  # 5% error rate threshold
            print(f"✅ Error rate: {result.error_rate:.2f}% (threshold: 5%)")
        else:
            print(f"❌ Error rate: {result.error_rate:.2f}% (threshold: 5%)")
        
        # Sample failures for debugging
        failed_workflows = [r for r in result.workflow_results if not r.success]
        if failed_workflows:
            print(f"\nSample Failures (first 5):")
            for failure in failed_workflows[:5]:
                print(f"  - Status: {failure.final_status}, Error: {failure.error_message}")


async def run_full_system_performance_tests():
    """Run comprehensive full system integration performance tests"""
    
    print("🚀 Starting comprehensive full system integration performance testing...")
    
    async with FullSystemPerformanceTester() as tester:
        all_results = []
        
        # Test 1: Basic concurrent workflows
        print(f"\n{'='*80}")
        print("TEST 1: BASIC CONCURRENT WORKFLOWS")
        print(f"{'='*80}")
        
        basic_result = await tester.test_concurrent_analysis_workflows(
            num_concurrent_users=10, workflows_per_user=2
        )
        all_results.append(basic_result)
        tester.print_integration_result(basic_result)
        
        await asyncio.sleep(30)  # Wait between tests
        
        # Test 2: System scalability
        print(f"\n{'='*80}")
        print("TEST 2: SYSTEM SCALABILITY")
        print(f"{'='*80}")
        
        scalability_results = await tester.test_system_scalability(
            max_users=30, user_increment=5
        )
        all_results.extend(scalability_results)
        
        await asyncio.sleep(60)  # Longer wait before sustained load test
        
        # Test 3: Sustained load
        print(f"\n{'='*80}")
        print("TEST 3: SUSTAINED LOAD")
        print(f"{'='*80}")
        
        sustained_result = await tester.test_sustained_load(
            num_users=15, duration_minutes=5  # Reduced for demo
        )
        all_results.append(sustained_result)
        tester.print_integration_result(sustained_result)
        
        # Export results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"full_system_performance_results_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in all_results:
            json_result = {
                "test_name": result.test_name,
                "total_workflows": result.total_workflows,
                "successful_workflows": result.successful_workflows,
                "failed_workflows": result.failed_workflows,
                "average_completion_time": result.average_completion_time,
                "p95_completion_time": result.p95_completion_time,
                "api_response_stats": result.api_response_stats,
                "websocket_stats": result.websocket_stats,
                "concurrent_user_capacity": result.concurrent_user_capacity,
                "system_throughput": result.system_throughput,
                "error_rate": result.error_rate,
                "test_duration": result.test_duration,
                "workflow_summary": [
                    {
                        "session_id": w.session_id,
                        "success": w.success,
                        "total_duration": w.total_duration,
                        "analysis_completion_time": w.analysis_completion_time,
                        "final_status": w.final_status,
                        "error_message": w.error_message
                    }
                    for w in result.workflow_results
                ]
            }
            json_results.append(json_result)
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Full system performance test results exported to: {results_file}")
        
        return all_results


if __name__ == "__main__":
    asyncio.run(run_full_system_performance_tests())