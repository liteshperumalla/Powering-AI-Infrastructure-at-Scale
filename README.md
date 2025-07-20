# 🚀 Infra Mind - AI-Powered Infrastructure Advisory Platform

Infra Mind is an intelligent, AI-powered advisory platform that empowers businesses to strategically plan, simulate, and scale their AI infrastructure. The platform leverages multi-agent AI systems and comprehensive cloud expertise to provide context-driven, actionable recommendations for building scalable, compliant, and cost-effective AI ecosystems.

## ✨ Features

- **Multi-Agent AI System**: Specialized AI agents for CTO strategy, MLOps, cloud engineering, compliance, and research
- **Multi-Cloud Intelligence**: Deep expertise across AWS, Azure, and GCP platforms
- **Compliance Integration**: Built-in regulatory awareness for GDPR, HIPAA, CCPA compliance
- **Professional Reports**: Detailed AI Infrastructure Strategy Reports with executive and technical roadmaps
- **Real-Time Pricing**: Live cloud service pricing and capability data
- **Simulation & Modeling**: Infrastructure scaling scenarios and cost projections

## 🏗️ Architecture

- **Backend**: FastAPI with async operations
- **Database**: MongoDB with Beanie ODM
- **Caching**: Redis for performance optimization
- **AI Framework**: LangChain + LangGraph for agent orchestration
- **Cloud APIs**: Integration with AWS, Azure, and GCP services
- **Frontend**: React with TypeScript (coming soon)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key (for AI agents)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd infra-mind
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start with Docker Compose (Recommended)**
   ```bash
   make docker-up
   ```

4. **Or install locally**
   ```bash
   make dev
   make run
   ```

### Verify Installation

```bash
# Test database connections
make test-conn

# View database info
make db-info

# Check API health
curl http://localhost:8000/health
```

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MongoDB Express**: http://localhost:8081 (with tools profile)
- **Redis Commander**: http://localhost:8082 (with tools profile)

## 🛠️ Development Commands

```bash
# Development
make run          # Run application with auto-reload
make test         # Run tests
make format       # Format code
make lint         # Run linting
make type-check   # Run type checking

# Docker
make docker-up    # Start all services
make docker-down  # Stop all services
make docker-logs  # View logs
make docker-tools # Start with management tools

# Database
make db-info      # Show database information
make test-conn    # Test connections
```

## 🏛️ Project Structure

```
src/infra_mind/
├── api/                 # FastAPI routes and endpoints
│   ├── endpoints/       # API endpoint implementations
│   └── routes.py        # Main router configuration
├── core/                # Core application components
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection and setup
│   └── logging.py       # Logging configuration
├── models/              # Beanie document models
│   ├── assessment.py    # Assessment data model
│   ├── recommendation.py # AI recommendations model
│   ├── report.py        # Generated reports model
│   ├── user.py          # User management model
│   └── ...
├── agents/              # AI agent implementations (coming soon)
├── services/            # Business logic services (coming soon)
└── main.py              # FastAPI application entry point
```

## 🤖 AI Agents (MVP)

The platform includes specialized AI agents:

1. **CTO Agent**: Strategic planning and business alignment
2. **Cloud Engineer Agent**: Multi-cloud service recommendations
3. **Research Agent**: Real-time cloud data collection and analysis

## 🔧 Configuration

Key environment variables:

```bash
# Application
INFRA_MIND_ENVIRONMENT=development
INFRA_MIND_DEBUG=true
INFRA_MIND_SECRET_KEY=your-secret-key

# Database
INFRA_MIND_MONGODB_URL=mongodb://localhost:27017
INFRA_MIND_REDIS_URL=redis://localhost:6379

# AI
INFRA_MIND_OPENAI_API_KEY=your-openai-key

# Cloud Providers
INFRA_MIND_AWS_ACCESS_KEY_ID=your-aws-key
INFRA_MIND_AZURE_CLIENT_ID=your-azure-id
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=src/infra_mind tests/
```

## 📦 Deployment

### Docker Production Build

```bash
docker build -t infra-mind:latest .
docker run -p 8000:8000 infra-mind:latest
```

### Environment-Specific Deployment

- **Development**: Use Docker Compose with hot reload
- **Staging**: Deploy with environment-specific configurations
- **Production**: Use container orchestration (Kubernetes recommended)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [Coming Soon]
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🗺️ Roadmap

### MVP (4 weeks)
- ✅ Project foundation and database setup
- 🔄 Core AI agents (CTO, Cloud Engineer, Research)
- 🔄 AWS and Azure API integration
- 🔄 Basic React frontend
- 🔄 Report generation

### Post-MVP Extensions
- Additional AI agents (MLOps, Compliance, AI Consultant, Web Research, Simulation)
- GCP integration
- Advanced analytics and monitoring
- Enterprise security features
- Advanced reporting and visualization

---

**Built with ❤️ for the AI infrastructure community**