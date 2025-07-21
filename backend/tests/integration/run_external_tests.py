#!/usr/bin/env python3
"""
Test runner for external service integration tests.

This script provides comprehensive testing of external service integrations including:
- Web scraping services (FinViz, BizToc, RSS feeds)
- LLM service integration (OpenAI, Anthropic)
- Rate limiting and retry mechanisms
- Redis caching integration
- Error handling and fallback scenarios
- Performance and reliability testing

Usage:
    python run_external_tests.py [options]
    
Options:
    --verbose       Enable verbose output
    --coverage      Run with coverage reporting
    --performance   Run performance tests
    --load-test     Run load tests
    --mock-only     Run only mock tests (no real API calls)
    --real-api      Run tests with real API calls (requires valid API keys)
    --parallel      Run tests in parallel
    --timeout=N     Set test timeout in seconds (default: 60)
    --report        Generate HTML test report
"""

import os
import sys
import asyncio
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

# Add the backend app to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.mocks.external_service_mocks import (
    MockScenarios,
    MockExternalService,
    MockServiceConfig,
    ServiceStatus,
    create_mock_environment,
    simulate_load_test
)


class TestRunner:
    """Test runner for external service integration tests"""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.setup_logging()
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('tests/integration/external_tests.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all external service integration tests"""
        self.logger.info("Starting external service integration tests")
        self.start_time = time.time()
        
        try:
            # Run different test categories
            if self.args.mock_only:
                self.run_mock_tests()
            elif self.args.real_api:
                self.run_real_api_tests()
            else:
                self.run_standard_tests()
            
            if self.args.performance:
                self.run_performance_tests()
            
            if self.args.load_test:
                self.run_load_tests()
            
            self.end_time = time.time()
            return self.generate_test_report()
            
        except Exception as e:
            self.logger.error(f"Test run failed: {e}")
            raise
    
    def run_standard_tests(self):
        """Run standard integration tests with mocking"""
        self.logger.info("Running standard integration tests")
        
        test_command = [
            "python", "-m", "pytest",
            "tests/integration/test_external.py",
            "-v",
            f"--timeout={self.args.timeout}",
            "--tb=short"
        ]
        
        if self.args.coverage:
            test_command.extend([
                "--cov=app.services",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing"
            ])
        
        if self.args.parallel:
            test_command.extend(["-n", "auto"])
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        self.test_results["standard_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        if result.returncode != 0:
            self.logger.error(f"Standard tests failed: {result.stderr}")
        else:
            self.logger.info("Standard tests passed")
    
    def run_mock_tests(self):
        """Run tests with full mocking (no external dependencies)"""
        self.logger.info("Running mock-only tests")
        
        test_command = [
            "python", "-m", "pytest",
            "tests/integration/test_external.py",
            "-v",
            "-k", "not real_api",
            "--tb=short"
        ]
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        self.test_results["mock_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_real_api_tests(self):
        """Run tests with real API calls (requires valid API keys)"""
        self.logger.info("Running real API tests")
        
        # Check for required API keys
        required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "REDIS_URL"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        
        if missing_keys:
            self.logger.error(f"Missing required environment variables: {missing_keys}")
            self.test_results["real_api_tests"] = {
                "returncode": 1,
                "error": f"Missing API keys: {missing_keys}"
            }
            return
        
        test_command = [
            "python", "-m", "pytest",
            "tests/integration/test_external.py",
            "-v",
            "-k", "real_api",
            "--tb=short"
        ]
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        self.test_results["real_api_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_performance_tests(self):
        """Run performance tests"""
        self.logger.info("Running performance tests")
        
        test_command = [
            "python", "-m", "pytest",
            "tests/integration/test_external.py::TestPerformanceAndReliability",
            "-v",
            "--tb=short"
        ]
        
        result = subprocess.run(test_command, capture_output=True, text=True)
        self.test_results["performance_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_load_tests(self):
        """Run load tests using mock services"""
        self.logger.info("Running load tests")
        
        # Create mock services for load testing
        scenarios = [
            ("healthy_services", MockScenarios.healthy_services()),
            ("degraded_services", MockScenarios.degraded_services()),
            ("rate_limited_services", MockScenarios.rate_limited_services())
        ]
        
        load_test_results = {}
        
        for scenario_name, scenario in scenarios:
            self.logger.info(f"Load testing scenario: {scenario_name}")
            
            # Create mock environment
            env = create_mock_environment(scenario)
            
            # Run load test on each service
            for service_name, service in scenario["services"].items():
                metrics = simulate_load_test(
                    service,
                    concurrent_requests=50,
                    duration=10.0
                )
                
                load_test_results[f"{scenario_name}_{service_name}"] = metrics
                self.logger.info(f"Load test results for {service_name}: {metrics}")
        
        self.test_results["load_tests"] = load_test_results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        duration = self.end_time - self.start_time if self.end_time else 0
        
        report = {
            "summary": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": duration,
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for result in self.test_results.values() 
                                  if result.get("returncode", 0) == 0),
                "failed_tests": sum(1 for result in self.test_results.values() 
                                  if result.get("returncode", 0) != 0)
            },
            "results": self.test_results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET",
                    "ANTHROPIC_API_KEY": "SET" if os.getenv("ANTHROPIC_API_KEY") else "NOT SET",
                    "REDIS_URL": "SET" if os.getenv("REDIS_URL") else "NOT SET"
                }
            }
        }
        
        # Save report to file
        if self.args.report:
            self.save_html_report(report)
        
        return report
    
    def save_html_report(self, report: Dict[str, Any]):
        """Save test report as HTML"""
        html_content = self.generate_html_report(report)
        
        report_file = Path("tests/integration/external_test_report.html")
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report saved to {report_file}")
    
    def generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML test report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>External Service Integration Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 15px; background-color: #e8f4f8; border-radius: 5px; }}
                .test-result {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .passed {{ border-left: 5px solid #4CAF50; }}
                .failed {{ border-left: 5px solid #f44336; }}
                .code {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
                pre {{ margin: 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>External Service Integration Test Report</h1>
                <p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Duration: {report['summary']['duration']:.2f} seconds</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Total Tests</h3>
                    <p>{report['summary']['total_tests']}</p>
                </div>
                <div class="metric">
                    <h3>Passed</h3>
                    <p>{report['summary']['passed_tests']}</p>
                </div>
                <div class="metric">
                    <h3>Failed</h3>
                    <p>{report['summary']['failed_tests']}</p>
                </div>
            </div>
            
            <h2>Test Results</h2>
        """
        
        for test_name, result in report["results"].items():
            status_class = "passed" if result.get("returncode", 0) == 0 else "failed"
            status_text = "PASSED" if result.get("returncode", 0) == 0 else "FAILED"
            
            html += f"""
            <div class="test-result {status_class}">
                <h3>{test_name.replace('_', ' ').title()} - {status_text}</h3>
            """
            
            if "stdout" in result:
                html += f"""
                <h4>Output:</h4>
                <div class="code"><pre>{result['stdout']}</pre></div>
                """
            
            if "stderr" in result and result["stderr"]:
                html += f"""
                <h4>Errors:</h4>
                <div class="code"><pre>{result['stderr']}</pre></div>
                """
            
            html += "</div>"
        
        html += """
            <h2>Environment</h2>
            <div class="code">
                <pre>{}</pre>
            </div>
        </body>
        </html>
        """.format(json.dumps(report["environment"], indent=2))
        
        return html
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "="*60)
        print("EXTERNAL SERVICE INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Duration: {report['summary']['duration']:.2f} seconds")
        print("="*60)
        
        if report['summary']['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            for test_name, result in report["results"].items():
                if result.get("returncode", 0) != 0:
                    print(f"  - {test_name}")
        else:
            print("\nAll tests passed! ✅")
        
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run external service integration tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--load-test", action="store_true", help="Run load tests")
    parser.add_argument("--mock-only", action="store_true", help="Run only mock tests")
    parser.add_argument("--real-api", action="store_true", help="Run tests with real API calls")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--timeout", type=int, default=60, help="Test timeout in seconds")
    parser.add_argument("--report", action="store_true", help="Generate HTML test report")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(args)
    
    try:
        # Run tests
        report = runner.run_all_tests()
        
        # Print summary
        runner.print_summary(report)
        
        # Exit with appropriate code
        sys.exit(0 if report['summary']['failed_tests'] == 0 else 1)
        
    except Exception as e:
        print(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()