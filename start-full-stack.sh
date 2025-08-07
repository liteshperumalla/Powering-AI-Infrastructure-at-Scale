#!/bin/bash

# Infra Mind Full Stack Startup Script
# This script builds and starts both the backend API and frontend React application

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

echo -e "${BLUE}🚀 Starting Infra Mind Full Stack Application${NC}"
echo -e "${BLUE}======================================${NC}"

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
    local max_attempts=30
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

# Check prerequisites
print_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

print_status "Prerequisites check passed"

# Clean up existing processes
print_info "Cleaning up existing processes..."
kill_port 8000  # Backend API
kill_port 3000  # Frontend React

# Setup Backend
print_info "Setting up backend..."
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install backend dependencies
print_info "Installing backend dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install -e .
fi

# Install additional dependencies that might be missing
print_info "Installing additional backend dependencies..."
pip install uvicorn[standard] fastapi python-multipart python-jose[cryptography] passlib[bcrypt] motor beanie aioredis loguru

print_status "Backend dependencies installed"

# Setup Frontend
print_info "Setting up frontend..."
cd "$FRONTEND_DIR"

# Install frontend dependencies
print_info "Installing frontend dependencies..."
npm install

print_status "Frontend dependencies installed"

# Start services
print_info "Starting services..."

# Start Backend API
print_info "Starting backend API server..."
cd "$BACKEND_DIR"

# Make sure we're in the virtual environment
source venv/bin/activate

# Start backend in background
print_info "Launching backend API on port 8000..."
nohup python api/app.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
if wait_for_service "http://localhost:8000/health" "Backend API"; then
    print_status "Backend API started successfully (PID: $BACKEND_PID)"
else
    print_error "Failed to start backend API"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Build and Start Frontend
print_info "Building and starting frontend..."
cd "$FRONTEND_DIR"

# Build the frontend
print_info "Building React application..."
npm run build

# Start frontend in background
print_info "Launching frontend on port 3000..."
nohup npm start > frontend.log 2>&1 &
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
echo -e "\n${GREEN}🎉 Infra Mind Full Stack Application Started Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo -e "${BLUE}Backend API:${NC}      http://localhost:8000"
echo -e "${BLUE}API Documentation:${NC} http://localhost:8000/docs"
echo -e "${BLUE}Frontend App:${NC}     http://localhost:3000"
echo -e "\n${YELLOW}Process IDs:${NC}"
echo -e "${YELLOW}Backend PID:${NC}      $BACKEND_PID"
echo -e "${YELLOW}Frontend PID:${NC}     $FRONTEND_PID"

# Create PID file for easy cleanup
echo "$BACKEND_PID" > backend.pid
echo "$FRONTEND_PID" > frontend.pid

echo -e "\n${BLUE}Logs:${NC}"
echo -e "${BLUE}Backend Log:${NC}      tail -f $BACKEND_DIR/backend.log"
echo -e "${BLUE}Frontend Log:${NC}     tail -f $FRONTEND_DIR/frontend.log"

echo -e "\n${YELLOW}To stop the services, run:${NC}"
echo -e "${YELLOW}./stop-full-stack.sh${NC}"

echo -e "\n${GREEN}✅ Setup complete! Open http://localhost:3000 in your browser${NC}"

# Keep script running to monitor services
trap 'echo -e "\n${RED}Stopping services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT TERM

# Optional: Follow logs
read -p "Would you like to follow the logs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Following logs (Ctrl+C to stop)..."
    tail -f "$BACKEND_DIR/backend.log" "$FRONTEND_DIR/frontend.log"
fi