#!/usr/bin/env python3
"""
Script to run comprehensive API load tests with different scenarios
"""
import subprocess
import sys
import time
import argparse
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import scenarios


def run_locust_test(scenario_name: str, scenario_config: dict, output_dir: str = "reports"):
    """Run a single Locust test scenario"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for unique file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare output files
    html_report = f"{output_dir}/locust_report_{scenario_name}_{timestamp}.html"
    csv_prefix = f"{output_dir}/locust_stats_{scenario_name}_{timestamp}"
    
    # Build Locust command
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "--users", str(scenario_config["users"]),
        "--spawn-rate", str(scenario_config["spawn_rate"]),
        "--run-time", f"{scenario_config['duration']}s",
        "--html", html_report,
        "--csv", csv_prefix,
        "--host", "http://localhost:8000"
    ]
    
    print(f"\n{'='*60}")
    print(f"Running {scenario_name}: {scenario_config['description']}")
    print(f"{'='*60}")
    print(f"Users: {scenario_config['users']}")
    print(f"Spawn Rate: {scenario_config['spawn_rate']} users/second")
    print(f"Duration: {scenario_config['duration']} seconds")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        # Run the test
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        end_time = time.time()
        
        print(f"\n✅ Test completed in {end_time - start_time:.2f} seconds")
        print(f"HTML Report: {html_report}")
        print(f"CSV Stats: {csv_prefix}_stats.csv")
        
        # Print Locust output
        if result.stdout:
            print("\n--- Locust Output ---")
            print(result.stdout)
        
        if result.stderr:
            print("\n--- Locust Errors ---")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def run_stress_test_user_class(user_class: str, users: int, spawn_rate: int, 
                              duration: int, output_dir: str = "reports"):
    """Run test with specific user class"""
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html_report = f"{output_dir}/locust_report_{user_class}_{timestamp}.html"
    csv_prefix = f"{output_dir}/locust_stats_{user_class}_{timestamp}"
    
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "--user-classes", user_class,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", f"{duration}s",
        "--html", html_report,
        "--csv", csv_prefix,
        "--host", "http://localhost:8000"
    ]
    
    print(f"\n{'='*60}")
    print(f"Running stress test with {user_class}")
    print(f"{'='*60}")
    print(f"Users: {users}")
    print(f"Spawn Rate: {spawn_rate} users/second")
    print(f"Duration: {duration} seconds")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        end_time = time.time()
        
        print(f"\n✅ Test completed in {end_time - start_time:.2f} seconds")
        print(f"HTML Report: {html_report}")
        
        if result.stdout:
            print("\n--- Locust Output ---")
            print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def run_all_scenarios():
    """Run all predefined test scenarios"""
    
    print("🚀 Starting comprehensive API load testing...")
    
    # Standard load test scenarios
    scenario_tests = [
        ("light_load", scenarios.light_load),
        ("medium_load", scenarios.medium_load),
        ("heavy_load", scenarios.heavy_load),
        ("stress_test", scenarios.stress_test)
    ]
    
    results = {}
    
    for scenario_name, scenario_config in scenario_tests:
        success = run_locust_test(scenario_name, scenario_config)
        results[scenario_name] = success
        
        # Wait between tests to allow system recovery
        if scenario_name != scenario_tests[-1][0]:  # Not the last test
            print("\n⏳ Waiting 30 seconds before next test...")
            time.sleep(30)
    
    # High volume stress tests
    print(f"\n{'='*60}")
    print("RUNNING SPECIALIZED STRESS TESTS")
    print(f"{'='*60}")
    
    # High volume user test
    success = run_stress_test_user_class("HighVolumeAPIUser", 50, 10, 180)
    results["high_volume_stress"] = success
    
    time.sleep(30)
    
    # Concurrent analysis test
    success = run_stress_test_user_class("ConcurrentAnalysisUser", 20, 5, 300)
    results["concurrent_analysis"] = success
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20}: {status}")
    
    total_passed = sum(results.values())
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    return all(results.values())


def main():
    parser = argparse.ArgumentParser(description="Run API performance tests")
    parser.add_argument("--scenario", choices=["light", "medium", "heavy", "stress", "all"],
                       default="all", help="Test scenario to run")
    parser.add_argument("--users", type=int, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, help="User spawn rate per second")
    parser.add_argument("--duration", type=int, help="Test duration in seconds")
    parser.add_argument("--user-class", choices=["MarketAnalysisAPIUser", "HighVolumeAPIUser", "ConcurrentAnalysisUser"],
                       help="Specific user class to test")
    parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Check if Locust is installed
    try:
        subprocess.run(["locust", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Locust is not installed. Install it with: pip install locust")
        sys.exit(1)
    
    # Check if backend is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend health check failed. Make sure the API server is running on localhost:8000")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend. Make sure the API server is running on localhost:8000")
        sys.exit(1)
    
    print("✅ Backend is running and accessible")
    
    if args.scenario == "all":
        success = run_all_scenarios()
        sys.exit(0 if success else 1)
    
    elif args.user_class:
        # Custom test with specific user class
        users = args.users or 25
        spawn_rate = args.spawn_rate or 2
        duration = args.duration or 180
        
        success = run_stress_test_user_class(args.user_class, users, spawn_rate, duration, args.output_dir)
        sys.exit(0 if success else 1)
    
    else:
        # Individual scenario
        scenario_map = {
            "light": scenarios.light_load,
            "medium": scenarios.medium_load,
            "heavy": scenarios.heavy_load,
            "stress": scenarios.stress_test
        }
        
        if args.scenario in scenario_map:
            success = run_locust_test(args.scenario, scenario_map[args.scenario], args.output_dir)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown scenario: {args.scenario}")
            sys.exit(1)


if __name__ == "__main__":
    main()