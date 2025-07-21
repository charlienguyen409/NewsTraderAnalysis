#!/usr/bin/env python3
"""
Integration Test Runner

This script runs the complete integration test suite with proper Docker
environment setup and cleanup.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

def check_docker():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def cleanup_test_containers():
    """Clean up any existing test containers"""
    containers = [
        "test_postgres_integration",
        "test_redis_integration"
    ]
    
    for container in containers:
        try:
            subprocess.run(
                ["docker", "container", "stop", container],
                capture_output=True,
                timeout=10
            )
            subprocess.run(
                ["docker", "container", "rm", container],
                capture_output=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout stopping container {container}")

def run_integration_tests(test_pattern=None, verbose=False, coverage=False):
    """Run integration tests with proper setup"""
    
    # Check prerequisites
    if not check_docker():
        print("Error: Docker is not available or not running")
        print("Please install Docker and ensure it's running")
        return 1
    
    # Clean up any existing containers
    print("Cleaning up existing test containers...")
    cleanup_test_containers()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent / "test_workflows.py"
    cmd.append(str(test_dir))
    
    # Add test pattern if specified
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(backend_dir),
        "TESTING": "true",
        "DATABASE_URL": "postgresql://test_user:test_password@localhost:5433/test_market_analysis",
        "REDIS_URL": "redis://localhost:6380"
    })
    
    print(f"Running integration tests...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {backend_dir}")
    print()
    
    # Run tests
    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            env=env,
            timeout=600  # 10 minutes timeout
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print("Error: Integration tests timed out")
        return 1
    except KeyboardInterrupt:
        print("\\nTests interrupted by user")
        return 1
    finally:
        # Clean up containers
        print("\\nCleaning up test containers...")
        cleanup_test_containers()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        "-k", "--pattern",
        help="Only run tests matching this pattern"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List available test classes and methods"
    )
    
    args = parser.parse_args()
    
    if args.list_tests:
        print("Available Integration Test Classes:")
        print("==================================")
        print("TestCompleteAnalysisWorkflows:")
        print("  - test_complete_analysis_workflow_success")
        print("  - test_headline_analysis_workflow_success")
        print("  - test_analysis_workflow_with_no_articles")
        print()
        print("TestAPIIntegrationWithRealisticDataFlows:")
        print("  - test_articles_api_with_filtering_and_pagination")
        print("  - test_positions_api_with_session_filtering")
        print("  - test_market_summary_api_with_real_data")
        print("  - test_activity_logs_api_with_filtering")
        print()
        print("TestServiceIntegration:")
        print("  - test_llm_service_integration_with_analysis_service")
        print("  - test_cache_service_integration")
        print("  - test_database_service_integration")
        print()
        print("TestWebSocketIntegration:")
        print("  - test_websocket_connection_and_subscription")
        print("  - test_websocket_analysis_updates")
        print("  - test_websocket_error_handling")
        print("  - test_websocket_concurrent_connections")
        print()
        print("TestErrorHandlingIntegration:")
        print("  - test_llm_service_error_propagation")
        print("  - test_database_error_handling")
        print("  - test_timeout_handling")
        print("  - test_fallback_mechanisms")
        print()
        print("TestPerformanceIntegration:")
        print("  - test_concurrent_analysis_sessions")
        print("  - test_large_dataset_handling")
        print("  - test_memory_usage_monitoring")
        print()
        print("TestDatabaseTransactionIntegration:")
        print("  - test_transaction_rollback_on_error")
        print("  - test_concurrent_transaction_handling")
        print("  - test_foreign_key_constraint_handling")
        print()
        print("Example usage:")
        print("  python run_integration_tests.py -k TestCompleteAnalysisWorkflows")
        print("  python run_integration_tests.py -k test_complete_analysis_workflow_success")
        print("  python run_integration_tests.py --coverage")
        return 0
    
    # Run the tests
    exit_code = run_integration_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())