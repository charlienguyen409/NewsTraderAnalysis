#!/bin/bash
# Run tests with coverage reporting

set -e  # Exit on any error

echo "📊 Running tests with coverage analysis..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Parse command line arguments
backend_only=false
frontend_only=false
open_reports=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            backend_only=true
            shift
            ;;
        --frontend-only)
            frontend_only=true
            shift
            ;;
        --no-open)
            open_reports=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--backend-only|--frontend-only] [--no-open]"
            exit 1
            ;;
    esac
done

# Step 1: Backend Coverage
if [ "$frontend_only" != true ]; then
    print_step "Running backend tests with coverage..."
    cd backend
    
    # Install coverage dependencies if not present
    pip install pytest-cov pytest-html 2>/dev/null || true
    
    # Run tests with coverage
    print_status "Generating backend coverage report..."
    pytest tests/unit/ \
        --cov=app \
        --cov-branch \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --cov-report=term-missing \
        --cov-fail-under=70
    
    # Display coverage summary
    echo ""
    print_status "Backend Coverage Summary:"
    python -m coverage report --show-missing
    
    cd ..
    print_status "✅ Backend coverage report generated at backend/htmlcov/index.html"
    echo ""
fi

# Step 2: Frontend Coverage
if [ "$backend_only" != true ]; then
    print_step "Running frontend tests with coverage..."
    cd frontend
    
    # Run tests with coverage
    print_status "Generating frontend coverage report..."
    npm test -- --coverage --watchAll=false --coverageReporters=html --coverageReporters=text --coverageReporters=lcov
    
    cd ..
    print_status "✅ Frontend coverage report generated at frontend/coverage/lcov-report/index.html"
    echo ""
fi

# Step 3: Generate Combined Coverage Report
print_step "Generating combined coverage analysis..."

# Create a combined coverage directory
mkdir -p coverage-reports

# Create a simple HTML index for both reports
cat > coverage-reports/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market News Analysis Agent - Coverage Reports</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .report-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .report-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }
        .report-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .report-card h3 {
            margin-top: 0;
            color: #007acc;
        }
        .btn {
            display: inline-block;
            background: #007acc;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #005fa3;
        }
        .stats {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .coverage-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        .coverage-good { background: #28a745; }
        .coverage-warning { background: #ffc107; color: #333; }
        .coverage-danger { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Test Coverage Reports</h1>
        <p>Generated on $(date)</p>
        
        <div class="report-grid">
            <div class="report-card">
                <h3>🐍 Backend Coverage</h3>
                <p>Python/FastAPI application coverage including API endpoints, services, and business logic.</p>
                <a href="../backend/htmlcov/index.html" class="btn">View Backend Report</a>
            </div>
            
            <div class="report-card">
                <h3>⚛️ Frontend Coverage</h3>
                <p>React/TypeScript application coverage including components, hooks, and utilities.</p>
                <a href="../frontend/coverage/lcov-report/index.html" class="btn">View Frontend Report</a>
            </div>
        </div>
        
        <h2>📈 Coverage Targets</h2>
        <div class="stats">
            <p><strong>Overall Target:</strong> <span class="coverage-badge coverage-good">≥80%</span></p>
            <p><strong>Critical Paths:</strong> <span class="coverage-badge coverage-good">≥85%</span></p>
            <p><strong>API Endpoints:</strong> <span class="coverage-badge coverage-good">≥90%</span></p>
            <p><strong>Service Layer:</strong> <span class="coverage-badge coverage-good">≥85%</span></p>
        </div>
        
        <h2>📋 Next Steps</h2>
        <ul>
            <li>Review coverage reports to identify gaps</li>
            <li>Focus on testing critical business logic</li>
            <li>Add tests for uncovered edge cases</li>
            <li>Update tests when modifying code</li>
        </ul>
        
        <h2>📚 Documentation</h2>
        <ul>
            <li><a href="../docs/testing-guide.md">Testing Guide</a> - Complete testing instructions</li>
            <li><a href="../docs/test-coverage.md">Coverage Documentation</a> - Coverage tracking and goals</li>
            <li><a href="../docs/README.md">Documentation Index</a> - All project documentation</li>
        </ul>
    </div>
</body>
</html>
EOF

print_status "✅ Combined coverage index created at coverage-reports/index.html"

# Step 4: Display coverage summary
echo ""
print_step "Coverage Summary"
echo "================"

if [ "$frontend_only" != true ] && [ -f "backend/coverage.xml" ]; then
    echo "Backend Coverage:"
    cd backend
    python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    line_rate = float(root.attrib['line-rate']) * 100
    branch_rate = float(root.attrib['branch-rate']) * 100
    print(f'  Lines: {line_rate:.1f}%')
    print(f'  Branches: {branch_rate:.1f}%')
except:
    print('  Unable to parse coverage data')
"
    cd ..
fi

if [ "$backend_only" != true ] && [ -f "frontend/coverage/lcov.info" ]; then
    echo "Frontend Coverage:"
    cd frontend
    if command -v lcov >/dev/null 2>&1; then
        lcov --summary coverage/lcov.info 2>/dev/null | grep -E "(lines|functions|branches)" || echo "  Coverage data available in coverage/lcov-report/"
    else
        echo "  Coverage report available at coverage/lcov-report/index.html"
    fi
    cd ..
fi

echo ""

# Step 5: Open reports if requested
if [ "$open_reports" = true ]; then
    print_status "Opening coverage reports..."
    
    # Try to open the combined index
    if command -v open >/dev/null 2>&1; then
        # macOS
        open coverage-reports/index.html
    elif command -v xdg-open >/dev/null 2>&1; then
        # Linux
        xdg-open coverage-reports/index.html
    elif command -v start >/dev/null 2>&1; then
        # Windows
        start coverage-reports/index.html
    else
        print_warning "Could not auto-open reports. Please open coverage-reports/index.html manually."
    fi
fi

echo ""
print_status "🎯 Coverage analysis complete!"
echo ""
echo "📁 Report locations:"
echo "  - Combined index: coverage-reports/index.html"
if [ "$frontend_only" != true ]; then
    echo "  - Backend: backend/htmlcov/index.html"
fi
if [ "$backend_only" != true ]; then
    echo "  - Frontend: frontend/coverage/lcov-report/index.html"
fi
echo ""
echo "💡 Tips:"
echo "  - Focus on testing business logic over getters/setters"
echo "  - Add tests for error handling and edge cases"
echo "  - Review the Test Coverage Guide: docs/test-coverage.md"