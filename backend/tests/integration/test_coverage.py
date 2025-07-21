"""
Test Coverage Verification for Integration Tests

This module provides comprehensive test coverage verification and reporting
for the integration test suite.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

def run_coverage_analysis():
    """Run coverage analysis on integration tests"""
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Run integration tests with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_workflows.py",
        "--cov=app",
        "--cov-report=json",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]
    
    print("Running integration tests with coverage analysis...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Integration tests passed with coverage analysis")
        else:
            print("✗ Integration tests failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("✗ Coverage analysis timed out")
        return False
    except Exception as e:
        print(f"✗ Error running coverage analysis: {e}")
        return False

def analyze_coverage_report():
    """Analyze the coverage report"""
    
    coverage_file = backend_dir / "coverage.json"
    
    if not coverage_file.exists():
        print("✗ Coverage report not found")
        return None
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        # Extract key metrics
        total_lines = coverage_data['totals']['num_statements']
        covered_lines = coverage_data['totals']['covered_lines']
        missing_lines = coverage_data['totals']['missing_lines']
        coverage_percent = coverage_data['totals']['percent_covered']
        
        print(f"📊 Coverage Analysis Results:")
        print(f"   Total Lines: {total_lines}")
        print(f"   Covered Lines: {covered_lines}")
        print(f"   Missing Lines: {missing_lines}")
        print(f"   Coverage Percentage: {coverage_percent:.1f}%")
        print()
        
        # Analyze per-file coverage
        file_coverage = {}
        for file_path, file_data in coverage_data['files'].items():
            if file_path.startswith('app/'):
                file_coverage[file_path] = {
                    'lines': file_data['summary']['num_statements'],
                    'covered': file_data['summary']['covered_lines'],
                    'missing': file_data['summary']['missing_lines'],
                    'percent': file_data['summary']['percent_covered']
                }
        
        # Show low coverage files
        low_coverage_files = [
            (file_path, data) for file_path, data in file_coverage.items()
            if data['percent'] < 80 and data['lines'] > 10
        ]
        
        if low_coverage_files:
            print("⚠️  Files with low coverage (<80%):")
            for file_path, data in sorted(low_coverage_files, key=lambda x: x[1]['percent']):
                print(f"   {file_path}: {data['percent']:.1f}% ({data['covered']}/{data['lines']})")
            print()
        
        # Show high coverage files
        high_coverage_files = [
            (file_path, data) for file_path, data in file_coverage.items()
            if data['percent'] >= 90 and data['lines'] > 10
        ]
        
        if high_coverage_files:
            print("✅ Files with high coverage (≥90%):")
            for file_path, data in sorted(high_coverage_files, key=lambda x: x[1]['percent'], reverse=True):
                print(f"   {file_path}: {data['percent']:.1f}% ({data['covered']}/{data['lines']})")
            print()
        
        return {
            'total_coverage': coverage_percent,
            'file_coverage': file_coverage,
            'low_coverage_files': low_coverage_files,
            'high_coverage_files': high_coverage_files
        }
        
    except Exception as e:
        print(f"✗ Error analyzing coverage report: {e}")
        return None

def check_critical_paths_coverage():
    """Check coverage of critical API paths"""
    
    critical_paths = [
        'app/api/routes/analysis.py',
        'app/api/routes/articles.py',
        'app/api/routes/positions.py',
        'app/api/routes/activity_logs.py',
        'app/services/analysis_service.py',
        'app/services/llm_service.py',
        'app/core/websocket.py',
        'app/core/database.py'
    ]
    
    coverage_file = backend_dir / "coverage.json"
    
    if not coverage_file.exists():
        print("✗ Coverage report not found for critical paths analysis")
        return False
    
    try:
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        print("🎯 Critical Path Coverage Analysis:")
        print()
        
        all_critical_covered = True
        
        for path in critical_paths:
            if path in coverage_data['files']:
                file_data = coverage_data['files'][path]
                percent = file_data['summary']['percent_covered']
                covered = file_data['summary']['covered_lines']
                total = file_data['summary']['num_statements']
                
                status = "✅" if percent >= 80 else "⚠️" if percent >= 60 else "❌"
                print(f"   {status} {path}: {percent:.1f}% ({covered}/{total})")
                
                if percent < 80:
                    all_critical_covered = False
            else:
                print(f"   ❓ {path}: Not found in coverage report")
                all_critical_covered = False
        
        print()
        
        if all_critical_covered:
            print("✅ All critical paths have adequate coverage (≥80%)")
        else:
            print("⚠️  Some critical paths need better coverage")
        
        return all_critical_covered
        
    except Exception as e:
        print(f"✗ Error checking critical paths coverage: {e}")
        return False

def verify_test_completeness():
    """Verify that all required test categories are covered"""
    
    required_test_categories = [
        'TestCompleteAnalysisWorkflows',
        'TestAPIIntegrationWithRealisticDataFlows',
        'TestServiceIntegration',
        'TestWebSocketIntegration',
        'TestErrorHandlingIntegration',
        'TestPerformanceIntegration',
        'TestDatabaseTransactionIntegration'
    ]
    
    test_file = backend_dir / "tests/integration/test_workflows.py"
    
    if not test_file.exists():
        print("✗ Test file not found")
        return False
    
    try:
        with open(test_file, 'r') as f:
            test_content = f.read()
        
        print("📋 Test Completeness Analysis:")
        print()
        
        all_categories_present = True
        
        for category in required_test_categories:
            if f"class {category}" in test_content:
                # Count test methods in this category
                lines = test_content.split('\n')
                in_category = False
                test_methods = []
                
                for line in lines:
                    if f"class {category}" in line:
                        in_category = True
                    elif in_category and line.startswith('class ') and category not in line:
                        in_category = False
                    elif in_category and line.strip().startswith('def test_'):
                        method_name = line.strip().split('(')[0].replace('def ', '')
                        test_methods.append(method_name)
                
                print(f"   ✅ {category}: {len(test_methods)} test methods")
                for method in test_methods:
                    print(f"      - {method}")
                print()
            else:
                print(f"   ❌ {category}: Missing")
                all_categories_present = False
        
        if all_categories_present:
            print("✅ All required test categories are present")
        else:
            print("⚠️  Some required test categories are missing")
        
        return all_categories_present
        
    except Exception as e:
        print(f"✗ Error verifying test completeness: {e}")
        return False

def generate_coverage_report():
    """Generate a comprehensive coverage report"""
    
    print("=" * 80)
    print("INTEGRATION TEST COVERAGE REPORT")
    print("=" * 80)
    print()
    
    # Run coverage analysis
    coverage_success = run_coverage_analysis()
    if not coverage_success:
        print("❌ Coverage analysis failed")
        return False
    
    print()
    
    # Analyze coverage report
    coverage_data = analyze_coverage_report()
    if not coverage_data:
        print("❌ Coverage report analysis failed")
        return False
    
    print()
    
    # Check critical paths
    critical_paths_ok = check_critical_paths_coverage()
    
    print()
    
    # Verify test completeness
    test_completeness_ok = verify_test_completeness()
    
    print()
    
    # Overall assessment
    print("=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    
    overall_score = 0
    max_score = 4
    
    if coverage_success:
        print("✅ Integration tests pass")
        overall_score += 1
    else:
        print("❌ Integration tests fail")
    
    if coverage_data and coverage_data['total_coverage'] >= 80:
        print(f"✅ Overall coverage is adequate ({coverage_data['total_coverage']:.1f}%)")
        overall_score += 1
    else:
        coverage_percent = coverage_data['total_coverage'] if coverage_data else 0
        print(f"⚠️  Overall coverage needs improvement ({coverage_percent:.1f}%)")
    
    if critical_paths_ok:
        print("✅ Critical paths have adequate coverage")
        overall_score += 1
    else:
        print("⚠️  Critical paths need better coverage")
    
    if test_completeness_ok:
        print("✅ All required test categories are present")
        overall_score += 1
    else:
        print("⚠️  Some test categories are missing")
    
    print()
    print(f"Overall Score: {overall_score}/{max_score}")
    
    if overall_score == max_score:
        print("🎉 Excellent! Integration test coverage is comprehensive")
        return True
    elif overall_score >= 3:
        print("👍 Good! Integration test coverage is adequate with room for improvement")
        return True
    else:
        print("⚠️  Integration test coverage needs significant improvement")
        return False

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick coverage check without running tests
        print("Running quick coverage analysis...")
        coverage_data = analyze_coverage_report()
        critical_paths_ok = check_critical_paths_coverage()
        test_completeness_ok = verify_test_completeness()
        
        if coverage_data and critical_paths_ok and test_completeness_ok:
            print("✅ Quick analysis passed")
            return 0
        else:
            print("⚠️  Quick analysis found issues")
            return 1
    else:
        # Full coverage report
        success = generate_coverage_report()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())