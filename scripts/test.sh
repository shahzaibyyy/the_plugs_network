#!/bin/bash

# Testing Script

set -e

echo "🧪 The Plugs - Test Runner"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-dev.txt

# Set test environment
export ENVIRONMENT=testing
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/15"

# Parse command line arguments
TEST_TYPE=${1:-"all"}
COVERAGE=${2:-"true"}

echo "🎯 Running tests: $TEST_TYPE"

case $TEST_TYPE in
    "unit")
        echo "🔬 Running unit tests..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/unit/ -v --cov=app --cov-report=html --cov-report=term
        else
            pytest tests/unit/ -v
        fi
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/integration/ -v --cov=app --cov-report=html --cov-report=term
        else
            pytest tests/integration/ -v
        fi
        ;;
    "e2e")
        echo "🎭 Running end-to-end tests..."
        pytest tests/e2e/ -v
        ;;
    "fast")
        echo "⚡ Running fast tests (unit only, no coverage)..."
        pytest tests/unit/ -v -x
        ;;
    "all")
        echo "🚀 Running all tests..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
        else
            pytest tests/ -v
        fi
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Available options: unit, integration, e2e, fast, all"
        exit 1
        ;;
esac

# Cleanup test database
if [ -f "test.db" ]; then
    rm test.db
    echo "🧹 Cleaned up test database"
fi

echo "✅ Tests completed!"
