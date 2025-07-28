#!/usr/bin/env python3
"""
Simple test for assessment creation to debug the issue.
"""

import asyncio
import json
import sys
import os
import httpx
from loguru import logger

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_assessment_creation():
    """Test assessment creation with detailed error logging."""
    
    # Minimal assessment data
    assessment_data = {
        "title": "Simple Test Assessment",
        "description": "Simple test",
        "business_requirements": {
            "company_size": "medium",
            "industry": "technology",
            "business_goals": [
                {
                    "goal": "Reduce infrastructure costs by 30%",
                    "priority": "high",
                    "timeline_months": 6,
                    "success_metrics": ["Monthly cost reduction", "Performance maintained"]
                }
            ],
            "growth_projection": {
                "current_users": 1000,
                "projected_users_6m": 2000,
                "projected_users_12m": 5000,
                "current_revenue": "500000",
                "projected_revenue_12m": "1000000"
            },
            "budget_constraints": {
                "total_budget_range": "100k_500k",
                "monthly_budget_limit": "25000",
                "compute_percentage": 40,
                "storage_percentage": 20,
                "networking_percentage": 20,
                "security_percentage": 20,
                "cost_optimization_priority": "high"
            },
            "team_structure": {
                "total_developers": 8,
                "senior_developers": 3,
                "devops_engineers": 2,
                "data_engineers": 1,
                "cloud_expertise_level": 3,
                "kubernetes_expertise": 2,
                "database_expertise": 4,
                "preferred_technologies": ["Python"]
            },
            "compliance_requirements": [],
            "project_timeline_months": 6,
            "urgency_level": "high",
            "current_pain_points": [],
            "success_criteria": [],
            "multi_cloud_acceptable": True
        },
        "technical_requirements": {
            "workload_types": ["web_application"],
            "performance_requirements": {
                "api_response_time_ms": 200,
                "requests_per_second": 1000,
                "concurrent_users": 500,
                "uptime_percentage": "99.9",
                "real_time_processing_required": False
            },
            "scalability_requirements": {
                "current_data_size_gb": 100,
                "current_daily_transactions": 10000,
                "expected_data_growth_rate": "20% monthly",
                "peak_load_multiplier": "5.0",
                "auto_scaling_required": True,
                "global_distribution_required": False,
                "cdn_required": True,
                "planned_regions": ["us-east-1"]
            },
            "security_requirements": {
                "encryption_at_rest_required": True,
                "encryption_in_transit_required": True,
                "multi_factor_auth_required": True,
                "vpc_isolation_required": True,
                "security_monitoring_required": True,
                "audit_logging_required": True
            },
            "integration_requirements": {
                "existing_databases": [],
                "existing_apis": [],
                "rest_api_required": True,
                "real_time_sync_required": False,
                "batch_sync_acceptable": True
            },
            "preferred_programming_languages": ["Python"],
            "monitoring_requirements": [],
            "backup_requirements": [],
            "ci_cd_requirements": []
        },
        "priority": "medium",
        "tags": [],
        "source": "api_test"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("Testing assessment creation...")
            logger.info(f"Data: {json.dumps(assessment_data, indent=2)}")
            
            response = await client.post(
                f"{API_BASE_URL}{API_PREFIX}/assessments/",
                json=assessment_data
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 201:
                logger.error(f"Response text: {response.text}")
            else:
                data = response.json()
                logger.success(f"Assessment created successfully: {data.get('id')}")
                
        except Exception as e:
            logger.error(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_assessment_creation())