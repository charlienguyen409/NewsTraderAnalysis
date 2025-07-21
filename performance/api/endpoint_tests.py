"""
Individual endpoint performance testing
"""
import asyncio
import httpx
import time
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator
from utils.metrics import performance_collector


@dataclass
class EndpointTestResult:
    """Result of an endpoint performance test"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class EndpointPerformanceTester:
    """Test individual API endpoints for performance"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_endpoint(self, method: str, endpoint: str, 
                          payload: Optional[Dict] = None,
                          params: Optional[Dict] = None,
                          num_requests: int = 100,
                          concurrent_requests: int = 10) -> EndpointTestResult:
        """Test a single endpoint with multiple requests"""
        
        print(f"Testing {method} {endpoint} - {num_requests} requests, {concurrent_requests} concurrent")
        
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        start_time = time.time()
        
        # Create batches of concurrent requests
        batch_size = concurrent_requests
        num_batches = (num_requests + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min((batch_num + 1) * batch_size, num_requests)
            batch_requests = batch_end - batch_start
            
            # Create tasks for this batch
            tasks = []
            for i in range(batch_requests):
                task = asyncio.create_task(
                    self._make_request(method, endpoint, payload, params)
                )
                tasks.append(task)
            
            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                    errors.append(str(result))
                else:
                    response_time, status_code, error = result
                    response_times.append(response_time)
                    
                    if 200 <= status_code < 400:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        if error:
                            errors.append(error)
            
            # Small delay between batches to avoid overwhelming the server
            if batch_num < num_batches - 1:
                await asyncio.sleep(0.1)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        error_rate = (failed_requests / num_requests) * 100 if num_requests > 0 else 0
        
        return EndpointTestResult(
            endpoint=endpoint,
            method=method,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]  # Keep only first 10 errors
        )
    
    async def _make_request(self, method: str, endpoint: str, 
                          payload: Optional[Dict] = None,
                          params: Optional[Dict] = None) -> tuple:
        """Make a single HTTP request and measure response time"""
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=payload, params=params)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=payload, params=params)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return response_time, response.status_code, None
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time, 0, str(e)
    
    async def test_all_endpoints(self, num_requests: int = 50, 
                               concurrent_requests: int = 5) -> Dict[str, EndpointTestResult]:
        """Test all major API endpoints"""
        
        print(f"Testing all endpoints with {num_requests} requests each, {concurrent_requests} concurrent")
        
        # Define endpoints to test
        endpoint_tests = [
            ("GET", "/", None, None),
            ("GET", "/health", None, None),
            ("GET", "/api/v1/articles/", None, {"limit": 20}),
            ("GET", "/api/v1/articles/", None, {"ticker": "AAPL", "limit": 10}),
            ("GET", "/api/v1/positions/", None, None),
            ("GET", "/api/v1/positions/", None, {"ticker": "AAPL"}),
            ("GET", "/api/v1/analysis/market-summary", None, None),
            ("GET", "/api/v1/activity-logs/", None, {"limit": 50}),
            ("GET", "/api/v1/models", None, None),
            ("POST", "/api/v1/analysis/start", test_data_generator.generate_analysis_request(), None),
            ("POST", "/api/v1/analysis/headlines", test_data_generator.generate_analysis_request(), None),
        ]
        
        results = {}
        
        for method, endpoint, payload, params in endpoint_tests:
            test_name = f"{method} {endpoint}"
            if params:
                test_name += f" {params}"
            
            try:
                result = await self.test_endpoint(
                    method, endpoint, payload, params, 
                    num_requests, concurrent_requests
                )
                results[test_name] = result
                
                # Print immediate results
                print(f"✅ {test_name}: {result.average_response_time:.2f}ms avg, "
                      f"{result.requests_per_second:.2f} req/s, {result.error_rate:.1f}% errors")
                
            except Exception as e:
                print(f"❌ {test_name}: Failed with error: {e}")
                
            # Small delay between endpoint tests
            await asyncio.sleep(1)
        
        return results
    
    def print_summary(self, results: Dict[str, EndpointTestResult]):
        """Print a comprehensive summary of test results"""
        
        print(f"\n{'='*80}")
        print("ENDPOINT PERFORMANCE TEST SUMMARY")
        print(f"{'='*80}")
        
        # Overall statistics
        total_requests = sum(r.total_requests for r in results.values())
        total_successful = sum(r.successful_requests for r in results.values())
        total_failed = sum(r.failed_requests for r in results.values())
        overall_error_rate = (total_failed / total_requests * 100) if total_requests > 0 else 0
        
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {total_successful}")
        print(f"Failed: {total_failed}")
        print(f"Overall Error Rate: {overall_error_rate:.2f}%")
        
        print(f"\n{'Endpoint':<40} {'Avg (ms)':<10} {'P95 (ms)':<10} {'RPS':<8} {'Errors':<8}")
        print(f"{'-'*40} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
        
        for endpoint, result in results.items():
            print(f"{endpoint:<40} {result.average_response_time:<10.2f} "
                  f"{result.p95_response_time:<10.2f} {result.requests_per_second:<8.2f} "
                  f"{result.error_rate:<8.1f}%")
        
        # Performance target analysis
        print(f"\n{'='*80}")
        print("PERFORMANCE TARGET ANALYSIS")
        print(f"{'='*80}")
        
        targets_met = 0
        total_targets = 0
        
        for endpoint, result in results.items():
            total_targets += 1
            
            # Check response time target
            if result.p95_response_time <= targets.api_response_time_95th:
                print(f"✅ {endpoint}: P95 response time {result.p95_response_time:.2f}ms "
                      f"(target: {targets.api_response_time_95th}ms)")
                targets_met += 1
            else:
                print(f"❌ {endpoint}: P95 response time {result.p95_response_time:.2f}ms "
                      f"(target: {targets.api_response_time_95th}ms)")
        
        print(f"\nTargets Met: {targets_met}/{total_targets} ({targets_met/total_targets*100:.1f}%)")
        
        # Error analysis
        if any(result.errors for result in results.values()):
            print(f"\n{'='*80}")
            print("ERROR ANALYSIS")
            print(f"{'='*80}")
            
            for endpoint, result in results.items():
                if result.errors:
                    print(f"\n{endpoint}:")
                    for error in result.errors:
                        print(f"  - {error}")


async def run_endpoint_performance_tests():
    """Run comprehensive endpoint performance tests"""
    
    print("🚀 Starting comprehensive endpoint performance testing...")
    
    async with EndpointPerformanceTester() as tester:
        # Test with different load levels
        test_scenarios = [
            ("Light Load", 25, 5),
            ("Medium Load", 50, 10),
            ("Heavy Load", 100, 20),
        ]
        
        all_results = {}
        
        for scenario_name, num_requests, concurrent in test_scenarios:
            print(f"\n{'='*60}")
            print(f"RUNNING {scenario_name.upper()}")
            print(f"{'='*60}")
            
            results = await tester.test_all_endpoints(num_requests, concurrent)
            all_results[scenario_name] = results
            
            tester.print_summary(results)
            
            # Save results to file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"endpoint_test_{scenario_name.lower().replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                # Convert results to JSON-serializable format
                json_results = {}
                for endpoint, result in results.items():
                    json_results[endpoint] = {
                        "endpoint": result.endpoint,
                        "method": result.method,
                        "total_requests": result.total_requests,
                        "successful_requests": result.successful_requests,
                        "failed_requests": result.failed_requests,
                        "average_response_time": result.average_response_time,
                        "median_response_time": result.median_response_time,
                        "p95_response_time": result.p95_response_time,
                        "p99_response_time": result.p99_response_time,
                        "min_response_time": result.min_response_time,
                        "max_response_time": result.max_response_time,
                        "requests_per_second": result.requests_per_second,
                        "error_rate": result.error_rate,
                        "errors": result.errors
                    }
                
                json.dump(json_results, f, indent=2)
            
            print(f"\nResults saved to: {filename}")
            
            # Wait between scenarios
            if scenario_name != test_scenarios[-1][0]:
                print("\n⏳ Waiting 30 seconds before next scenario...")
                await asyncio.sleep(30)
        
        return all_results


if __name__ == "__main__":
    asyncio.run(run_endpoint_performance_tests())