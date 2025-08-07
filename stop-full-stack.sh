#!/bin/bash

# Infra Mind Full Stack Stop Script
# This script stops both the backend API and frontend React application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🛑 Stopping Infra Mind Full Stack Application${NC}"
echo -e "${BLUE}==========================================${NC}"

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

# Function to kill process by PID
kill_process() {
    local pid=$1
    local service_name=$2
    
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        print_info "Stopping $service_name (PID: $pid)..."
        kill "$pid"
        
        # Wait for process to terminate
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Force killing $service_name..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        print_status "$service_name stopped"
    else
        print_warning "$service_name was not running"
    fi
}

# Function to kill processes on port
kill_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_info "Stopping processes on port $port ($service_name)..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        print_status "Processes on port $port stopped"
    else
        print_info "No processes running on port $port"
    fi
}

cd "$PROJECT_ROOT"

# Stop processes using PID files if they exist
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    kill_process "$BACKEND_PID" "Backend API"
    rm -f backend.pid
fi

if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill_process "$FRONTEND_PID" "Frontend"
    rm -f frontend.pid
fi

# Also kill any processes on the ports as backup
kill_port 8000 "Backend API"
kill_port 3000 "Frontend"

# Clean up log files
print_info "Cleaning up log files..."
[ -f "backend.log" ] && rm -f backend.log
[ -f "frontend-react/frontend.log" ] && rm -f frontend-react/frontend.log

# Kill any remaining python or node processes related to our app
print_info "Cleaning up any remaining processes..."
pkill -f "api/app.py" 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

print_status "All processes stopped"

echo -e "\n${GREEN}🎉 Infra Mind Full Stack Application Stopped Successfully!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo -e "${BLUE}Both backend and frontend services have been stopped.${NC}"
echo -e "${BLUE}All log files have been cleaned up.${NC}"
echo -e "\n${GREEN}✅ Cleanup complete!${NC}"