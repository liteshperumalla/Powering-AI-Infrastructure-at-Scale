#!/bin/bash
# Health check script for Infra Mind deployment
# Learning Note: Health checks ensure all services are running correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking Infra Mind deployment health...${NC}"
echo ""

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local service=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ $service health check failed${NC}"
        return 1
    fi
}

# Function to check container status
check_container() {
    local container=$1
    local service=$2
    
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        echo -e "${GREEN}✅ $service container is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $service container is not running${NC}"
        return 1
    fi
}

# Check container status
echo -e "${BLUE}📦 Container Status:${NC}"
check_container "infra_mind_api" "API"
check_container "infra_mind_frontend" "Frontend"
check_container "infra_mind_mongodb" "MongoDB"
check_container "infra_mind_redis" "Redis"

echo ""

# Check HTTP endpoints
echo -e "${BLUE}🌐 HTTP Health Checks:${NC}"
check_http "http://localhost:8000/health" "API"
check_http "http://localhost:3000/health" "Frontend"

echo ""

# Check database connections
echo -e "${BLUE}🗄️ Database Connections:${NC}"

# MongoDB check
if docker-compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✅ MongoDB connection is healthy${NC}"
else
    echo -e "${RED}❌ MongoDB connection failed${NC}"
fi

# Redis check
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis connection is healthy${NC}"
else
    echo -e "${RED}❌ Redis connection failed${NC}"
fi

echo ""

# Resource usage
echo -e "${BLUE}📊 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -5

echo ""

# Service URLs
echo -e "${BLUE}🔗 Service URLs:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API:      ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"

echo ""
echo -e "${GREEN}🎉 Health check completed!${NC}"