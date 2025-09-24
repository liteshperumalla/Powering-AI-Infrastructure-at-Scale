# Infra Mind: AI Infrastructure Advisory Platform

An enterprise-grade AI platform that empowers organizations to strategically plan, optimize, and scale their AI infrastructure across multi-cloud environments.

[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue)](https://www.docker.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green)](https://www.mongodb.com/)

## Overview

**Infra Mind** is a comprehensive AI-powered advisory platform that transforms how organizations approach AI infrastructure planning and scaling. Built for modern enterprises dealing with complex multi-cloud environments, cost optimization challenges, and compliance requirements.

### Problem Statement

Organizations struggle with:
- Complex AI Infrastructure Decisions: Multi-cloud strategy, vendor selection, architecture design
- Cost Optimization: Balancing performance, cost, and scalability across cloud providers
- Compliance Requirements: Meeting regulatory standards while maintaining operational efficiency
- Strategic Planning: Long-term infrastructure roadmaps and technology decisions

### Solution Architecture

A multi-agent AI system featuring specialized AI agents that collaboratively:
- Analyze infrastructure requirements and current architecture
- Provide real-time cloud provider comparisons (AWS, Azure, GCP)
- Generate comprehensive assessments and strategic recommendations
- Deliver actionable insights for infrastructure optimization

## Technical Stack

### Frontend (Next.js 14 + TypeScript)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.0+
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Redux Toolkit
- **Styling**: Emotion + Material-UI theming
- **Charts**: Recharts, D3.js integration
- **Authentication**: Google OAuth integration

### Backend (FastAPI + Python)
- **Framework**: FastAPI with async/await support
- **Language**: Python 3.11+
- **AI Integration**: OpenAI GPT-4, Azure OpenAI
- **Orchestration**: LangChain for AI workflow management
- **Authentication**: JWT tokens, OAuth2 flows
- **API Documentation**: Auto-generated OpenAPI/Swagger
- **Background Tasks**: Celery with Redis broker

### Database & Storage
- **Primary Database**: MongoDB 7.0
- **Caching**: Redis 7.2
- **Session Management**: Redis-based session store
- **File Storage**: Local filesystem with Docker volumes
- **Data Models**: Pydantic for validation and serialization

### Infrastructure & Deployment
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development
- **Process Management**: Gunicorn with Uvicorn workers
- **Reverse Proxy**: Built-in Docker networking
- **Health Checks**: Container-level health monitoring
- **Logging**: Structured logging with JSON format

## Quick Start

### Prerequisites
```bash
# Required
Docker >= 20.10
Docker Compose >= 2.0
Git

# API Keys (OpenAI required)
OpenAI API Key or Azure OpenAI credentials
Google OAuth Client ID (optional)
```

### Installation
```bash
# Clone repository
git clone https://github.com/your-org/Powering-AI-Infrastructure-at-Scale.git
cd Powering-AI-Infrastructure-at-Scale

# Setup environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration
Edit `.env` file:
```bash
# Required - AI Integration
INFRA_MIND_AZURE_OPENAI_API_KEY=your_api_key
INFRA_MIND_AZURE_OPENAI_ENDPOINT=your_endpoint
INFRA_MIND_AZURE_OPENAI_DEPLOYMENT=gpt-4
INFRA_MIND_AZURE_OPENAI_API_VERSION=2024-02-01

# Optional - Authentication
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id

# Database
INFRA_MIND_MONGODB_URL=mongodb://admin:password@mongodb:27017/infra_mind?authSource=admin
INFRA_MIND_REDIS_URL=redis://redis:6379

# Security
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
INFRA_MIND_SECRET_KEY=your_app_secret_key_change_in_production
```

### Run Application
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Points
```
Frontend:    http://localhost:3000
API:         http://localhost:8000
API Docs:    http://localhost:8000/docs
MongoDB:     mongodb://localhost:27017
Redis:       redis://localhost:6379
```

## Development

### Local Development Setup
```bash
# Start development environment
docker-compose up -d

# Access containers for debugging
docker exec -it infra_mind_frontend bash
docker exec -it infra_mind_api bash
docker exec -it infra_mind_mongodb mongosh -u admin -p password --authenticationDatabase admin
```

### Frontend Development
```bash
cd frontend-react

# Install dependencies
npm install

# Development server (outside container)
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Testing
npm test
npm run test:coverage
```

### Backend Development
```bash
cd src

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn infra_mind.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest

# Type checking
mypy .
```

### Database Operations
```bash
# MongoDB shell
docker exec -it infra_mind_mongodb mongosh -u admin -p password --authenticationDatabase admin infra_mind

# Redis CLI
docker exec -it infra_mind_redis redis-cli

# Clear all data
docker exec infra_mind_mongodb mongosh -u admin -p password --authenticationDatabase admin infra_mind --eval "db.dropDatabase()"
docker exec infra_mind_redis redis-cli FLUSHALL
```

## Application Features

### Core Modules
- **Dashboard**: Executive overview, metrics, and KPIs
- **Assessments**: Infrastructure evaluation workflows
- **Analytics**: Performance analysis and cost optimization
- **Recommendations**: AI-generated improvement suggestions
- **Chat**: Interactive AI assistant for infrastructure guidance
- **Reports**: Comprehensive analysis and strategy documents

### Assessment Engine
- Multi-step infrastructure evaluation
- AI-powered analysis with specialized agents
- Real-time cloud provider comparisons
- Custom assessment templates
- Progress tracking and session management

### AI Agent System
- **CTO Agent**: Strategic decision-making and high-level architecture
- **Cloud Engineer Agent**: Technical implementation and best practices
- **Research Agent**: Market analysis and technology trends
- **Report Agent**: Documentation and professional report generation

### Additional Features
- Quality management and scoring
- Budget forecasting and cost modeling
- Executive dashboards with strategic KPIs
- GitOps workflow integration
- Vendor lock-in analysis
- Compliance gap analysis

## API Reference

### Authentication
```bash
# Get JWT token
POST /auth/login
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "password"
}

# Use token in requests
Authorization: Bearer <jwt_token>
```

### Core Endpoints
```bash
# Assessments
GET    /api/assessments              # List assessments
POST   /api/assessments              # Create assessment
GET    /api/assessments/{id}         # Get assessment
PUT    /api/assessments/{id}         # Update assessment
DELETE /api/assessments/{id}         # Delete assessment

# Reports
GET    /api/reports                  # List reports
POST   /api/reports                  # Generate report
GET    /api/reports/{id}             # Get report

# Chat
POST   /api/chat/conversations       # Start conversation
POST   /api/chat/messages            # Send message
GET    /api/chat/conversations/{id}  # Get conversation

# Health check
GET    /health                       # Service health status
```

## Testing

### Frontend Testing
```bash
cd frontend-react

# Unit tests
npm test

# Coverage report
npm run test:coverage

# E2E tests (if configured)
npm run test:e2e
```

### Backend Testing
```bash
cd src

# Run all tests
python -m pytest

# With coverage
python -m pytest --cov=infra_mind --cov-report=html

# Specific test file
python -m pytest tests/test_assessments.py

# Integration tests
python -m pytest tests/integration/
```

## Deployment

### Production Build
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production environment
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
```bash
# Production settings
INFRA_MIND_ENVIRONMENT=production
INFRA_MIND_DEBUG=false

# Security (generate secure keys)
JWT_SECRET_KEY=<secure-random-key>
INFRA_MIND_SECRET_KEY=<secure-random-key>

# Database
INFRA_MIND_MONGODB_URL=<production-mongodb-url>
INFRA_MIND_REDIS_URL=<production-redis-url>

# CORS origins
INFRA_MIND_CORS_ORIGINS='["https://yourdomain.com"]'
```

## Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/db

# Service metrics
docker-compose ps
docker stats
```

### Logging
```bash
# Application logs
docker-compose logs frontend
docker-compose logs api

# Follow logs
docker-compose logs -f --tail=100
```

## Troubleshooting

### Common Issues
```bash
# Port conflicts
docker-compose down
sudo lsof -i :3000  # Check what's using port 3000
sudo lsof -i :8000  # Check what's using port 8000

# Container issues
docker-compose down --volumes  # Remove volumes
docker system prune            # Clean up Docker

# Permission issues
sudo chown -R $USER:$USER .    # Fix file permissions
```

### Database Issues
```bash
# Reset database
docker-compose down
docker volume rm powering-ai-infrastructure-at-scale_mongodb_data
docker-compose up -d

# Check MongoDB connection
docker exec infra_mind_mongodb mongosh --eval "db.adminCommand('ping')"
```

## Documentation

- **[API Documentation](API_README.md)** - Detailed API reference
- **[Cloud Setup Guide](CLOUD_API_SETUP.md)** - Cloud provider integration
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **[Testing Guide](TESTING_GUIDE.md)** - Testing strategies

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes with tests
4. Run linting and tests
5. Submit pull request

### Code Standards
- **TypeScript**: Strict mode enabled
- **Python**: PEP 8 compliance, type hints required
- **Testing**: Unit tests for new features
- **Documentation**: Update relevant docs

## Recent Updates

### September 2024
- Complete system rebuild with improved architecture
- Enhanced UI/UX with Material-UI design system
- Performance optimizations and code cleanup
- Database schema improvements
- Comprehensive documentation updates
- Removed 25+ deprecated fix scripts and temporary files
- Streamlined environment configuration
- Improved error handling and user feedback

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Infra Mind** - Enterprise AI infrastructure advisory platform for strategic decision-making and optimization.