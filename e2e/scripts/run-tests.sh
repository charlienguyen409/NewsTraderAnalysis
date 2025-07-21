#!/bin/bash

# E2E Test Runner Script
# This script sets up the test environment and runs E2E tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
E2E_DIR="$( dirname "$SCRIPT_DIR" )"
PROJECT_ROOT="$( dirname "$E2E_DIR" )"

# Default values
BROWSER="chromium"
HEADED=false
DEBUG=false
UI_MODE=false
CLEANUP=true
SETUP=true
DOCKER_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --browser)
      BROWSER="$2"
      shift 2
      ;;
    --headed)
      HEADED=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --ui)
      UI_MODE=true
      shift
      ;;
    --no-cleanup)
      CLEANUP=false
      shift
      ;;
    --no-setup)
      SETUP=false
      shift
      ;;
    --docker)
      DOCKER_MODE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --browser BROWSER    Browser to use (chromium, firefox, webkit, mobile)"
      echo "  --headed            Run tests in headed mode"
      echo "  --debug             Run tests in debug mode"
      echo "  --ui                Run tests in UI mode"
      echo "  --no-cleanup        Don't cleanup after tests"
      echo "  --no-setup          Don't setup test environment"
      echo "  --docker            Use Docker for test environment"
      echo "  --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Run all tests with chromium"
      echo "  $0 --browser firefox --headed         # Run with Firefox in headed mode"
      echo "  $0 --debug                           # Run in debug mode"
      echo "  $0 --ui                              # Run in UI mode"
      echo "  $0 --docker                          # Use Docker environment"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Function to print colored output
print_status() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a service is running
check_service() {
  local url=$1
  local service_name=$2
  local max_attempts=30
  local attempt=1

  print_status "Waiting for $service_name to be ready..."
  
  while [ $attempt -le $max_attempts ]; do
    if curl -f -s "$url" > /dev/null 2>&1; then
      print_success "$service_name is ready!"
      return 0
    fi
    
    echo -n "."
    sleep 2
    ((attempt++))
  done
  
  print_error "$service_name failed to start within expected time"
  return 1
}

# Function to setup test environment
setup_environment() {
  print_status "Setting up test environment..."
  
  cd "$E2E_DIR"
  
  if [ "$DOCKER_MODE" = true ]; then
    print_status "Starting Docker test environment..."
    docker-compose -f docker-compose.test.yml up -d
    
    # Wait for services
    check_service "http://localhost:8001/health" "Backend API"
    check_service "http://localhost:5174" "Frontend"
    
  else
    print_status "Starting local test environment..."
    
    # Start PostgreSQL and Redis if not running
    if ! docker ps | grep -q postgres-test; then
      print_status "Starting test database..."
      docker-compose -f docker-compose.test.yml up -d postgres-test redis-test
      sleep 5
    fi
    
    # Check if backend is running
    if ! curl -f -s "http://localhost:8001/health" > /dev/null 2>&1; then
      print_status "Starting backend service..."
      cd "$PROJECT_ROOT/backend"
      export DATABASE_URL="postgresql://testuser:testpass@localhost:5433/market_analysis_test"
      export REDIS_URL="redis://localhost:6380"
      export ENVIRONMENT="test"
      uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/backend-test.log 2>&1 &
      echo $! > /tmp/backend-test.pid
      cd "$E2E_DIR"
    fi
    
    # Check if frontend is running
    if ! curl -f -s "http://localhost:5174" > /dev/null 2>&1; then
      print_status "Starting frontend service..."
      cd "$PROJECT_ROOT/frontend"
      export VITE_API_URL="http://localhost:8001"
      export VITE_WS_URL="ws://localhost:8001/ws"
      npm run dev -- --host 0.0.0.0 --port 5174 > /tmp/frontend-test.log 2>&1 &
      echo $! > /tmp/frontend-test.pid
      cd "$E2E_DIR"
    fi
    
    # Wait for services
    check_service "http://localhost:8001/health" "Backend API"
    check_service "http://localhost:5174" "Frontend"
  fi
  
  print_success "Test environment is ready!"
}

# Function to install dependencies
install_dependencies() {
  print_status "Installing E2E test dependencies..."
  
  cd "$E2E_DIR"
  
  if [ ! -d "node_modules" ]; then
    npm ci
  fi
  
  # Install Playwright browsers
  print_status "Installing Playwright browsers..."
  if [ "$BROWSER" = "mobile" ]; then
    npx playwright install --with-deps chromium
  else
    npx playwright install --with-deps "$BROWSER"
  fi
  
  print_success "Dependencies installed!"
}

# Function to run tests
run_tests() {
  print_status "Running E2E tests..."
  
  cd "$E2E_DIR"
  
  # Set environment variables
  export BASE_URL="http://localhost:5174"
  export API_URL="http://localhost:8001"
  export CI=${CI:-false}
  
  # Build test command
  local test_cmd="npx playwright test"
  
  if [ "$BROWSER" = "mobile" ]; then
    test_cmd="$test_cmd --project=mobile"
  else
    test_cmd="$test_cmd --project=$BROWSER"
  fi
  
  if [ "$HEADED" = true ]; then
    test_cmd="$test_cmd --headed"
  fi
  
  if [ "$DEBUG" = true ]; then
    test_cmd="$test_cmd --debug"
  fi
  
  if [ "$UI_MODE" = true ]; then
    test_cmd="$test_cmd --ui"
  fi
  
  print_status "Executing: $test_cmd"
  
  # Run tests
  if eval "$test_cmd"; then
    print_success "All tests passed!"
    return 0
  else
    print_error "Some tests failed!"
    return 1
  fi
}

# Function to generate test report
generate_report() {
  print_status "Generating test report..."
  
  cd "$E2E_DIR"
  
  if [ -d "playwright-report" ]; then
    print_status "Opening test report..."
    npx playwright show-report --host 0.0.0.0
  else
    print_warning "No test report found"
  fi
}

# Function to cleanup
cleanup() {
  if [ "$CLEANUP" = false ]; then
    print_warning "Skipping cleanup"
    return 0
  fi
  
  print_status "Cleaning up test environment..."
  
  if [ "$DOCKER_MODE" = true ]; then
    cd "$E2E_DIR"
    docker-compose -f docker-compose.test.yml down -v
  else
    # Stop local services
    if [ -f "/tmp/backend-test.pid" ]; then
      kill $(cat /tmp/backend-test.pid) 2>/dev/null || true
      rm /tmp/backend-test.pid
    fi
    
    if [ -f "/tmp/frontend-test.pid" ]; then
      kill $(cat /tmp/frontend-test.pid) 2>/dev/null || true
      rm /tmp/frontend-test.pid
    fi
    
    # Stop Docker services
    cd "$E2E_DIR"
    docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
  fi
  
  print_success "Cleanup completed!"
}

# Function to handle script interruption
handle_interrupt() {
  print_warning "Script interrupted, cleaning up..."
  cleanup
  exit 130
}

# Set up interrupt handler
trap handle_interrupt SIGINT SIGTERM

# Main execution
main() {
  print_status "Starting E2E test execution..."
  print_status "Browser: $BROWSER"
  print_status "Headed: $HEADED"
  print_status "Debug: $DEBUG"
  print_status "UI Mode: $UI_MODE"
  print_status "Docker Mode: $DOCKER_MODE"
  
  local exit_code=0
  
  # Setup environment
  if [ "$SETUP" = true ]; then
    setup_environment || exit_code=$?
    if [ $exit_code -ne 0 ]; then
      print_error "Failed to setup test environment"
      cleanup
      exit $exit_code
    fi
    
    install_dependencies || exit_code=$?
    if [ $exit_code -ne 0 ]; then
      print_error "Failed to install dependencies"
      cleanup
      exit $exit_code
    fi
  fi
  
  # Run tests
  run_tests || exit_code=$?
  
  # Generate report if tests completed
  if [ $exit_code -eq 0 ] && [ "$UI_MODE" = false ] && [ "$DEBUG" = false ]; then
    generate_report
  fi
  
  # Cleanup
  cleanup
  
  if [ $exit_code -eq 0 ]; then
    print_success "E2E tests completed successfully!"
  else
    print_error "E2E tests failed with exit code $exit_code"
  fi
  
  exit $exit_code
}

# Check if running directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi