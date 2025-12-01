"""
Enhanced API documentation for Infra Mind platform.
Provides comprehensive OpenAPI documentation with examples and integration guides.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_enhanced_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """Generate enhanced OpenAPI schema with comprehensive documentation."""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Infra Mind API",
        version="2.0.0",
        description="""
# Infra Mind API Documentation

Welcome to the comprehensive Infra Mind API documentation. This platform provides AI-powered infrastructure advisory services with enterprise-grade features.

## 🚀 Getting Started

### Authentication
All API endpoints require authentication using JWT tokens. Obtain your token by registering and logging in:

1. **Register**: `POST /api/v2/auth/register`
2. **Login**: `POST /api/v2/auth/login`
3. **Use Token**: Include `Authorization: Bearer <token>` header in all requests

### Base URLs
- **Production**: `https://api.infra-mind.com`
- **Staging**: `https://staging-api.infra-mind.com`
- **Development**: `http://localhost:8000`

## 🏗️ Core Features

### Infrastructure Assessments
Create and manage comprehensive infrastructure assessments with AI-powered recommendations:
- **Create Assessment**: `POST /api/v2/assessments/`
- **List Assessments**: `GET /api/v2/assessments/`
- **Get Assessment**: `GET /api/v2/assessments/{assessment_id}`
- **Start Assessment**: `POST /api/v2/assessments/{assessment_id}/start`

### AI-Powered Recommendations
Get intelligent recommendations from our multi-agent AI system:
- **Get Recommendations**: `GET /api/v2/recommendations/{assessment_id}`
- **Generate Recommendations**: `POST /api/v2/recommendations/{assessment_id}/generate`
- **Validate Recommendations**: `POST /api/v2/recommendations/{assessment_id}/validate`

### Enterprise Reports
Generate professional reports in multiple formats:
- **Generate Report**: `POST /api/v2/reports/assessment/{assessment_id}/generate`
- **Download Report**: `GET /api/v2/reports/{report_id}/download`
- **Share Report**: `POST /api/v2/reports/{report_id}/share`

## 🎯 Enterprise Features

### A/B Testing & Experiments
Advanced experimentation platform for testing infrastructure changes:
- **Create Experiment**: `POST /api/v2/experiments/`
- **Get User Variant**: `GET /api/v2/experiments/feature/{feature_flag}/variant`
- **Track Events**: `POST /api/v2/experiments/feature/{feature_flag}/track`

### Feedback Collection
Comprehensive feedback system for continuous improvement:
- **Submit Feedback**: `POST /api/v2/feedback/`
- **Get Analytics**: `GET /api/v2/feedback/analytics/dashboard`
- **Health Check**: `GET /api/v2/feedback/health`

### Quality Assurance
Advanced quality metrics and validation:
- **Submit Quality Metrics**: `POST /api/v2/quality/metrics`
- **Get Quality Overview**: `GET /api/v2/quality/overview`
- **Quality Trends**: `GET /api/v2/quality/trends`

### Third-Party Integrations
Connect with your existing tools and workflows:
- **Business Tools**: Slack, Teams, Email, Calendar
- **Compliance**: Industry-specific compliance frameworks
- **SSO Providers**: SAML, OAuth, OIDC

## 📊 Analytics & Monitoring

### Performance Monitoring
Real-time performance insights and optimization:
- **Dashboard Data**: `GET /api/v2/performance/dashboard-data`
- **Metrics**: `GET /api/v2/performance/metrics`
- **Alerts**: `GET /api/v2/performance/alerts`

### Compliance Monitoring
Automated compliance tracking and reporting:
- **Compliance Dashboard**: `GET /api/v2/compliance/dashboard`
- **Audit Trail**: `GET /api/v2/compliance/audits`
- **Generate Reports**: `POST /api/v2/compliance/reports/compliance`

### Advanced Analytics
Deep insights into your infrastructure and usage patterns:
- **Comprehensive Dashboard**: `GET /api/v2/advanced-analytics/dashboard`
- **Cost Predictions**: `GET /api/v2/advanced-analytics/cost-predictions`
- **Security Audit**: `POST /api/v2/advanced-analytics/security-audit`

## 🔧 Administration

### Admin Features (Admin Access Required)
- **User Management**: `GET /api/v2/admin/users`
- **System Health**: `GET /api/v2/admin/health/detailed`
- **Analytics**: `GET /api/v2/admin/analytics/comprehensive`

### System Resilience
Built-in resilience and failover capabilities:
- **Health Checks**: `GET /api/v2/resilience/health/system`
- **Circuit Breakers**: `GET /api/v2/resilience/circuit-breakers`
- **Failover Management**: `GET /api/v2/resilience/failover/status`

## 📝 Response Formats

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔐 Security

- **HTTPS**: All communications encrypted with TLS 1.3
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Input Validation**: Comprehensive validation of all inputs
- **CORS**: Properly configured cross-origin resource sharing

## 💡 Best Practices

1. **Use appropriate HTTP methods**: GET for retrieval, POST for creation, PUT for updates
2. **Handle errors gracefully**: Always check response status and handle errors appropriately
3. **Implement pagination**: Use `page` and `limit` parameters for large datasets
4. **Cache responses**: Cache GET responses when appropriate to reduce API calls
5. **Use webhooks**: Subscribe to webhooks for real-time updates instead of polling

## 🚀 SDKs and Libraries

Official SDKs available for:
- **JavaScript/TypeScript**: `npm install @infra-mind/api-client`
- **Python**: `pip install infra-mind-api`
- **Go**: `go get github.com/infra-mind/go-client`
- **Java**: Available via Maven Central

## 📞 Support

- **Documentation**: [https://docs.infra-mind.com](https://docs.infra-mind.com)
- **Support Email**: support@infra-mind.com
- **Discord Community**: [https://discord.gg/infra-mind](https://discord.gg/infra-mind)
- **GitHub Issues**: [https://github.com/infra-mind/api/issues](https://github.com/infra-mind/api/issues)

## 📋 Changelog

### v2.0.0 (Current)
- ✅ Enterprise A/B testing platform
- ✅ Advanced feedback collection system
- ✅ Quality assurance framework
- ✅ Third-party integrations
- ✅ Enhanced security and monitoring

### v1.0.0
- ✅ Core assessment functionality
- ✅ AI-powered recommendations
- ✅ Report generation
- ✅ User management
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints. Handle user registration, login, password management, and token operations."
            },
            {
                "name": "Assessments",
                "description": "Core infrastructure assessment functionality. Create, manage, and execute comprehensive infrastructure assessments with AI-powered analysis."
            },
            {
                "name": "Recommendations", 
                "description": "AI-powered recommendation system. Generate and manage intelligent infrastructure improvement recommendations using our multi-agent AI platform."
            },
            {
                "name": "Reports",
                "description": "Professional report generation and management. Create, download, and share detailed infrastructure reports in multiple formats."
            },
            {
                "name": "Enterprise Experiments",
                "description": "Advanced A/B testing and experimentation platform. Design and run experiments to test infrastructure changes safely."
            },
            {
                "name": "Enterprise Feedback",
                "description": "Comprehensive feedback collection and analysis system. Gather insights from users and stakeholders for continuous improvement."
            },
            {
                "name": "Enterprise Quality",
                "description": "Quality assurance and metrics platform. Monitor and improve the quality of assessments and recommendations."
            },
            {
                "name": "Cloud Services",
                "description": "Cloud service catalog and comparison tools. Discover and compare cloud services across multiple providers."
            },
            {
                "name": "Compliance",
                "description": "Compliance monitoring and reporting. Automated compliance tracking for various industry standards and regulations."
            },
            {
                "name": "Performance Monitoring",
                "description": "Real-time performance monitoring and optimization. Track system performance and receive optimization recommendations."
            },
            {
                "name": "Advanced Analytics",
                "description": "Deep analytics and insights platform. Advanced data analysis, cost predictions, and security auditing capabilities."
            },
            {
                "name": "Integrations",
                "description": "Third-party integrations and connectors. Connect with existing tools like Slack, Teams, and compliance databases."
            },
            {
                "name": "Admin",
                "description": "Administrative functions and system management. Admin-only endpoints for user management, system health, and analytics."
            },
            {
                "name": "Chat",
                "description": "AI-powered chat interface. Interactive conversations with AI agents for infrastructure guidance and support."
            },
            {
                "name": "Dashboard",
                "description": "Dashboard data and visualization endpoints. Retrieve data for various dashboards and administrative interfaces."
            },
            {
                "name": "Resilience",
                "description": "System resilience and failover management. Monitor and manage system reliability, circuit breakers, and recovery procedures."
            },
            {
                "name": "Testing",
                "description": "API testing and validation tools. Utilities for testing API functionality and generating sample data."
            },
            {
                "name": "Webhooks",
                "description": "Webhook management and delivery system. Create and manage webhooks for real-time event notifications."
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from login endpoint"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add contact information
    openapi_schema["info"]["contact"] = {
        "name": "Infra Mind Support",
        "email": "support@infra-mind.com",
        "url": "https://docs.infra-mind.com"
    }
    
    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "Commercial License",
        "url": "https://infra-mind.com/license"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.infra-mind.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.infra-mind.com", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add example responses to common endpoints
    add_example_responses(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def add_example_responses(openapi_schema: Dict[str, Any]):
    """Add comprehensive examples to API endpoints."""
    
    examples = {
        # Authentication examples
        "/api/v2/auth/login": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "examples": {
                                "basic_login": {
                                    "summary": "Basic Login",
                                    "value": {
                                        "email": "user@example.com",
                                        "password": "securepassword123"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "successful_login": {
                                        "summary": "Successful Login",
                                        "value": {
                                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                            "token_type": "bearer",
                                            "expires_in": 3600,
                                            "user": {
                                                "id": "60d5ecb74f96e8001f5e4a23",
                                                "email": "user@example.com",
                                                "full_name": "John Doe",
                                                "role": "user"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        # Assessment examples
        "/api/v2/assessments/": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "examples": {
                                "basic_assessment": {
                                    "summary": "Basic Assessment",
                                    "value": {
                                        "name": "Production Infrastructure Review",
                                        "description": "Comprehensive review of production infrastructure for cost optimization",
                                        "cloud_provider": "aws",
                                        "services": ["ec2", "rds", "s3", "lambda"],
                                        "priority": "high"
                                    }
                                },
                                "multi_cloud_assessment": {
                                    "summary": "Multi-Cloud Assessment",
                                    "value": {
                                        "name": "Multi-Cloud Migration Assessment",
                                        "description": "Assessment for migrating from AWS to hybrid Azure/GCP setup",
                                        "cloud_provider": "multi",
                                        "services": ["compute", "storage", "database", "networking"],
                                        "priority": "medium"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "assessment_list": {
                                        "summary": "List of Assessments",
                                        "value": {
                                            "assessments": [
                                                {
                                                    "id": "60d5ecb74f96e8001f5e4a23",
                                                    "name": "Production Infrastructure Review",
                                                    "status": "completed",
                                                    "completion_percentage": 100,
                                                    "created_at": "2024-01-15T10:00:00Z",
                                                    "updated_at": "2024-01-15T14:30:00Z"
                                                }
                                            ],
                                            "total": 25,
                                            "page": 1,
                                            "limit": 20,
                                            "total_pages": 2
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        # Experiment examples
        "/api/v2/experiments/feature/{feature_flag}/variant": {
            "get": {
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "active_experiment": {
                                        "summary": "Active Experiment Variant",
                                        "value": {
                                            "feature_flag": "new-recommendation-algorithm",
                                            "user_id": "user123",
                                            "variant": "treatment",
                                            "assigned_at": "2024-01-15T10:00:00Z",
                                            "experiment_id": "60d5ecb74f96e8001f5e4a24"
                                        }
                                    },
                                    "no_experiment": {
                                        "summary": "No Active Experiment",
                                        "value": {
                                            "feature_flag": "non-existent-flag",
                                            "user_id": "user123",
                                            "variant": "control",
                                            "assigned_at": "2024-01-15T10:00:00Z",
                                            "experiment_id": None
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        
        # Feedback examples
        "/api/v2/feedback/": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "examples": {
                                "assessment_feedback": {
                                    "summary": "Assessment Quality Feedback",
                                    "value": {
                                        "feedback_type": "assessment_quality",
                                        "rating": 4,
                                        "comments": "The assessment was thorough but took longer than expected. The recommendations were very helpful.",
                                        "assessment_id": "60d5ecb74f96e8001f5e4a23"
                                    }
                                },
                                "ui_feedback": {
                                    "summary": "UI Experience Feedback",
                                    "value": {
                                        "feedback_type": "ui_experience",
                                        "rating": 5,
                                        "comments": "The new dashboard design is much more intuitive. Great improvement!"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add comprehensive error response examples
    error_examples = {
        "/api/v2/auth/login": {
            "post": {
                "responses": {
                    "401": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "invalid_credentials": {
                                        "summary": "Invalid Credentials",
                                        "value": {
                                            "detail": "Invalid credentials"
                                        }
                                    },
                                    "mfa_required": {
                                        "summary": "MFA Required",
                                        "value": {
                                            "mfa_required": True,
                                            "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                            "message": "MFA verification required"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "429": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "rate_limit_exceeded": {
                                        "summary": "Rate Limit Exceeded",
                                        "value": {
                                            "detail": "Rate limit exceeded. Please try again in 60 seconds.",
                                            "retry_after": 60
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/v2/auth/register": {
            "post": {
                "responses": {
                    "400": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "email_exists": {
                                        "summary": "Email Already Registered",
                                        "value": {
                                            "detail": "Email already registered"
                                        }
                                    },
                                    "validation_error": {
                                        "summary": "Validation Error",
                                        "value": {
                                            "detail": [
                                                {
                                                    "loc": ["body", "password"],
                                                    "msg": "ensure this value has at least 8 characters",
                                                    "type": "value_error.any_str.min_length"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/v2/assessments/": {
            "post": {
                "responses": {
                    "401": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "unauthorized": {
                                        "summary": "Unauthorized",
                                        "value": {
                                            "detail": "Authentication credentials were not provided"
                                        }
                                    },
                                    "token_expired": {
                                        "summary": "Token Expired",
                                        "value": {
                                            "detail": "Token expired"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "422": {
                        "content": {
                            "application/json": {
                                "examples": {
                                    "validation_error": {
                                        "summary": "Validation Error",
                                        "value": {
                                            "detail": [
                                                {
                                                    "loc": ["body", "cloud_provider"],
                                                    "msg": "value is not a valid enumeration member; permitted: 'aws', 'azure', 'gcp', 'multi'",
                                                    "type": "type_error.enum"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Apply error examples to the schema
    for path, methods in error_examples.items():
        if path in openapi_schema.get("paths", {}):
            for method, config in methods.items():
                if method in openapi_schema["paths"][path]:
                    endpoint = openapi_schema["paths"][path][method]
                    
                    # Add error response examples
                    if "responses" in config:
                        for status_code, response_data in config["responses"].items():
                            # Create response if it doesn't exist
                            if status_code not in endpoint.get("responses", {}):
                                if "responses" not in endpoint:
                                    endpoint["responses"] = {}
                                endpoint["responses"][status_code] = {
                                    "description": get_status_description(status_code),
                                    "content": {}
                                }
                            
                            # Add examples
                            if "content" in response_data:
                                for content_type, content_data in response_data["content"].items():
                                    if content_type not in endpoint["responses"][status_code].get("content", {}):
                                        if "content" not in endpoint["responses"][status_code]:
                                            endpoint["responses"][status_code]["content"] = {}
                                        endpoint["responses"][status_code]["content"][content_type] = {}
                                    
                                    if "examples" in content_data:
                                        endpoint["responses"][status_code]["content"][content_type]["examples"] = content_data["examples"]


def get_status_description(status_code: str) -> str:
    """Get description for HTTP status code."""
    descriptions = {
        "400": "Bad Request - Invalid input data",
        "401": "Unauthorized - Authentication required or failed",
        "403": "Forbidden - Insufficient permissions",
        "404": "Not Found - Resource not found",
        "422": "Unprocessable Entity - Validation error",
        "429": "Too Many Requests - Rate limit exceeded",
        "500": "Internal Server Error - Server error occurred"
    }
    return descriptions.get(status_code, "Error")
    
    # Apply examples to the schema
    for path, methods in examples.items():
        if path in openapi_schema.get("paths", {}):
            for method, config in methods.items():
                if method in openapi_schema["paths"][path]:
                    # Merge examples into existing endpoint
                    endpoint = openapi_schema["paths"][path][method]
                    
                    # Add request body examples
                    if "requestBody" in config and "requestBody" in endpoint:
                        if "content" in config["requestBody"]:
                            for content_type, content_data in config["requestBody"]["content"].items():
                                if content_type in endpoint["requestBody"]["content"]:
                                    if "examples" in content_data:
                                        endpoint["requestBody"]["content"][content_type]["examples"] = content_data["examples"]
                    
                    # Add response examples
                    if "responses" in config:
                        for status_code, response_data in config["responses"].items():
                            if status_code in endpoint["responses"]:
                                if "content" in response_data:
                                    for content_type, content_data in response_data["content"].items():
                                        if "responses" in endpoint and status_code in endpoint["responses"]:
                                            if "content" in endpoint["responses"][status_code]:
                                                if content_type in endpoint["responses"][status_code]["content"]:
                                                    if "examples" in content_data:
                                                        endpoint["responses"][status_code]["content"][content_type]["examples"] = content_data["examples"]


def get_api_integration_guide() -> Dict[str, Any]:
    """Generate comprehensive API integration guide."""
    
    return {
        "title": "Infra Mind API Integration Guide",
        "sections": [
            {
                "title": "Quick Start",
                "content": """
## Quick Start Guide

### 1. Authentication
```bash
# Register a new account
curl -X POST https://api.infra-mind.com/api/v2/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "your@email.com",
    "password": "secure_password",
    "full_name": "Your Name",
    "company": "Your Company"
  }'

# Login and get access token
curl -X POST https://api.infra-mind.com/api/v2/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "your@email.com", 
    "password": "secure_password"
  }'
```

### 2. Create Your First Assessment
```bash
# Create an assessment
curl -X POST https://api.infra-mind.com/api/v2/assessments/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My First Assessment",
    "description": "Testing the Infra Mind API",
    "cloud_provider": "aws",
    "services": ["ec2", "s3"]
  }'
```

### 3. Start the Assessment
```bash
# Start the assessment process
curl -X POST https://api.infra-mind.com/api/v2/assessments/{assessment_id}/start \\
  -H "Authorization: Bearer YOUR_TOKEN"
```
                """
            },
            {
                "title": "SDK Usage",
                "content": """
## SDK Usage Examples

### JavaScript/TypeScript
```javascript
import { InfraMindAPI } from '@infra-mind/api-client';

const client = new InfraMindAPI({
  baseURL: 'https://api.infra-mind.com',
  token: 'your_jwt_token'
});

// Create an assessment
const assessment = await client.assessments.create({
  name: 'My Assessment',
  description: 'API test assessment',
  cloud_provider: 'aws',
  services: ['ec2', 's3', 'rds']
});

// Start the assessment
await client.assessments.start(assessment.id);

// Get recommendations
const recommendations = await client.recommendations.list(assessment.id);
```

### Python
```python
from infra_mind_api import InfraMindClient

client = InfraMindClient(
    base_url='https://api.infra-mind.com',
    token='your_jwt_token'
)

# Create assessment
assessment = client.assessments.create(
    name='My Assessment',
    description='API test assessment',
    cloud_provider='aws',
    services=['ec2', 's3', 'rds']
)

# Start assessment
client.assessments.start(assessment.id)

# Get recommendations
recommendations = client.recommendations.list(assessment.id)
```
                """
            },
            {
                "title": "Webhooks",
                "content": """
## Webhook Integration

### Setting Up Webhooks
```bash
# Register a webhook endpoint
curl -X POST https://api.infra-mind.com/api/v2/webhooks/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://your-app.com/webhooks/infra-mind",
    "events": ["assessment.completed", "recommendation.generated"],
    "secret": "your_webhook_secret"
  }'
```

### Webhook Event Examples
```json
{
  "event": "assessment.completed",
  "data": {
    "assessment_id": "60d5ecb74f96e8001f5e4a23",
    "status": "completed",
    "completion_percentage": 100,
    "completed_at": "2024-01-15T14:30:00Z"
  },
  "timestamp": "2024-01-15T14:30:01Z",
  "signature": "sha256=..."
}
```

### Verifying Webhook Signatures
```python
import hashlib
import hmac

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```
                """
            },
            {
                "title": "Rate Limiting",
                "content": """
## Rate Limiting and Best Practices

### Rate Limits
- **Standard Users**: 100 requests/minute
- **Premium Users**: 1000 requests/minute  
- **Enterprise Users**: 10000 requests/minute

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642681200
```

### Handling Rate Limits
```python
import time
import requests

def make_api_request(url, headers, data=None):
    while True:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            # Rate limit exceeded, wait and retry
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(1, reset_time - int(time.time()))
            time.sleep(wait_time)
            continue
        
        return response
```

### Best Practices
1. **Implement exponential backoff** for retries
2. **Cache responses** when appropriate
3. **Use pagination** for large datasets
4. **Batch operations** when possible
5. **Monitor rate limit headers** and adjust accordingly
                """
            }
        ]
    }


# Export functions
__all__ = ["get_enhanced_openapi_schema", "get_api_integration_guide"]