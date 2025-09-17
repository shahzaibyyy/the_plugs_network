#!/bin/bash

# The Plugs - Development Server Start Script

set -e

echo "🚀 Starting The Plugs API Development Server"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env file. Please edit it with your configuration."
    else
        echo "❌ .env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "⚠️  Alembic not found. Skipping migrations."
fi

# Start Redis if not running (optional)
if command -v redis-cli &> /dev/null; then
    if ! redis-cli ping &> /dev/null; then
        echo "⚠️  Redis is not running. Please start Redis manually."
    else
        echo "✅ Redis is running"
    fi
else
    echo "⚠️  Redis CLI not found. Please ensure Redis is installed and running."
fi

# Set environment variables for development
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the development server
echo "🎯 Starting FastAPI development server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🩺 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start uvicorn with hot reload
uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
