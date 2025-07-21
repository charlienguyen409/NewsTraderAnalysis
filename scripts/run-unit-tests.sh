#!/bin/bash
# Run unit tests for both backend and frontend

set -e  # Exit on any error

echo "🧪 Running unit tests for Market News Analysis Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Initialize test results
backend_tests_passed=false
frontend_tests_passed=false

# Run backend unit tests
print_status "Running backend unit tests..."
cd backend

if [ -d "tests/unit" ]; then
    if pytest tests/unit/ -v --tb=short; then
        print_status "✅ Backend unit tests passed"
        backend_tests_passed=true
    else
        print_error "❌ Backend unit tests failed"
        backend_tests_passed=false
    fi
else
    print_warning "No backend unit tests found at backend/tests/unit/"
fi

cd ..

# Run frontend unit tests
print_status "Running frontend unit tests..."
cd frontend

if [ -f "package.json" ]; then
    if npm test -- --watchAll=false --coverage=false; then
        print_status "✅ Frontend unit tests passed"
        frontend_tests_passed=true
    else
        print_error "❌ Frontend unit tests failed"
        frontend_tests_passed=false
    fi
else
    print_warning "No frontend package.json found"
fi

cd ..

# Summary
echo ""
echo "📊 Test Results Summary:"
echo "========================"

if [ "$backend_tests_passed" = true ]; then
    echo -e "Backend Unit Tests:  ${GREEN}✅ PASSED${NC}"
else
    echo -e "Backend Unit Tests:  ${RED}❌ FAILED${NC}"
fi

if [ "$frontend_tests_passed" = true ]; then
    echo -e "Frontend Unit Tests: ${GREEN}✅ PASSED${NC}"
else
    echo -e "Frontend Unit Tests: ${RED}❌ FAILED${NC}"
fi

echo ""

# Exit with error if any tests failed
if [ "$backend_tests_passed" = true ] && [ "$frontend_tests_passed" = true ]; then
    print_status "🎉 All unit tests passed!"
    exit 0
else
    print_error "💥 Some tests failed. Please fix the issues and try again."
    echo ""
    echo "💡 Tips:"
    echo "  - Check test output above for specific failures"
    echo "  - Run individual test suites to isolate issues:"
    echo "    Backend: cd backend && pytest tests/unit/ -v"
    echo "    Frontend: cd frontend && npm test"
    echo "  - Check the Testing Guide: docs/testing-guide.md"
    exit 1
fi