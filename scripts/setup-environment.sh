#!/bin/bash
# Setup script for Market News Analysis Agent development environment

set -e  # Exit on any error

echo "🚀 Setting up Market News Analysis Agent development environment..."

# Check if we're in the project root
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker Desktop and try again."
    exit 1
fi

# Check Docker Compose
if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ and try again."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Setup environment files
echo "📝 Setting up environment files..."

# Root environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created root .env file"
else
    echo "ℹ️ Root .env file already exists"
fi

# Backend environment file
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend .env file"
else
    echo "ℹ️ Backend .env file already exists"
fi

# Frontend environment file
if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend .env file"
else
    echo "ℹ️ Frontend .env file already exists"
fi

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
if command_exists pip3; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install E2E test dependencies
echo "🎭 Installing E2E test dependencies..."
cd e2e
npm install
npx playwright install --with-deps
cd ..

# Install performance test dependencies
echo "📊 Installing performance test dependencies..."
cd performance
if command_exists pip3; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi
cd ..

# Setup test databases
echo "🗄️ Setting up test databases..."
docker-compose -f docker/docker-compose.yml up -d postgres redis

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Run database migrations (if they exist)
echo "🔄 Running database setup..."
cd backend
if [ -f "alembic.ini" ]; then
    alembic upgrade head
else
    echo "ℹ️ No Alembic migrations found, skipping database migrations"
fi
cd ..

echo "✅ Environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Update your .env files with your actual API keys:"
echo "   - OPENAI_API_KEY in backend/.env"
echo "   - ANTHROPIC_API_KEY in backend/.env (optional)"
echo ""
echo "2. Start the development environment:"
echo "   cd docker && docker-compose up -d"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "4. Run tests:"
echo "   ./scripts/run-unit-tests.sh"
echo ""
echo "📚 For more information, see docs/README.md"