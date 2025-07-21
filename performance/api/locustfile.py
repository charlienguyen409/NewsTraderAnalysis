"""
Locust load testing configuration for Market News Analysis API
"""
import random
import json
import uuid
from locust import HttpUser, task, between, events
from locust.env import Environment
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, targets
from utils.test_data import test_data_generator
from utils.metrics import performance_collector


class MarketAnalysisAPIUser(HttpUser):
    """Locust user simulating typical API usage patterns"""
    
    wait_time = between(config.MIN_WAIT_TIME / 1000, config.MAX_WAIT_TIME / 1000)
    host = config.API_BASE_URL
    
    def on_start(self):
        """Setup for each user session"""
        self.session_id = None
        self.analysis_sessions = []
        
        # Start performance collection
        performance_collector.start_collection()
    
    def on_stop(self):
        """Cleanup for each user session"""
        performance_collector.stop_collection()
    
    @task(10)
    def get_health_check(self):
        """Health check endpoint - highest frequency"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(8)
    def get_root(self):
        """Root endpoint check"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Root endpoint failed: {response.status_code}")
    
    @task(15)
    def list_articles(self):
        """List articles with various parameters"""
        params = {}
        
        # Add random parameters
        if random.choice([True, False]):
            params['limit'] = random.randint(10, 50)
        
        if random.choice([True, False]):
            params['ticker'] = random.choice(config.SAMPLE_TICKERS)
        
        if random.choice([True, False]):
            params['source'] = random.choice([
                "finviz.com", "biztoc.com", "yahoo.com", "marketwatch.com"
            ])
        
        with self.client.get("/api/v1/articles/", params=params, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Invalid response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Articles list failed: {response.status_code}")
    
    @task(12)
    def list_positions(self):
        """List positions with filters"""
        params = {}
        
        if random.choice([True, False]):
            params['ticker'] = random.choice(config.SAMPLE_TICKERS)
        
        if random.choice([True, False]):
            params['position_type'] = random.choice([
                "STRONG_BUY", "BUY", "HOLD", "SHORT", "STRONG_SHORT"
            ])
        
        with self.client.get("/api/v1/positions/", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Positions list failed: {response.status_code}")
    
    @task(10)
    def get_market_summary(self):
        """Get market summary"""
        with self.client.get("/api/v1/analysis/market-summary", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "summary" in data or "error" in data:
                        response.success()
                    else:
                        response.failure("Invalid market summary format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Market summary failed: {response.status_code}")
    
    @task(5)
    def start_analysis(self):
        """Start a new analysis"""
        request_data = test_data_generator.generate_analysis_request()
        
        with self.client.post(
            "/api/v1/analysis/start",
            json=request_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                        self.analysis_sessions.append(self.session_id)
                        response.success()
                    else:
                        response.failure("No session_id in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Analysis start failed: {response.status_code}")
    
    @task(3)
    def start_headline_analysis(self):
        """Start headline-only analysis"""
        request_data = test_data_generator.generate_analysis_request()
        
        with self.client.post(
            "/api/v1/analysis/headlines",
            json=request_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                        self.analysis_sessions.append(self.session_id)
                        response.success()
                    else:
                        response.failure("No session_id in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Headline analysis start failed: {response.status_code}")
    
    @task(8)
    def check_analysis_status(self):
        """Check analysis status"""
        if self.analysis_sessions:
            session_id = random.choice(self.analysis_sessions)
            
            with self.client.get(
                f"/api/v1/analysis/status/{session_id}/",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "status" in data:
                            response.success()
                        else:
                            response.failure("No status in response")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
                else:
                    response.failure(f"Status check failed: {response.status_code}")
    
    @task(6)
    def list_activity_logs(self):
        """List activity logs"""
        params = {}
        
        if random.choice([True, False]):
            params['limit'] = random.randint(10, 100)
        
        if self.analysis_sessions and random.choice([True, False]):
            params['session_id'] = random.choice(self.analysis_sessions)
        
        with self.client.get("/api/v1/activity-logs/", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Activity logs failed: {response.status_code}")
    
    @task(4)
    def get_models_config(self):
        """Get available models configuration"""
        with self.client.get("/api/v1/models", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "models" in data:
                        response.success()
                    else:
                        response.failure("No models in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Models config failed: {response.status_code}")


class HighVolumeAPIUser(HttpUser):
    """High volume user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Much shorter wait times
    host = config.API_BASE_URL
    
    @task(20)
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/health")
    
    @task(15)
    def rapid_article_requests(self):
        """Rapid article list requests"""
        params = {
            'limit': random.randint(5, 20),
            'ticker': random.choice(config.SAMPLE_TICKERS)
        }
        self.client.get("/api/v1/articles/", params=params)
    
    @task(10)
    def rapid_position_requests(self):
        """Rapid position requests"""
        params = {'ticker': random.choice(config.SAMPLE_TICKERS)}
        self.client.get("/api/v1/positions/", params=params)
    
    @task(5)
    def rapid_market_summary_requests(self):
        """Rapid market summary requests"""
        self.client.get("/api/v1/analysis/market-summary")


class ConcurrentAnalysisUser(HttpUser):
    """User focused on concurrent analysis operations"""
    
    wait_time = between(1, 3)
    host = config.API_BASE_URL
    
    def on_start(self):
        self.active_sessions = []
    
    @task(20)
    def start_multiple_analyses(self):
        """Start multiple concurrent analyses"""
        for _ in range(random.randint(1, 3)):
            request_data = test_data_generator.generate_analysis_request()
            response = self.client.post("/api/v1/analysis/start", json=request_data)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "session_id" in data:
                        self.active_sessions.append(data["session_id"])
                except json.JSONDecodeError:
                    pass
    
    @task(30)
    def monitor_analysis_progress(self):
        """Monitor multiple analysis sessions"""
        if self.active_sessions:
            # Check up to 5 random sessions
            sessions_to_check = random.sample(
                self.active_sessions, 
                min(5, len(self.active_sessions))
            )
            
            for session_id in sessions_to_check:
                self.client.get(f"/api/v1/analysis/status/{session_id}/")


# Event handlers for metrics collection
@events.request.add_listener
def record_request_metrics(request_type, name, response_time, response_length, exception, **kwargs):
    """Record request metrics for performance analysis"""
    status_code = getattr(exception, 'response', {}).get('status_code', 0) if exception else 200
    error_msg = str(exception) if exception else None
    
    performance_collector.record_response_time(
        url=name,
        method=request_type,
        response_time=response_time,
        status_code=status_code,
        error=error_msg
    )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize performance collection when test starts"""
    print("Starting performance collection...")
    performance_collector.start_collection()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate performance report when test stops"""
    print("Generating performance report...")
    
    report = performance_collector.generate_report()
    
    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test Duration: {report['test_duration']:.2f} seconds")
    print(f"Total Requests: {report['total_requests']}")
    print(f"Total Errors: {report['total_errors']}")
    print(f"Error Rate: {report['error_rate']:.2f}%")
    print(f"Throughput: {report['throughput_rps']:.2f} requests/second")
    
    if report['response_time_stats']:
        stats = report['response_time_stats']
        print(f"\nResponse Time Statistics:")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  95th Percentile: {stats['p95']:.2f}ms")
        print(f"  99th Percentile: {stats['p99']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
    
    if report['resource_stats']:
        cpu_stats = report['resource_stats'].get('cpu', {})
        memory_stats = report['resource_stats'].get('memory', {})
        print(f"\nResource Usage:")
        print(f"  CPU Mean: {cpu_stats.get('mean', 0):.1f}%")
        print(f"  CPU Max: {cpu_stats.get('max', 0):.1f}%")
        print(f"  Memory Mean: {memory_stats.get('mean', 0):.1f}MB")
        print(f"  Memory Max: {memory_stats.get('max', 0):.1f}MB")
    
    # Export detailed results
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_report_{timestamp}.json"
    performance_collector.export_to_json(filename)
    print(f"\nDetailed report exported to: {filename}")
    
    # Check if targets were met
    print(f"\n{'='*60}")
    print("TARGET ANALYSIS")
    print(f"{'='*60}")
    
    if report['response_time_stats']:
        p95_time = report['response_time_stats']['p95']
        if p95_time <= targets.api_response_time_95th:
            print(f"✅ 95th percentile response time: {p95_time:.2f}ms (target: {targets.api_response_time_95th}ms)")
        else:
            print(f"❌ 95th percentile response time: {p95_time:.2f}ms (target: {targets.api_response_time_95th}ms)")
    
    if report['throughput_rps'] >= targets.api_requests_per_second:
        print(f"✅ Throughput: {report['throughput_rps']:.2f} req/s (target: {targets.api_requests_per_second} req/s)")
    else:
        print(f"❌ Throughput: {report['throughput_rps']:.2f} req/s (target: {targets.api_requests_per_second} req/s)")
    
    if report['error_rate'] <= 5.0:  # 5% error rate threshold
        print(f"✅ Error rate: {report['error_rate']:.2f}% (threshold: 5%)")
    else:
        print(f"❌ Error rate: {report['error_rate']:.2f}% (threshold: 5%)")


if __name__ == "__main__":
    # This allows running the locustfile directly for testing
    print("Use 'locust -f locustfile.py' to run the load tests")
    print("Available user classes:")
    print("  - MarketAnalysisAPIUser (default)")
    print("  - HighVolumeAPIUser (stress testing)")  
    print("  - ConcurrentAnalysisUser (concurrent operations)")