#!/usr/bin/env python3
"""
Comprehensive Audit Tool for Infra Mind System

This script performs a thorough audit of:
- Visualizations and Dashboard data flow
- Reports generation and validation
- Assessment workflow and agent integration
- Database models and consistency
- LLM agent utilization
- End-to-end real data flow

Run with: python comprehensive_audit.py
"""

import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import requests

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class ComprehensiveAuditor:
    def __init__(self):
        self.mongodb_client = None
        self.db = None
        self.audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "sections": {},
            "issues_found": [],
            "recommendations": [],
            "summary": {}
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_issue(self, section: str, issue: str, severity: str = "MEDIUM"):
        """Add an issue to the audit results."""
        self.audit_results["issues_found"].append({
            "section": section,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def add_recommendation(self, section: str, recommendation: str):
        """Add a recommendation to the audit results."""
        self.audit_results["recommendations"].append({
            "section": section,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def connect_to_database(self):
        """Connect to MongoDB."""
        try:
            self.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.mongodb_client.get_database("infra_mind")
            
            # Test connection
            await self.db.command("ping")
            self.log("✅ Successfully connected to MongoDB")
            return True
        except Exception as e:
            self.log(f"❌ Failed to connect to MongoDB: {e}", "ERROR")
            return False

    async def audit_database_structure(self):
        """Audit database structure and collections."""
        self.log("🔍 Auditing database structure...")
        
        try:
            # Get all collections
            collections = await self.db.list_collection_names()
            self.log(f"Found {len(collections)} collections: {', '.join(collections)}")
            
            # Expected collections
            expected_collections = [
                "assessments", "recommendations", "reports", "users", 
                "metrics", "workflows", "agent_metrics"
            ]
            
            missing_collections = [col for col in expected_collections if col not in collections]
            if missing_collections:
                self.add_issue("Database", f"Missing collections: {missing_collections}", "HIGH")
            
            # Check each collection
            collection_stats = {}
            for collection_name in collections:
                try:
                    count = await self.db[collection_name].count_documents({})
                    sample = await self.db[collection_name].find_one({})
                    collection_stats[collection_name] = {
                        "document_count": count,
                        "has_sample_data": sample is not None,
                        "sample_keys": list(sample.keys()) if sample else []
                    }
                    self.log(f"  📊 {collection_name}: {count} documents")
                except Exception as e:
                    self.log(f"  ❌ Error analyzing {collection_name}: {e}", "WARNING")
                    
            self.audit_results["sections"]["database"] = {
                "collections": collection_stats,
                "missing_collections": missing_collections,
                "total_collections": len(collections)
            }
            
        except Exception as e:
            self.log(f"❌ Database audit failed: {e}", "ERROR")
            self.add_issue("Database", f"Audit failed: {e}", "HIGH")

    async def audit_agents_registration(self):
        """Audit agent registration and availability."""
        self.log("🤖 Auditing agent registration...")
        
        try:
            # Import and check agent registry
            from infra_mind.agents import agent_registry, AgentRole
            
            registered_agents = agent_registry.list_agent_types()
            self.log(f"Registered agent types: {registered_agents}")
            
            # Check against expected agents
            expected_agent_roles = [role.value for role in AgentRole]
            missing_agents = [role for role in expected_agent_roles if role not in registered_agents]
            
            if missing_agents:
                self.add_issue("Agents", f"Missing agent registrations: {missing_agents}", "HIGH")
            else:
                self.log("✅ All expected agents are registered")
                
            # Try to create each agent type
            agent_creation_status = {}
            from infra_mind.agents import agent_factory
            
            for role in AgentRole:
                try:
                    agent = await agent_factory.create_agent(role)
                    if agent:
                        agent_creation_status[role.value] = {
                            "status": "SUCCESS",
                            "name": agent.name,
                            "capabilities": len(agent.get_capabilities())
                        }
                        self.log(f"  ✅ {role.value}: Created successfully")
                    else:
                        agent_creation_status[role.value] = {"status": "FAILED", "error": "Agent creation returned None"}
                        self.add_issue("Agents", f"Failed to create {role.value} agent", "MEDIUM")
                except Exception as e:
                    agent_creation_status[role.value] = {"status": "ERROR", "error": str(e)}
                    self.add_issue("Agents", f"Error creating {role.value} agent: {e}", "HIGH")
                    
            self.audit_results["sections"]["agents"] = {
                "registered_types": registered_agents,
                "missing_registrations": missing_agents,
                "creation_test": agent_creation_status
            }
            
        except Exception as e:
            self.log(f"❌ Agent audit failed: {e}", "ERROR")
            self.add_issue("Agents", f"Audit failed: {e}", "HIGH")

    async def audit_assessment_workflow(self):
        """Audit assessment workflow and data flow."""
        self.log("📋 Auditing assessment workflow...")
        
        try:
            # Check assessments in database
            assessments = await self.db.assessments.find({}).to_list(10)  # Get up to 10 assessments
            self.log(f"Found {len(assessments)} assessments in database")
            
            assessment_analysis = {
                "total_count": await self.db.assessments.count_documents({}),
                "status_distribution": {},
                "with_recommendations": 0,
                "with_reports": 0,
                "workflow_issues": []
            }
            
            # Analyze assessment statuses
            status_pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_results = await self.db.assessments.aggregate(status_pipeline).to_list(None)
            for result in status_results:
                assessment_analysis["status_distribution"][result["_id"]] = result["count"]
            
            # Check data integrity
            for assessment in assessments:
                assessment_id = str(assessment["_id"])
                
                # Check for recommendations
                recommendations = await self.db.recommendations.find({"assessment_id": assessment_id}).to_list(None)
                if recommendations:
                    assessment_analysis["with_recommendations"] += 1
                
                # Check for reports
                reports = await self.db.reports.find({"assessment_id": assessment_id}).to_list(None)
                if reports:
                    assessment_analysis["with_reports"] += 1
                
                # Check for required fields
                required_fields = ["title", "status", "user_id", "created_at"]
                missing_fields = [field for field in required_fields if field not in assessment]
                if missing_fields:
                    assessment_analysis["workflow_issues"].append({
                        "assessment_id": assessment_id,
                        "issue": f"Missing required fields: {missing_fields}"
                    })
            
            self.audit_results["sections"]["workflow"] = assessment_analysis
            
            # Check if workflow orchestration is working
            try:
                from infra_mind.workflows.orchestrator import agent_orchestrator
                self.log("✅ Workflow orchestrator imported successfully")
            except Exception as e:
                self.add_issue("Workflow", f"Failed to import orchestrator: {e}", "HIGH")
                
        except Exception as e:
            self.log(f"❌ Workflow audit failed: {e}", "ERROR")
            self.add_issue("Workflow", f"Audit failed: {e}", "HIGH")

    async def audit_visualization_data_flow(self):
        """Audit visualization data generation and API endpoints."""
        self.log("📊 Auditing visualization data flow...")
        
        try:
            # Test API endpoints
            api_health = self.test_api_endpoint("/health")
            if not api_health["success"]:
                self.add_issue("Visualization", "API health check failed", "HIGH")
                return
                
            # Get a sample assessment for testing
            assessment = await self.db.assessments.find_one({})
            if not assessment:
                self.add_issue("Visualization", "No assessments found for testing", "MEDIUM")
                return
                
            assessment_id = str(assessment["_id"])
            
            # Test visualization endpoint (without auth for now - this is internal audit)
            viz_endpoint = f"/api/v1/assessments/{assessment_id}/visualization-data"
            self.log(f"Testing visualization endpoint: {viz_endpoint}")
            
            # Note: This would require authentication in a real test
            # For internal audit, we'll check the data structure in the assessment
            
            viz_data_issues = []
            
            # Check if assessment has metadata for visualization
            if "metadata" not in assessment:
                viz_data_issues.append("Assessment missing metadata field")
            elif "visualization_data" not in assessment.get("metadata", {}):
                viz_data_issues.append("Assessment metadata missing visualization_data")
                
            # Check for recommendations that should drive visualizations
            recommendations = await self.db.recommendations.find({"assessment_id": assessment_id}).to_list(None)
            if not recommendations:
                viz_data_issues.append("No recommendations found for visualization generation")
            else:
                self.log(f"Found {len(recommendations)} recommendations for visualization")
                
                # Validate recommendation structure
                for i, rec in enumerate(recommendations):
                    required_rec_fields = ["agent_name", "confidence_score", "alignment_score"]
                    missing_rec_fields = [field for field in required_rec_fields if field not in rec]
                    if missing_rec_fields:
                        viz_data_issues.append(f"Recommendation {i} missing fields: {missing_rec_fields}")
            
            self.audit_results["sections"]["visualization"] = {
                "api_health": api_health,
                "test_assessment_id": assessment_id,
                "issues": viz_data_issues,
                "recommendations_count": len(recommendations) if 'recommendations' in locals() else 0
            }
            
            if viz_data_issues:
                for issue in viz_data_issues:
                    self.add_issue("Visualization", issue, "MEDIUM")
            else:
                self.log("✅ Visualization data flow appears healthy")
                
        except Exception as e:
            self.log(f"❌ Visualization audit failed: {e}", "ERROR")
            self.add_issue("Visualization", f"Audit failed: {e}", "HIGH")

    def test_api_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test an API endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            return {
                "success": True,
                "status_code": response.status_code,
                "response_size": len(response.text)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def audit_reports_system(self):
        """Audit reports generation and download system."""
        self.log("📄 Auditing reports system...")
        
        try:
            # Check reports in database
            reports = await self.db.reports.find({}).to_list(10)
            self.log(f"Found {len(reports)} reports in database")
            
            reports_analysis = {
                "total_count": await self.db.reports.count_documents({}),
                "type_distribution": {},
                "format_distribution": {},
                "status_distribution": {},
                "validation_issues": []
            }
            
            # Analyze report types
            type_pipeline = [{"$group": {"_id": "$report_type", "count": {"$sum": 1}}}]
            type_results = await self.db.reports.aggregate(type_pipeline).to_list(None)
            for result in type_results:
                reports_analysis["type_distribution"][result["_id"]] = result["count"]
            
            # Analyze report formats
            format_pipeline = [{"$group": {"_id": "$format", "count": {"$sum": 1}}}]
            format_results = await self.db.reports.aggregate(format_pipeline).to_list(None)
            for result in format_results:
                reports_analysis["format_distribution"][result["_id"]] = result["count"]
                
            # Analyze report statuses
            status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
            status_results = await self.db.reports.aggregate(status_pipeline).to_list(None)
            for result in status_results:
                reports_analysis["status_distribution"][result["_id"]] = result["count"]
            
            # Validate report structure
            for report in reports:
                required_fields = ["assessment_id", "user_id", "title", "report_type", "status"]
                missing_fields = [field for field in required_fields if field not in report]
                if missing_fields:
                    reports_analysis["validation_issues"].append({
                        "report_id": str(report["_id"]),
                        "issue": f"Missing required fields: {missing_fields}"
                    })
                    
                # Check if report_type is valid (should be one of the enum values)
                valid_types = ["executive_summary", "technical_roadmap", "cost_analysis", 
                             "compliance_report", "architecture_overview", "full_assessment", "comprehensive"]
                if report.get("report_type") not in valid_types:
                    reports_analysis["validation_issues"].append({
                        "report_id": str(report["_id"]),
                        "issue": f"Invalid report_type: {report.get('report_type')}"
                    })
            
            self.audit_results["sections"]["reports"] = reports_analysis
            
            if reports_analysis["validation_issues"]:
                for issue in reports_analysis["validation_issues"]:
                    self.add_issue("Reports", issue["issue"], "MEDIUM")
            else:
                self.log("✅ Reports system validation passed")
                
        except Exception as e:
            self.log(f"❌ Reports audit failed: {e}", "ERROR")
            self.add_issue("Reports", f"Audit failed: {e}", "HIGH")

    async def audit_real_data_flow(self):
        """Audit end-to-end real data flow from agents to frontend."""
        self.log("🔄 Auditing real data flow...")
        
        try:
            # Check if we have recent agent executions
            agent_metrics = await self.db.agent_metrics.find({}).sort("created_at", -1).limit(10).to_list(None)
            
            data_flow_analysis = {
                "recent_agent_executions": len(agent_metrics),
                "mock_data_usage": {
                    "assessments_with_real_data": 0,
                    "assessments_with_mock_data": 0,
                    "fallback_usage": 0
                },
                "agent_data_quality": {},
                "data_flow_issues": []
            }
            
            # Analyze recent assessments for real vs mock data
            recent_assessments = await self.db.assessments.find({}).sort("created_at", -1).limit(5).to_list(None)
            
            for assessment in recent_assessments:
                assessment_id = str(assessment["_id"])
                
                # Check if assessment has real recommendations
                recommendations = await self.db.recommendations.find({"assessment_id": assessment_id}).to_list(None)
                
                if not recommendations:
                    data_flow_analysis["mock_data_usage"]["assessments_with_mock_data"] += 1
                    data_flow_analysis["data_flow_issues"].append(
                        f"Assessment {assessment_id} has no real recommendations"
                    )
                else:
                    # Check quality of recommendations
                    real_data_indicators = 0
                    for rec in recommendations:
                        if rec.get("agent_name") and rec.get("confidence_score", 0) > 0:
                            real_data_indicators += 1
                    
                    if real_data_indicators > 0:
                        data_flow_analysis["mock_data_usage"]["assessments_with_real_data"] += 1
                    else:
                        data_flow_analysis["mock_data_usage"]["assessments_with_mock_data"] += 1
                
                # Check for fallback data in metadata
                metadata = assessment.get("metadata", {})
                if metadata.get("fallback_data") or metadata.get("degraded_mode"):
                    data_flow_analysis["mock_data_usage"]["fallback_usage"] += 1
            
            # Analyze agent execution patterns
            if agent_metrics:
                for metric in agent_metrics:
                    agent_name = metric.get("agent_name", "unknown")
                    if agent_name not in data_flow_analysis["agent_data_quality"]:
                        data_flow_analysis["agent_data_quality"][agent_name] = {
                            "executions": 0,
                            "successes": 0,
                            "failures": 0
                        }
                    
                    data_flow_analysis["agent_data_quality"][agent_name]["executions"] += 1
                    if metric.get("status") == "completed":
                        data_flow_analysis["agent_data_quality"][agent_name]["successes"] += 1
                    else:
                        data_flow_analysis["agent_data_quality"][agent_name]["failures"] += 1
            else:
                data_flow_analysis["data_flow_issues"].append("No recent agent metrics found")
                self.add_issue("Data Flow", "No recent agent executions detected", "HIGH")
            
            self.audit_results["sections"]["data_flow"] = data_flow_analysis
            
            # Evaluate data flow health
            real_data_ratio = data_flow_analysis["mock_data_usage"]["assessments_with_real_data"] / max(1, len(recent_assessments))
            if real_data_ratio < 0.5:
                self.add_issue("Data Flow", f"Low real data usage: {real_data_ratio:.2%}", "HIGH")
                self.add_recommendation("Data Flow", 
                    "Ensure agents are properly executing and generating real recommendations")
            
        except Exception as e:
            self.log(f"❌ Data flow audit failed: {e}", "ERROR")
            self.add_issue("Data Flow", f"Audit failed: {e}", "HIGH")

    async def generate_summary(self):
        """Generate audit summary and recommendations."""
        self.log("📝 Generating audit summary...")
        
        # Count issues by severity
        issue_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.audit_results["issues_found"]:
            issue_counts[issue["severity"]] += 1
        
        # Calculate health score
        total_issues = sum(issue_counts.values())
        health_score = max(0, 100 - (issue_counts["HIGH"] * 20 + issue_counts["MEDIUM"] * 10 + issue_counts["LOW"] * 5))
        
        self.audit_results["summary"] = {
            "health_score": health_score,
            "total_issues": total_issues,
            "issue_breakdown": issue_counts,
            "sections_audited": len(self.audit_results["sections"]),
            "recommendations_count": len(self.audit_results["recommendations"]),
            "audit_status": "CRITICAL" if health_score < 50 else "WARNING" if health_score < 80 else "HEALTHY"
        }
        
        # Generate high-level recommendations
        if issue_counts["HIGH"] > 0:
            self.add_recommendation("System", "Address HIGH severity issues immediately")
        
        if self.audit_results["sections"].get("agents", {}).get("missing_registrations"):
            self.add_recommendation("Agents", "Register missing agents to ensure full functionality")
            
        if self.audit_results["sections"].get("data_flow", {}).get("data_flow_issues"):
            self.add_recommendation("Data Flow", "Investigate and fix data flow issues to ensure real data usage")

    def print_report(self):
        """Print the audit report."""
        print("\n" + "="*80)
        print("COMPREHENSIVE SYSTEM AUDIT REPORT")
        print("="*80)
        print(f"Audit Timestamp: {self.audit_results['timestamp']}")
        print(f"Health Score: {self.audit_results['summary']['health_score']}/100")
        print(f"Overall Status: {self.audit_results['summary']['audit_status']}")
        print(f"Total Issues: {self.audit_results['summary']['total_issues']}")
        
        # Issues breakdown
        if self.audit_results["issues_found"]:
            print(f"\n🚨 ISSUES FOUND ({self.audit_results['summary']['total_issues']}):")
            for issue in self.audit_results["issues_found"]:
                severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                print(f"  {severity_emoji[issue['severity']]} [{issue['section']}] {issue['issue']}")
        
        # Recommendations
        if self.audit_results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS ({len(self.audit_results['recommendations'])}):")
            for rec in self.audit_results["recommendations"]:
                print(f"  • [{rec['section']}] {rec['recommendation']}")
        
        # Section summaries
        print(f"\n📊 SECTION SUMMARIES:")
        for section, data in self.audit_results["sections"].items():
            print(f"  • {section.upper()}: {self._summarize_section(section, data)}")
        
        print("="*80)

    def _summarize_section(self, section: str, data: Dict) -> str:
        """Generate a summary for a section."""
        if section == "database":
            return f"{data['total_collections']} collections, {len(data['missing_collections'])} missing"
        elif section == "agents":
            successful = sum(1 for status in data["creation_test"].values() if status["status"] == "SUCCESS")
            total = len(data["creation_test"])
            return f"{successful}/{total} agents created successfully"
        elif section == "workflow":
            return f"{data['total_count']} assessments, {data['with_recommendations']} with recommendations"
        elif section == "visualization":
            return f"API healthy: {data['api_health']['success']}, {len(data['issues'])} issues"
        elif section == "reports":
            return f"{data['total_count']} reports, {len(data['validation_issues'])} validation issues"
        elif section == "data_flow":
            real_data = data["mock_data_usage"]["assessments_with_real_data"]
            mock_data = data["mock_data_usage"]["assessments_with_mock_data"]
            return f"Real data: {real_data}, Mock data: {mock_data}"
        return "No summary available"

    async def save_report(self, filename: str = None):
        """Save the audit report to a file."""
        if not filename:
            filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.audit_results, f, indent=2, default=str)
            self.log(f"✅ Audit report saved to {filename}")
        except Exception as e:
            self.log(f"❌ Failed to save report: {e}", "ERROR")

    async def run_audit(self):
        """Run the complete audit."""
        self.log("🚀 Starting comprehensive system audit...")
        
        # Connect to database
        if not await self.connect_to_database():
            return False
        
        try:
            # Run all audit sections
            await self.audit_database_structure()
            await self.audit_agents_registration()
            await self.audit_assessment_workflow()
            await self.audit_visualization_data_flow()
            await self.audit_reports_system()
            await self.audit_real_data_flow()
            
            # Generate summary
            await self.generate_summary()
            
            # Print and save report
            self.print_report()
            await self.save_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Audit failed: {e}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            if self.mongodb_client:
                self.mongodb_client.close()

async def main():
    """Main function."""
    auditor = ComprehensiveAuditor()
    success = await auditor.run_audit()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())