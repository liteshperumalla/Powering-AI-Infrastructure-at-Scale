# Infra Mind API Gateway

## Overview

The Infra Mind API Gateway provides REST endpoints for the AI-powered infrastructure advisory platform. It coordinates specialized AI agents to provide comprehensive infrastructure recommendations, compliance guidance, and strategic roadmaps for enterprises scaling their AI initiatives.

## Features

- **Multi-Agent Orchestration**: Coordinate specialized AI agents (CTO, Cloud Engineer, Research)
- **Cloud Service Integration**: Real-time data from AWS, Azure, and GCP APIs
- **Professional Reports**: Generate executive summaries and technical roadmaps
- **Compliance Guidance**: GDPR, HIPAA, and CCPA compliance recommendations
- **OpenAPI Documentation**: Auto-generated API documentation with Swagger UI

## Quick Start

### 1. Start the API Server

```bash
# Navigate to the project directory
cd Powering-AI-Infrastructure-at-Scale

# Start the API server
python api/app.py
```

The API will be available at `http://localhost:8000`

### 2. View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# List assessments
curl http://localhost:8000/api/v1/assessments/

# Get recommendations
curl http://localhost:8000/api/v1/recommendations/test-123
```

## API Endpoints

### Health & System
- `GET /health` - System health check
- `GET /` - API information

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/profile` - Get user profile
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/change-password` - Change password
- `GET /api/v1/auth/verify-token` - Verify JWT token

### Assessments
- `POST /api/v1/assessments/` - Create new assessment
- `GET /api/v1/assessments/` - List assessments (paginated)
- `GET /api/v1/assessments/{id}` - Get specific assessment
- `PUT /api/v1/assessments/{id}` - Update assessment
- `DELETE /api/v1/assessments/{id}` - Delete assessment
- `POST /api/v1/assessments/{id}/start` - Start AI agent analysis

### Recommendations
- `GET /api/v1/recommendations/{assessment_id}` - Get all recommendations
- `POST /api/v1/recommendations/{assessment_id}/generate` - Generate new recommendations
- `GET /api/v1/recommendations/{assessment_id}/agents/{agent_name}` - Get agent-specific recommendation
- `POST /api/v1/recommendations/{assessment_id}/validate` - Validate recommendations

### Reports
- `GET /api/v1/reports/{assessment_id}` - List reports for assessment
- `POST /api/v1/reports/{assessment_id}/generate` - Generate new report
- `GET /api/v1/reports/{assessment_id}/reports/{report_id}` - Get specific report
- `GET /api/v1/reports/{assessment_id}/reports/{report_id}/download` - Download report file
- `GET /api/v1/reports/{assessment_id}/preview` - Preview report content
- `POST /api/v1/reports/{assessment_id}/reports/{report_id}/retry` - Retry failed report generation

## Example Usage

### Create an Assessment

```bash
curl -X POST "http://localhost:8000/api/v1/assessments/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Infrastructure Assessment",
    "description": "Assessment for scaling our AI platform",
    "business_requirements": {
      "company_size": "medium",
      "industry": "technology",
      "business_goals": [
        {
          "goal": "Reduce costs by 30%",
          "priority": "high",
          "timeline_months": 6,
          "success_metrics": ["Cost reduction", "Performance maintained"]
        }
      ],
      "growth_projection": {
        "current_users": 1000,
        "projected_users_12m": 5000
      },
      "budget_constraints": {
        "total_budget_range": "100k_500k",
        "cost_optimization_priority": "high"
      },
      "team_structure": {
        "total_developers": 5,
        "senior_developers": 2,
        "cloud_expertise_level": 3
      },
      "project_timeline_months": 6
    },
    "technical_requirements": {
      "workload_types": ["web_application", "data_processing"],
      "performance_requirements": {
        "api_response_time_ms": 200,
        "requests_per_second": 1000
      },
      "scalability_requirements": {
        "auto_scaling_required": true,
        "peak_load_multiplier": 5.0
      },
      "security_requirements": {
        "encryption_at_rest_required": true,
        "encryption_in_transit_required": true
      },
      "integration_requirements": {
        "rest_api_required": true
      }
    }
  }'
```

### Generate Recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/{assessment_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_names": ["cto_agent", "cloud_engineer_agent", "research_agent"],
    "priority_override": "high"
  }'
```

### Generate Report

```bash
curl -X POST "http://localhost:8000/api/v1/reports/{assessment_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "executive_summary",
    "format": "pdf",
    "title": "Executive Infrastructure Strategy",
    "sections": ["summary", "recommendations", "cost_analysis"]
  }'
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "id": "assessment-123",
  "title": "My Assessment",
  "status": "completed",
  "created_at": "2025-01-23T10:00:00Z",
  ...
}
```

### Error Response
```json
{
  "error": "Validation error",
  "message": "Invalid input data",
  "status_code": 400,
  "request_id": "req-123"
}
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/assessments/
```

## Rate Limiting

API calls are rate-limited to ensure fair usage:
- 100 requests per minute per user
- 1000 requests per hour per user

## Testing

Run the test suite to verify API functionality:

```bash
python test_api_gateway.py
```

This will:
- Test all endpoint functionality
- Generate OpenAPI specification
- Validate response formats
- Create endpoint summary

## Development

### Project Structure
```
api/
├── app.py                 # Main FastAPI application
└── routers/              # API route handlers

src/infra_mind/
├── api/
│   ├── routes.py         # Main API router
│   └── endpoints/        # Individual endpoint modules
│       ├── auth.py       # Authentication endpoints
│       ├── assessments.py # Assessment endpoints
│       ├── recommendations.py # Recommendation endpoints
│       └── reports.py    # Report endpoints
├── schemas/              # Pydantic data models
├── models/               # Database models
└── core/                 # Core functionality
```

### Adding New Endpoints

1. Create endpoint module in `src/infra_mind/api/endpoints/`
2. Add router to `src/infra_mind/api/routes.py`
3. Update OpenAPI documentation
4. Add tests to `test_api_gateway.py`

## Configuration

The API uses environment variables for configuration:

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=infra_mind

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
```

## Next Steps

1. **Database Integration**: Connect to MongoDB for persistent data storage
2. **Authentication**: Implement JWT token validation and user management
3. **Agent Integration**: Connect to LangGraph multi-agent workflow system
4. **Cloud APIs**: Integrate with AWS, Azure, and GCP APIs for real-time data
5. **Report Generation**: Implement PDF and document generation
6. **Monitoring**: Add metrics collection and health monitoring
7. **Deployment**: Configure for production deployment with Docker/Kubernetes

## Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the OpenAPI specification at `/openapi.json`
3. Run the test suite with `python test_api_gateway.py`
4. Check logs for detailed error information