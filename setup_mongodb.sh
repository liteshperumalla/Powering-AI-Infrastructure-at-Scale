#!/bin/bash
# MongoDB Setup Script for macOS

echo "🚀 Setting up MongoDB for Infra Mind"
echo "=================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "📦 Installing MongoDB Community Edition..."
brew tap mongodb/brew
brew install mongodb-community

echo "🔧 Creating MongoDB data directory..."
sudo mkdir -p /usr/local/var/mongodb
sudo mkdir -p /usr/local/var/log/mongodb
sudo chown $(whoami) /usr/local/var/mongodb
sudo chown $(whoami) /usr/local/var/log/mongodb

echo "🚀 Starting MongoDB service..."
brew services start mongodb/brew/mongodb-community

echo "⏳ Waiting for MongoDB to start..."
sleep 5

echo "🧪 Testing MongoDB connection..."
if mongosh --eval "db.runCommand('ping').ok" --quiet; then
    echo "✅ MongoDB is running successfully!"
    echo ""
    echo "📋 MongoDB Information:"
    echo "   • Service: mongodb-community"
    echo "   • Port: 27017"
    echo "   • Data Directory: /usr/local/var/mongodb"
    echo "   • Log Directory: /usr/local/var/log/mongodb"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   • Start: brew services start mongodb/brew/mongodb-community"
    echo "   • Stop: brew services stop mongodb/brew/mongodb-community"
    echo "   • Restart: brew services restart mongodb/brew/mongodb-community"
    echo "   • Connect: mongosh"
else
    echo "❌ MongoDB connection failed. Please check the installation."
fi

echo ""
echo "🎉 MongoDB setup completed!"
echo "   You can now run your Infra Mind application with database support."