# Deployment Guide

This guide covers deploying Infra Mind using Docker containers for both development and production environments.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available for containers
- 10GB+ disk space

## Quick Start (Development)

1. **Clone and setup environment**:
   ```bash
   git clone <repository>
   cd Powering-AI-Infrastructure-at-Scale
   cp .env.example .env
   ```

2. **Configure environment variables**:
   Edit `.env` with your API keys and configuration:
   ```bash
   # Required for basic functionality
   INFRA_MIND_OPENAI_API_KEY=your-openai-api-key
   INFRA_MIND_SECRET_KEY=your-secret-key
   
   # Optional cloud provider keys
   INFRA_MIND_AWS_ACCESS_KEY_ID=your-aws-key
   INFRA_MIND_AWS_SECRET_ACCESS_KEY=your-aws-secret
   ```

3. **Deploy development environment**:
   ```bash
   make deploy-dev
   # or
   ./scripts/deploy.sh development
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Production Deployment

1. **Setup production environment**:
   ```bash
   cp .env.prod.example .env.prod
   ```

2. **Configure production variables**:
   Edit `.env.prod` with secure production values:
   ```bash
   # Database security
   MONGO_ROOT_USERNAME=admin
   MONGO_ROOT_PASSWORD=secure-password-here
   REDIS_PASSWORD=secure-redis-password
   
   # Application security
   SECRET_KEY=very-secure-secret-key-at-least-32-chars
   CORS_ORIGINS=["https://yourdomain.com"]
   
   # API keys
   OPENAI_API_KEY=your-production-openai-key
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   ```

3. **Deploy production environment**:
   ```bash
   make deploy-prod
   # or
   ./scripts/deploy.sh production
   ```

## Architecture Overview

The deployment consists of the following containers:

### Core Services
- **API Container**: FastAPI application with multi-agent system
- **Frontend Container**: Next.js React application
- **MongoDB**: Document database for assessments and recommendations
- **Redis**: Cache and session storage

### Optional Services
- **Nginx**: Reverse proxy and load balancer (production)
- **MongoDB Express**: Database management UI (development)
- **Redis Commander**: Redis management UI (development)

## Container Details

### API Container
- **Base Image**: Python 3.11 slim
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Volumes**: `./logs:/app/logs`

### Frontend Container
- **Base Image**: Node 20 Alpine
- **Port**: 3000
- **Health Check**: `/health` endpoint
- **Build**: Next.js standalone output

### Database Containers
- **MongoDB**: Port 27017, persistent volume
- **Redis**: Port 6379, persistent volume with AOF

## Environment Configuration

### Development (.env)
```bash
# Application
INFRA_MIND_ENVIRONMENT=development
INFRA_MIND_DEBUG=true
INFRA_MIND_SECRET_KEY=dev-secret-key

# Database
INFRA_MIND_MONGODB_URL=mongodb://localhost:27017
INFRA_MIND_REDIS_URL=redis://localhost:6379

# LLM
INFRA_MIND_OPENAI_API_KEY=your-key
```

### Production (.env.prod)
```bash
# Application
INFRA_MIND_ENVIRONMENT=production
INFRA_MIND_DEBUG=false
SECRET_KEY=secure-production-key

# Database with authentication
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=secure-password
REDIS_PASSWORD=secure-redis-password

# Security
CORS_ORIGINS=["https://yourdomain.com"]
RATE_LIMIT_REQUESTS=1000
```

## Management Commands

### Basic Operations
```bash
# Start services
make deploy-dev          # Development
make deploy-prod         # Production

# Check status
make deploy-status       # Container status
docker-compose ps        # Detailed status

# View logs
make docker-logs         # All services
docker-compose logs api  # Specific service

# Stop services
make docker-down         # Stop all
docker-compose stop api  # Stop specific service
```

### Development Tools
```bash
# Start with management tools
docker-compose --profile tools up -d

# Access tools
# MongoDB Express: http://localhost:8081
# Redis Commander: http://localhost:8082
```

### Maintenance
```bash
# Update containers
docker-compose pull
make docker-build
make deploy-dev

# Clean up
docker system prune -f
docker volume prune -f
```

## Health Monitoring

All services include health checks:

```bash
# Check all service health
curl http://localhost:8000/health  # API
curl http://localhost:3000/health  # Frontend

# Container health status
docker-compose ps
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using ports
   lsof -i :3000
   lsof -i :8000
   lsof -i :27017
   ```

2. **Memory issues**:
   ```bash
   # Check Docker memory usage
   docker stats
   
   # Increase Docker memory limit in Docker Desktop
   ```

3. **Permission issues**:
   ```bash
   # Fix log directory permissions
   sudo chown -R $USER:$USER logs/
   ```

4. **Database connection issues**:
   ```bash
   # Check MongoDB logs
   docker-compose logs mongodb
   
   # Test connection
   docker-compose exec mongodb mongosh
   ```

### Log Locations

- **Application logs**: `./logs/` directory
- **Container logs**: `docker-compose logs <service>`
- **System logs**: Docker Desktop logs

### Performance Tuning

1. **Resource allocation**:
   - Minimum 4GB RAM for all services
   - 2 CPU cores recommended
   - 10GB disk space for data volumes

2. **Database optimization**:
   - MongoDB indexes are created automatically
   - Redis persistence enabled with AOF

3. **Caching**:
   - API responses cached for 1 hour
   - Static assets cached by Nginx

## Security Considerations

### Development
- Default passwords (change for any network-accessible deployment)
- Debug mode enabled
- CORS allows localhost origins

### Production
- Strong passwords required
- Debug mode disabled
- HTTPS recommended (configure Nginx SSL)
- Rate limiting enabled
- Security headers configured

## Backup and Recovery

### Database Backup
```bash
# MongoDB backup
docker-compose exec mongodb mongodump --out /data/backup

# Redis backup
docker-compose exec redis redis-cli BGSAVE
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v infra_mind_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz /data
```

## Scaling

### Horizontal Scaling
- API containers can be scaled with load balancer
- Frontend containers can be scaled behind CDN
- Database requires replica set configuration

### Vertical Scaling
- Increase container resource limits in docker-compose
- Monitor with `docker stats`

## Support

For deployment issues:
1. Check logs: `make docker-logs`
2. Verify health: `curl http://localhost:8000/health`
3. Check configuration: Environment variables
4. Review documentation: API docs at `/docs`