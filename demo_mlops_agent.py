#!/usr/bin/env python3
"""
Demo script for MLOps Agent.

This script demonstrates the MLOps Agent's capabilities for ML pipeline optimization,
MLOps platform recommendations, and CI/CD pipeline design.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.infra_mind.agents.mlops_agent import MLOpsAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_assessment():
    """Create a sample assessment for testing MLOps Agent."""
    # Create a simple object that mimics Assessment for demo purposes
    class MockAssessment:
        def __init__(self):
            self.user_id = "demo_user_123"
            self.title = "MLOps Demo Assessment"
            self.description = "Demo assessment for MLOps agent capabilities"
            self.id = "demo_assessment_id"
            self.business_requirements = {
                "company_size": "medium",
                "industry": "technology",
                "budget_range": "$50k-100k",
                "primary_goals": ["innovation", "scalability", "efficiency"],
                "timeline": "6 months",
                "compliance_requirements": {
                    "regulations": ["GDPR"]
                }
            }
            self.technical_requirements = {
                "workload_types": ["ai_ml", "machine_learning", "data_processing"],
                "expected_users": 5000,
                "performance_requirements": {
                    "latency": "low",
                    "throughput": "high",
                    "availability": "99.9%"
                },
                "current_infrastructure": {
                    "cloud_provider": "aws",
                    "compute": "ec2",
                    "storage": "s3"
                },
                "ml_specific": {
                    "model_types": ["deep_learning", "nlp"],
                    "data_volume": "large",
                    "training_frequency": "daily"
                }
            }
        
        def dict(self):
            return {
                "user_id": self.user_id,
                "title": self.title,
                "description": self.description,
                "business_requirements": self.business_requirements,
                "technical_requirements": self.technical_requirements
            }
    
    return MockAssessment()


async def demo_mlops_analysis():
    """Demonstrate MLOps Agent analysis capabilities."""
    print("=" * 80)
    print("MLOps AGENT DEMO - ML Pipeline Optimization and Deployment")
    print("=" * 80)
    
    # Create MLOps Agent
    config = AgentConfig(
        name="Demo MLOps Agent",
        role=AgentRole.MLOPS,
        tools_enabled=["cloud_api", "calculator", "data_processor"],
        temperature=0.2,
        max_tokens=2500,
        metrics_enabled=False  # Disable metrics for demo
    )
    
    mlops_agent = MLOpsAgent(config)
    
    # Create sample assessment
    assessment = create_sample_assessment()
    
    print(f"\n📊 Assessment Overview:")
    print(f"Company Size: {assessment.business_requirements['company_size']}")
    print(f"Industry: {assessment.business_requirements['industry']}")
    print(f"Budget: {assessment.business_requirements['budget_range']}")
    print(f"Workloads: {', '.join(assessment.technical_requirements['workload_types'])}")
    print(f"Expected Users: {assessment.technical_requirements['expected_users']:,}")
    
    try:
        # Execute MLOps analysis
        print(f"\n🤖 Executing MLOps Agent analysis...")
        start_time = datetime.now()
        
        result = await mlops_agent.execute(assessment)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Analysis completed in {execution_time:.2f} seconds")
        
        # Display results
        await display_mlops_results(result)
        
    except Exception as e:
        print(f"❌ MLOps analysis failed: {str(e)}")
        logger.error(f"MLOps analysis error: {str(e)}", exc_info=True)


async def display_mlops_results(result):
    """Display MLOps Agent results in a formatted way."""
    if result.status.value != "completed":
        print(f"❌ Analysis Status: {result.status.value}")
        if result.error:
            print(f"Error: {result.error}")
        return
    
    print(f"\n✅ Analysis Status: {result.status.value}")
    print(f"⏱️  Execution Time: {result.execution_time:.2f} seconds")
    
    # Display recommendations
    recommendations = result.recommendations
    if recommendations:
        print(f"\n🎯 MLOps RECOMMENDATIONS ({len(recommendations)} total):")
        print("-" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"\n{i}. {priority_emoji} {rec['title']} ({rec['priority']} priority)")
            print(f"   Category: {rec['category']}")
            print(f"   Description: {rec['description']}")
            print(f"   Rationale: {rec['rationale']}")
            print(f"   Timeline: {rec['timeline']}")
            print(f"   Investment: {rec['investment_required']}")
            print(f"   Business Impact: {rec['business_impact']}")
            
            if rec.get('implementation_steps'):
                print(f"   Implementation Steps:")
                for step in rec['implementation_steps'][:3]:  # Show first 3 steps
                    print(f"     • {step}")
    
    # Display detailed analysis data
    data = result.data
    if data:
        print(f"\n📈 DETAILED ANALYSIS:")
        print("-" * 60)
        
        # ML Analysis
        ml_analysis = data.get("ml_analysis", {})
        if ml_analysis:
            print(f"\n🧠 ML Workload Analysis:")
            ml_workloads = ml_analysis.get("ml_workloads", [])
            if ml_workloads:
                print(f"   ML Workloads: {', '.join(ml_workloads)}")
            
            ml_use_cases = ml_analysis.get("ml_use_cases", [])
            if ml_use_cases:
                print(f"   Use Cases:")
                for uc in ml_use_cases[:3]:  # Show first 3
                    print(f"     • {uc.get('type', 'Unknown')}: {uc.get('description', 'No description')}")
            
            model_complexity = ml_analysis.get("model_complexity", {})
            if model_complexity:
                print(f"   Model Complexity: {model_complexity.get('overall_complexity', 'Unknown')}")
                print(f"   Compute Requirements: {model_complexity.get('compute_requirements', 'Unknown')}")
        
        # Maturity Assessment
        maturity_assessment = data.get("maturity_assessment", {})
        if maturity_assessment:
            print(f"\n📊 MLOps Maturity Assessment:")
            print(f"   Overall Maturity: {maturity_assessment.get('maturity_level', 'Unknown')}")
            print(f"   Maturity Score: {maturity_assessment.get('overall_maturity_score', 0):.2f}/1.0")
            
            key_gaps = maturity_assessment.get("key_gaps", [])
            if key_gaps:
                print(f"   Key Gaps:")
                for gap in key_gaps[:3]:  # Show first 3 gaps
                    print(f"     • {gap}")
        
        # Platform Recommendations
        platform_recommendations = data.get("platform_recommendations", {})
        if platform_recommendations:
            print(f"\n🛠️  MLOps Platform Recommendations:")
            platform_recs = platform_recommendations.get("recommendations", [])
            if platform_recs:
                for i, platform in enumerate(platform_recs[:3], 1):  # Top 3 platforms
                    print(f"   {i}. {platform.get('platform', 'Unknown').title()}")
                    print(f"      Score: {platform.get('suitability_score', 0):.2f}/1.0")
                    print(f"      Rationale: {platform.get('rationale', 'No rationale')}")
        
        # CI/CD Design
        cicd_design = data.get("cicd_design", {})
        if cicd_design:
            print(f"\n🔄 CI/CD Pipeline Design:")
            pipeline_stages = cicd_design.get("pipeline_stages", [])
            if pipeline_stages:
                print(f"   Pipeline Stages:")
                for stage in pipeline_stages:
                    print(f"     • {stage.get('stage', 'Unknown')}: {stage.get('description', 'No description')}")
        
        # Deployment Strategy
        deployment_strategy = data.get("deployment_strategy", {})
        if deployment_strategy:
            print(f"\n🚀 Deployment Strategy:")
            deployment_patterns = deployment_strategy.get("deployment_patterns", [])
            if deployment_patterns:
                primary_pattern = deployment_patterns[0]
                print(f"   Primary Pattern: {primary_pattern.get('pattern', 'Unknown')}")
                print(f"   Description: {primary_pattern.get('description', 'No description')}")
                print(f"   Use Case: {primary_pattern.get('use_case', 'No use case')}")
        
        # Monitoring Plan
        monitoring_plan = data.get("monitoring_plan", {})
        if monitoring_plan:
            print(f"\n📊 Monitoring Plan:")
            monitoring_metrics = monitoring_plan.get("monitoring_metrics", {})
            if monitoring_metrics:
                model_metrics = monitoring_metrics.get("model_performance", [])
                if model_metrics:
                    print(f"   Model Performance Metrics: {', '.join(model_metrics[:4])}")
                
                system_metrics = monitoring_metrics.get("system_performance", [])
                if system_metrics:
                    print(f"   System Performance Metrics: {', '.join(system_metrics[:4])}")


async def demo_platform_comparison():
    """Demonstrate MLOps platform comparison."""
    print(f"\n" + "=" * 80)
    print("MLOPS PLATFORM COMPARISON DEMO")
    print("=" * 80)
    
    # Create MLOps Agent
    config = AgentConfig(
        name="Platform Comparison MLOps Agent",
        role=AgentRole.MLOPS,
        metrics_enabled=False
    )
    mlops_agent = MLOpsAgent(config)
    
    # Create assessment focused on platform selection
    class MockAssessment:
        def __init__(self):
            self.user_id = "demo_user_platform"
            self.title = "Platform Comparison Demo"
            self.description = "Demo for MLOps platform comparison"
            self.id = "platform_demo_id"
            self.business_requirements = {
                "company_size": "startup",
                "industry": "fintech",
                "budget_range": "$10k-50k",
                "primary_goals": ["cost_reduction", "scalability"]
            }
            self.technical_requirements = {
                "workload_types": ["ai_ml", "data_processing"],
                "expected_users": 1000,
                "performance_requirements": {
                    "latency": "medium",
                    "throughput": "medium"
                }
            }
        
        def dict(self):
            return {
                "user_id": self.user_id,
                "title": self.title,
                "description": self.description,
                "business_requirements": self.business_requirements,
                "technical_requirements": self.technical_requirements
            }
    
    assessment = MockAssessment()
    
    print(f"\n📊 Platform Comparison Scenario:")
    print(f"Company: {assessment.business_requirements['company_size']} {assessment.business_requirements['industry']} company")
    print(f"Budget: {assessment.business_requirements['budget_range']}")
    print(f"Goals: {', '.join(assessment.business_requirements['primary_goals'])}")
    
    try:
        result = await mlops_agent.execute(assessment)
        
        if result.status.value == "completed":
            platform_data = result.data.get("platform_recommendations", {})
            platform_recs = platform_data.get("recommendations", [])
            
            if platform_recs:
                print(f"\n🏆 TOP MLOPS PLATFORMS:")
                print("-" * 50)
                
                for i, platform in enumerate(platform_recs, 1):
                    print(f"\n{i}. {platform.get('platform', 'Unknown').upper()}")
                    print(f"   Suitability Score: {platform.get('suitability_score', 0):.2f}/1.0")
                    print(f"   Rationale: {platform.get('rationale', 'No rationale')}")
                    
                    pros = platform.get('pros', [])
                    if pros:
                        print(f"   Pros: {', '.join(pros[:3])}")
                    
                    cons = platform.get('cons', [])
                    if cons:
                        print(f"   Cons: {', '.join(cons[:2])}")
        
    except Exception as e:
        print(f"❌ Platform comparison failed: {str(e)}")


async def demo_cicd_pipeline_design():
    """Demonstrate CI/CD pipeline design for ML."""
    print(f"\n" + "=" * 80)
    print("ML CI/CD PIPELINE DESIGN DEMO")
    print("=" * 80)
    
    # Create MLOps Agent
    config = AgentConfig(
        name="CI/CD Pipeline MLOps Agent",
        role=AgentRole.MLOPS,
        metrics_enabled=False
    )
    mlops_agent = MLOpsAgent(config)
    
    # Create assessment focused on CI/CD
    class MockAssessment:
        def __init__(self):
            self.user_id = "demo_user_cicd"
            self.title = "CI/CD Pipeline Demo"
            self.description = "Demo for ML CI/CD pipeline design"
            self.id = "cicd_demo_id"
            self.business_requirements = {
                "company_size": "medium",
                "industry": "healthcare",
                "budget_range": "$100k+",
                "primary_goals": ["compliance", "reliability"]
            }
            self.technical_requirements = {
                "workload_types": ["ai_ml", "machine_learning"],
                "expected_users": 10000,
                "performance_requirements": {
                    "latency": "low",
                    "availability": "99.99%"
                }
            }
        
        def dict(self):
            return {
                "user_id": self.user_id,
                "title": self.title,
                "description": self.description,
                "business_requirements": self.business_requirements,
                "technical_requirements": self.technical_requirements
            }
    
    assessment = MockAssessment()
    
    print(f"\n📊 CI/CD Design Scenario:")
    print(f"Industry: {assessment.business_requirements['industry']} (high compliance)")
    print(f"Scale: {assessment.technical_requirements['expected_users']:,} users")
    print(f"Requirements: {assessment.technical_requirements['performance_requirements']['availability']} availability")
    
    try:
        result = await mlops_agent.execute(assessment)
        
        if result.status.value == "completed":
            cicd_data = result.data.get("cicd_design", {})
            
            # Display pipeline stages
            pipeline_stages = cicd_data.get("pipeline_stages", [])
            if pipeline_stages:
                print(f"\n🔄 ML CI/CD PIPELINE STAGES:")
                print("-" * 50)
                
                for i, stage in enumerate(pipeline_stages, 1):
                    print(f"\n{i}. {stage.get('stage', 'Unknown').upper()}")
                    print(f"   Description: {stage.get('description', 'No description')}")
                    print(f"   Automation Level: {stage.get('automation_level', 'Unknown')}")
                    
                    tools = stage.get('tools', [])
                    if tools:
                        print(f"   Tools: {', '.join(tools[:3])}")
            
            # Display testing strategy
            testing_strategy = cicd_data.get("testing_strategy", {})
            if testing_strategy:
                print(f"\n🧪 TESTING STRATEGY:")
                print("-" * 30)
                
                for test_type, tests in testing_strategy.items():
                    if isinstance(tests, list) and test_type != "recommended_tools":
                        print(f"\n{test_type.replace('_', ' ').title()}:")
                        for test in tests[:3]:  # Show first 3
                            print(f"   • {test}")
        
    except Exception as e:
        print(f"❌ CI/CD pipeline design failed: {str(e)}")


async def main():
    """Main demo function."""
    print("🚀 Starting MLOps Agent Demo...")
    
    try:
        # Run main MLOps analysis demo
        await demo_mlops_analysis()
        
        # Run platform comparison demo
        await demo_platform_comparison()
        
        # Run CI/CD pipeline design demo
        await demo_cicd_pipeline_design()
        
        print(f"\n" + "=" * 80)
        print("✅ MLOps Agent Demo completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logger.error(f"Demo error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())