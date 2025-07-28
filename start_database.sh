#!/bin/bash
# Start Database Services Script

echo "🚀 Starting Infra Mind Database Services"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "🐳 Starting MongoDB and Redis with Docker Compose..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🧪 Testing database connections..."

# Test MongoDB
echo "📊 Testing MongoDB connection..."
if docker exec infra-mind-mongodb mongosh --eval "db.runCommand('ping').ok" --quiet > /dev/null 2>&1; then
    echo "✅ MongoDB is running successfully!"
    echo "   • URL: mongodb://localhost:27017"
    echo "   • Admin UI: http://localhost:8081 (Mongo Express)"
else
    echo "❌ MongoDB connection failed"
fi

# Test Redis
echo "🔄 Testing Redis connection..."
if docker exec infra-mind-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running successfully!"
    echo "   • URL: redis://localhost:6379"
else
    echo "❌ Redis connection failed"
fi

echo ""
echo "🎉 Database services are ready!"
echo ""
echo "📋 Service Information:"
echo "   • MongoDB: localhost:27017"
echo "   • Redis: localhost:6379"
echo "   • Mongo Express (Web UI): http://localhost:8081"
echo ""
echo "🔧 Useful Commands:"
echo "   • Stop services: docker-compose -f docker-compose.dev.yml down"
echo "   • View logs: docker-compose -f docker-compose.dev.yml logs"
echo "   • Restart: docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "🧪 Test your database connection:"
echo "   python test_database_connection.py"