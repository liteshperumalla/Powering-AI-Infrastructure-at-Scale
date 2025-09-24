"""
Main API router for Infra Mind with versioning support.

Combines all API routes into versioned routers for the main application.
Supports API versioning for backward compatibility and evolution.
"""

from fastapi import APIRouter, HTTPException, status
from .endpoints import auth, assessments, recommendations, reports, monitoring, webhooks, admin, testing, resilience, compliance, integrations, compliance_dashboard, business_tools, performance_monitoring, forms, cloud_services, chat, advanced_analytics, scenarios, validation, dashboard, experiments, feedback, quality, vendor_lockin, rollback, budget_forecasting, change_impact, gitops, approval_workflows
from .documentation import get_api_integration_guide

# Create versioned API routers
api_v1_router = APIRouter()
api_v2_router = APIRouter()

# V1 API Routes (Legacy/Stable)
api_v1_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_v1_router.include_router(
    assessments.router,
    prefix="/assessments",
    tags=["Assessments"]
)

api_v1_router.include_router(
    recommendations.router,
    prefix="/recommendations", 
    tags=["Recommendations"]
)

api_v1_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

api_v1_router.include_router(
    forms.router,
    prefix="/forms",
    tags=["Forms"]
)

api_v1_router.include_router(
    performance_monitoring.router,
    prefix="/performance",
    tags=["Performance Monitoring"]
)

api_v1_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["Monitoring"]
)

api_v1_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

api_v1_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_v1_router.include_router(
    cloud_services.router,
    prefix="/cloud-services",
    tags=["Cloud Services"]
)

api_v1_router.include_router(
    scenarios.router,
    prefix="/scenarios",
    tags=["Scenarios"]
)

api_v1_router.include_router(
    vendor_lockin.router,
    prefix="/vendor-lockin",
    tags=["Vendor Lock-in"]
)

api_v1_router.include_router(
    rollback.router,
    prefix="/rollback",
    tags=["Rollback Automation"]
)

api_v1_router.include_router(
    budget_forecasting.router,
    prefix="/budget-forecasting",
    tags=["Budget Forecasting"]
)

api_v1_router.include_router(
    change_impact.router,
    prefix="/change-impact",
    tags=["Change Impact Analysis"]
)

api_v1_router.include_router(
    gitops.router,
    prefix="/gitops",
    tags=["GitOps Integration"]
)

api_v1_router.include_router(
    approval_workflows.router,
    prefix="/approval-workflows",
    tags=["Approval Workflows"]
)

# V2 API Routes (Enhanced with new features)
api_v2_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_v2_router.include_router(
    assessments.router,
    prefix="/assessments",
    tags=["Assessments"]
)

api_v2_router.include_router(
    recommendations.router,
    prefix="/recommendations", 
    tags=["Recommendations"]
)

api_v2_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

api_v2_router.include_router(
    forms.router,
    prefix="/forms",
    tags=["Forms"]
)

api_v2_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["Monitoring"]
)

api_v2_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"]
)

api_v2_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

api_v2_router.include_router(
    testing.router,
    prefix="/testing",
    tags=["Testing"]
)

api_v2_router.include_router(
    resilience.router,
    prefix="/resilience",
    tags=["Resilience"]
)

api_v2_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["Compliance"]
)

api_v2_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["Integrations"]
)

api_v2_router.include_router(
    compliance_dashboard.router,
    prefix="/compliance-dashboard",
    tags=["Compliance Dashboard"]
)

api_v2_router.include_router(
    business_tools.router,
    prefix="/business-tools",
    tags=["Business Tools"]
)

api_v2_router.include_router(
    performance_monitoring.router,
    prefix="/performance",
    tags=["Performance Monitoring"]
)

# Add alias for performance monitoring
api_v2_router.include_router(
    performance_monitoring.router,
    prefix="/performance-monitoring",
    tags=["Performance Monitoring"]
)

api_v2_router.include_router(
    cloud_services.router,
    prefix="/cloud-services",
    tags=["Cloud Services"]
)

api_v2_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_v2_router.include_router(
    advanced_analytics.router,
    prefix="/advanced-analytics",
    tags=["Advanced Analytics"]
)

api_v2_router.include_router(
    scenarios.router,
    prefix="/scenarios",
    tags=["Scenarios"]
)

api_v2_router.include_router(
    validation.router,
    prefix="/validation",
    tags=["Data Validation"]
)

api_v2_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

api_v2_router.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["A/B Testing & Experiments"]
)

api_v2_router.include_router(
    feedback.router,
    prefix="/feedback",
    tags=["User Feedback"]
)

api_v2_router.include_router(
    quality.router,
    prefix="/quality",
    tags=["Quality Assurance"]
)

api_v2_router.include_router(
    vendor_lockin.router,
    prefix="/vendor-lockin",
    tags=["Vendor Lock-in"]
)

api_v2_router.include_router(
    rollback.router,
    prefix="/rollback",
    tags=["Rollback Automation"]
)

api_v2_router.include_router(
    budget_forecasting.router,
    prefix="/budget-forecasting",
    tags=["Budget Forecasting"]
)

api_v2_router.include_router(
    change_impact.router,
    prefix="/change-impact",
    tags=["Change Impact Analysis"]
)

api_v2_router.include_router(
    gitops.router,
    prefix="/gitops",
    tags=["GitOps Integration"]
)

api_v2_router.include_router(
    approval_workflows.router,
    prefix="/approval-workflows",
    tags=["Approval Workflows"]
)

# Documentation endpoints are now included directly in main api_router

# Main API router that includes all versions
api_router = APIRouter()

# Include versioned routers
api_router.include_router(api_v1_router, prefix="/v1")
api_router.include_router(api_v2_router, prefix="/v2")

# Default to latest version (v2)
api_router.include_router(api_v2_router, prefix="")

# API version info endpoint
@api_router.get("/versions")
async def get_api_versions():
    """
    Get information about available API versions.
    
    Returns details about all supported API versions and their features.
    """
    return {
        "current_version": "v2",
        "supported_versions": [
            {
                "version": "v1",
                "status": "stable",
                "deprecated": False,
                "sunset_date": None,
                "description": "Original API with core functionality",
                "endpoints": [
                    "/auth", "/assessments", "/recommendations", "/reports", "/forms", "/cloud-services"
                ]
            },
            {
                "version": "v2", 
                "status": "current",
                "deprecated": False,
                "sunset_date": None,
                "description": "Enhanced API with webhooks, monitoring, and admin features",
                "endpoints": [
                    "/auth", "/assessments", "/recommendations", "/reports", "/forms", 
                    "/monitoring", "/webhooks", "/admin", "/testing", "/resilience", "/compliance", "/integrations", "/chat", "/advanced-analytics", "/cloud-services", "/experiments", "/feedback", "/quality", "/docs"
                ],
                "new_features": [
                    "Webhook support with delivery tracking",
                    "Real-time monitoring and analytics",
                    "Admin endpoints for system management",
                    "Enhanced OpenAPI documentation with examples",
                    "Interactive testing and sample data generation",
                    "Advanced rate limiting and security",
                    "API versioning support",
                    "Comprehensive error handling",
                    "System resilience management with health checks",
                    "Automatic failover and recovery capabilities",
                    "Circuit breaker monitoring and control",
                    "Comprehensive compliance management with GDPR support",
                    "Data retention policies and lifecycle management",
                    "Consent management and privacy controls",
                    "Data export and portability features",
                    "Audit trail and compliance reporting",
                    "Third-party integrations with compliance databases",
                    "Business tools integration (Slack, Teams, email)",
                    "SSO integration with enterprise identity providers",
                    "Real-time notifications and workflow updates",
                    "Advanced analytics dashboard with D3.js visualizations",
                    "Predictive cost modeling and infrastructure scaling simulations",
                    "Multi-cloud service recommendations (AWS, Azure, GCP, Alibaba, IBM)",
                    "Security audit automation with vulnerability scanning",
                    "Performance benchmarking across cloud providers",
                    "A/B testing framework with experiment management and statistical analysis",
                    "User feedback collection system with sentiment analysis and analytics",
                    "Quality assurance framework with automated validation gates",
                    "Enterprise-grade third-party integrations with rate limiting and monitoring"
                ]
            }
        ],
        "migration_guide": "https://docs.infra-mind.com/api/migration",
        "changelog": "https://docs.infra-mind.com/api/changelog"
    }

# Version deprecation endpoint
@api_router.get("/v1/deprecation-notice")
async def v1_deprecation_notice():
    """
    Get deprecation notice for API v1.
    
    Returns information about v1 deprecation timeline and migration guidance.
    """
    return {
        "message": "API v1 is stable and fully supported",
        "deprecated": False,
        "sunset_date": None,
        "migration_required": False,
        "migration_guide": "https://docs.infra-mind.com/api/migration/v1-to-v2",
        "support_contact": "api-support@infra-mind.com"
    }

# API Integration Guide endpoint
@api_router.get("/integration-guide")
async def get_integration_guide():
    """
    Get comprehensive API integration guide.
    
    Returns detailed integration examples, SDKs, webhooks, and best practices.
    """
    return {
        "title": "Infra Mind API Integration Guide",
        "version": "2.0.0",
        "quick_start": {
            "authentication": {
                "description": "Register and obtain JWT token",
                "endpoints": {
                    "register": "POST /api/v2/auth/register",
                    "login": "POST /api/v2/auth/login"
                }
            },
            "first_assessment": {
                "description": "Create and run your first assessment",
                "steps": [
                    "POST /api/v2/assessments/ - Create assessment",
                    "POST /api/v2/assessments/{id}/start - Start assessment",
                    "GET /api/v2/recommendations/{id} - Get recommendations"
                ]
            }
        },
        "enterprise_features": {
            "experiments": {
                "description": "A/B testing platform",
                "key_endpoints": [
                    "GET /api/v2/experiments/feature/{flag}/variant",
                    "POST /api/v2/experiments/feature/{flag}/track"
                ]
            },
            "feedback": {
                "description": "User feedback collection",
                "key_endpoints": [
                    "POST /api/v2/feedback/",
                    "GET /api/v2/feedback/analytics/dashboard"
                ]
            },
            "quality": {
                "description": "Quality assurance metrics",
                "key_endpoints": [
                    "POST /api/v2/quality/metrics",
                    "GET /api/v2/quality/overview"
                ]
            }
        },
        "rate_limits": {
            "standard": "100 requests/minute",
            "premium": "1000 requests/minute",
            "enterprise": "10000 requests/minute"
        },
        "contact": {
            "support": "support@infra-mind.com",
            "docs": "https://docs.infra-mind.com",
            "github": "https://github.com/infra-mind/api"
        }
    }

# API Examples endpoint
@api_router.get("/examples")
async def get_api_examples():
    """
    Get comprehensive API usage examples.
    
    Returns detailed examples for common API operations.
    """
    return {
        "title": "Infra Mind API Examples",
        "authentication": {
            "register": {
                "method": "POST",
                "url": "/api/v2/auth/register",
                "body": {
                    "email": "developer@company.com",
                    "password": "secure_password123",
                    "full_name": "API Developer",
                    "company": "Tech Corp"
                },
                "response": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
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
                "body": {
                    "name": "Production Infrastructure Review",
                    "description": "Comprehensive AWS infrastructure assessment",
                    "cloud_provider": "aws",
                    "services": ["ec2", "rds", "s3"],
                    "priority": "high"
                }
            }
        },
        "enterprise": {
            "experiments": {
                "get_variant": {
                    "method": "GET",
                    "url": "/api/v2/experiments/feature/new-ui/variant?user_id=user123",
                    "response": {
                        "feature_flag": "new-ui",
                        "user_id": "user123",
                        "variant": "treatment",
                        "experiment_id": "exp_456"
                    }
                }
            },
            "feedback": {
                "submit": {
                    "method": "POST",
                    "url": "/api/v2/feedback/",
                    "body": {
                        "feedback_type": "assessment_quality",
                        "rating": 5,
                        "comments": "Excellent recommendations"
                    }
                }
            }
        }
    }