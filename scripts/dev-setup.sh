#!/bin/bash
# Development setup script for Infra Mind
# Learning Note: Shell scripts automate repetitive setup tasks

set -e  # Exit on any error

echo "🚀 Setting up Infra Mind development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before running the application"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -e ".[dev]"

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d mongodb redis

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test connections
echo "🔌 Testing connections..."
python -c "
import asyncio
from src.infra_mind.core.database import init_database, close_database, get_database_info
from src.infra_mind.core.logging import setup_logging

async def test():
    setup_logging()
    try:
        await init_database()
        info = await get_database_info()
        print(f'✅ Database connected: {info[\"status\"]}')
        await close_database()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)

asyncio.run(test())
"

echo ""
echo "✅ Development environment ready!"
echo ""
echo "🌐 Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: infra-mind run --reload"
echo "  3. Visit: http://localhost:8000/docs"
echo ""
echo "🛠️  Useful commands:"
echo "  make help          - Show all available commands"
echo "  make test          - Run tests"
echo "  make docker-up     - Start all services"
echo "  infra-mind --help  - CLI help"