#!/usr/bin/env python3
"""
Master script to run all performance tests and generate comprehensive report
"""
import asyncio
import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import config
from reports.dashboard import generate_performance_dashboard


class PerformanceTestRunner:
    """Orchestrates all performance tests and generates final report"""
    
    def __init__(self, test_level: str = "standard"):
        self.test_level = test_level
        self.start_time = time.time()
        self.results = {
            "api_tests": {"status": "pending", "duration": 0},
            "websocket_tests": {"status": "pending", "duration": 0},
            "database_tests": {"status": "pending", "duration": 0},
            "integration_tests": {"status": "pending", "duration": 0},
            "stress_tests": {"status": "pending", "duration": 0}
        }
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        
        print("🔍 Checking prerequisites...")
        
        # Check if backend is running
        try:
            import requests
            response = requests.get(f"{config.API_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Backend health check failed")
                return False
            print("✅ Backend is running and accessible")
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            return False
        
        # Check required Python packages
        required_packages = [
            "locust", "httpx", "websockets", "asyncpg", "aioredis",
            "matplotlib", "seaborn", "pandas", "numpy", "psutil"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print("Install them with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All required packages are installed")
        
        # Check if database is accessible
        try:
            import asyncpg
            
            async def check_db():
                conn = await asyncpg.connect(config.TEST_DATABASE_URL)
                await conn.execute("SELECT 1")
                await conn.close()
            
            asyncio.run(check_db())
            print("✅ Database is accessible")
        except Exception as e:
            print(f"⚠️  Database check failed: {e}")
            print("   Some tests may fail without database access")
        
        return True
    
    async def run_api_tests(self) -> bool:
        """Run API performance tests"""
        
        print(f"\n{'='*60}")
        print("RUNNING API PERFORMANCE TESTS")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            # Run endpoint tests
            from api.endpoint_tests import run_endpoint_performance_tests
            await run_endpoint_performance_tests()
            
            # Run Locust tests (in background)
            if self.test_level in ["comprehensive", "full"]:
                print("\n🔄 Running Locust load tests...")
                cmd = [
                    sys.executable, "api/run_load_tests.py", "--scenario", "medium"
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=Path(__file__).parent,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"⚠️  Locust tests had issues: {result.stderr}")
                else:
                    print("✅ Locust tests completed successfully")
            
            self.results["api_tests"]["status"] = "completed"
            return True
            
        except Exception as e:
            print(f"❌ API tests failed: {e}")
            self.results["api_tests"]["status"] = "failed"
            return False
        
        finally:
            self.results["api_tests"]["duration"] = time.time() - test_start
    
    async def run_websocket_tests(self) -> bool:
        """Run WebSocket performance tests"""
        
        print(f"\n{'='*60}")
        print("RUNNING WEBSOCKET PERFORMANCE TESTS")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            from websocket.websocket_tests import run_websocket_performance_tests
            await run_websocket_performance_tests()
            
            self.results["websocket_tests"]["status"] = "completed"
            return True
            
        except Exception as e:
            print(f"❌ WebSocket tests failed: {e}")
            self.results["websocket_tests"]["status"] = "failed"
            return False
        
        finally:
            self.results["websocket_tests"]["duration"] = time.time() - test_start
    
    async def run_database_tests(self) -> bool:
        """Run database performance tests"""
        
        print(f"\n{'='*60}")
        print("RUNNING DATABASE PERFORMANCE TESTS")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            from database.db_performance_tests import run_database_performance_tests
            await run_database_performance_tests()
            
            self.results["database_tests"]["status"] = "completed"
            return True
            
        except Exception as e:
            print(f"❌ Database tests failed: {e}")
            self.results["database_tests"]["status"] = "failed"
            return False
        
        finally:
            self.results["database_tests"]["duration"] = time.time() - test_start
    
    async def run_integration_tests(self) -> bool:
        """Run full system integration tests"""
        
        print(f"\n{'='*60}")
        print("RUNNING INTEGRATION PERFORMANCE TESTS")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            from integration.full_system_tests import run_full_system_performance_tests
            await run_full_system_performance_tests()
            
            self.results["integration_tests"]["status"] = "completed"
            return True
            
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            self.results["integration_tests"]["status"] = "failed"
            return False
        
        finally:
            self.results["integration_tests"]["duration"] = time.time() - test_start
    
    async def run_stress_tests(self) -> bool:
        """Run stress tests"""
        
        if self.test_level not in ["comprehensive", "full", "stress"]:
            print("⏭️  Skipping stress tests (not in test level)")
            self.results["stress_tests"]["status"] = "skipped"
            return True
        
        print(f"\n{'='*60}")
        print("RUNNING STRESS TESTS")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            from stress.stress_tests import run_comprehensive_stress_tests
            await run_comprehensive_stress_tests()
            
            self.results["stress_tests"]["status"] = "completed"
            return True
            
        except Exception as e:
            print(f"❌ Stress tests failed: {e}")
            self.results["stress_tests"]["status"] = "failed"
            return False
        
        finally:
            self.results["stress_tests"]["duration"] = time.time() - test_start
    
    async def run_all_tests(self) -> bool:
        """Run all performance tests"""
        
        print(f"🚀 Starting comprehensive performance test suite ({self.test_level} level)")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Aborting test run.")
            return False
        
        test_sequence = [
            ("API Tests", self.run_api_tests),
            ("WebSocket Tests", self.run_websocket_tests),
            ("Database Tests", self.run_database_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Stress Tests", self.run_stress_tests)
        ]
        
        successful_tests = 0
        total_tests = len(test_sequence)
        
        for test_name, test_func in test_sequence:
            print(f"\n📋 Progress: {successful_tests}/{total_tests} test suites completed")
            
            try:
                success = await test_func()
                if success:
                    successful_tests += 1
                    print(f"✅ {test_name} completed successfully")
                else:
                    print(f"❌ {test_name} failed")
                
                # Wait between test suites for system recovery
                if test_name != test_sequence[-1][0]:  # Not the last test
                    print("⏳ Waiting 30 seconds for system recovery...")
                    await asyncio.sleep(30)
                    
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
        
        total_duration = time.time() - self.start_time
        
        # Print final summary
        print(f"\n{'='*80}")
        print("PERFORMANCE TEST SUITE SUMMARY")
        print(f"{'='*80}")
        print(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        print(f"Tests Completed: {successful_tests}/{total_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        for test_type, result in self.results.items():
            status_icon = {"completed": "✅", "failed": "❌", "skipped": "⏭️", "pending": "⏳"}
            icon = status_icon.get(result["status"], "❓")
            print(f"  {icon} {test_type.replace('_', ' ').title()}: {result['status']} "
                  f"({result['duration']:.1f}s)")
        
        return successful_tests >= total_tests * 0.75  # 75% success rate threshold
    
    def generate_final_report(self):
        """Generate comprehensive performance report"""
        
        print(f"\n{'='*60}")
        print("GENERATING COMPREHENSIVE PERFORMANCE REPORT")
        print(f"{'='*60}")
        
        try:
            report_file, chart_files = generate_performance_dashboard()
            
            print(f"\n🎉 Performance test suite completed!")
            print(f"📊 Comprehensive report: {report_file}")
            
            if chart_files:
                print(f"📈 Visualization charts:")
                for chart in chart_files:
                    print(f"   - {chart}")
            
            return report_file
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return None


async def main():
    """Main function to run performance test suite"""
    
    parser = argparse.ArgumentParser(description="Run comprehensive performance test suite")
    parser.add_argument("--level", choices=["basic", "standard", "comprehensive", "full", "stress"],
                       default="standard", help="Test level to run")
    parser.add_argument("--skip-report", action="store_true", help="Skip report generation")
    parser.add_argument("--tests-only", action="store_true", help="Run only specified test type")
    parser.add_argument("--test-type", choices=["api", "websocket", "database", "integration", "stress"],
                       help="Run only specific test type")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(test_level=args.level)
    
    # Run specific test type if requested
    if args.test_type:
        test_functions = {
            "api": runner.run_api_tests,
            "websocket": runner.run_websocket_tests,
            "database": runner.run_database_tests,
            "integration": runner.run_integration_tests,
            "stress": runner.run_stress_tests
        }
        
        if args.test_type in test_functions:
            print(f"🎯 Running only {args.test_type} tests...")
            success = await test_functions[args.test_type]()
            
            if not args.skip_report:
                runner.generate_final_report()
            
            return 0 if success else 1
    
    # Run all tests
    success = await runner.run_all_tests()
    
    # Generate final report
    if not args.skip_report:
        runner.generate_final_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())