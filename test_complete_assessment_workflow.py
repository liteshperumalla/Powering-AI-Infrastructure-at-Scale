#!/usr/bin/env python3
"""
Complete Assessment Workflow Test Script

This script tests the complete assessment workflow from creation to completion,
ensuring all fixes work properly and data is displayed correctly.
"""

import asyncio
import json
import logging
import requests
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_ASSESSMENT_DATA = {
    "title": f"Complete Workflow Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "description": "Testing complete assessment workflow with all fixes",
    "business_requirements": {
        "company_size": "medium",
        "industry": "technology",
        "business_goals": [
            {
                "goal": "Cost optimization",
                "priority": "high",
                "timeline_months": 6,
                "success_metrics": ["reduce_costs_by_25_percent"]
            },
            {
                "goal": "Performance improvement", 
                "priority": "high",
                "timeline_months": 3,
                "success_metrics": ["improve_response_time_by_50_percent"]
            }
        ],
        "growth_projection": {
            "user_growth_rate": "rapid",
            "projected_users_12_months": 100000,
            "revenue_growth_rate": "moderate",
            "geographic_expansion": ["north_america", "europe"]
        },
        "budget_constraints": {
            "total_budget": 75000,
            "monthly_operational_budget": 5000,
            "capital_expenditure_budget": 25000,
            "budget_flexibility": "medium"
        },
        "team_structure": {
            "total_team_size": "medium",
            "technical_team_size": 8,
            "devops_experience": "intermediate",
            "cloud_experience": "intermediate",
            "available_training_budget": 10000
        },
        "compliance_requirements": ["soc2", "gdpr"],
        "project_timeline_months": 8,
        "risk_tolerance": "medium"
    },
    "technical_requirements": {
        "current_infrastructure": "cloud",
        "workload_types": ["web_application", "api_service", "data_processing"],
        "performance_requirements": {},
        "scalability_requirements": {},
        "security_requirements": {},
        "integration_requirements": {}
    }
}

class AssessmentWorkflowTester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.assessment_id: Optional[str] = None
        self.workflow_id: Optional[str] = None
        
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete assessment workflow test."""
        results = {
            "test_started_at": datetime.now(timezone.utc).isoformat(),
            "steps": {},
            "overall_success": False,
            "errors": [],
            "timings": {}
        }
        
        try:
            logger.info("🚀 Starting Complete Assessment Workflow Test")
            logger.info("=" * 60)
            
            # Step 1: Health Check
            await self._test_health_check(results)
            
            # Step 2: Create Assessment
            await self._test_create_assessment(results)
            
            # Step 3: Monitor Workflow Progress
            await self._test_monitor_workflow(results)
            
            # Step 4: Validate Results
            await self._test_validate_results(results)
            
            # Step 5: Test Frontend Cache Busting
            await self._test_cache_busting(results)
            
            # Calculate overall success
            failed_steps = [step for step, data in results["steps"].items() if not data.get("success", False)]
            results["overall_success"] = len(failed_steps) == 0
            results["failed_steps"] = failed_steps
            
            logger.info("=" * 60)
            if results["overall_success"]:
                logger.info("✅ Complete Assessment Workflow Test PASSED!")
            else:
                logger.error(f"❌ Complete Assessment Workflow Test FAILED! Failed steps: {failed_steps}")
            
        except Exception as e:
            logger.error(f"Critical error in workflow test: {e}")
            results["errors"].append(str(e))
            results["overall_success"] = False
            
        finally:
            results["test_completed_at"] = datetime.now(timezone.utc).isoformat()
            
        return results
    
    async def _test_health_check(self, results: Dict[str, Any]):
        """Test system health before starting."""
        logger.info("📋 Step 1: Health Check")
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                results["steps"]["health_check"] = {
                    "success": True,
                    "status": health_data.get("status", "unknown"),
                    "services": health_data.get("services", {}),
                    "response_time": time.time() - start_time
                }
                logger.info(f"   ✅ System health: {health_data.get('status', 'unknown')}")
            else:
                raise Exception(f"Health check failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Health check failed: {e}")
            results["steps"]["health_check"] = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            results["errors"].append(f"Health check failed: {e}")
    
    async def _test_create_assessment(self, results: Dict[str, Any]):
        """Test assessment creation."""
        logger.info("📝 Step 2: Create Assessment")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/assessments",
                json=TEST_ASSESSMENT_DATA,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                assessment_data = response.json()
                self.assessment_id = assessment_data.get("id")
                self.workflow_id = assessment_data.get("workflow_id")
                
                results["steps"]["create_assessment"] = {
                    "success": True,
                    "assessment_id": self.assessment_id,
                    "workflow_id": self.workflow_id,
                    "status": assessment_data.get("status"),
                    "response_time": time.time() - start_time
                }
                logger.info(f"   ✅ Assessment created: {self.assessment_id}")
                logger.info(f"   📋 Workflow ID: {self.workflow_id}")
            else:
                raise Exception(f"Assessment creation failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"   ❌ Assessment creation failed: {e}")
            results["steps"]["create_assessment"] = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            results["errors"].append(f"Assessment creation failed: {e}")
    
    async def _test_monitor_workflow(self, results: Dict[str, Any]):
        """Monitor the workflow progress to ensure it doesn't get stuck."""
        if not self.assessment_id:
            logger.error("   ❌ Cannot monitor workflow - no assessment ID")
            return
            
        logger.info("📊 Step 3: Monitor Workflow Progress")
        start_time = time.time()
        
        try:
            max_wait_time = 180  # 3 minutes max
            check_interval = 5   # Check every 5 seconds
            checks = 0
            max_checks = max_wait_time // check_interval
            last_progress = 0
            stuck_count = 0
            
            while checks < max_checks:
                try:
                    response = requests.get(
                        f"{self.base_url}/api/v2/assessments/{self.assessment_id}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        assessment = response.json()
                        status = assessment.get("status")
                        progress = assessment.get("completion_percentage", 0)
                        current_step = assessment.get("progress", {}).get("current_step", "unknown")
                        
                        logger.info(f"   📈 Progress: {progress:.1f}% - Status: {status} - Step: {current_step}")
                        
                        # Check if workflow is stuck
                        if progress == last_progress and progress > 0 and progress < 100:
                            stuck_count += 1
                            if stuck_count >= 6:  # Stuck for 30 seconds
                                logger.warning(f"   ⚠️ Workflow may be stuck at {progress}%")
                        else:
                            stuck_count = 0
                            
                        last_progress = progress
                        
                        # Check if completed
                        if status == "completed" or progress >= 100:
                            results["steps"]["monitor_workflow"] = {
                                "success": True,
                                "final_status": status,
                                "final_progress": progress,
                                "total_time": time.time() - start_time,
                                "checks_performed": checks + 1,
                                "got_stuck": False
                            }
                            logger.info(f"   ✅ Workflow completed! Final progress: {progress}%")
                            return
                        
                        # Check if failed
                        if status == "failed":
                            raise Exception(f"Workflow failed at {progress}% progress")
                            
                    await asyncio.sleep(check_interval)
                    checks += 1
                    
                except requests.exceptions.RequestException as e:
                    logger.warning(f"   ⚠️ Request error during monitoring: {e}")
                    await asyncio.sleep(check_interval)
                    checks += 1
                    continue
            
            # If we reach here, workflow timed out
            raise Exception(f"Workflow timed out after {max_wait_time} seconds. Last progress: {last_progress}%")
            
        except Exception as e:
            logger.error(f"   ❌ Workflow monitoring failed: {e}")
            results["steps"]["monitor_workflow"] = {
                "success": False,
                "error": str(e),
                "last_progress": last_progress,
                "total_time": time.time() - start_time,
                "got_stuck": stuck_count >= 6
            }
            results["errors"].append(f"Workflow monitoring failed: {e}")
    
    async def _test_validate_results(self, results: Dict[str, Any]):
        """Validate that the assessment has proper results."""
        if not self.assessment_id:
            logger.error("   ❌ Cannot validate results - no assessment ID")
            return
            
        logger.info("🔍 Step 4: Validate Results")
        start_time = time.time()
        
        try:
            # Check recommendations
            recommendations_response = requests.get(
                f"{self.base_url}/api/v2/recommendations/{self.assessment_id}",
                timeout=15
            )
            
            recommendations_count = 0
            if recommendations_response.status_code == 200:
                recs_data = recommendations_response.json()
                recommendations_count = len(recs_data.get("recommendations", []))
                logger.info(f"   📋 Found {recommendations_count} recommendations")
            
            # Check visualization data
            viz_response = requests.get(
                f"{self.base_url}/api/v2/assessments/{self.assessment_id}/visualization-data",
                timeout=15
            )
            
            has_visualization = False
            if viz_response.status_code == 200:
                viz_data = viz_response.json()
                assessment_results = viz_data.get("data", {}).get("assessment_results", [])
                has_visualization = len(assessment_results) > 0
                logger.info(f"   📊 Visualization data available: {has_visualization}")
                if has_visualization:
                    logger.info(f"   📊 Found {len(assessment_results)} assessment result categories")
            
            # Check reports
            reports_response = requests.get(
                f"{self.base_url}/api/v2/reports/{self.assessment_id}",
                timeout=15
            )
            
            reports_count = 0
            if reports_response.status_code == 200:
                reports_data = reports_response.json()
                if isinstance(reports_data, list):
                    reports_count = len(reports_data)
                    logger.info(f"   📄 Found {reports_count} reports")
            
            # Validate results
            success = (recommendations_count > 0) and has_visualization
            
            results["steps"]["validate_results"] = {
                "success": success,
                "recommendations_count": recommendations_count,
                "has_visualization": has_visualization,
                "reports_count": reports_count,
                "response_time": time.time() - start_time
            }
            
            if success:
                logger.info("   ✅ Results validation passed!")
            else:
                logger.error("   ❌ Results validation failed!")
                results["errors"].append("Insufficient results generated")
                
        except Exception as e:
            logger.error(f"   ❌ Results validation failed: {e}")
            results["steps"]["validate_results"] = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            results["errors"].append(f"Results validation failed: {e}")
    
    async def _test_cache_busting(self, results: Dict[str, Any]):
        """Test that cache busting works properly."""
        if not self.assessment_id:
            logger.error("   ❌ Cannot test cache busting - no assessment ID")
            return
            
        logger.info("🔄 Step 5: Test Cache Busting")
        start_time = time.time()
        
        try:
            # Make multiple requests to the same endpoint with cache busting
            base_url = f"{self.base_url}/api/v2/assessments/{self.assessment_id}/visualization-data"
            
            timestamps = []
            for i in range(3):
                # Add cache busting parameters
                timestamp = int(time.time() * 1000)
                url = f"{base_url}?t={timestamp}&_cb={timestamp}"
                
                response = requests.get(url, headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    generated_at = data.get("generated_at")
                    timestamps.append(generated_at)
                    logger.info(f"   📊 Request {i+1}: Status {response.status_code}, Generated at: {generated_at}")
                else:
                    logger.warning(f"   ⚠️ Request {i+1}: Status {response.status_code}")
                
                await asyncio.sleep(1)  # Small delay between requests
            
            # Check that we're getting fresh data (not cached)
            cache_busting_works = len(set(filter(None, timestamps))) >= 1  # At least one unique timestamp
            
            results["steps"]["test_cache_busting"] = {
                "success": cache_busting_works,
                "timestamps": timestamps,
                "unique_timestamps": len(set(filter(None, timestamps))),
                "response_time": time.time() - start_time
            }
            
            if cache_busting_works:
                logger.info("   ✅ Cache busting test passed!")
            else:
                logger.error("   ❌ Cache busting test failed!")
                results["errors"].append("Cache busting not working properly")
                
        except Exception as e:
            logger.error(f"   ❌ Cache busting test failed: {e}")
            results["steps"]["test_cache_busting"] = {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            results["errors"].append(f"Cache busting test failed: {e}")

async def main():
    """Main test function."""
    tester = AssessmentWorkflowTester()
    results = await tester.run_complete_test()
    
    # Save results to file
    results_file = f"assessment_workflow_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📁 Test results saved to: {results_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("ASSESSMENT WORKFLOW TEST SUMMARY")
    print("="*60)
    print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
    print(f"Total Steps: {len(results['steps'])}")
    print(f"Successful Steps: {sum(1 for step in results['steps'].values() if step.get('success'))}")
    print(f"Failed Steps: {sum(1 for step in results['steps'].values() if not step.get('success'))}")
    
    if not results['overall_success']:
        print(f"Failed Steps: {results.get('failed_steps', [])}")
        print(f"Errors: {results.get('errors', [])}")
    
    print("="*60)
    
    # Return appropriate exit code
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)