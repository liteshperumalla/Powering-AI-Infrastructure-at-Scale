"""
Documentation endpoints for enhanced API documentation.
Provides comprehensive documentation, examples, and integration guides.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/integration-guide")
async def get_integration_guide() -> Dict[str, Any]:
    """
    Get comprehensive API integration guide.
    
    Returns detailed integration examples, SDKs, webhooks, and best practices.
    """
    return {
        "title": "Infra Mind API Integration Guide",
        "version": "2.0.0",
        "sections": [
            {
                "title": "Quick Start",
                "content": {
                    "description": "Get started with the Infra Mind API in minutes",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Authentication",
                            "description": "Register and obtain your JWT token",
                            "example": {
                                "curl": """curl -X POST https://api.infra-mind.com/api/v2/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "your@email.com",
    "password": "secure_password",
    "full_name": "Your Name",
    "company": "Your Company"
  }'""",
                                "response": {
                                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                    "token_type": "bearer",
                                    "expires_in": 3600
                                }
                            }
                        },
                        {
                            "step": 2,
                            "title": "Create Assessment",
                            "description": "Create your first infrastructure assessment",
                            "example": {
                                "curl": """curl -X POST https://api.infra-mind.com/api/v2/assessments/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My First Assessment",
    "description": "Testing the Infra Mind API",
    "cloud_provider": "aws",
    "services": ["ec2", "s3"]
  }'"""
                            }
                        }
                    ]
                }
            },
            {
                "title": "SDK Usage",
                "content": {
                    "javascript": {
                        "installation": "npm install @infra-mind/api-client",
                        "example": """import { InfraMindAPI } from '@infra-mind/api-client';

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
await client.assessments.start(assessment.id);"""
                    },
                    "python": {
                        "installation": "pip install infra-mind-api",
                        "example": """from infra_mind_api import InfraMindClient

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
client.assessments.start(assessment.id)"""
                    }
                }
            },
            {
                "title": "Enterprise Features",
                "content": {
                    "experiments": {
                        "description": "A/B testing and experimentation platform",
                        "endpoints": [
                            "GET /api/v2/experiments/feature/{feature_flag}/variant",
                            "POST /api/v2/experiments/feature/{feature_flag}/track",
                            "POST /api/v2/experiments/"
                        ],
                        "example": """# Get user variant for A/B test
curl -X GET "https://api.infra-mind.com/api/v2/experiments/feature/new-ui/variant?user_id=user123" \\
  -H "Authorization: Bearer YOUR_TOKEN"

# Track conversion event
curl -X POST "https://api.infra-mind.com/api/v2/experiments/feature/new-ui/track" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "user123",
    "event_type": "conversion",
    "value": 1.0
  }'"""
                    },
                    "feedback": {
                        "description": "Comprehensive feedback collection system",
                        "endpoints": [
                            "POST /api/v2/feedback/",
                            "GET /api/v2/feedback/analytics/dashboard",
                            "GET /api/v2/feedback/health"
                        ],
                        "example": """# Submit feedback
curl -X POST "https://api.infra-mind.com/api/v2/feedback/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "feedback_type": "assessment_quality",
    "rating": 4,
    "comments": "Great assessment, very helpful recommendations"
  }'"""
                    },
                    "quality": {
                        "description": "Quality assurance and metrics platform",
                        "endpoints": [
                            "POST /api/v2/quality/metrics",
                            "GET /api/v2/quality/overview",
                            "GET /api/v2/quality/trends"
                        ]
                    }
                }
            },
            {
                "title": "Webhooks",
                "content": {
                    "setup": """# Register a webhook endpoint
curl -X POST https://api.infra-mind.com/api/v2/webhooks/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://your-app.com/webhooks/infra-mind",
    "events": ["assessment.completed", "recommendation.generated"],
    "secret": "your_webhook_secret"
  }'""",
                    "events": [
                        {
                            "event": "assessment.completed",
                            "description": "Triggered when an assessment is completed",
                            "payload_example": {
                                "event": "assessment.completed",
                                "data": {
                                    "assessment_id": "60d5ecb74f96e8001f5e4a23",
                                    "status": "completed",
                                    "completion_percentage": 100,
                                    "completed_at": "2024-01-15T14:30:00Z"
                                },
                                "timestamp": "2024-01-15T14:30:01Z"
                            }
                        }
                    ]
                }
            },
            {
                "title": "Rate Limiting & Best Practices",
                "content": {
                    "rate_limits": {
                        "standard": "100 requests/minute",
                        "premium": "1000 requests/minute",
                        "enterprise": "10000 requests/minute"
                    },
                    "headers": {
                        "X-RateLimit-Limit": "Maximum requests allowed",
                        "X-RateLimit-Remaining": "Requests remaining in current window",
                        "X-RateLimit-Reset": "Unix timestamp when window resets"
                    },
                    "best_practices": [
                        "Implement exponential backoff for retries",
                        "Cache responses when appropriate",
                        "Use pagination for large datasets",
                        "Batch operations when possible",
                        "Monitor rate limit headers"
                    ]
                }
            }
        ],
        "contact": {
            "support_email": "support@infra-mind.com",
            "documentation": "https://docs.infra-mind.com",
            "discord": "https://discord.gg/infra-mind",
            "github": "https://github.com/infra-mind/api"
        },
        "generated_at": "2024-01-15T10:00:00Z"
    }

@router.get("/examples")
async def get_api_examples() -> Dict[str, Any]:
    """
    Get comprehensive API usage examples.
    
    Returns detailed examples for all major API operations.
    """
    return {
        "title": "Infra Mind API Examples",
        "categories": {
            "authentication": {
                "register": {
                    "method": "POST",
                    "url": "/api/v2/auth/register",
                    "request": {
                        "email": "developer@company.com",
                        "password": "secure_password123",
                        "full_name": "API Developer",
                        "company": "Tech Corp"
                    },
                    "response": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": "60d5ecb74f96e8001f5e4a23",
                            "email": "developer@company.com",
                            "full_name": "API Developer"
                        }
                    }
                },
                "login": {
                    "method": "POST", 
                    "url": "/api/v2/auth/login",
                    "request": {
                        "email": "developer@company.com",
                        "password": "secure_password123"
                    }
                }
            },
            "assessments": {
                "create": {
                    "method": "POST",
                    "url": "/api/v2/assessments/",
                    "headers": {
                        "Authorization": "Bearer YOUR_TOKEN"
                    },
                    "request": {
                        "name": "Production Infrastructure Review",
                        "description": "Comprehensive review of production AWS infrastructure",
                        "cloud_provider": "aws",
                        "services": ["ec2", "rds", "s3", "lambda"],
                        "priority": "high"
                    },
                    "response": {
                        "id": "60d5ecb74f96e8001f5e4a24",
                        "name": "Production Infrastructure Review", 
                        "status": "created",
                        "created_at": "2024-01-15T10:00:00Z"
                    }
                },
                "start": {
                    "method": "POST",
                    "url": "/api/v2/assessments/{assessment_id}/start",
                    "description": "Start the AI-powered assessment process"
                },
                "get_recommendations": {
                    "method": "GET",
                    "url": "/api/v2/recommendations/{assessment_id}",
                    "response": {
                        "recommendations": [
                            {
                                "id": "rec_001",
                                "title": "Optimize RDS Instance Sizes",
                                "description": "Right-size your RDS instances to reduce costs",
                                "priority": "high",
                                "estimated_savings": "$2,400/month",
                                "implementation_effort": "medium"
                            }
                        ]
                    }
                }
            },
            "enterprise_experiments": {
                "get_variant": {
                    "method": "GET",
                    "url": "/api/v2/experiments/feature/new-algorithm/variant",
                    "parameters": {
                        "user_id": "user_123"
                    },
                    "response": {
                        "feature_flag": "new-algorithm",
                        "user_id": "user_123", 
                        "variant": "treatment",
                        "assigned_at": "2024-01-15T10:00:00Z",
                        "experiment_id": "exp_456"
                    }
                },
                "track_event": {
                    "method": "POST",
                    "url": "/api/v2/experiments/feature/new-algorithm/track",
                    "request": {
                        "user_id": "user_123",
                        "event_type": "conversion",
                        "value": 1.0,
                        "custom_metrics": {
                            "session_duration": 300,
                            "pages_viewed": 5
                        }
                    }
                }
            },
            "feedback": {
                "submit": {
                    "method": "POST",
                    "url": "/api/v2/feedback/",
                    "request": {
                        "feedback_type": "assessment_quality",
                        "rating": 5,
                        "comments": "Excellent recommendations, saved us significant costs",
                        "assessment_id": "60d5ecb74f96e8001f5e4a24"
                    }
                },
                "analytics": {
                    "method": "GET",
                    "url": "/api/v2/feedback/analytics/dashboard",
                    "response": {
                        "average_rating": 4.2,
                        "total_feedback": 1567,
                        "sentiment_breakdown": {
                            "positive": 78,
                            "neutral": 18,
                            "negative": 4
                        }
                    }
                }
            }
        }
    }

@router.get("/postman-collection")
async def get_postman_collection() -> Dict[str, Any]:
    """
    Get Postman collection for API testing.
    
    Returns a complete Postman collection with all endpoints and examples.
    """
    return {
        "info": {
            "name": "Infra Mind API",
            "description": "Complete API collection for Infra Mind platform",
            "version": "2.0.0",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": "https://api.infra-mind.com"
            },
            {
                "key": "token",
                "value": "YOUR_JWT_TOKEN"
            }
        ],
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Register",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/v2/auth/register",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"email\": \"developer@company.com\",\n  \"password\": \"secure_password123\",\n  \"full_name\": \"API Developer\",\n  \"company\": \"Tech Corp\"\n}"
                            }
                        }
                    },
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST", 
                            "url": "{{baseUrl}}/api/v2/auth/login",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"email\": \"developer@company.com\",\n  \"password\": \"secure_password123\"\n}"
                            }
                        }
                    }
                ]
            },
            {
                "name": "Assessments",
                "item": [
                    {
                        "name": "Create Assessment",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/v2/assessments/",
                            "header": [
                                {
                                    "key": "Authorization",
                                    "value": "Bearer {{token}}"
                                },
                                {
                                    "key": "Content-Type", 
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"name\": \"Production Infrastructure Review\",\n  \"description\": \"Comprehensive AWS infrastructure assessment\",\n  \"cloud_provider\": \"aws\",\n  \"services\": [\"ec2\", \"rds\", \"s3\"],\n  \"priority\": \"high\"\n}"
                            }
                        }
                    },
                    {
                        "name": "List Assessments",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/v2/assessments/",
                            "header": [
                                {
                                    "key": "Authorization",
                                    "value": "Bearer {{token}}"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "name": "Enterprise Features",
                "item": [
                    {
                        "name": "Get Experiment Variant", 
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/v2/experiments/feature/new-ui/variant?user_id=user123",
                            "header": [
                                {
                                    "key": "Authorization",
                                    "value": "Bearer {{token}}"
                                }
                            ]
                        }
                    },
                    {
                        "name": "Submit Feedback",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/v2/feedback/",
                            "header": [
                                {
                                    "key": "Authorization",
                                    "value": "Bearer {{token}}"
                                },
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n  \"feedback_type\": \"assessment_quality\",\n  \"rating\": 5,\n  \"comments\": \"Excellent recommendations\"\n}"
                            }
                        }
                    }
                ]
            }
        ]
    }

@router.get("/changelog")
async def get_api_changelog() -> Dict[str, Any]:
    """
    Get API changelog with version history.
    
    Returns detailed changelog with new features, improvements, and breaking changes.
    """
    return {
        "title": "Infra Mind API Changelog",
        "versions": [
            {
                "version": "2.0.0",
                "release_date": "2024-01-15",
                "status": "current",
                "highlights": [
                    "Enterprise A/B testing platform",
                    "Advanced feedback collection system",
                    "Quality assurance framework",
                    "Third-party integrations",
                    "Enhanced security and monitoring"
                ],
                "breaking_changes": [
                    "Authentication tokens now expire in 1 hour (was 24 hours)",
                    "Assessment status field renamed from 'state' to 'status'"
                ],
                "new_features": [
                    {
                        "feature": "A/B Testing",
                        "description": "Complete experimentation platform with variant assignment and event tracking",
                        "endpoints": [
                            "GET /api/v2/experiments/feature/{feature_flag}/variant",
                            "POST /api/v2/experiments/feature/{feature_flag}/track",
                            "POST /api/v2/experiments/"
                        ]
                    },
                    {
                        "feature": "Feedback Collection",
                        "description": "Comprehensive feedback system with analytics and sentiment analysis",
                        "endpoints": [
                            "POST /api/v2/feedback/",
                            "GET /api/v2/feedback/analytics/dashboard",
                            "GET /api/v2/feedback/summary/period"
                        ]
                    },
                    {
                        "feature": "Quality Assurance",
                        "description": "Quality metrics and validation framework",
                        "endpoints": [
                            "POST /api/v2/quality/metrics",
                            "GET /api/v2/quality/overview",
                            "GET /api/v2/quality/trends"
                        ]
                    }
                ],
                "improvements": [
                    "Enhanced OpenAPI documentation with examples",
                    "Improved error messages and validation",
                    "Better performance with database optimization",
                    "Added comprehensive test coverage"
                ]
            },
            {
                "version": "1.0.0",
                "release_date": "2023-12-01",
                "status": "stable",
                "highlights": [
                    "Core assessment functionality",
                    "AI-powered recommendations",
                    "Report generation",
                    "User management"
                ]
            }
        ]
    }