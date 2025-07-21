"""
Cloud Engineer Agent for Infra Mind.

Provides cloud-specific service curation and platform optimization expertise.
Focuses on multi-cloud service comparison, cost optimization, and best practices.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from ..models.assessment import Assessment

logger = logging.getLogger(__name__)


class CloudEngineerAgent(BaseAgent):
    """
    Cloud Engineer Agent for cloud-specific service curation and optimization.
    
    This agent focuses on:
    - Cloud service curation and selection
    - Multi-cloud service comparison and ranking
    - Cost optimization using real-time pricing
    - Platform-specific optimization recommendations
    - Service alignment with business goals
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Cloud Engineer Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="Cloud Engineer Agent",
                role=AgentRole.CLOUD_ENGINEER,
                tools_enabled=["cloud_api", "calculator", "data_processor"],
                temperature=0.2,  # Lower temperature for more consistent technical recommendations
                max_tokens=2500,
                custom_config={
                    "focus_areas": [
                        "service_curation",
                        "cost_optimization",
                        "platform_expertise",
                        "multi_cloud_comparison",
                        "best_practices"
                    ],
                    "cloud_platforms": ["aws", "azure", "gcp"],
                    "service_categories": [
                        "compute", "storage", "database", 
                        "networking", "security", "ai_ml"
                    ]
                }
            )
        
        super().__init__(config)
        
        # Cloud Engineer-specific attributes
        self.cloud_platforms = ["aws", "azure", "gcp"]
        self.service_categories = [
            "compute", "storage", "database", 
            "networking", "security", "ai_ml"
        ]
        
        # Service ranking criteria
        self.ranking_criteria = [
            "cost_effectiveness",
            "performance",
            "reliability",
            "scalability",
            "ease_of_use",
            "vendor_lock_in_risk"
        ]
        
        logger.info("Cloud Engineer Agent initialized with multi-cloud expertise")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute Cloud Engineer agent's main service curation logic.
        
        Returns:
            Dictionary with service recommendations and analysis
        """
        logger.info("Cloud Engineer Agent starting service curation analysis")
        
        try:
            # Step 1: Analyze technical requirements
            technical_analysis = await self._analyze_technical_requirements()
            
            # Step 2: Collect cloud service data
            service_data = await self._collect_cloud_service_data()
            
            # Step 3: Curate and rank services
            curated_services = await self._curate_services(technical_analysis, service_data)
            
            # Step 4: Perform cost optimization analysis
            cost_analysis = await self._perform_cost_optimization(curated_services)
            
            # Step 5: Generate service recommendations
            service_recommendations = await self._generate_service_recommendations(
                technical_analysis, curated_services, cost_analysis
            )
            
            # Step 6: Create implementation guidance
            implementation_guidance = await self._create_implementation_guidance(
                service_recommendations
            )
            
            result = {
                "recommendations": service_recommendations,
                "data": {
                    "technical_analysis": technical_analysis,
                    "service_data": service_data,
                    "curated_services": curated_services,
                    "cost_analysis": cost_analysis,
                    "implementation_guidance": implementation_guidance,
                    "platforms_analyzed": self.cloud_platforms,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("Cloud Engineer Agent completed service curation successfully")
            return result
            
        except Exception as e:
            logger.error(f"Cloud Engineer Agent analysis failed: {str(e)}")
            raise   
 
    async def _analyze_technical_requirements(self) -> Dict[str, Any]:
        """Analyze technical requirements to understand service needs."""
        logger.debug("Analyzing technical requirements")
        
        assessment_data = self.current_assessment.dict() if self.current_assessment else {}
        technical_req = assessment_data.get("technical_requirements", {})
        business_req = assessment_data.get("business_requirements", {})
        
        # Use data processing tool to analyze requirements
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        # Extract workload characteristics
        workload_types = technical_req.get("workload_types", [])
        expected_users = technical_req.get("expected_users", 1000)
        performance_req = technical_req.get("performance_requirements", {})
        
        # Determine service needs based on workloads
        service_needs = self._determine_service_needs(workload_types, expected_users, performance_req)
        
        # Assess scalability requirements
        scalability_needs = self._assess_scalability_needs(technical_req, business_req)
        
        # Determine compliance requirements
        compliance_needs = self._assess_compliance_needs(business_req)
        
        return {
            "workload_analysis": {
                "types": workload_types,
                "expected_users": expected_users,
                "performance_requirements": performance_req
            },
            "service_needs": service_needs,
            "scalability_needs": scalability_needs,
            "compliance_needs": compliance_needs,
            "data_insights": analysis_result.data if analysis_result.is_success else {},
            "priority_services": self._prioritize_service_categories(service_needs)
        }
    
    async def _collect_cloud_service_data(self) -> Dict[str, Any]:
        """Collect service data from multiple cloud providers."""
        logger.debug("Collecting cloud service data")
        
        service_data = {}
        
        # Collect data from each cloud provider
        for provider in self.cloud_platforms:
            provider_data = {}
            
            try:
                # Get compute services
                compute_result = await self._use_tool(
                    "cloud_api",
                    provider=provider,
                    service="compute",
                    operation="list_services"
                )
                if compute_result.is_success:
                    provider_data["compute"] = compute_result.data
                
                # Get storage services
                storage_result = await self._use_tool(
                    "cloud_api",
                    provider=provider,
                    service="storage",
                    operation="list_services"
                )
                if storage_result.is_success:
                    provider_data["storage"] = storage_result.data
                
                # Get database services
                database_result = await self._use_tool(
                    "cloud_api",
                    provider=provider,
                    service="database",
                    operation="list_services"
                )
                if database_result.is_success:
                    provider_data["database"] = database_result.data
                
                service_data[provider] = provider_data
                
            except Exception as e:
                logger.warning(f"Failed to collect data from {provider}: {e}")
                service_data[provider] = {"error": str(e)}
        
        return {
            "providers": service_data,
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "successful_providers": [p for p in service_data.keys() if "error" not in service_data[p]]
        }
    
    async def _curate_services(self, technical_analysis: Dict[str, Any], 
                              service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Curate and rank services based on requirements."""
        logger.debug("Curating and ranking services")
        
        curated_services = {}
        service_needs = technical_analysis.get("service_needs", {})
        
        # Curate services for each category
        for category in self.service_categories:
            if category in service_needs and service_needs[category]["needed"]:
                category_services = self._curate_category_services(
                    category, service_needs[category], service_data
                )
                if category_services:
                    curated_services[category] = category_services
        
        # Rank services within each category
        ranked_services = {}
        for category, services in curated_services.items():
            ranked_services[category] = self._rank_services(
                services, service_needs.get(category, {}), technical_analysis
            )
        
        return {
            "curated_services": curated_services,
            "ranked_services": ranked_services,
            "curation_criteria": self.ranking_criteria,
            "total_services_evaluated": sum(len(services) for services in curated_services.values())
        }
    
    async def _perform_cost_optimization(self, curated_services: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cost optimization analysis."""
        logger.debug("Performing cost optimization analysis")
        
        ranked_services = curated_services.get("ranked_services", {})
        
        # Calculate cost estimates for top services
        cost_estimates = {}
        total_monthly_cost = 0
        
        for category, services in ranked_services.items():
            if services:
                # Get top 3 services for cost comparison
                top_services = services[:3]
                category_costs = []
                
                for service in top_services:
                    cost_estimate = await self._calculate_service_cost(service)
                    category_costs.append({
                        "service": service,
                        "monthly_cost": cost_estimate
                    })
                
                cost_estimates[category] = category_costs
                
                # Add cheapest option to total
                if category_costs:
                    cheapest_cost = min(cost["monthly_cost"] for cost in category_costs)
                    total_monthly_cost += cheapest_cost
        
        # Generate cost optimization recommendations
        optimization_recommendations = self._generate_cost_optimizations(cost_estimates)
        
        return {
            "cost_estimates": cost_estimates,
            "total_monthly_cost": total_monthly_cost,
            "annual_cost": total_monthly_cost * 12,
            "optimization_recommendations": optimization_recommendations,
            "cost_breakdown": self._create_cost_breakdown(cost_estimates)
        }
    
    async def _generate_service_recommendations(self, technical_analysis: Dict[str, Any],
                                              curated_services: Dict[str, Any],
                                              cost_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate final service recommendations."""
        logger.debug("Generating service recommendations")
        
        recommendations = []
        ranked_services = curated_services.get("ranked_services", {})
        
        # Generate recommendations for each service category
        for category, services in ranked_services.items():
            if services:
                top_service = services[0]  # Best ranked service
                
                recommendation = {
                    "category": category,
                    "priority": self._determine_recommendation_priority(category, technical_analysis),
                    "title": f"Recommended {category.title()} Service",
                    "service": top_service,
                    "rationale": self._create_service_rationale(top_service, category, technical_analysis),
                    "alternatives": services[1:3] if len(services) > 1 else [],
                    "implementation_steps": self._create_implementation_steps(top_service, category),
                    "cost_impact": self._get_cost_impact(category, cost_analysis),
                    "business_alignment": self._assess_business_alignment(top_service, technical_analysis)
                }
                
                recommendations.append(recommendation)
        
        # Sort recommendations by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return recommendations
    
    async def _create_implementation_guidance(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation guidance for recommended services."""
        logger.debug("Creating implementation guidance")
        
        # Create deployment roadmap
        roadmap = self._create_deployment_roadmap(recommendations)
        
        # Generate best practices
        best_practices = self._generate_best_practices(recommendations)
        
        # Create monitoring recommendations
        monitoring_guidance = self._create_monitoring_guidance(recommendations)
        
        # Generate cost management strategies
        cost_management = self._create_cost_management_strategies(recommendations)
        
        return {
            "deployment_roadmap": roadmap,
            "best_practices": best_practices,
            "monitoring_guidance": monitoring_guidance,
            "cost_management": cost_management,
            "estimated_implementation_time": self._estimate_implementation_time(recommendations),
            "risk_mitigation": self._create_risk_mitigation_strategies(recommendations)
        }  
  
    # Helper methods
    
    def _determine_service_needs(self, workload_types: List[str], expected_users: int, 
                                performance_req: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what cloud services are needed based on workloads."""
        service_needs = {}
        
        # Compute needs
        compute_needed = len(workload_types) > 0
        compute_scale = "small" if expected_users < 1000 else "medium" if expected_users < 10000 else "large"
        
        service_needs["compute"] = {
            "needed": compute_needed,
            "scale": compute_scale,
            "requirements": {
                "expected_users": expected_users,
                "performance": performance_req
            }
        }
        
        # Storage needs
        storage_needed = any(wl in ["web_application", "data_processing", "ai_ml"] for wl in workload_types)
        storage_type = "object" if "web_application" in workload_types else "block"
        
        service_needs["storage"] = {
            "needed": storage_needed,
            "type": storage_type,
            "scale": compute_scale
        }
        
        # Database needs
        database_needed = any(wl in ["web_application", "data_processing"] for wl in workload_types)
        db_type = "relational" if "web_application" in workload_types else "nosql"
        
        service_needs["database"] = {
            "needed": database_needed,
            "type": db_type,
            "scale": compute_scale
        }
        
        # AI/ML services
        ai_needed = "ai_ml" in workload_types or "machine_learning" in workload_types
        service_needs["ai_ml"] = {
            "needed": ai_needed,
            "type": "managed_ml",
            "scale": compute_scale
        }
        
        # Networking needs
        service_needs["networking"] = {
            "needed": expected_users > 1000,
            "type": "load_balancer",
            "cdn_needed": expected_users > 5000
        }
        
        # Security needs
        service_needs["security"] = {
            "needed": True,  # Always needed
            "type": "basic",
            "compliance_level": "standard"
        }
        
        return service_needs
    
    def _assess_scalability_needs(self, technical_req: Dict[str, Any], 
                                 business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess scalability requirements."""
        expected_users = technical_req.get("expected_users", 1000)
        growth_goals = business_req.get("primary_goals", [])
        
        auto_scaling_needed = expected_users > 5000 or "scalability" in growth_goals
        global_distribution = expected_users > 50000
        
        return {
            "auto_scaling_needed": auto_scaling_needed,
            "global_distribution": global_distribution,
            "load_balancing_needed": expected_users > 1000,
            "cdn_recommended": expected_users > 5000,
            "scaling_strategy": "horizontal" if auto_scaling_needed else "vertical"
        }
    
    def _assess_compliance_needs(self, business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance requirements."""
        industry = business_req.get("industry", "")
        compliance_reqs = business_req.get("compliance_requirements", {})
        
        high_compliance = industry in ["healthcare", "finance", "fintech"]
        regulations = compliance_reqs.get("regulations", []) if isinstance(compliance_reqs, dict) else []
        
        return {
            "high_compliance_needed": high_compliance,
            "regulations": regulations,
            "data_residency_required": len(regulations) > 0,
            "encryption_required": high_compliance or len(regulations) > 0
        }
    
    def _prioritize_service_categories(self, service_needs: Dict[str, Any]) -> List[str]:
        """Prioritize service categories based on needs."""
        priorities = []
        
        # High priority services
        if service_needs.get("compute", {}).get("needed"):
            priorities.append("compute")
        if service_needs.get("database", {}).get("needed"):
            priorities.append("database")
        
        # Medium priority services
        if service_needs.get("storage", {}).get("needed"):
            priorities.append("storage")
        if service_needs.get("security", {}).get("needed"):
            priorities.append("security")
        
        # Lower priority services
        if service_needs.get("ai_ml", {}).get("needed"):
            priorities.append("ai_ml")
        if service_needs.get("networking", {}).get("needed"):
            priorities.append("networking")
        
        return priorities
    
    def _curate_category_services(self, category: str, category_needs: Dict[str, Any], 
                                 service_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Curate services for a specific category."""
        curated = []
        providers_data = service_data.get("providers", {})
        
        for provider, provider_services in providers_data.items():
            if "error" in provider_services:
                continue
                
            category_services = provider_services.get(category, {})
            if isinstance(category_services, dict) and "services" in category_services:
                services = category_services["services"]
                
                # Filter services based on needs
                for service in services:
                    if self._service_matches_needs(service, category_needs):
                        service_info = {
                            "provider": provider,
                            "category": category,
                            "name": service.get("name", "Unknown"),
                            "service_id": service.get("service_id", ""),
                            "pricing": service.get("pricing", {}),
                            "specifications": service.get("specifications", {}),
                            "features": service.get("features", [])
                        }
                        curated.append(service_info)
        
        return curated
    
    def _service_matches_needs(self, service: Dict[str, Any], needs: Dict[str, Any]) -> bool:
        """Check if a service matches the specified needs."""
        # Basic matching logic - can be enhanced
        if not needs.get("needed", False):
            return False
        
        # Check scale requirements
        scale = needs.get("scale", "small")
        specs = service.get("specifications", {})
        
        if scale == "large":
            # For large scale, prefer services with high CPU/memory
            cpu_cores = specs.get("vcpus", specs.get("cpu_cores", 1))
            if cpu_cores < 4:
                return False
        
        return True
    
    def _rank_services(self, services: List[Dict[str, Any]], category_needs: Dict[str, Any],
                      technical_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank services based on multiple criteria."""
        if not services:
            return []
        
        # Score each service
        scored_services = []
        for service in services:
            score = self._calculate_service_score(service, category_needs, technical_analysis)
            scored_services.append({
                **service,
                "ranking_score": score
            })
        
        # Sort by score (highest first)
        scored_services.sort(key=lambda x: x["ranking_score"], reverse=True)
        
        return scored_services
    
    def _calculate_service_score(self, service: Dict[str, Any], category_needs: Dict[str, Any],
                                technical_analysis: Dict[str, Any]) -> float:
        """Calculate a ranking score for a service."""
        score = 0.0
        
        # Cost effectiveness (30% weight)
        pricing = service.get("pricing", {})
        hourly_price = pricing.get("hourly", pricing.get("hourly_price", 1.0))
        if hourly_price < 0.1:
            score += 30
        elif hourly_price < 0.5:
            score += 20
        elif hourly_price < 1.0:
            score += 10
        
        # Performance (25% weight)
        specs = service.get("specifications", {})
        cpu_cores = specs.get("vcpus", specs.get("cpu_cores", 1))
        memory_gb = specs.get("memory_gb", 1)
        
        if cpu_cores >= 4 and memory_gb >= 8:
            score += 25
        elif cpu_cores >= 2 and memory_gb >= 4:
            score += 15
        else:
            score += 5
        
        # Provider preference (20% weight)
        provider = service.get("provider", "")
        if provider == "aws":
            score += 20  # AWS gets slight preference for maturity
        elif provider == "azure":
            score += 18
        elif provider == "gcp":
            score += 16
        
        # Feature richness (15% weight)
        features = service.get("features", [])
        score += min(len(features) * 2, 15)
        
        # Reliability/availability (10% weight)
        if "high_availability" in features or "99.9%" in str(specs):
            score += 10
        else:
            score += 5
        
        return score
    
    async def _calculate_service_cost(self, service: Dict[str, Any]) -> float:
        """Calculate monthly cost estimate for a service."""
        pricing = service.get("pricing", {})
        hourly_price = pricing.get("hourly", pricing.get("hourly_price", 0.1))
        
        # Estimate monthly cost (730 hours per month)
        monthly_cost = hourly_price * 730
        
        # Use calculator tool for more complex calculations if needed
        cost_result = await self._use_tool(
            "calculator",
            operation="cost_estimate",
            base_cost=monthly_cost,
            users=1000,  # Default assumption
            scaling_factor=1.0
        )
        
        if cost_result.is_success:
            return cost_result.data.get("monthly_cost", monthly_cost)
        
        return monthly_cost
    
    def _generate_cost_optimizations(self, cost_estimates: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        optimizations = []
        
        for category, costs in cost_estimates.items():
            if len(costs) > 1:
                cheapest = min(costs, key=lambda x: x["monthly_cost"])
                most_expensive = max(costs, key=lambda x: x["monthly_cost"])
                
                savings = most_expensive["monthly_cost"] - cheapest["monthly_cost"]
                if savings > 50:  # Significant savings opportunity
                    optimizations.append({
                        "category": category,
                        "recommendation": f"Choose {cheapest['service']['name']} over {most_expensive['service']['name']}",
                        "monthly_savings": savings,
                        "annual_savings": savings * 12,
                        "trade_offs": "May have different performance characteristics"
                    })
        
        return optimizations
    
    def _create_cost_breakdown(self, cost_estimates: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed cost breakdown."""
        breakdown = {}
        total_cost = 0
        
        for category, costs in cost_estimates.items():
            if costs:
                cheapest_cost = min(cost["monthly_cost"] for cost in costs)
                breakdown[category] = {
                    "monthly_cost": cheapest_cost,
                    "percentage": 0  # Will calculate after total
                }
                total_cost += cheapest_cost
        
        # Calculate percentages
        for category in breakdown:
            if total_cost > 0:
                breakdown[category]["percentage"] = (breakdown[category]["monthly_cost"] / total_cost) * 100
        
        return {
            "by_category": breakdown,
            "total_monthly": total_cost,
            "total_annual": total_cost * 12
        }
    
    def _determine_recommendation_priority(self, category: str, technical_analysis: Dict[str, Any]) -> str:
        """Determine priority level for a recommendation."""
        priority_services = technical_analysis.get("priority_services", [])
        
        if category in priority_services[:2]:  # Top 2 priorities
            return "high"
        elif category in priority_services[:4]:  # Next 2 priorities
            return "medium"
        else:
            return "low"
    
    def _create_service_rationale(self, service: Dict[str, Any], category: str, 
                                 technical_analysis: Dict[str, Any]) -> str:
        """Create rationale for service recommendation."""
        provider = service.get("provider", "").upper()
        name = service.get("name", "")
        score = service.get("ranking_score", 0)
        
        rationale = f"{provider} {name} scored highest ({score:.1f}/100) based on cost-effectiveness, performance, and feature set."
        
        # Add specific reasons based on category
        if category == "compute":
            specs = service.get("specifications", {})
            cpu = specs.get("vcpus", specs.get("cpu_cores", 1))
            memory = specs.get("memory_gb", 1)
            rationale += f" Provides {cpu} vCPUs and {memory}GB RAM suitable for your workload requirements."
        
        elif category == "database":
            features = service.get("features", [])
            if "automated_backups" in features:
                rationale += " Includes automated backups for data protection."
        
        return rationale
    
    def _create_implementation_steps(self, service: Dict[str, Any], category: str) -> List[str]:
        """Create implementation steps for a service."""
        provider = service.get("provider", "").lower()
        name = service.get("name", "")
        
        base_steps = [
            f"Set up {provider.upper()} account and configure billing",
            f"Create {name} instance in appropriate region",
            "Configure security groups and access controls",
            "Set up monitoring and alerting",
            "Test service functionality",
            "Implement backup and disaster recovery"
        ]
        
        # Add category-specific steps
        if category == "compute":
            base_steps.insert(2, "Configure auto-scaling policies")
        elif category == "database":
            base_steps.insert(2, "Configure database parameters and performance settings")
        elif category == "storage":
            base_steps.insert(2, "Set up lifecycle policies and access permissions")
        
        return base_steps
    
    def _get_cost_impact(self, category: str, cost_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get cost impact information for a category."""
        cost_estimates = cost_analysis.get("cost_estimates", {})
        category_costs = cost_estimates.get(category, [])
        
        if category_costs:
            recommended_cost = category_costs[0]["monthly_cost"]
            return {
                "monthly_cost": recommended_cost,
                "annual_cost": recommended_cost * 12,
                "cost_category": "low" if recommended_cost < 100 else "medium" if recommended_cost < 500 else "high"
            }
        
        return {"monthly_cost": 0, "annual_cost": 0, "cost_category": "unknown"}
    
    def _assess_business_alignment(self, service: Dict[str, Any], technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well service aligns with business goals."""
        # Simple alignment assessment
        provider = service.get("provider", "")
        pricing = service.get("pricing", {})
        hourly_price = pricing.get("hourly", pricing.get("hourly_price", 1.0))
        
        cost_alignment = "high" if hourly_price < 0.5 else "medium" if hourly_price < 1.0 else "low"
        
        return {
            "cost_alignment": cost_alignment,
            "scalability_alignment": "high" if provider in ["aws", "azure", "gcp"] else "medium",
            "reliability_alignment": "high",  # Assume cloud services are reliable
            "overall_alignment": "high" if cost_alignment == "high" else "medium"
        }   
 
    def _create_deployment_roadmap(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create deployment roadmap for recommended services."""
        phases = []
        
        # Phase 1: Core Infrastructure (High priority services)
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        if high_priority:
            phases.append({
                "phase": 1,
                "name": "Core Infrastructure Setup",
                "duration_weeks": 2,
                "services": [r["service"]["name"] for r in high_priority],
                "description": "Deploy essential compute, database, and security services"
            })
        
        # Phase 2: Supporting Services (Medium priority)
        medium_priority = [r for r in recommendations if r["priority"] == "medium"]
        if medium_priority:
            phases.append({
                "phase": 2,
                "name": "Supporting Services",
                "duration_weeks": 3,
                "services": [r["service"]["name"] for r in medium_priority],
                "description": "Add storage, networking, and optimization services"
            })
        
        # Phase 3: Advanced Features (Low priority)
        low_priority = [r for r in recommendations if r["priority"] == "low"]
        if low_priority:
            phases.append({
                "phase": 3,
                "name": "Advanced Features",
                "duration_weeks": 2,
                "services": [r["service"]["name"] for r in low_priority],
                "description": "Implement AI/ML, analytics, and specialized services"
            })
        
        return {
            "phases": phases,
            "total_duration_weeks": sum(p["duration_weeks"] for p in phases),
            "parallel_deployment": len(high_priority) > 1,
            "critical_path": "Core Infrastructure → Supporting Services → Advanced Features"
        }
    
    def _generate_best_practices(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate best practices for recommended services."""
        practices = []
        
        # General cloud best practices
        practices.extend([
            {
                "category": "Security",
                "practice": "Enable encryption at rest and in transit for all services",
                "rationale": "Protects sensitive data and meets compliance requirements"
            },
            {
                "category": "Cost Management",
                "practice": "Set up billing alerts and cost monitoring",
                "rationale": "Prevents unexpected charges and enables cost optimization"
            },
            {
                "category": "Reliability",
                "practice": "Deploy across multiple availability zones",
                "rationale": "Ensures high availability and disaster recovery"
            },
            {
                "category": "Monitoring",
                "practice": "Implement comprehensive logging and monitoring",
                "rationale": "Enables proactive issue detection and performance optimization"
            }
        ])
        
        # Service-specific best practices
        providers = set(r["service"]["provider"] for r in recommendations)
        for provider in providers:
            if provider == "aws":
                practices.append({
                    "category": "AWS Specific",
                    "practice": "Use IAM roles and policies for fine-grained access control",
                    "rationale": "Follows AWS security best practices and principle of least privilege"
                })
            elif provider == "azure":
                practices.append({
                    "category": "Azure Specific", 
                    "practice": "Leverage Azure Resource Manager templates for infrastructure as code",
                    "rationale": "Ensures consistent and repeatable deployments"
                })
        
        return practices
    
    def _create_monitoring_guidance(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create monitoring guidance for recommended services."""
        monitoring_stack = []
        key_metrics = []
        alerting_rules = []
        
        # Determine monitoring tools based on providers
        providers = set(r["service"]["provider"] for r in recommendations)
        
        if "aws" in providers:
            monitoring_stack.append("Amazon CloudWatch")
        if "azure" in providers:
            monitoring_stack.append("Azure Monitor")
        if "gcp" in providers:
            monitoring_stack.append("Google Cloud Monitoring")
        
        # Key metrics to monitor
        categories = set(r["category"] for r in recommendations)
        
        if "compute" in categories:
            key_metrics.extend(["CPU utilization", "Memory usage", "Network I/O"])
            alerting_rules.append("CPU > 80% for 5 minutes")
        
        if "database" in categories:
            key_metrics.extend(["Database connections", "Query performance", "Storage usage"])
            alerting_rules.append("Database connections > 80% of limit")
        
        if "storage" in categories:
            key_metrics.extend(["Storage usage", "I/O operations", "Access patterns"])
            alerting_rules.append("Storage usage > 85% of capacity")
        
        return {
            "monitoring_tools": monitoring_stack,
            "key_metrics": key_metrics,
            "alerting_rules": alerting_rules,
            "dashboard_recommendations": [
                "Infrastructure overview dashboard",
                "Application performance dashboard", 
                "Cost and billing dashboard"
            ]
        }
    
    def _create_cost_management_strategies(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create cost management strategies."""
        strategies = []
        
        # Right-sizing strategy
        strategies.append({
            "strategy": "Right-sizing",
            "description": "Regularly review and adjust service sizes based on actual usage",
            "implementation": [
                "Monitor resource utilization weekly",
                "Downsize underutilized resources",
                "Use auto-scaling to match demand"
            ],
            "potential_savings": "15-30%"
        })
        
        # Reserved instances/savings plans
        providers = set(r["service"]["provider"] for r in recommendations)
        if providers:
            strategies.append({
                "strategy": "Reserved Capacity",
                "description": "Purchase reserved instances or savings plans for predictable workloads",
                "implementation": [
                    "Analyze usage patterns over 3-6 months",
                    "Purchase 1-year reserved instances for stable workloads",
                    "Use savings plans for flexible workloads"
                ],
                "potential_savings": "30-60%"
            })
        
        # Automated cost optimization
        strategies.append({
            "strategy": "Automation",
            "description": "Implement automated cost optimization policies",
            "implementation": [
                "Schedule non-production resources to shut down after hours",
                "Use spot instances for batch processing",
                "Implement lifecycle policies for storage"
            ],
            "potential_savings": "20-40%"
        })
        
        return strategies
    
    def _estimate_implementation_time(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate implementation time for recommendations."""
        total_services = len(recommendations)
        
        # Base time estimates per service category
        time_estimates = {
            "compute": 3,      # days
            "database": 4,     # days  
            "storage": 2,      # days
            "networking": 2,   # days
            "security": 3,     # days
            "ai_ml": 5         # days
        }
        
        total_days = 0
        for rec in recommendations:
            category = rec["category"]
            total_days += time_estimates.get(category, 3)
        
        # Account for parallel deployment
        if total_services > 1:
            total_days = total_days * 0.7  # 30% reduction for parallel work
        
        critical_path_days = 0
        if recommendations:
            critical_path_days = max(time_estimates.get(rec["category"], 3) for rec in recommendations)
        
        return {
            "total_implementation_days": int(total_days),
            "total_implementation_weeks": int(total_days / 5),
            "services_count": total_services,
            "parallel_deployment_possible": total_services > 1,
            "critical_path_days": critical_path_days
        }
    
    def _create_risk_mitigation_strategies(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create risk mitigation strategies."""
        risks = []
        
        # Vendor lock-in risk
        providers = set(r["service"]["provider"] for r in recommendations)
        if len(providers) == 1:
            risks.append({
                "risk": "Vendor Lock-in",
                "impact": "medium",
                "probability": "high",
                "mitigation": [
                    "Use containerization for application portability",
                    "Avoid proprietary services where possible",
                    "Maintain infrastructure as code for easy migration"
                ]
            })
        
        # Cost overrun risk
        total_cost = sum(rec.get("cost_impact", {}).get("monthly_cost", 0) for rec in recommendations)
        if total_cost > 1000:
            risks.append({
                "risk": "Cost Overrun",
                "impact": "high",
                "probability": "medium",
                "mitigation": [
                    "Set up strict billing alerts",
                    "Implement cost allocation tags",
                    "Regular cost reviews and optimization"
                ]
            })
        
        # Performance risk
        risks.append({
            "risk": "Performance Issues",
            "impact": "medium",
            "probability": "medium",
            "mitigation": [
                "Implement comprehensive monitoring",
                "Conduct load testing before production",
                "Have auto-scaling policies in place"
            ]
        })
        
        return risks