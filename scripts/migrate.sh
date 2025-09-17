#!/bin/bash

# Database Migration Script

set -e

echo "🗄️  The Plugs - Database Migration Script"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Installing..."
    pip install alembic
fi

# Run migrations
echo "🔄 Running database migrations..."

if [ "$1" = "init" ]; then
    echo "🆕 Initializing Alembic..."
    alembic init alembic
elif [ "$1" = "create" ]; then
    if [ -z "$2" ]; then
        echo "❌ Please provide a migration message: ./scripts/migrate.sh create 'migration message'"
        exit 1
    fi
    echo "📝 Creating new migration: $2"
    alembic revision --autogenerate -m "$2"
elif [ "$1" = "upgrade" ]; then
    echo "⬆️  Upgrading database to latest version..."
    alembic upgrade head
elif [ "$1" = "downgrade" ]; then
    echo "⬇️  Downgrading database by 1 version..."
    alembic downgrade -1
elif [ "$1" = "history" ]; then
    echo "📋 Migration history:"
    alembic history
elif [ "$1" = "current" ]; then
    echo "📍 Current migration version:"
    alembic current
else
    echo "🔄 Running default migration (upgrade to head)..."
    alembic upgrade head
fi

echo "✅ Migration script completed!"
