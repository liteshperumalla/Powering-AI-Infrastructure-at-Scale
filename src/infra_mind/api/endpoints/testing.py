"""
API Testing endpoints for Infra Mind.

Provides interactive API testing capabilities and sample data generation.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import json

router = APIRouter()


# Testing Models
class TestScenario(BaseModel):
    """Test scenario definition."""
    name: str
    description: str
    endpoint: str
    method: str
    sample_request: Dict[str, Any]
    expected_response: Dict[str, Any]
    test_data: Dict[str, Any]


class TestResult(BaseModel):
    """Test execution result."""
    scenario_name: str
    success: bool
    response_status: int
    response_data: Dict[str, Any]
    execution_time_ms: int
    error_message: Optional[str]
    timestamp: datetime


class SampleDataRequest(BaseModel):
    """Sample data generation request."""
    data_type: str = Field(..., description="Type of sample data to generate")
    count: int = Field(default=1, ge=1, le=100, description="Number of samples")
    customization: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.get("/scenarios")
async def get_test_scenarios():
    """
    Get available test scenarios.
    
    Returns a list of predefined test scenarios that can be executed
    to test various API endpoints with realistic data.
    """
    try:
        scenarios = [
            TestScenario(
                name="Create Assessment",
                description="Test creating a new infrastructure assessment",
                endpoint="/api/v2/assessments",
                method="POST",
                sample_request={
                    "title": "E-commerce Platform Assessment",
                    "description": "Infrastructure assessment for scaling e-commerce platform",
                    "business_requirements": {
                        "company_size": "medium",
                        "industry": "retail",
                        "budget_range": "100k_500k",
                        "compliance_requirements": ["gdpr"],
                        "business_goals": [
                            {
                                "goal": "Reduce infrastructure costs by 30%",
                                "priority": "high",
                                "timeline_months": 6
                            }
                        ]
                    },
                    "technical_requirements": {
                        "workload_types": ["web_application", "data_processing"],
                        "performance_requirements": {
                            "api_response_time_ms": 200,
                            "requests_per_second": 1000,
                            "concurrent_users": 500
                        }
                    },
                    "priority": "medium",
                    "source": "api_test"
                },
                expected_response={
                    "id": "uuid",
                    "title": "E-commerce Platform Assessment",
                    "status": "draft",
                    "progress": {"progress_percentage": 0.0}
                },
                test_data={}
            ),
            TestScenario(
                name="Generate Recommendations",
                description="Test generating AI agent recommendations",
                endpoint="/api/v2/recommendations/{assessment_id}/generate",
                method="POST",
                sample_request={
                    "agent_names": ["cto_agent", "cloud_engineer_agent", "research_agent"],
                    "priority_override": "high"
                },
                expected_response={
                    "message": "Recommendation generation started",
                    "workflow_id": "uuid",
                    "agents_triggered": ["cto_agent", "cloud_engineer_agent", "research_agent"]
                },
                test_data={"assessment_id": "sample_assessment_id"}
            ),
            TestScenario(
                name="Create Webhook",
                description="Test creating a webhook endpoint",
                endpoint="/api/v2/webhooks",
                method="POST",
                sample_request={
                    "url": "https://webhook.site/unique-id",
                    "events": ["assessment.completed", "report.generated"],
                    "description": "Test webhook for assessment completion",
                    "timeout_seconds": 30,
                    "retry_attempts": 3
                },
                expected_response={
                    "id": "uuid",
                    "url": "https://webhook.site/unique-id",
                    "events": ["assessment.completed", "report.generated"],
                    "status": "active"
                },
                test_data={}
            ),
            TestScenario(
                name="Generate Report",
                description="Test generating a professional report",
                endpoint="/api/v2/reports/{assessment_id}/generate",
                method="POST",
                sample_request={
                    "report_type": "executive_summary",
                    "format": "pdf",
                    "title": "Executive Infrastructure Summary",
                    "sections": ["executive_summary", "key_recommendations", "cost_analysis"],
                    "priority": "high"
                },
                expected_response={
                    "id": "uuid",
                    "report_type": "executive_summary",
                    "status": "generating",
                    "progress_percentage": 5.0
                },
                test_data={"assessment_id": "sample_assessment_id"}
            )
        ]
        
        logger.info(f"Retrieved {len(scenarios)} test scenarios")
        return {"scenarios": scenarios, "total": len(scenarios)}
        
    except Exception as e:
        logger.error(f"Failed to get test scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get test scenarios"
        )


@router.post("/scenarios/{scenario_name}/execute")
async def execute_test_scenario(
    scenario_name: str,
    custom_data: Optional[Dict[str, Any]] = None
):
    """
    Execute a test scenario.
    
    Runs a predefined test scenario against the API and returns the results.
    Useful for testing API functionality and integration.
    """
    try:
        # TODO: Implement actual test execution
        # This would make real API calls and measure responses
        
        start_time = datetime.utcnow()
        
        # Mock test execution
        import time
        time.sleep(0.1)  # Simulate API call time
        
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Mock successful result
        result = TestResult(
            scenario_name=scenario_name,
            success=True,
            response_status=200,
            response_data={
                "message": f"Test scenario '{scenario_name}' executed successfully",
                "mock_response": True
            },
            execution_time_ms=execution_time_ms,
            error_message=None,
            timestamp=end_time
        )
        
        logger.info(f"Executed test scenario: {scenario_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute test scenario {scenario_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute test scenario"
        )


@router.post("/sample-data")
async def generate_sample_data(request: SampleDataRequest):
    """
    Generate sample data for testing.
    
    Creates realistic sample data that can be used for testing API endpoints.
    Supports various data types including assessments, recommendations, and reports.
    """
    try:
        sample_data = []
        
        for i in range(request.count):
            if request.data_type == "assessment":
                sample = {
                    "id": str(uuid.uuid4()),
                    "title": f"Sample Assessment {i+1}",
                    "description": f"Sample infrastructure assessment for testing purposes",
                    "business_requirements": {
                        "company_size": "medium",
                        "industry": "technology",
                        "budget_range": "100k_500k",
                        "compliance_requirements": ["gdpr"],
                        "business_goals": [
                            {
                                "goal": "Improve system scalability",
                                "priority": "high",
                                "timeline_months": 6,
                                "success_metrics": ["Handle 10x traffic", "Auto-scaling implemented"]
                            }
                        ]
                    },
                    "technical_requirements": {
                        "workload_types": ["web_application", "data_processing"],
                        "performance_requirements": {
                            "api_response_time_ms": 200,
                            "requests_per_second": 1000,
                            "concurrent_users": 500,
                            "uptime_percentage": 99.9
                        }
                    },
                    "status": "draft",
                    "priority": "medium",
                    "created_at": datetime.utcnow().isoformat()
                }
                
            elif request.data_type == "recommendation":
                sample = {
                    "id": str(uuid.uuid4()),
                    "assessment_id": str(uuid.uuid4()),
                    "agent_name": "cloud_engineer_agent",
                    "title": f"Sample Recommendation {i+1}",
                    "summary": "Sample multi-cloud service recommendation",
                    "confidence_score": 0.85,
                    "recommended_services": [
                        {
                            "service_name": "EC2",
                            "provider": "aws",
                            "service_category": "compute",
                            "estimated_monthly_cost": 2500.00,
                            "configuration": {"instance_type": "m5.large", "count": 5}
                        }
                    ],
                    "total_estimated_monthly_cost": 2500.00,
                    "implementation_steps": [
                        "Set up AWS account and IAM roles",
                        "Create VPC and security groups",
                        "Deploy EC2 instances"
                    ],
                    "created_at": datetime.utcnow().isoformat()
                }
                
            elif request.data_type == "report":
                sample = {
                    "id": str(uuid.uuid4()),
                    "assessment_id": str(uuid.uuid4()),
                    "title": f"Sample Report {i+1}",
                    "report_type": "executive_summary",
                    "format": "pdf",
                    "status": "completed",
                    "progress_percentage": 100.0,
                    "sections": ["executive_summary", "key_recommendations", "cost_analysis"],
                    "total_pages": 12,
                    "word_count": 3500,
                    "generated_by": ["cto_agent", "report_generator_agent"],
                    "created_at": datetime.utcnow().isoformat()
                }
                
            elif request.data_type == "webhook":
                sample = {
                    "id": str(uuid.uuid4()),
                    "url": f"https://webhook.site/sample-{i+1}",
                    "events": ["assessment.completed", "report.generated"],
                    "description": f"Sample webhook {i+1}",
                    "status": "active",
                    "success_count": 15,
                    "failure_count": 2,
                    "created_at": datetime.utcnow().isoformat()
                }
                
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported data type: {request.data_type}"
                )
            
            # Apply customizations
            if request.customization:
                sample.update(request.customization)
            
            sample_data.append(sample)
        
        logger.info(f"Generated {len(sample_data)} samples of type {request.data_type}")
        
        return {
            "data_type": request.data_type,
            "count": len(sample_data),
            "samples": sample_data,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sample data"
        )


@router.get("/openapi-examples")
async def get_openapi_examples():
    """
    Get OpenAPI examples for interactive testing.
    
    Returns comprehensive examples that can be used in the OpenAPI documentation
    for interactive testing of all endpoints.
    """
    try:
        examples = {
            "assessment_create": {
                "summary": "Create E-commerce Assessment",
                "description": "Example of creating an assessment for an e-commerce platform",
                "value": {
                    "title": "E-commerce Platform Assessment",
                    "description": "Infrastructure assessment for scaling e-commerce platform to handle Black Friday traffic",
                    "business_requirements": {
                        "company_size": "medium",
                        "industry": "retail",
                        "budget_range": "100k_500k",
                        "compliance_requirements": ["gdpr", "pci_dss"],
                        "business_goals": [
                            {
                                "goal": "Handle 10x traffic during peak sales",
                                "priority": "high",
                                "timeline_months": 3,
                                "success_metrics": ["Zero downtime during Black Friday", "Sub-200ms response times"]
                            }
                        ]
                    },
                    "technical_requirements": {
                        "workload_types": ["web_application", "data_processing", "real_time_analytics"],
                        "performance_requirements": {
                            "api_response_time_ms": 150,
                            "requests_per_second": 5000,
                            "concurrent_users": 2000,
                            "uptime_percentage": 99.99
                        }
                    },
                    "priority": "high",
                    "source": "web_form"
                }
            },
            "recommendation_generate": {
                "summary": "Generate Multi-Agent Recommendations",
                "description": "Example of triggering recommendation generation from multiple AI agents",
                "value": {
                    "agent_names": ["cto_agent", "cloud_engineer_agent", "research_agent", "compliance_agent"],
                    "priority_override": "high",
                    "custom_config": {
                        "focus_areas": ["cost_optimization", "scalability", "security"],
                        "cloud_preferences": ["aws", "azure"],
                        "budget_constraints": {"max_monthly": 50000}
                    }
                }
            },
            "report_generate": {
                "summary": "Generate Executive Report",
                "description": "Example of generating a comprehensive executive report",
                "value": {
                    "report_type": "executive_summary",
                    "format": "pdf",
                    "title": "AI Infrastructure Strategy Report",
                    "sections": [
                        "executive_summary",
                        "key_recommendations", 
                        "cost_analysis",
                        "implementation_roadmap",
                        "risk_assessment"
                    ],
                    "priority": "high"
                }
            },
            "webhook_create": {
                "summary": "Create Webhook for Notifications",
                "description": "Example of setting up a webhook for real-time notifications",
                "value": {
                    "url": "https://your-app.com/webhooks/infra-mind",
                    "events": [
                        "assessment.completed",
                        "recommendation.generated",
                        "report.completed",
                        "system.alert"
                    ],
                    "secret": "your-webhook-secret-key",
                    "description": "Production webhook for assessment notifications",
                    "headers": {
                        "X-Custom-Header": "your-value"
                    },
                    "timeout_seconds": 30,
                    "retry_attempts": 3
                }
            }
        }
        
        logger.info("Retrieved OpenAPI examples")
        
        return {
            "examples": examples,
            "usage_guide": "https://docs.infra-mind.com/api/examples",
            "interactive_testing": "Use these examples in the /docs endpoint for interactive testing"
        }
        
    except Exception as e:
        logger.error(f"Failed to get OpenAPI examples: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OpenAPI examples"
        )


@router.get("/postman-collection")
async def get_postman_collection():
    """
    Get Postman collection for API testing.
    
    Returns a Postman collection file that can be imported for comprehensive API testing.
    """
    try:
        postman_collection = {
            "info": {
                "name": "Infra Mind API",
                "description": "Complete API collection for Infra Mind platform testing",
                "version": "2.0.0",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{jwt_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000/api/v2",
                    "type": "string"
                },
                {
                    "key": "jwt_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": [
                {
                    "name": "Authentication",
                    "item": [
                        {
                            "name": "Register User",
                            "request": {
                                "method": "POST",
                                "header": [],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "email": "test@example.com",
                                        "password": "testpassword123",
                                        "full_name": "Test User",
                                        "company": "Test Company"
                                    }),
                                    "options": {"raw": {"language": "json"}}
                                },
                                "url": {
                                    "raw": "{{base_url}}/auth/register",
                                    "host": ["{{base_url}}"],
                                    "path": ["auth", "register"]
                                }
                            }
                        },
                        {
                            "name": "Login User",
                            "request": {
                                "method": "POST",
                                "header": [],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "email": "test@example.com",
                                        "password": "testpassword123"
                                    }),
                                    "options": {"raw": {"language": "json"}}
                                },
                                "url": {
                                    "raw": "{{base_url}}/auth/login",
                                    "host": ["{{base_url}}"],
                                    "path": ["auth", "login"]
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
                                "header": [],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "title": "Sample Assessment",
                                        "description": "Test assessment",
                                        "business_requirements": {
                                            "company_size": "medium",
                                            "industry": "technology",
                                            "budget_range": "100k_500k"
                                        },
                                        "technical_requirements": {
                                            "workload_types": ["web_application"]
                                        },
                                        "priority": "medium"
                                    }),
                                    "options": {"raw": {"language": "json"}}
                                },
                                "url": {
                                    "raw": "{{base_url}}/assessments",
                                    "host": ["{{base_url}}"],
                                    "path": ["assessments"]
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        logger.info("Generated Postman collection")
        
        return postman_collection
        
    except Exception as e:
        logger.error(f"Failed to generate Postman collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Postman collection"
        )