# Infra Mind - AI Infrastructure Advisory Platform

An intelligent, AI-powered advisory platform that empowers businesses to strategically plan, simulate, and scale their AI infrastructure.

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Deploy System**:
   ```bash
   make deploy-dev
   ```

3. **Access Services**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Testing

Run comprehensive integration tests:
```bash
make test-mvp
```

## Documentation

- [Testing Guide](TESTING_GUIDE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [MVP Testing Summary](MVP_TESTING_SUMMARY.md)

## Features

- Multi-agent AI system (CTO, Cloud Engineer, Research, Report agents)
- Real-time cloud provider analysis (AWS, Azure, GCP)
- Intelligent cost optimization recommendations
- Compliance requirement mapping
- Professional report generation
- Interactive web interface

## Architecture

- **Backend**: FastAPI with multi-agent orchestration
- **Frontend**: React.js with TypeScript
- **Database**: MongoDB + Redis
- **AI**: OpenAI GPT-4 integration
- **Cloud**: Multi-cloud provider APIs
- **Deployment**: Docker + Docker Compose