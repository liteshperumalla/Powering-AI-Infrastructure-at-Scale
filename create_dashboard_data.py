#!/usr/bin/env python3
"""
Create sample dashboard data for testing visualizations.
This script populates the database with recommendations and reports.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database connection
MONGODB_URL = os.environ.get("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

# Assessment ID (our test assessment)
ASSESSMENT_ID = "6897837f756d073a70aab31b"
USER_ID = "68974e164c353fd77dc117d8"  # Our test user ID

# Sample recommendations data
SAMPLE_RECOMMENDATIONS = [
    {
        "_id": ObjectId(),
        "assessment_id": ASSESSMENT_ID,
        "agent_name": "cto_agent",
        "title": "Strategic Infrastructure Modernization",
        "summary": "Comprehensive strategy for transitioning to cloud-native infrastructure with focus on scalability and cost optimization",
        "confidence_level": "high",
        "confidence_score": 0.92,
        "recommendation_data": {
            "strategic_priorities": ["cost_optimization", "scalability", "security", "reliability"],
            "investment_timeline": "12_months",
            "expected_roi": "280%",
            "risk_level": "medium"
        },
        "recommended_services": [
            {
                "service_id": "ecs_cto_001",
                "service_name": "Amazon ECS",
                "provider": "aws",
                "service_category": "container_orchestration",
                "estimated_monthly_cost": 800.00,
                "cost_model": "pay_per_use",
                "configuration": {
                    "cpu": "2 vCPU",
                    "memory": "4 GB",
                    "instances": "3-10 (auto-scaling)"
                },
                "reasons": [
                    "Native AWS integration",
                    "Cost-effective for variable workloads",
                    "Excellent auto-scaling capabilities"
                ],
                "alternatives": ["Amazon EKS", "Google Cloud Run"],
                "setup_complexity": "medium",
                "implementation_time_hours": 40
            },
            {
                "service_id": "rds_cto_002",
                "service_name": "Amazon RDS PostgreSQL",
                "provider": "aws",
                "service_category": "database",
                "estimated_monthly_cost": 450.00,
                "cost_model": "reserved_instance",
                "configuration": {
                    "instance_type": "db.t3.large",
                    "storage": "500 GB SSD",
                    "backup_retention": "7 days"
                },
                "reasons": [
                    "Managed service reduces operational overhead",
                    "Built-in backup and monitoring",
                    "High availability with Multi-AZ"
                ],
                "alternatives": ["Amazon Aurora", "Google Cloud SQL"],
                "setup_complexity": "low",
                "implementation_time_hours": 16
            }
        ],
        "cost_estimates": {
            "monthly_infrastructure": 1250,
            "annual_savings": 45000,
            "implementation_cost": 15000
        },
        "total_estimated_monthly_cost": 1250.00,
        "implementation_steps": [
            "Set up AWS account and billing alerts",
            "Create VPC and security groups",
            "Deploy ECS cluster with auto-scaling",
            "Migrate database to RDS",
            "Implement monitoring and logging",
            "Set up CI/CD pipeline"
        ],
        "prerequisites": [
            "AWS account with appropriate permissions",
            "Development team training on containerization",
            "Migration plan for existing applications"
        ],
        "risks_and_considerations": [
            "Vendor lock-in with AWS services",
            "Learning curve for containerization",
            "Potential downtime during migration"
        ],
        "business_impact": "High - 280% ROI expected with 60% reduction in operational costs",
        "alignment_score": 0.94,
        "tags": ["cloud_migration", "cost_optimization", "scalability", "aws"],
        "priority": "high",
        "category": "infrastructure",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "_id": ObjectId(),
        "assessment_id": ASSESSMENT_ID,
        "agent_name": "cloud_engineer_agent",
        "title": "Multi-Cloud Architecture Implementation",
        "summary": "Design and implementation of resilient multi-cloud infrastructure for high availability and disaster recovery",
        "confidence_level": "high",
        "confidence_score": 0.88,
        "recommendation_data": {
            "architecture_type": "multi_cloud",
            "primary_provider": "aws",
            "secondary_provider": "gcp",
            "availability_target": "99.99%"
        },
        "recommended_services": [
            {
                "service_id": "alb_cloud_001",
                "service_name": "AWS Application Load Balancer (Multi-Cloud)",
                "provider": "aws",
                "service_category": "load_balancing",
                "estimated_monthly_cost": 200.00,
                "cost_model": "pay_per_use",
                "configuration": {
                    "type": "application",
                    "scheme": "internet-facing",
                    "target_groups": 3
                },
                "reasons": [
                    "Advanced routing capabilities",
                    "SSL termination",
                    "Health checks"
                ],
                "alternatives": ["NGINX Plus", "Google Cloud Load Balancer"],
                "setup_complexity": "medium",
                "implementation_time_hours": 24
            },
            {
                "service_id": "gcs_cloud_002",
                "service_name": "Google Cloud Storage",
                "provider": "gcp",
                "service_category": "object_storage",
                "estimated_monthly_cost": 150.00,
                "cost_model": "pay_per_use",
                "configuration": {
                    "storage_class": "standard",
                    "size": "2 TB",
                    "replication": "multi_regional"
                },
                "reasons": [
                    "Cross-cloud backup strategy",
                    "Excellent durability (99.999999999%)",
                    "Cost-effective for backup storage"
                ],
                "alternatives": ["AWS S3", "Azure Blob Storage"],
                "setup_complexity": "low",
                "implementation_time_hours": 8
            }
        ],
        "cost_estimates": {
            "monthly_infrastructure": 950,
            "annual_savings": 25000,
            "implementation_cost": 12000
        },
        "total_estimated_monthly_cost": 950.00,
        "implementation_steps": [
            "Design multi-cloud network topology",
            "Set up cross-cloud VPN connections",
            "Implement load balancing strategy",
            "Configure backup and disaster recovery",
            "Set up monitoring across both clouds"
        ],
        "prerequisites": [
            "Both AWS and GCP accounts",
            "Network security expertise",
            "Disaster recovery procedures"
        ],
        "risks_and_considerations": [
            "Increased complexity",
            "Higher networking costs",
            "Need for multi-cloud expertise"
        ],
        "business_impact": "Medium-High - Improved reliability and reduced downtime risk",
        "alignment_score": 0.86,
        "tags": ["multi_cloud", "high_availability", "disaster_recovery"],
        "priority": "medium",
        "category": "architecture",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "_id": ObjectId(),
        "assessment_id": ASSESSMENT_ID,
        "agent_name": "research_agent",
        "title": "Emerging Technologies Integration",
        "summary": "Analysis of cutting-edge technologies that can provide competitive advantages for infrastructure modernization",
        "confidence_level": "medium",
        "confidence_score": 0.75,
        "recommendation_data": {
            "technology_focus": ["serverless", "ai_ops", "edge_computing"],
            "maturity_level": "emerging",
            "adoption_timeline": "6-18_months"
        },
        "recommended_services": [
            {
                "service_id": "lambda_research_001",
                "service_name": "AWS Lambda",
                "provider": "aws",
                "service_category": "serverless",
                "estimated_monthly_cost": 300.00,
                "cost_model": "pay_per_execution",
                "configuration": {
                    "runtime": "python3.9",
                    "memory": "512 MB",
                    "timeout": "30 seconds"
                },
                "reasons": [
                    "Zero server management",
                    "Automatic scaling",
                    "Pay only for compute time"
                ],
                "alternatives": ["Google Cloud Functions", "Azure Functions"],
                "setup_complexity": "low",
                "implementation_time_hours": 20
            }
        ],
        "cost_estimates": {
            "monthly_infrastructure": 300,
            "annual_savings": 15000,
            "implementation_cost": 8000
        },
        "total_estimated_monthly_cost": 300.00,
        "implementation_steps": [
            "Identify functions suitable for serverless",
            "Develop and test Lambda functions",
            "Set up API Gateway integration",
            "Implement monitoring and logging"
        ],
        "prerequisites": [
            "Code refactoring for serverless architecture",
            "Team training on serverless patterns"
        ],
        "risks_and_considerations": [
            "Cold start latency",
            "Vendor lock-in",
            "Debugging complexity"
        ],
        "business_impact": "Medium - Reduced operational overhead and improved scalability",
        "alignment_score": 0.72,
        "tags": ["serverless", "innovation", "cost_reduction"],
        "priority": "low",
        "category": "innovation",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
]

# Sample reports data
SAMPLE_REPORTS = [
    {
        "_id": ObjectId(),
        "report_id": "exec_summary_001",
        "assessment_id": ASSESSMENT_ID,
        "user_id": USER_ID,
        "title": "Infrastructure Assessment Executive Summary",
        "report_type": "executive_summary",
        "format": "pdf",
        "status": "completed",
        "sections": ["exec_summary", "key_findings", "recommendations", "timeline", "financial_impact"],
        "metadata": {
            "generated_by": "report_generator_agent",
            "template_version": "2.1",
            "word_count": 850,
            "page_count": 12
        },
        "tags": ["executive", "summary", "financial"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "generated_at": datetime.now(timezone.utc)
    },
    {
        "_id": ObjectId(),
        "report_id": "tech_guide_002",
        "assessment_id": ASSESSMENT_ID,
        "user_id": USER_ID,
        "title": "Technical Implementation Guide",
        "report_type": "technical_roadmap",
        "format": "markdown",
        "status": "completed",
        "sections": ["architecture", "service_config", "security", "monitoring"],
        "metadata": {
            "generated_by": "cloud_engineer_agent",
            "template_version": "1.8",
            "word_count": 1200,
            "page_count": 18
        },
        "tags": ["technical", "implementation", "architecture"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "generated_at": datetime.now(timezone.utc)
    },
    {
        "_id": ObjectId(),
        "report_id": "cost_analysis_003",
        "assessment_id": ASSESSMENT_ID,
        "user_id": USER_ID,
        "title": "Cost Analysis and Optimization Report",
        "report_type": "cost_analysis",
        "format": "pdf",
        "status": "completed",
        "sections": ["current_costs", "proposed_costs", "savings_analysis"],
        "metadata": {
            "generated_by": "cost_optimization_agent",
            "template_version": "1.5",
            "word_count": 650,
            "page_count": 8
        },
        "tags": ["cost", "optimization", "financial"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "generated_at": datetime.now(timezone.utc)
    }
]

async def populate_database():
    """Populate the database with sample recommendations and reports."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.infra_mind
    
    try:
        # Insert recommendations
        print("Inserting sample recommendations...")
        recommendations_collection = db.recommendations
        result = await recommendations_collection.insert_many(SAMPLE_RECOMMENDATIONS)
        print(f"✅ Inserted {len(result.inserted_ids)} recommendations")
        
        # Insert reports
        print("Inserting sample reports...")
        reports_collection = db.reports
        result = await reports_collection.insert_many(SAMPLE_REPORTS)
        print(f"✅ Inserted {len(result.inserted_ids)} reports")
        
        # Verify data
        print("\nVerifying data...")
        rec_count = await recommendations_collection.count_documents({"assessment_id": ASSESSMENT_ID})
        report_count = await reports_collection.count_documents({"assessment_id": ASSESSMENT_ID})
        
        print(f"📊 Assessment {ASSESSMENT_ID} now has:")
        print(f"   • {rec_count} recommendations")
        print(f"   • {report_count} reports")
        
        print("\n🎉 Dashboard data population complete!")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False
    finally:
        client.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(populate_database())
    sys.exit(0 if success else 1)