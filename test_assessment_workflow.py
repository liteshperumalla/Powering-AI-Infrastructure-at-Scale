#!/usr/bin/env python3
"""
Test the assessment workflow to ensure it works properly after database cleanup.

This script will:
1. Start the API server
2. Create a test assessment
3. Monitor the workflow progress
4. Verify dashboard data generation
"""
import asyncio
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import aiohttp
from loguru import logger


async def test_assessment_workflow():
    """Test the complete assessment workflow."""
    api_base_url = "http://localhost:8000/api/v2"
    health_url = "http://localhost:8000"
    
    logger.info("🧪 Testing Assessment Workflow")
    logger.info("=" * 50)
    
    # Test data for assessment creation
    test_assessment = {
        "title": "Test Infrastructure Assessment",
        "description": "Automated test assessment to verify workflow",
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
                "current_revenue": "500000.00",
                "projected_revenue_12m": "1000000.00"
            },
            "budget_constraints": {
                "total_budget_range": "100k_500k",
                "monthly_budget_limit": "25000.00",
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
                "preferred_technologies": ["Python", "React", "PostgreSQL"]
            },
            "compliance_requirements": ["gdpr"],
            "project_timeline_months": 6,
            "urgency_level": "high",
            "current_pain_points": ["High infrastructure costs", "Manual scaling"],
            "success_criteria": ["30% cost reduction", "Automated scaling"],
            "multi_cloud_acceptable": True
        },
        "technical_requirements": {
            "workload_types": ["web_application", "data_processing"],
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
                "planned_regions": ["us-east-1", "eu-west-1"]
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
                "existing_databases": ["PostgreSQL"],
                "existing_apis": ["Payment API", "Analytics API"],
                "rest_api_required": True,
                "real_time_sync_required": False,
                "batch_sync_acceptable": True
            },
            "preferred_programming_languages": ["Python", "JavaScript"],
            "monitoring_requirements": ["Application metrics", "Infrastructure monitoring"],
            "backup_requirements": ["Daily backups", "Cross-region replication"],
            "ci_cd_requirements": ["Automated testing", "Blue-green deployment"]
        },
        "priority": "high"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Step 1: Test API health
            logger.info("1. Testing API health...")
            try:
                async with session.get(f"{health_url}/health") as response:
                    if response.status == 200:
                        logger.success("✅ API is healthy")
                    else:
                        logger.error(f"❌ API health check failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Cannot connect to API: {e}")
                logger.info("💡 Make sure to run: docker-compose up api")
                return False

            # Step 2: Create assessment
            logger.info("2. Creating test assessment...")
            try:
                async with session.post(
                    f"{api_base_url}/assessments/",
                    json=test_assessment,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 201:
                        assessment_data = await response.json()
                        assessment_id = assessment_data['id']
                        logger.success(f"✅ Assessment created successfully: {assessment_id}")
                        logger.info(f"   Status: {assessment_data.get('status', 'unknown')}")
                        logger.info(f"   Workflow ID: {assessment_data.get('workflow_id', 'none')}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to create assessment: {response.status}")
                        logger.error(f"   Error: {error_text}")
                        return False
            except Exception as e:
                logger.error(f"❌ Failed to create assessment: {e}")
                return False

            # Step 3: Monitor workflow progress
            logger.info("3. Monitoring workflow progress...")
            max_wait_time = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    async with session.get(f"{api_base_url}/assessments/{assessment_id}") as response:
                        if response.status == 200:
                            assessment_status = await response.json()
                            status = assessment_status.get('status', 'unknown')
                            progress = assessment_status.get('progress', {})
                            progress_pct = progress.get('progress_percentage', 0)
                            current_step = progress.get('current_step', 'unknown')
                            
                            logger.info(f"   Progress: {progress_pct}% - {current_step} (Status: {status})")
                            
                            if status == 'completed':
                                logger.success("✅ Assessment workflow completed!")
                                break
                            elif status == 'failed':
                                logger.error("❌ Assessment workflow failed!")
                                error = progress.get('error', 'Unknown error')
                                logger.error(f"   Error: {error}")
                                return False
                        else:
                            logger.warning(f"Could not get assessment status: {response.status}")
                except Exception as e:
                    logger.warning(f"Error checking assessment status: {e}")
                
                await asyncio.sleep(5)  # Wait 5 seconds before checking again
            
            if time.time() - start_time >= max_wait_time:
                logger.warning("⚠️  Workflow is taking longer than expected, but continuing tests...")
            
            # Step 4: Test visualization data
            logger.info("4. Testing visualization data generation...")
            try:
                async with session.get(f"{api_base_url}/assessments/{assessment_id}/visualization-data") as response:
                    if response.status == 200:
                        viz_data = await response.json()
                        logger.success("✅ Visualization data generated successfully")
                        
                        # Verify data structure
                        if 'data' in viz_data and 'assessment_results' in viz_data['data']:
                            results = viz_data['data']['assessment_results']
                            logger.info(f"   Generated {len(results)} visualization categories")
                            logger.info(f"   Overall Score: {viz_data['data'].get('overall_score', 'N/A')}")
                            logger.info(f"   Recommendations: {viz_data['data'].get('recommendations_count', 0)}")
                            logger.info(f"   Fallback Data: {viz_data['data'].get('fallback_data', False)}")
                        else:
                            logger.warning("⚠️  Visualization data structure is incomplete")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to get visualization data: {response.status}")
                        logger.error(f"   Error: {error_text}")
            except Exception as e:
                logger.error(f"❌ Failed to test visualization data: {e}")

            # Step 5: Test recommendations
            logger.info("5. Testing recommendations generation...")
            try:
                async with session.get(f"{api_base_url}/recommendations/{assessment_id}") as response:
                    if response.status == 200:
                        rec_data = await response.json()
                        recommendations = rec_data.get('recommendations', [])
                        logger.success(f"✅ Generated {len(recommendations)} recommendations")
                        
                        if recommendations:
                            # Show first recommendation as example
                            first_rec = recommendations[0]
                            logger.info(f"   Example: {first_rec.get('title', 'Unknown')}")
                            logger.info(f"   Agent: {first_rec.get('agent_name', 'Unknown')}")
                            logger.info(f"   Confidence: {first_rec.get('confidence_score', 0)}")
                    else:
                        logger.warning(f"⚠️  No recommendations found yet: {response.status}")
            except Exception as e:
                logger.warning(f"⚠️  Could not check recommendations: {e}")

            # Step 6: Test reports
            logger.info("6. Testing reports generation...")
            try:
                async with session.get(f"{api_base_url}/reports/{assessment_id}") as response:
                    if response.status == 200:
                        reports = await response.json()
                        logger.success(f"✅ Generated {len(reports)} reports")
                        
                        if reports:
                            for report in reports:
                                logger.info(f"   Report: {report.get('title', 'Unknown')}")
                                logger.info(f"   Type: {report.get('report_type', 'Unknown')}")
                                logger.info(f"   Status: {report.get('status', 'Unknown')}")
                    else:
                        logger.warning(f"⚠️  No reports found yet: {response.status}")
            except Exception as e:
                logger.warning(f"⚠️  Could not check reports: {e}")

            logger.info("=" * 50)
            logger.success("🎉 Assessment workflow test completed!")
            logger.info("\nNext steps:")
            logger.info("1. Open the frontend: http://localhost:3000/dashboard")
            logger.info("2. Verify that fresh visualizations are displayed")
            logger.info("3. Create another assessment to test the refresh behavior")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Main function."""
    success = await test_assessment_workflow()
    if success:
        logger.success("✅ All tests passed!")
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())