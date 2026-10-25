#!/usr/bin/env python3
"""
Real Data Generation Script for Infra Mind Platform

This script generates comprehensive real data using LLM agents and APIs
to replace any demo/fallback data across all endpoints.
"""

import asyncio
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfraMindDataGenerator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.session = requests.Session()

    async def authenticate(self) -> bool:
        """Authenticate with the API to get access token"""
        try:
            # Try to register a test user
            register_data = {
                "email": "data.generator@infra-mind.com",
                "password": "SecurePassword123!",
                "full_name": "Data Generator",
                "company": "Infra Mind Systems"
            }

            # Try registration first
            response = self.session.post(
                f"{self.base_url}/api/v2/auth/register",
                json=register_data
            )

            if response.status_code in [200, 201]:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                logger.info("✅ Successfully registered and authenticated")
            else:
                # Try login if registration fails (user might already exist)
                login_data = {
                    "username": register_data["email"],
                    "password": register_data["password"]
                }

                response = self.session.post(
                    f"{self.base_url}/api/v2/auth/login",
                    data=login_data
                )

                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get("access_token")
                    logger.info("✅ Successfully logged in")
                else:
                    logger.error(f"❌ Authentication failed: {response.text}")
                    return False

            # Set authorization header for all future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            })

            return True

        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False

    async def create_sample_assessment(self) -> str:
        """Create a comprehensive sample assessment"""
        try:
            assessment_data = {
                "title": "Enterprise Cloud Infrastructure Assessment",
                "description": "Comprehensive multi-cloud infrastructure evaluation for digital transformation",
                "company_name": "TechCorp Global Inc.",
                "industry": "Technology Services",
                "cloud_providers": ["aws", "azure", "gcp"],
                "current_infrastructure": {
                    "servers": 450,
                    "databases": 25,
                    "storage_tb": 2500,
                    "monthly_cost": 125000,
                    "compliance_requirements": ["SOC2", "ISO27001", "HIPAA"],
                    "current_challenges": [
                        "High operational costs",
                        "Manual scaling processes",
                        "Limited disaster recovery",
                        "Security compliance gaps",
                        "Multi-cloud complexity"
                    ]
                },
                "business_requirements": {
                    "performance_targets": {
                        "availability": 99.9,
                        "response_time_ms": 200,
                        "throughput_rps": 10000
                    },
                    "scaling_requirements": {
                        "expected_growth": "300% over 2 years",
                        "seasonal_peaks": "Black Friday: 10x traffic",
                        "geographic_expansion": ["EU", "APAC"]
                    },
                    "budget_constraints": {
                        "current_monthly_budget": 125000,
                        "target_savings": 0.25,
                        "acceptable_increase": 0.15
                    }
                },
                "technical_requirements": {
                    "workload_types": ["web_applications", "api_services", "data_processing", "ml_training"],
                    "data_sensitivity": "high",
                    "integration_needs": ["CI/CD", "monitoring", "backup", "logging"],
                    "preferred_technologies": ["kubernetes", "serverless", "microservices"]
                }
            }

            response = self.session.post(
                f"{self.base_url}/api/v2/assessments/",
                json=assessment_data
            )

            if response.status_code in [200, 201]:
                assessment = response.json()
                assessment_id = assessment.get("id") or assessment.get("_id")
                logger.info(f"✅ Created assessment: {assessment_id}")

                # Start the assessment to trigger agent processing
                start_response = self.session.post(
                    f"{self.base_url}/api/v2/assessments/{assessment_id}/start"
                )

                if start_response.status_code in [200, 201]:
                    logger.info(f"✅ Started assessment processing: {assessment_id}")

                return assessment_id
            else:
                logger.error(f"❌ Failed to create assessment: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating assessment: {str(e)}")
            return None

    async def generate_analytics_data(self, assessment_id: str = None):
        """Generate comprehensive analytics data"""
        try:
            # Get analytics dashboard data
            response = self.session.get(f"{self.base_url}/api/v2/advanced-analytics/dashboard")

            if response.status_code == 200:
                logger.info("✅ Analytics dashboard data available")
                return response.json()
            else:
                logger.warning(f"⚠️ Analytics data not ready: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error generating analytics data: {str(e)}")
            return None

    async def generate_recommendations(self, assessment_id: str):
        """Generate AI-powered recommendations"""
        try:
            # Trigger recommendation generation
            response = self.session.get(f"{self.base_url}/api/v2/recommendations/{assessment_id}")

            if response.status_code == 200:
                recommendations = response.json()
                logger.info(f"✅ Generated {len(recommendations.get('recommendations', []))} recommendations")
                return recommendations
            else:
                logger.warning(f"⚠️ Recommendations not ready: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {str(e)}")
            return None

    async def generate_reports(self, assessment_id: str):
        """Generate comprehensive reports"""
        try:
            # Trigger report generation
            response = self.session.get(f"{self.base_url}/api/v2/reports/{assessment_id}")

            if response.status_code == 200:
                reports = response.json()
                logger.info(f"✅ Generated reports for assessment {assessment_id}")
                return reports
            else:
                logger.warning(f"⚠️ Reports not ready: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error generating reports: {str(e)}")
            return None

    async def trigger_ai_agents(self, assessment_id: str):
        """Trigger all AI agents to generate comprehensive data"""
        try:
            agents_to_trigger = [
                "infrastructure_analysis",
                "cost_optimization",
                "security_audit",
                "performance_optimization",
                "compliance_check"
            ]

            for agent in agents_to_trigger:
                try:
                    # Trigger agent processing
                    response = self.session.post(
                        f"{self.base_url}/api/v2/assessments/{assessment_id}/agents/{agent}/trigger"
                    )

                    if response.status_code in [200, 201, 202]:
                        logger.info(f"✅ Triggered {agent} agent")
                    else:
                        logger.warning(f"⚠️ Failed to trigger {agent} agent: {response.status_code}")

                except Exception as e:
                    logger.warning(f"⚠️ Error triggering {agent}: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Error triggering AI agents: {str(e)}")

    async def generate_dashboard_data(self):
        """Generate dashboard overview data"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/dashboard/")

            if response.status_code == 200:
                dashboard_data = response.json()
                logger.info("✅ Dashboard data generated")
                return dashboard_data
            else:
                logger.warning(f"⚠️ Dashboard data not ready: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error generating dashboard data: {str(e)}")
            return None

    async def run_comprehensive_data_generation(self):
        """Run comprehensive data generation across all endpoints"""
        logger.info("🚀 Starting comprehensive data generation...")

        # Step 1: Authenticate
        if not await self.authenticate():
            logger.error("❌ Authentication failed, cannot proceed")
            return

        # Step 2: Create sample assessment
        assessment_id = await self.create_sample_assessment()
        if not assessment_id:
            logger.error("❌ Failed to create assessment, cannot proceed")
            return

        # Step 3: Trigger AI agents
        await self.trigger_ai_agents(assessment_id)

        # Step 4: Wait for processing (in real scenario, you might poll status)
        logger.info("⏳ Waiting for AI agents to process...")
        await asyncio.sleep(30)  # Give agents time to process

        # Step 5: Generate all data types
        tasks = [
            self.generate_analytics_data(assessment_id),
            self.generate_recommendations(assessment_id),
            self.generate_reports(assessment_id),
            self.generate_dashboard_data()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Step 6: Summary
        logger.info("🎉 Data generation completed!")
        logger.info(f"📊 Assessment ID: {assessment_id}")

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Task {i} failed: {str(result)}")
            elif result:
                logger.info(f"✅ Task {i} completed successfully")
            else:
                logger.warning(f"⚠️ Task {i} returned no data")

async def main():
    """Main function to run data generation"""
    generator = InfraMindDataGenerator()
    await generator.run_comprehensive_data_generation()

if __name__ == "__main__":
    print("🔥 Infra Mind Real Data Generator")
    print("=" * 50)
    asyncio.run(main())