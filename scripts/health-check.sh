#!/bin/bash
# Comprehensive Health Check Script for Production Containers
# Learning Note: Monitors all system components and provides detailed health status

set -e

# Configuration
TIMEOUT=10
RETRY_COUNT=3
HEALTH_CHECK_INTERVAL=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}"
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    log "Checking $name at $url"
    
    for i in $(seq 1 $RETRY_COUNT); do
        if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null); then
            if [ "$response" = "$expected_status" ]; then
                success "$name is healthy (HTTP $response)"
                return 0
            else
                warn "$name returned HTTP $response (expected $expected_status)"
            fi
        else
            warn "$name check failed (attempt $i/$RETRY_COUNT)"
        fi
        
        if [ $i -lt $RETRY_COUNT ]; then
            sleep 2
        fi
    done
    
    error "$name is unhealthy"
    return 1
}

# Function to check TCP port
check_tcp() {
    local host=$1
    local port=$2
    local name=$3
    
    log "Checking $name TCP connection at $host:$port"
    
    for i in $(seq 1 $RETRY_COUNT); do
        if timeout $TIMEOUT bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            success "$name TCP connection is healthy"
            return 0
        else
            warn "$name TCP connection failed (attempt $i/$RETRY_COUNT)"
        fi
        
        if [ $i -lt $RETRY_COUNT ]; then
            sleep 2
        fi
    done
    
    error "$name TCP connection is unhealthy"
    return 1
}

# Function to check Docker container
check_container() {
    local container_name=$1
    local service_name=$2
    
    log "Checking Docker container: $container_name"
    
    if docker ps --filter "name=$container_name" --filter "status=running" --format "{{.Names}}" | grep -q "$container_name"; then
        # Check container health status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
        
        case $health_status in
            "healthy")
                success "$service_name container is healthy"
                return 0
                ;;
            "unhealthy")
                error "$service_name container is unhealthy"
                return 1
                ;;
            "starting")
                warn "$service_name container is starting"
                return 1
                ;;
            "no-healthcheck")
                warn "$service_name container has no health check configured"
                return 0
                ;;
            *)
                warn "$service_name container health status unknown: $health_status"
                return 1
                ;;
        esac
    else
        error "$service_name container is not running"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    log "Checking database connectivity"
    
    # Check MongoDB
    if check_container "infra_mind_mongodb_prod" "MongoDB"; then
        # Test MongoDB connection
        if docker exec infra_mind_mongodb_prod mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
            success "MongoDB connection test passed"
        else
            error "MongoDB connection test failed"
            return 1
        fi
    else
        return 1
    fi
    
    # Check Redis
    if check_container "infra_mind_redis_prod" "Redis"; then
        # Test Redis connection
        if docker exec infra_mind_redis_prod redis-cli ping | grep -q "PONG"; then
            success "Redis connection test passed"
        else
            error "Redis connection test failed"
            return 1
        fi
    else
        return 1
    fi
}

# Function to check application services
check_application() {
    log "Checking application services"
    
    # Check API service
    if check_container "infra_mind_api_prod" "API"; then
        check_http "http://localhost:8000/health" "API Health Endpoint"
        check_http "http://localhost:8000/docs" "API Documentation" 200
    else
        return 1
    fi
    
    # Check Frontend service
    if check_container "infra_mind_frontend_prod" "Frontend"; then
        check_http "http://localhost:3000" "Frontend" 200
    else
        return 1
    fi
}

# Function to check monitoring services
check_monitoring() {
    log "Checking monitoring services"
    
    # Check Prometheus (if running)
    if docker ps --filter "name=infra_mind_prometheus_prod" --filter "status=running" --format "{{.Names}}" | grep -q "infra_mind_prometheus_prod"; then
        check_http "http://localhost:9090/-/healthy" "Prometheus"
        check_http "http://localhost:9090/api/v1/query?query=up" "Prometheus Query API"
    else
        warn "Prometheus is not running"
    fi
    
    # Check Grafana (if running)
    if docker ps --filter "name=infra_mind_grafana_prod" --filter "status=running" --format "{{.Names}}" | grep -q "infra_mind_grafana_prod"; then
        check_http "http://localhost:3001/api/health" "Grafana"
    else
        warn "Grafana is not running"
    fi
}

# Function to check system resources
check_resources() {
    log "Checking system resources"
    
    # Check disk space
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        success "Disk usage is healthy ($disk_usage%)"
    elif [ "$disk_usage" -lt 90 ]; then
        warn "Disk usage is high ($disk_usage%)"
    else
        error "Disk usage is critical ($disk_usage%)"
    fi
    
    # Check memory usage
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -lt 80 ]; then
        success "Memory usage is healthy ($memory_usage%)"
    elif [ "$memory_usage" -lt 90 ]; then
        warn "Memory usage is high ($memory_usage%)"
    else
        error "Memory usage is critical ($memory_usage%)"
    fi
    
    # Check CPU load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    cpu_cores=$(nproc)
    cpu_load_percent=$(echo "$cpu_load * 100 / $cpu_cores" | bc -l | cut -d. -f1)
    
    if [ "$cpu_load_percent" -lt 70 ]; then
        success "CPU load is healthy ($cpu_load_percent%)"
    elif [ "$cpu_load_percent" -lt 90 ]; then
        warn "CPU load is high ($cpu_load_percent%)"
    else
        error "CPU load is critical ($cpu_load_percent%)"
    fi
}

# Function to check network connectivity
check_network() {
    log "Checking network connectivity"
    
    # Check external connectivity
    if curl -s --max-time 5 https://api.openai.com > /dev/null; then
        success "External network connectivity is healthy"
    else
        error "External network connectivity failed"
    fi
    
    # Check Docker network
    if docker network ls | grep -q "infra_mind_network"; then
        success "Docker network is healthy"
    else
        error "Docker network is missing"
    fi
}

# Function to generate health report
generate_report() {
    local timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    local report_file="health-report-$(date +'%Y%m%d-%H%M%S').json"
    
    log "Generating health report: $report_file"
    
    cat > "$report_file" <<EOF
{
  "timestamp": "$timestamp",
  "system": {
    "hostname": "$(hostname)",
    "uptime": "$(uptime -p)",
    "load_average": "$(uptime | awk -F'load average:' '{print $2}')",
    "disk_usage": "$disk_usage%",
    "memory_usage": "$memory_usage%",
    "cpu_cores": $cpu_cores
  },
  "containers": {
    "mongodb": "$(docker inspect --format='{{.State.Health.Status}}' infra_mind_mongodb_prod 2>/dev/null || echo 'not-running')",
    "redis": "$(docker inspect --format='{{.State.Health.Status}}' infra_mind_redis_prod 2>/dev/null || echo 'not-running')",
    "api": "$(docker inspect --format='{{.State.Health.Status}}' infra_mind_api_prod 2>/dev/null || echo 'not-running')",
    "frontend": "$(docker inspect --format='{{.State.Health.Status}}' infra_mind_frontend_prod 2>/dev/null || echo 'not-running')"
  },
  "services": {
    "api_health": "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null || echo 'failed')",
    "frontend_health": "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>/dev/null || echo 'failed')"
  }
}
EOF
    
    success "Health report generated: $report_file"
}

# Main health check function
main() {
    log "Starting comprehensive health check..."
    
    local overall_status=0
    
    # Run all health checks
    check_resources || overall_status=1
    check_database || overall_status=1
    check_application || overall_status=1
    check_monitoring || overall_status=1
    check_network || overall_status=1
    
    # Generate report
    generate_report
    
    if [ $overall_status -eq 0 ]; then
        success "All health checks passed!"
        exit 0
    else
        error "Some health checks failed!"
        exit 1
    fi
}

# Handle script arguments
case "${1:-check}" in
    "check")
        main
        ;;
    "monitor")
        log "Starting continuous health monitoring (interval: ${HEALTH_CHECK_INTERVAL}s)"
        while true; do
            main
            sleep $HEALTH_CHECK_INTERVAL
        done
        ;;
    "report")
        generate_report
        ;;
    *)
        echo "Usage: $0 [check|monitor|report]"
        echo "  check   - Run health check once (default)"
        echo "  monitor - Run continuous health monitoring"
        echo "  report  - Generate health report only"
        exit 1
        ;;
esac