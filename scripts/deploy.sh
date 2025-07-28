#!/bin/bash
# Deployment script for Infra Mind
# Learning Note: Deployment scripts automate production deployment tasks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    ENV_FILE=".env.prod"
fi

echo -e "${BLUE}🚀 Deploying Infra Mind ($ENVIRONMENT environment)...${NC}"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file $ENV_FILE not found!${NC}"
    echo -e "${YELLOW}💡 Copy from ${ENV_FILE}.example and configure your values${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed.${NC}"
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

echo -e "${BLUE}📦 Building Docker images...${NC}"
docker-compose -f "$COMPOSE_FILE" build

echo -e "${BLUE}🛑 Stopping existing services...${NC}"
docker-compose -f "$COMPOSE_FILE" down

echo -e "${BLUE}🗂️ Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p nginx/ssl

echo -e "${BLUE}🚀 Starting services...${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    # Production deployment with nginx
    docker-compose -f "$COMPOSE_FILE" --profile nginx up -d
else
    # Development deployment
    docker-compose -f "$COMPOSE_FILE" up -d
fi

echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Health checks
echo -e "${BLUE}🔍 Checking service health...${NC}"

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API service is healthy${NC}"
else
    echo -e "${RED}❌ API service health check failed${NC}"
fi

# Check Frontend health
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend service is healthy${NC}"
else
    echo -e "${RED}❌ Frontend service health check failed${NC}"
fi

# Check MongoDB
if docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MongoDB is healthy${NC}"
else
    echo -e "${RED}❌ MongoDB health check failed${NC}"
fi

# Check Redis
if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is healthy${NC}"
else
    echo -e "${RED}❌ Redis health check failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service URLs:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API:      ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"

if [ "$ENVIRONMENT" = "development" ]; then
    echo -e "  MongoDB Express: ${GREEN}http://localhost:8081${NC} (run with --profile tools)"
    echo -e "  Redis Commander: ${GREEN}http://localhost:8082${NC} (run with --profile tools)"
fi

echo ""
echo -e "${BLUE}🛠️ Useful commands:${NC}"
echo -e "  View logs:    ${YELLOW}docker-compose -f $COMPOSE_FILE logs -f${NC}"
echo -e "  Stop services: ${YELLOW}docker-compose -f $COMPOSE_FILE down${NC}"
echo -e "  Restart:      ${YELLOW}docker-compose -f $COMPOSE_FILE restart${NC}"
echo ""