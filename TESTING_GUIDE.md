# MVP Testing Guide - Real API Integration

This guide walks you through testing the Infra Mind MVP with real APIs, databases, and LLM integration.

## 🎯 What We're Testing

The MVP integration test validates:

- **Environment Configuration**: All required API keys and settings
- **Database Connectivity**: MongoDB and Redis connections
- **LLM Integration**: OpenAI GPT-4 for intelligent recommendations
- **Cloud Provider APIs**: AWS, Azure, GCP service data (optional)
- **Multi-Agent System**: CTO, Cloud Engineer, Research, and Report agents
- **Assessment Processing**: Form validation and data processing
- **Workflow Orchestration**: Agent coordination and task execution
- **API Endpoints**: RESTful API functionality
- **End-to-End Journey**: Complete user workflow from assessment to report

## 🚀 Quick Start (Automated)

The easiest way to test the complete system:

```bash
# Run complete automated test
make test-mvp
```

This will:
1. Check/setup your environment
2. Start all Docker services
3. Run comprehensive integration tests
4. Perform health checks
5. Show you the results

## 📋 Manual Setup Process

If you prefer step-by-step control:

### Step 1: Setup API Keys

```bash
# Interactive setup for real API keys
make setup-test
# or
python setup_real_test.py
```

This will prompt you for:

**Required:**
- OpenAI API Key (get from https://platform.openai.com/api-keys)

**Optional (for enhanced testing):**
- AWS credentials (for real pricing data)
- Azure credentials (for service comparisons)  
- GCP credentials (for multi-cloud analysis)

### Step 2: Start the System

```bash
# Deploy development environment
make deploy-dev
```

Wait 30-60 seconds for all services to start.

### Step 3: Run Integration Tests

```bash
# Run comprehensive integration tests
make test-integration
# or
python test_full_integration.py
```

### Step 4: Check System Health

```bash
# Run health check
make health-check
```

## 🔑 API Key Requirements

### Required APIs

| Service | Purpose | How to Get |
|---------|---------|------------|
| OpenAI | LLM for intelligent recommendations | https://platform.openai.com/api-keys |

### Optional APIs (Enhanced Testing)

| Service | Purpose | How to Get |
|---------|---------|------------|
| AWS | Real pricing data, service info | https://console.aws.amazon.com/iam/ |
| Azure | Service comparisons, pricing | https://portal.azure.com/ (App Registration) |
| GCP | Multi-cloud analysis | https://console.cloud.google.com/ (Service Account) |

## 🧪 Test Scenarios

The integration test covers these scenarios:

### 1. Basic System Health
- Environment variables loaded correctly
- Database connections established
- Cache system operational
- API endpoints responding

### 2. LLM Integration
- OpenAI API connectivity
- Intelligent response generation
- Error handling and retries

### 3. Cloud Provider Integration
- AWS service discovery (if configured)
- Azure pricing data (if configured)
- GCP resource analysis (if configured)

### 4. Multi-Agent Workflow
- CTO Agent: Strategic analysis
- Cloud Engineer Agent: Architecture recommendations
- Research Agent: Market intelligence
- Report Generator Agent: Professional reports

### 5. End-to-End User Journey
```
User Assessment → Multi-Agent Analysis → Comprehensive Report
```

## 📊 Understanding Test Results

### Success Indicators
- ✅ **PASS**: Test completed successfully
- 🎉 **80%+ Success Rate**: System ready for production

### Warning Indicators  
- ⚠️ **60-79% Success Rate**: Some issues, but functional
- 🔥 **ERROR**: Critical failure requiring attention

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| OpenAI API Error | Invalid/missing API key | Run `make setup-test` |
| Database Connection Failed | Docker not running | Start Docker, run `make deploy-dev` |
| Port Already in Use | Previous deployment running | Run `make docker-down` first |
| Cloud API Timeout | Network/credential issues | Check credentials, network |

## 🔍 Detailed Test Output

The integration test generates:

1. **Console Output**: Real-time test progress with colors
2. **JSON Report**: Detailed results saved to `integration_test_results_*.json`
3. **Health Check**: System resource usage and status

### Sample Success Output
```
🔍 Checking Infra Mind deployment health...

📦 Container Status:
✅ API container is running
✅ Frontend container is running  
✅ MongoDB container is running
✅ Redis container is running

🌐 HTTP Health Checks:
✅ API is healthy
✅ Frontend is healthy

🗄️ Database Connections:
✅ MongoDB connection is healthy
✅ Redis connection is healthy

🎉 Health check completed!
```

## 🌐 Accessing the System

After successful testing, access your MVP:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | User interface |
| API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| MongoDB Express | http://localhost:8081 | Database management (dev only) |
| Redis Commander | http://localhost:8082 | Cache management (dev only) |

## 🛠️ Troubleshooting

### Docker Issues
```bash
# Check Docker status
docker info

# View container logs
make docker-logs

# Restart services
make docker-down
make deploy-dev
```

### API Key Issues
```bash
# Reconfigure API keys
make setup-test

# Check environment
cat .env | grep -v "SECRET\|PASSWORD"
```

### Database Issues
```bash
# Check database connectivity
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec redis redis-cli ping
```

### Network Issues
```bash
# Check port availability
lsof -i :3000
lsof -i :8000
lsof -i :27017
lsof -i :6379
```

## 📈 Performance Expectations

### Resource Usage
- **Memory**: ~2-4GB total for all containers
- **CPU**: Moderate during LLM calls, low at rest
- **Disk**: ~1GB for Docker images, ~100MB for data

### Response Times
- **Simple API calls**: <100ms
- **LLM-powered responses**: 2-10 seconds
- **Cloud API queries**: 1-5 seconds
- **Complete assessment**: 30-60 seconds

## 🔒 Security Notes

### Development Environment
- Default passwords (change for production)
- Debug mode enabled
- CORS allows localhost

### Production Considerations
- Use strong passwords in `.env.prod`
- Disable debug mode
- Configure proper CORS origins
- Use HTTPS with SSL certificates
- Implement proper authentication

## 📝 Next Steps

After successful testing:

1. **Production Deployment**: Use `make deploy-prod` with `.env.prod`
2. **Custom Configuration**: Modify settings in `src/infra_mind/core/config.py`
3. **Add Features**: Extend agents in `src/infra_mind/agents/`
4. **Scale System**: Configure load balancing and clustering
5. **Monitor Performance**: Set up logging and metrics collection

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**: `make docker-logs`
2. **Run Health Check**: `make health-check`
3. **Review Test Results**: Check the generated JSON report
4. **Verify Configuration**: Ensure all required API keys are set
5. **Restart System**: `make docker-down && make deploy-dev`

The MVP is designed to be robust and provide clear error messages to help you identify and resolve issues quickly.