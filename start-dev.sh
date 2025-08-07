#!/bin/bash

# Infra Mind Development Startup Script
# This script starts both services in development mode (no build, faster startup)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend-react"

echo -e "${BLUE}🚀 Starting Infra Mind Development Environment${NC}"
echo -e "${BLUE}===========================================${NC}"

# Function to print colored status messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    print_info "Checking port $port..."
    if check_port $port; then
        print_warning "Port $port is in use. Killing existing process..."
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=15
    local attempt=1
    
    print_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Clean up existing processes
print_info "Cleaning up existing processes..."
kill_port 8000  # Backend API
kill_port 3000  # Frontend React

# Setup Backend (Quick)
print_info "Setting up backend (development mode)..."
cd "$BACKEND_DIR"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_info "Installing backend dependencies..."
    pip install -r requirements.txt || pip install -e .
    pip install uvicorn[standard] fastapi python-multipart python-jose[cryptography] passlib[bcrypt] motor beanie aioredis loguru
else
    source venv/bin/activate
fi

print_status "Backend environment ready"

# Setup Frontend (Quick)
print_info "Setting up frontend (development mode)..."
cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

print_status "Frontend environment ready"

# Start Backend API (Development Mode)
print_info "Starting backend API in development mode..."
cd "$BACKEND_DIR"
source venv/bin/activate

# Start with uvicorn directly for faster startup
print_info "Launching backend API on port 8000..."
nohup uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
if wait_for_service "http://localhost:8000/health" "Backend API"; then
    print_status "Backend API started successfully (PID: $BACKEND_PID)"
else
    print_error "Failed to start backend API"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start Frontend (Development Mode)
print_info "Starting frontend in development mode..."
cd "$FRONTEND_DIR"

# Start with npm run dev for hot reload
print_info "Launching frontend on port 3000 with hot reload..."
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
if wait_for_service "http://localhost:3000" "Frontend"; then
    print_status "Frontend started successfully (PID: $FRONTEND_PID)"
else
    print_error "Failed to start frontend"
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Final status
echo -e "\n${GREEN}🎉 Infra Mind Development Environment Started!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo -e "${BLUE}Backend API:${NC}      http://localhost:8000"
echo -e "${BLUE}API Documentation:${NC} http://localhost:8000/docs"
echo -e "${BLUE}Frontend App:${NC}     http://localhost:3000"
echo -e "\n${YELLOW}Development Features:${NC}"
echo -e "${YELLOW}• Backend Hot Reload:${NC} ✅ Enabled"
echo -e "${YELLOW}• Frontend Hot Reload:${NC} ✅ Enabled"
echo -e "${YELLOW}• TypeScript:${NC}     ✅ Turbopack enabled"

# Create PID file for easy cleanup
echo "$BACKEND_PID" > backend.pid
echo "$FRONTEND_PID" > frontend.pid

echo -e "\n${BLUE}Logs:${NC}"
echo -e "${BLUE}Backend Log:${NC}      tail -f $BACKEND_DIR/backend.log"
echo -e "${BLUE}Frontend Log:${NC}     tail -f $FRONTEND_DIR/frontend.log"

echo -e "\n${YELLOW}To stop the services, run:${NC}"
echo -e "${YELLOW}./stop-full-stack.sh${NC}"

echo -e "\n${GREEN}✅ Development environment ready! Open http://localhost:3000${NC}"

# Optional: Open browser
read -p "Would you like to open the app in your browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || true
fi

# Optional: Follow logs
read -p "Would you like to follow the logs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Following logs (Ctrl+C to stop)..."
    tail -f "$BACKEND_DIR/backend.log" "$FRONTEND_DIR/frontend.log"
fi