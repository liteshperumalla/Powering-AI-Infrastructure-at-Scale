#!/usr/bin/env python3
"""
Demo Data Creation Script

This script creates realistic demo data for the Infra Mind platform to test
the production migration process. It generates:
- Sample users with realistic profiles
- Assessment data with business requirements
- Recommendations from different agents
- Reports with various statuses
- Metrics and performance data

Usage:
    python scripts/create_demo_data.py --database infra_mind_demo --count 50
    python scripts/create_demo_data.py --database infra_mind_demo --reset
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import random
from faker import Faker
import uuid

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.core.database import init_database, db
from infra_mind.core.config import settings
from infra_mind.models import (
    User, Assessment, Recommendation, Report, Metric, 
    AgentMetrics
)
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import bcrypt
from bson import ObjectId


class DemoDataGenerator:
    """
    Generates realistic demo data for the Infra Mind platform.
    
    Features:
    - Realistic user profiles and business scenarios
    - Comprehensive assessment data with various industries
    - Multi-agent recommendations with different priorities
    - Report generation with various statuses and types
    - Performance metrics and audit trails
    """
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.fake = Faker()
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        
        # Business scenarios and industries
        self.industries = [
            "Healthcare", "Financial Services", "E-commerce", "Manufacturing",
            "Education", "Government", "Retail", "Technology", "Media",
            "Transportation", "Energy", "Real Estate"
        ]
        
        self.company_sizes = [
            {"name": "Startup", "employees": "1-50", "revenue": "< $1M"},
            {"name": "Small Business", "employees": "51-200", "revenue": "$1M-$10M"},
            {"name": "Mid-Market", "employees": "201-1000", "revenue": "$10M-$100M"},
            {"name": "Enterprise", "employees": "1000+", "revenue": "$100M+"}
        ]
        
        self.cloud_maturity_levels = [
            "Cloud Beginner", "Cloud Adopter", "Cloud Native", "Multi-Cloud Expert"
        ]
        
        self.ai_use_cases = [
            "Customer Service Automation", "Predictive Analytics", "Fraud Detection",
            "Recommendation Systems", "Document Processing", "Image Recognition",
            "Natural Language Processing", "Supply Chain Optimization",
            "Risk Assessment", "Personalization", "Quality Control", "Forecasting"
        ]
        
        # Agent types and their specialties
        self.agent_types = {
            "cto_agent": {
                "name": "CTO Agent",
                "focus": "Strategic technology decisions and architecture",
                "recommendations": ["Technology Stack", "Architecture Design", "Scalability Planning"]
            },
            "cloud_engineer_agent": {
                "name": "Cloud Engineer Agent", 
                "focus": "Cloud infrastructure and deployment",
                "recommendations": ["Infrastructure Setup", "Cost Optimization", "Security Configuration"]
            },
            "mlops_agent": {
                "name": "MLOps Agent",
                "focus": "ML pipeline and model deployment",
                "recommendations": ["ML Pipeline", "Model Deployment", "Data Management"]
            },
            "compliance_agent": {
                "name": "Compliance Agent",
                "focus": "Regulatory compliance and security",
                "recommendations": ["Compliance Framework", "Security Audit", "Risk Assessment"]
            },
            "infrastructure_agent": {
                "name": "Infrastructure Agent",
                "focus": "System infrastructure and monitoring",
                "recommendations": ["Monitoring Setup", "Performance Optimization", "Disaster Recovery"]
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_connection()
    
    async def initialize_connection(self):
        """Initialize database connection."""
        try:
            logger.info(f"🔌 Connecting to demo database: {self.database_name}")
            
            # Get database URL and modify for demo database
            db_url = settings.get_database_url()
            if self.database_name != settings.mongodb_database:
                db_url = db_url.replace(settings.mongodb_database, self.database_name)
            
            self.client = AsyncIOMotorClient(db_url)
            self.database = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.success("✅ Demo database connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to demo database: {e}")
            raise
    
    async def cleanup_connection(self):
        """Clean up database connection."""
        if self.client:
            self.client.close()
            logger.info("🔌 Demo database connection closed")
    
    async def reset_database(self):
        """Reset the demo database by dropping all collections."""
        try:
            logger.info("🗑️ Resetting demo database...")
            
            collections = await self.database.list_collection_names()
            for collection_name in collections:
                await self.database[collection_name].drop()
                logger.info(f"  Dropped collection: {collection_name}")
            
            logger.success("✅ Demo database reset completed")
            
        except Exception as e:
            logger.error(f"❌ Failed to reset demo database: {e}")
            raise
    
    async def generate_demo_data(self, user_count: int = 50):
        """Generate comprehensive demo data."""
        try:
            logger.info(f"🎭 Generating demo data for {user_count} users...")
            
            # Step 1: Generate users
            users = await self.generate_users(user_count)
            logger.success(f"✅ Generated {len(users)} users")
            
            # Step 2: Generate assessments
            assessments = await self.generate_assessments(users)
            logger.success(f"✅ Generated {len(assessments)} assessments")
            
            # Step 3: Generate recommendations
            recommendations = await self.generate_recommendations(assessments)
            logger.success(f"✅ Generated {len(recommendations)} recommendations")
            
            # Step 4: Generate reports
            reports = await self.generate_reports(assessments)
            logger.success(f"✅ Generated {len(reports)} reports")
            
            # Step 5: Generate metrics
            metrics = await self.generate_metrics(users, assessments)
            logger.success(f"✅ Generated {len(metrics)} metrics")
            
            # Step 6: Generate agent metrics
            agent_metrics = await self.generate_agent_metrics()
            logger.success(f"✅ Generated {len(agent_metrics)} agent metrics")
            
            # Step 7: Generate workflow states (simplified)
            workflow_states = await self.generate_workflow_states(assessments)
            logger.success(f"✅ Generated {len(workflow_states)} workflow states")
            
            # Step 8: Generate audit logs (simplified)
            audit_logs = await self.generate_audit_logs(users, assessments)
            logger.success(f"✅ Generated {len(audit_logs)} audit logs")
            
            # Summary
            total_records = (len(users) + len(assessments) + len(recommendations) + 
                           len(reports) + len(metrics) + len(agent_metrics) + 
                           len(workflow_states) + len(audit_logs))
            
            logger.success(f"🎉 Demo data generation completed: {total_records} total records")
            
            return {
                "users": len(users),
                "assessments": len(assessments),
                "recommendations": len(recommendations),
                "reports": len(reports),
                "metrics": len(metrics),
                "agent_metrics": len(agent_metrics),
                "workflow_states": len(workflow_states),
                "audit_logs": len(audit_logs),
                "total": total_records
            }
            
        except Exception as e:
            logger.error(f"❌ Demo data generation failed: {e}")
            raise
    
    async def generate_users(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic user data."""
        users = []
        
        for i in range(count):
            # Generate realistic user profile
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{self.fake.domain_name()}"
            
            # Hash password (using bcrypt for realism)
            password = "demo_password_123"
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Random company and role
            company_size = random.choice(self.company_sizes)
            industry = random.choice(self.industries)
            
            user_data = {
                "_id": ObjectId(),
                "email": email,
                "full_name": f"{first_name} {last_name}",
                "hashed_password": hashed_password,
                "is_active": True,
                "is_verified": random.choice([True, True, True, False]),  # 75% verified
                "role": random.choice(["user", "admin", "analyst"]),
                "company_name": self.fake.company(),
                "industry": industry,
                "company_size": company_size["name"],
                "job_title": random.choice([
                    "CTO", "VP Engineering", "DevOps Manager", "Cloud Architect",
                    "Data Scientist", "IT Director", "Software Engineer", "Product Manager"
                ]),
                "phone": self.fake.phone_number(),
                "timezone": random.choice([
                    "America/New_York", "America/Los_Angeles", "Europe/London",
                    "Asia/Tokyo", "Australia/Sydney", "America/Chicago"
                ]),
                "preferences": {
                    "notifications": {
                        "email": random.choice([True, False]),
                        "sms": random.choice([True, False]),
                        "push": True
                    },
                    "dashboard_layout": random.choice(["compact", "detailed", "minimal"]),
                    "theme": random.choice(["light", "dark", "auto"])
                },
                "subscription": {
                    "plan": random.choice(["free", "professional", "enterprise"]),
                    "status": "active",
                    "expires_at": datetime.utcnow() + timedelta(days=random.randint(30, 365))
                },
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                "last_login": datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
                "login_count": random.randint(1, 100),
                "profile_completion": random.randint(60, 100)
            }
            
            users.append(user_data)
        
        # Insert users into database
        if users:
            await self.database["users"].insert_many(users)
        
        return users
    
    async def generate_assessments(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic assessment data."""
        assessments = []
        
        # Generate 1-3 assessments per user
        for user in users:
            num_assessments = random.randint(1, 3)
            
            for _ in range(num_assessments):
                # Random assessment scenario
                use_case = random.choice(self.ai_use_cases)
                cloud_maturity = random.choice(self.cloud_maturity_levels)
                
                # Assessment status and completion
                status = random.choice([
                    "draft", "in_progress", "completed", "completed", "completed"  # More completed
                ])
                
                completion_percentage = 100 if status == "completed" else random.randint(20, 95)
                
                assessment_data = {
                    "_id": ObjectId(),
                    "user_id": user["_id"],
                    "title": f"{use_case} - {user['company_name']}",
                    "description": f"AI infrastructure assessment for {use_case.lower()} implementation in {user['industry'].lower()} industry",
                    "status": status,
                    "completion_percentage": completion_percentage,
                    "business_requirements": {
                        "industry": user["industry"],
                        "company_size": user["company_size"],
                        "primary_use_case": use_case,
                        "cloud_maturity": cloud_maturity,
                        "budget_range": random.choice([
                            "$10K-$50K", "$50K-$100K", "$100K-$500K", "$500K-$1M", "$1M+"
                        ]),
                        "timeline": random.choice([
                            "3 months", "6 months", "12 months", "18 months"
                        ]),
                        "compliance_requirements": random.sample([
                            "GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001", "CCPA"
                        ], random.randint(1, 3)),
                        "performance_requirements": {
                            "availability": random.choice(["99.9%", "99.95%", "99.99%"]),
                            "latency": random.choice(["< 100ms", "< 200ms", "< 500ms"]),
                            "throughput": random.choice(["1K req/s", "10K req/s", "100K req/s"])
                        }
                    },
                    "technical_requirements": {
                        "preferred_cloud": random.choice(["AWS", "Azure", "GCP", "Multi-Cloud"]),
                        "current_infrastructure": random.choice([
                            "On-Premises", "Hybrid", "Cloud-Native", "Legacy Systems"
                        ]),
                        "data_volume": random.choice([
                            "< 1TB", "1-10TB", "10-100TB", "100TB-1PB", "> 1PB"
                        ]),
                        "user_base": random.choice([
                            "< 1K users", "1K-10K users", "10K-100K users", "100K-1M users", "> 1M users"
                        ]),
                        "integration_requirements": random.sample([
                            "CRM", "ERP", "Database", "API", "Third-party Services", "Legacy Systems"
                        ], random.randint(2, 4))
                    },
                    "risk_assessment": {
                        "security_level": random.choice(["Low", "Medium", "High", "Critical"]),
                        "data_sensitivity": random.choice(["Public", "Internal", "Confidential", "Restricted"]),
                        "regulatory_impact": random.choice(["Low", "Medium", "High"]),
                        "business_criticality": random.choice(["Low", "Medium", "High", "Critical"])
                    },
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                    "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                    "completed_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)) if status == "completed" else None,
                    "metadata": {
                        "source": "web_form",
                        "version": "1.0",
                        "tags": random.sample([
                            "ai", "ml", "cloud", "scalability", "security", "compliance", "cost-optimization"
                        ], random.randint(2, 4))
                    }
                }
                
                assessments.append(assessment_data)
        
        # Insert assessments into database
        if assessments:
            await self.database["assessments"].insert_many(assessments)
        
        return assessments
    
    async def generate_recommendations(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic recommendation data from different agents."""
        recommendations = []
        
        for assessment in assessments:
            if assessment["status"] == "completed":
                # Generate 3-5 recommendations per completed assessment
                num_recommendations = random.randint(3, 5)
                
                for _ in range(num_recommendations):
                    agent_type = random.choice(list(self.agent_types.keys()))
                    agent_info = self.agent_types[agent_type]
                    
                    recommendation_type = random.choice(agent_info["recommendations"])
                    
                    recommendation_data = {
                        "_id": ObjectId(),
                        "assessment_id": assessment["_id"],
                        "agent_name": agent_type,
                        "agent_version": "1.0.0",
                        "recommendation_type": recommendation_type,
                        "title": f"{recommendation_type} for {assessment['business_requirements']['primary_use_case']}",
                        "description": self._generate_recommendation_description(
                            recommendation_type, 
                            assessment["business_requirements"]
                        ),
                        "priority": random.choice(["Low", "Medium", "High", "Critical"]),
                        "confidence_score": round(random.uniform(0.7, 0.95), 2),
                        "estimated_cost_monthly": random.randint(500, 50000),
                        "estimated_implementation_time": random.choice([
                            "1-2 weeks", "2-4 weeks", "1-2 months", "2-3 months", "3-6 months"
                        ]),
                        "cloud_provider": random.choice(["AWS", "Azure", "GCP"]),
                        "services": self._generate_cloud_services(recommendation_type),
                        "benefits": self._generate_benefits(recommendation_type),
                        "risks": self._generate_risks(recommendation_type),
                        "implementation_steps": self._generate_implementation_steps(recommendation_type),
                        "metrics": {
                            "performance_impact": random.choice(["Low", "Medium", "High"]),
                            "cost_impact": random.choice(["Low", "Medium", "High"]),
                            "complexity": random.choice(["Low", "Medium", "High"]),
                            "roi_estimate": f"{random.randint(150, 400)}%"
                        },
                        "status": random.choice(["pending", "approved", "rejected", "implemented"]),
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                        "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 7))
                    }
                    
                    recommendations.append(recommendation_data)
        
        # Insert recommendations into database
        if recommendations:
            await self.database["recommendations"].insert_many(recommendations)
        
        return recommendations
    
    async def generate_reports(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic report data."""
        reports = []
        
        for assessment in assessments:
            if assessment["status"] == "completed":
                # Generate 1-2 reports per completed assessment
                num_reports = random.randint(1, 2)
                
                for i in range(num_reports):
                    report_type = random.choice([
                        "Infrastructure Assessment Report",
                        "AI Implementation Strategy",
                        "Cloud Migration Plan",
                        "Security Compliance Report",
                        "Cost Optimization Analysis"
                    ])
                    
                    status = random.choice([
                        "generating", "completed", "completed", "completed", "failed"
                    ])
                    
                    report_data = {
                        "_id": ObjectId(),
                        "assessment_id": assessment["_id"],
                        "user_id": assessment["user_id"],
                        "title": f"{report_type} - {assessment['title']}",
                        "report_type": report_type,
                        "status": status,
                        "progress_percentage": 100 if status == "completed" else random.randint(10, 90),
                        "format": random.choice(["PDF", "HTML", "JSON"]),
                        "sections": [
                            {
                                "title": "Executive Summary",
                                "content": "High-level overview of recommendations and strategic insights",
                                "order": 1
                            },
                            {
                                "title": "Technical Analysis",
                                "content": "Detailed technical assessment and architecture recommendations",
                                "order": 2
                            },
                            {
                                "title": "Implementation Roadmap",
                                "content": "Step-by-step implementation plan with timelines",
                                "order": 3
                            },
                            {
                                "title": "Cost Analysis",
                                "content": "Detailed cost breakdown and ROI projections",
                                "order": 4
                            }
                        ],
                        "file_path": f"/reports/{assessment['_id']}/{report_type.lower().replace(' ', '_')}.pdf" if status == "completed" else None,
                        "file_size_bytes": random.randint(500000, 5000000) if status == "completed" else None,
                        "generated_by": random.choice(list(self.agent_types.keys())),
                        "template_version": "1.0",
                        "sharing": {
                            "is_public": False,
                            "shared_with": [],
                            "access_level": "private"
                        },
                        "metadata": {
                            "page_count": random.randint(15, 50) if status == "completed" else None,
                            "word_count": random.randint(5000, 15000) if status == "completed" else None,
                            "charts_count": random.randint(5, 15) if status == "completed" else None,
                            "tables_count": random.randint(3, 10) if status == "completed" else None
                        },
                        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                        "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                        "completed_at": datetime.utcnow() - timedelta(days=random.randint(0, 7)) if status == "completed" else None
                    }
                    
                    reports.append(report_data)
        
        # Insert reports into database
        if reports:
            await self.database["reports"].insert_many(reports)
        
        return reports
    
    async def generate_metrics(self, users: List[Dict[str, Any]], assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic metrics data."""
        metrics = []
        
        # Generate system metrics over the last 30 days
        for day in range(30):
            date = datetime.utcnow() - timedelta(days=day)
            
            # Daily system metrics
            daily_metrics = [
                {
                    "_id": ObjectId(),
                    "metric_type": "user_activity",
                    "metric_name": "daily_active_users",
                    "value": random.randint(10, len(users)),
                    "unit": "count",
                    "timestamp": date,
                    "source": "system",
                    "tags": {"period": "daily"}
                },
                {
                    "_id": ObjectId(),
                    "metric_type": "assessment",
                    "metric_name": "assessments_created",
                    "value": random.randint(0, 5),
                    "unit": "count",
                    "timestamp": date,
                    "source": "system",
                    "tags": {"period": "daily"}
                },
                {
                    "_id": ObjectId(),
                    "metric_type": "assessment",
                    "metric_name": "assessments_completed",
                    "value": random.randint(0, 3),
                    "unit": "count",
                    "timestamp": date,
                    "source": "system",
                    "tags": {"period": "daily"}
                },
                {
                    "_id": ObjectId(),
                    "metric_type": "performance",
                    "metric_name": "api_response_time",
                    "value": round(random.uniform(50, 200), 2),
                    "unit": "milliseconds",
                    "timestamp": date,
                    "source": "monitoring",
                    "tags": {"endpoint": "api"}
                },
                {
                    "_id": ObjectId(),
                    "metric_type": "performance",
                    "metric_name": "database_query_time",
                    "value": round(random.uniform(10, 100), 2),
                    "unit": "milliseconds",
                    "timestamp": date,
                    "source": "monitoring",
                    "tags": {"database": "mongodb"}
                }
            ]
            
            metrics.extend(daily_metrics)
        
        # Insert metrics into database
        if metrics:
            await self.database["metrics"].insert_many(metrics)
        
        return metrics
    
    async def generate_agent_metrics(self) -> List[Dict[str, Any]]:
        """Generate agent performance metrics."""
        agent_metrics = []
        
        for agent_type, agent_info in self.agent_types.items():
            # Generate metrics for each agent over the last 7 days
            for day in range(7):
                date = datetime.utcnow() - timedelta(days=day)
                
                metric_data = {
                    "_id": ObjectId(),
                    "agent_name": agent_type,
                    "agent_version": "1.0.0",
                    "execution_count": random.randint(5, 20),
                    "success_count": random.randint(4, 18),
                    "failure_count": random.randint(0, 2),
                    "average_execution_time": round(random.uniform(30, 300), 2),
                    "total_tokens_used": random.randint(10000, 100000),
                    "total_cost": round(random.uniform(5, 50), 2),
                    "performance_score": round(random.uniform(0.8, 0.98), 3),
                    "created_at": date,
                    "completed_at": date + timedelta(minutes=random.randint(1, 60)),
                    "metadata": {
                        "model_used": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-3"]),
                        "temperature": 0.1,
                        "max_tokens": 4000
                    }
                }
                
                agent_metrics.append(metric_data)
        
        # Insert agent metrics into database
        if agent_metrics:
            await self.database["agent_metrics"].insert_many(agent_metrics)
        
        return agent_metrics
    
    async def generate_workflow_states(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate workflow state data."""
        workflow_states = []
        
        for assessment in assessments:
            if assessment["status"] in ["in_progress", "completed"]:
                # Generate workflow progression
                workflow_data = {
                    "_id": ObjectId(),
                    "workflow_id": str(uuid.uuid4()),
                    "assessment_id": assessment["_id"],
                    "current_state": random.choice([
                        "requirements_analysis", "agent_orchestration", "recommendation_generation",
                        "report_creation", "completed"
                    ]),
                    "state_history": [
                        {
                            "state": "initiated",
                            "timestamp": assessment["created_at"],
                            "agent": "system"
                        },
                        {
                            "state": "requirements_analysis",
                            "timestamp": assessment["created_at"] + timedelta(minutes=5),
                            "agent": "cto_agent"
                        }
                    ],
                    "next_agents": random.sample(list(self.agent_types.keys()), random.randint(1, 3)),
                    "execution_context": {
                        "priority": random.choice(["low", "medium", "high"]),
                        "timeout": 3600,
                        "retry_count": 0,
                        "max_retries": 3
                    },
                    "created_at": assessment["created_at"],
                    "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 7))
                }
                
                workflow_states.append(workflow_data)
        
        # Insert workflow states into database (as generic documents)
        if workflow_states:
            await self.database["workflow_states"].insert_many(workflow_states)
        
        return workflow_states
    
    async def generate_audit_logs(self, users: List[Dict[str, Any]], assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate audit log data."""
        audit_logs = []
        
        actions = [
            "user_login", "user_logout", "assessment_created", "assessment_updated",
            "assessment_completed", "recommendation_generated", "report_created",
            "settings_updated", "password_changed", "profile_updated"
        ]
        
        # Generate audit logs for the last 30 days
        for _ in range(200):  # 200 random audit events
            user = random.choice(users)
            action = random.choice(actions)
            
            # Determine resource based on action
            resource_type = "user"
            resource_id = str(user["_id"])
            
            if "assessment" in action and assessments:
                resource_type = "assessment"
                resource_id = str(random.choice(assessments)["_id"])
            
            audit_data = {
                "_id": ObjectId(),
                "user_id": user["_id"],
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": self.fake.ipv4(),
                "user_agent": self.fake.user_agent(),
                "details": {
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                    "endpoint": f"/api/v1/{resource_type}s",
                    "status_code": random.choice([200, 201, 400, 401, 403, 404, 500]),
                    "response_time": random.randint(50, 500)
                },
                "timestamp": datetime.utcnow() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            }
            
            audit_logs.append(audit_data)
        
        # Insert audit logs into database (as generic documents)
        if audit_logs:
            await self.database["audit_logs"].insert_many(audit_logs)
        
        return audit_logs
    
    # Helper methods for generating realistic content
    
    def _generate_recommendation_description(self, rec_type: str, business_req: Dict[str, Any]) -> str:
        """Generate realistic recommendation descriptions."""
        templates = {
            "Technology Stack": f"Recommended technology stack for {business_req['primary_use_case']} in {business_req['industry']} industry, optimized for {business_req['company_size']} organizations.",
            "Architecture Design": f"Scalable architecture design supporting {business_req['primary_use_case']} with {business_req['performance_requirements']['availability']} availability.",
            "Infrastructure Setup": f"Cloud infrastructure setup on {business_req.get('preferred_cloud', 'AWS')} optimized for {business_req['primary_use_case']} workloads.",
            "Cost Optimization": f"Cost optimization strategy for {business_req['primary_use_case']} implementation within {business_req['budget_range']} budget.",
            "Security Configuration": f"Security configuration meeting {', '.join(business_req['compliance_requirements'])} compliance requirements.",
            "ML Pipeline": f"Machine learning pipeline for {business_req['primary_use_case']} with automated model deployment and monitoring.",
            "Compliance Framework": f"Compliance framework addressing {', '.join(business_req['compliance_requirements'])} requirements for {business_req['industry']} industry.",
            "Monitoring Setup": f"Comprehensive monitoring setup for {business_req['primary_use_case']} with {business_req['performance_requirements']['availability']} SLA.",
        }
        
        return templates.get(rec_type, f"Recommendation for {rec_type} implementation")
    
    def _generate_cloud_services(self, rec_type: str) -> List[str]:
        """Generate relevant cloud services for recommendation type."""
        service_mapping = {
            "Technology Stack": ["EC2", "RDS", "ElastiCache", "Lambda", "API Gateway"],
            "Architecture Design": ["ECS", "EKS", "Application Load Balancer", "CloudFront", "Route 53"],
            "Infrastructure Setup": ["VPC", "EC2", "RDS", "S3", "CloudWatch"],
            "Cost Optimization": ["Reserved Instances", "Spot Instances", "S3 Intelligent Tiering", "CloudWatch"],
            "Security Configuration": ["IAM", "KMS", "WAF", "GuardDuty", "Security Hub"],
            "ML Pipeline": ["SageMaker", "Lambda", "Step Functions", "S3", "ECR"],
            "Compliance Framework": ["Config", "CloudTrail", "Security Hub", "Inspector", "Macie"],
            "Monitoring Setup": ["CloudWatch", "X-Ray", "Systems Manager", "SNS", "CloudTrail"]
        }
        
        return service_mapping.get(rec_type, ["EC2", "S3", "RDS"])
    
    def _generate_benefits(self, rec_type: str) -> List[str]:
        """Generate benefits for recommendation type."""
        benefit_mapping = {
            "Technology Stack": ["Improved performance", "Better scalability", "Reduced technical debt"],
            "Architecture Design": ["High availability", "Fault tolerance", "Scalable design"],
            "Infrastructure Setup": ["Automated deployment", "Infrastructure as code", "Consistent environments"],
            "Cost Optimization": ["Reduced operational costs", "Better resource utilization", "Predictable pricing"],
            "Security Configuration": ["Enhanced security posture", "Compliance adherence", "Risk mitigation"],
            "ML Pipeline": ["Automated model deployment", "Continuous training", "Model monitoring"],
            "Compliance Framework": ["Regulatory compliance", "Audit readiness", "Risk management"],
            "Monitoring Setup": ["Proactive issue detection", "Performance insights", "Operational visibility"]
        }
        
        return benefit_mapping.get(rec_type, ["Improved efficiency", "Better performance"])
    
    def _generate_risks(self, rec_type: str) -> List[str]:
        """Generate risks for recommendation type."""
        return [
            "Implementation complexity",
            "Resource requirements",
            "Learning curve for team",
            "Potential downtime during migration"
        ]
    
    def _generate_implementation_steps(self, rec_type: str) -> List[str]:
        """Generate implementation steps for recommendation type."""
        return [
            "Planning and requirements analysis",
            "Environment setup and configuration",
            "Implementation and testing",
            "Deployment and monitoring",
            "Documentation and training"
        ]


async def main():
    """Main entry point for demo data generation."""
    parser = argparse.ArgumentParser(
        description="Demo Data Generator for Infra Mind",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--database', default='infra_mind_demo', help='Demo database name')
    parser.add_argument('--count', type=int, default=50, help='Number of users to generate')
    parser.add_argument('--reset', action='store_true', help='Reset database before generating data')
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    try:
        async with DemoDataGenerator(args.database) as generator:
            if args.reset:
                await generator.reset_database()
            
            summary = await generator.generate_demo_data(args.count)
            
            print("\n" + "="*60)
            print("📊 DEMO DATA GENERATION SUMMARY")
            print("="*60)
            for key, value in summary.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            print("="*60)
            
        return 0
        
    except Exception as e:
        logger.error(f"❌ Demo data generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)