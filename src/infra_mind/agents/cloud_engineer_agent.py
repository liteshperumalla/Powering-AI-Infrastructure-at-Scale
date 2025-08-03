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
    
    async def analyze_technical_requirements(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze technical requirements from a Cloud Engineer perspective.
        
        Args:
            workflow_data: Dictionary containing assessment data and technical requirements
            
        Returns:
            Dictionary containing technical analysis results
        """
        try:
            business_requirements = workflow_data.get("business_requirements", {})
            technical_requirements = workflow_data.get("technical_requirements", {})
            
            # Perform technical analysis
            analysis = {
                "infrastructure_assessment": self._assess_infrastructure_needs(business_requirements),
                "cloud_recommendations": self._recommend_cloud_services(business_requirements),
                "architecture_design": self._design_architecture(business_requirements),
                "cost_estimation": self._estimate_infrastructure_costs(business_requirements)
            }
            
            return {
                "status": "completed",
                "analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cloud Engineer technical analysis failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _assess_infrastructure_needs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess infrastructure needs based on requirements."""
        company_size = requirements.get("company_size", "unknown")
        industry = requirements.get("industry", "unknown")
        
        return {
            "compute_requirements": "medium" if company_size == "medium" else "high",
            "storage_requirements": "high" if industry in ["finance", "healthcare"] else "medium",
            "network_requirements": "high",
            "security_requirements": "high" if industry in ["finance", "healthcare"] else "medium"
        }
    
    def _recommend_cloud_services(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend cloud services."""
        return {
            "primary_provider": "AWS",
            "secondary_provider": "Azure",
            "recommended_services": {
                "compute": ["EC2", "Lambda", "ECS"],
                "storage": ["S3", "EBS", "EFS"],
                "database": ["RDS", "DynamoDB"],
                "networking": ["VPC", "CloudFront", "Route53"]
            }
        }
    
    def _design_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture."""
        return {
            "architecture_pattern": "microservices",
            "deployment_strategy": "containerized",
            "scalability_approach": "horizontal",
            "availability_target": "99.9%"
        }
    
    def _estimate_infrastructure_costs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate infrastructure costs."""
        return {
            "monthly_estimate": "$2,000-$5,000",
            "annual_estimate": "$24,000-$60,000",
            "cost_breakdown": {
                "compute": "40%",
                "storage": "20%",
                "networking": "15%",
                "other": "25%"
            }
        }
    
    async def recommend_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend cloud architecture based on requirements.
        
        Args:
            requirements: Dictionary containing workload and business requirements
            
        Returns:
            Dictionary containing architecture recommendations
        """
        try:
            workload_type = requirements.get("workload_type", "web_application")
            scale = requirements.get("scale", "medium")
            budget = requirements.get("budget", "moderate")
            compliance = requirements.get("compliance", [])
            
            # Determine primary cloud provider based on requirements
            primary_provider = self._select_primary_provider(workload_type, compliance, budget)
            
            # Design architecture components
            architecture_components = self._design_architecture_components(
                workload_type, scale, compliance
            )
            
            # Estimate costs
            cost_estimate = self._calculate_architecture_costs(
                architecture_components, scale, primary_provider
            )
            
            # Generate deployment strategy
            deployment_strategy = self._create_deployment_strategy(
                architecture_components, scale
            )
            
            return {
                "status": "success",
                "primary_provider": primary_provider,
                "architecture": {
                    "pattern": "microservices" if scale in ["medium", "large"] else "monolithic",
                    "components": architecture_components,
                    "deployment_strategy": deployment_strategy,
                    "scalability": "horizontal" if scale == "large" else "vertical",
                    "availability_target": "99.9%" if scale in ["medium", "large"] else "99.5%"
                },
                "cost_estimate": cost_estimate,
                "compliance_alignment": self._assess_compliance_alignment(
                    architecture_components, compliance
                ),
                "implementation_timeline": self._estimate_implementation_timeline(
                    architecture_components, scale
                ),
                "recommendations": self._generate_architecture_recommendations(
                    workload_type, scale, budget, compliance
                ),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Architecture recommendation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _select_primary_provider(self, workload_type: str, compliance: List[str], budget: str) -> str:
        """Select the best primary cloud provider."""
        # AWS for ML workloads and enterprise features
        if workload_type in ["ml_training_inference", "machine_learning", "ai_ml"]:
            return "AWS"
        
        # Azure for Microsoft-heavy environments
        if "microsoft" in workload_type.lower():
            return "Azure"
        
        # GCP for cost-conscious deployments
        if budget == "low":
            return "GCP"
        
        # AWS as default for enterprise workloads
        return "AWS"
    
    def _design_architecture_components(self, workload_type: str, scale: str, compliance: List[str]) -> Dict[str, Any]:
        """Design architecture components based on requirements."""
        components = {
            "compute": {
                "primary": "containers" if scale in ["medium", "large"] else "virtual_machines",
                "orchestration": "kubernetes" if scale == "large" else "docker_compose",
                "auto_scaling": scale in ["medium", "large"]
            },
            "storage": {
                "object_storage": True,
                "block_storage": workload_type in ["database", "ml_training_inference"],
                "backup_strategy": "automated_daily",
                "encryption": len(compliance) > 0
            },
            "database": {
                "type": "managed_relational" if workload_type == "web_application" else "managed_nosql",
                "high_availability": scale in ["medium", "large"],
                "backup_retention": "30_days" if len(compliance) > 0 else "7_days"
            },
            "networking": {
                "load_balancer": scale in ["medium", "large"],
                "cdn": scale == "large",
                "vpc": True,
                "private_subnets": len(compliance) > 0
            },
            "security": {
                "waf": len(compliance) > 0,
                "identity_management": True,
                "encryption_at_rest": len(compliance) > 0,
                "encryption_in_transit": True,
                "monitoring": True
            }
        }
        
        # Add ML-specific components
        if workload_type in ["ml_training_inference", "machine_learning", "ai_ml"]:
            components["ml_services"] = {
                "managed_ml_platform": True,
                "model_registry": True,
                "feature_store": scale in ["medium", "large"],
                "ml_pipelines": True
            }
        
        return components
    
    def _calculate_architecture_costs(self, components: Dict[str, Any], scale: str, provider: str) -> Dict[str, Any]:
        """Calculate estimated costs for the architecture."""
        base_costs = {
            "small": {"compute": 200, "storage": 50, "database": 100, "networking": 30},
            "medium": {"compute": 800, "storage": 200, "database": 400, "networking": 150},
            "large": {"compute": 2000, "storage": 500, "database": 1000, "networking": 400}
        }
        
        costs = base_costs.get(scale, base_costs["medium"])
        
        # Add ML service costs if needed
        if "ml_services" in components:
            costs["ml_services"] = {"small": 300, "medium": 800, "large": 2000}[scale]
        
        # Add security costs for compliance
        if components.get("security", {}).get("waf"):
            costs["security"] = {"small": 50, "medium": 150, "large": 300}[scale]
        
        total_monthly = sum(costs.values())
        
        return {
            "monthly_breakdown": costs,
            "total_monthly": total_monthly,
            "total_annual": total_monthly * 12,
            "currency": "USD",
            "provider": provider,
            "cost_optimization_potential": "15-25%"
        }
    
    def _create_deployment_strategy(self, components: Dict[str, Any], scale: str) -> Dict[str, Any]:
        """Create deployment strategy."""
        return {
            "approach": "blue_green" if scale in ["medium", "large"] else "rolling",
            "environments": ["development", "staging", "production"],
            "ci_cd": True,
            "infrastructure_as_code": True,
            "monitoring": {
                "application_monitoring": True,
                "infrastructure_monitoring": True,
                "log_aggregation": True,
                "alerting": True
            },
            "backup_strategy": {
                "frequency": "daily",
                "retention": "30_days",
                "cross_region": scale == "large"
            }
        }
    
    def _assess_compliance_alignment(self, components: Dict[str, Any], compliance: List[str]) -> Dict[str, Any]:
        """Assess how well the architecture aligns with compliance requirements."""
        alignment_score = 0
        max_score = len(compliance) * 10 if compliance else 10
        
        security = components.get("security", {})
        
        # Check encryption
        if security.get("encryption_at_rest") and security.get("encryption_in_transit"):
            alignment_score += 3
        
        # Check network security
        networking = components.get("networking", {})
        if networking.get("private_subnets") and networking.get("vpc"):
            alignment_score += 3
        
        # Check monitoring
        if security.get("monitoring"):
            alignment_score += 2
        
        # Check backup strategy
        database = components.get("database", {})
        if database.get("backup_retention") == "30_days":
            alignment_score += 2
        
        return {
            "compliance_requirements": compliance,
            "alignment_score": min(alignment_score, max_score),
            "max_score": max_score,
            "alignment_percentage": (alignment_score / max_score * 100) if max_score > 0 else 100,
            "recommendations": self._generate_compliance_recommendations(compliance, components)
        }
    
    def _estimate_implementation_timeline(self, components: Dict[str, Any], scale: str) -> Dict[str, Any]:
        """Estimate implementation timeline."""
        base_weeks = {"small": 4, "medium": 8, "large": 16}[scale]
        
        # Add time for complex components
        if "ml_services" in components:
            base_weeks += 4
        
        if components.get("security", {}).get("waf"):
            base_weeks += 2
        
        return {
            "total_weeks": base_weeks,
            "phases": {
                "infrastructure_setup": f"{base_weeks // 4} weeks",
                "application_deployment": f"{base_weeks // 3} weeks",
                "testing_optimization": f"{base_weeks // 4} weeks",
                "go_live": "1 week"
            },
            "critical_path": ["infrastructure_setup", "application_deployment"],
            "parallel_activities": ["security_configuration", "monitoring_setup"]
        }
    
    def _generate_architecture_recommendations(self, workload_type: str, scale: str, budget: str, compliance: List[str]) -> List[str]:
        """Generate specific architecture recommendations."""
        recommendations = []
        
        if workload_type in ["ml_training_inference", "machine_learning"]:
            recommendations.append("Use managed ML services to reduce operational overhead")
            recommendations.append("Implement MLOps pipeline for model lifecycle management")
        
        if scale == "large":
            recommendations.append("Implement microservices architecture for better scalability")
            recommendations.append("Use container orchestration (Kubernetes) for deployment")
        
        if len(compliance) > 0:
            recommendations.append("Enable encryption at rest and in transit")
            recommendations.append("Implement comprehensive logging and monitoring")
            recommendations.append("Use private subnets for sensitive workloads")
        
        if budget == "low":
            recommendations.append("Consider spot instances for non-critical workloads")
            recommendations.append("Implement auto-scaling to optimize costs")
        
        return recommendations
    
    def _generate_compliance_recommendations(self, compliance: List[str], components: Dict[str, Any]) -> List[str]:
        """Generate compliance-specific recommendations."""
        recommendations = []
        
        for req in compliance:
            if req.lower() in ["gdpr", "pci_dss", "hipaa"]:
                recommendations.append(f"Ensure data encryption for {req} compliance")
                recommendations.append(f"Implement access logging for {req} requirements")
            
        if not components.get("security", {}).get("waf"):
            recommendations.append("Consider adding Web Application Firewall for enhanced security")
        
        return recommendations
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute Cloud Engineer agent's main service curation logic using real LLM.
        
        Returns:
            Dictionary with service recommendations and analysis
        """
        logger.info("Cloud Engineer Agent starting real LLM-powered analysis")
        
        try:
            # Step 1: Analyze assessment data
            assessment_data = self._prepare_assessment_data()
            
            # Step 2: Generate LLM-powered technical analysis
            technical_analysis = await self._llm_analyze_technical_requirements(assessment_data)
            
            # Step 3: Collect real cloud service data
            service_data = await self._collect_cloud_service_data()
            
            # Step 4: Use LLM to curate and recommend services
            service_recommendations = await self._llm_generate_service_recommendations(
                assessment_data, technical_analysis, service_data
            )
            
            # Step 5: Generate cost analysis with real API data
            cost_analysis = await self._perform_real_cost_analysis(service_recommendations)
            
            # Step 6: Create implementation roadmap using LLM
            implementation_guidance = await self._llm_create_implementation_guidance(
                service_recommendations, cost_analysis
            )
            
            # Step 7: Store recommendations in database
            stored_recommendations = await self._store_recommendations_in_database(
                service_recommendations, cost_analysis
            )
            
            result = {
                "recommendations": service_recommendations,
                "data": {
                    "technical_analysis": technical_analysis,
                    "service_data": service_data,
                    "cost_analysis": cost_analysis,
                    "implementation_guidance": implementation_guidance,
                    "stored_recommendations": stored_recommendations,
                    "platforms_analyzed": self.cloud_platforms,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "llm_powered": True
                }
            }
            
            logger.info("Cloud Engineer Agent completed real LLM-powered analysis successfully")
            return result
            
        except Exception as e:
            logger.error(f"Cloud Engineer Agent LLM analysis failed: {str(e)}")
            # Fallback to simpler analysis if LLM fails
            return await self._fallback_analysis()
    
    def _prepare_assessment_data(self) -> Dict[str, Any]:
        """Prepare assessment data for LLM analysis."""
        if not self.current_assessment:
            return {}
        
        try:
            # Extract key information from assessment
            assessment_dict = self.current_assessment.dict() if hasattr(self.current_assessment, 'dict') else self.current_assessment.__dict__
            
            business_req = assessment_dict.get("business_requirements", {})
            technical_req = assessment_dict.get("technical_requirements", {})
            
            return {
                "title": assessment_dict.get("title", "Infrastructure Assessment"),
                "description": assessment_dict.get("description", ""),
                "business_requirements": business_req,
                "technical_requirements": technical_req,
                "assessment_id": str(assessment_dict.get("id", "")),
                "created_at": assessment_dict.get("created_at"),
                "priority": assessment_dict.get("priority", "medium")
            }
        except Exception as e:
            logger.warning(f"Failed to prepare assessment data: {e}")
            return {}
    
    async def _llm_analyze_technical_requirements(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze technical requirements."""
        prompt = f"""As a Cloud Engineer, analyze the following infrastructure assessment and provide detailed technical analysis:

ASSESSMENT OVERVIEW:
Title: {assessment_data.get('title', 'N/A')}
Description: {assessment_data.get('description', 'N/A')}

BUSINESS REQUIREMENTS:
{self._format_requirements(assessment_data.get('business_requirements', {}))}

TECHNICAL REQUIREMENTS:
{self._format_requirements(assessment_data.get('technical_requirements', {}))}

Please provide a comprehensive technical analysis including:

1. **Workload Characteristics**:
   - Primary workload types and their technical implications
   - Expected user load and traffic patterns
   - Performance and scalability requirements

2. **Infrastructure Needs Assessment**:
   - Compute requirements (CPU, memory, instance types)
   - Storage requirements (type, capacity, performance)
   - Network requirements (bandwidth, latency, security)
   - Database requirements (type, size, performance)

3. **Architecture Recommendations**:
   - Recommended architecture pattern (monolithic, microservices, serverless)
   - Deployment strategy (containers, VMs, hybrid)
   - Scalability approach (horizontal, vertical, auto-scaling)

4. **Security and Compliance**:
   - Security requirements analysis
   - Compliance considerations
   - Data protection needs

5. **Technology Stack Recommendations**:
   - Programming languages and frameworks compatibility
   - Integration requirements
   - Monitoring and observability needs

Please respond in JSON format with structured data for each section."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are an expert Cloud Engineer with deep knowledge of AWS, Azure, and GCP services. Provide detailed, actionable technical analysis based on the assessment data.",
                temperature=0.3,
                max_tokens=2000
            )
            
            # Try to parse JSON response
            import json
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured fallback
                return self._parse_llm_analysis_response(response)
            
        except Exception as e:
            logger.error(f"LLM technical analysis failed: {e}")
            return self._get_fallback_technical_analysis(assessment_data)
    
    async def _llm_generate_service_recommendations(
        self, 
        assessment_data: Dict[str, Any], 
        technical_analysis: Dict[str, Any], 
        service_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use LLM to generate specific cloud service recommendations."""
        
        prompt = f"""Based on the technical analysis and available cloud services, recommend specific cloud services for this infrastructure assessment.

TECHNICAL ANALYSIS:
{json.dumps(technical_analysis, indent=2)}

AVAILABLE CLOUD SERVICES:
{self._format_service_data_for_llm(service_data)}

Please recommend specific cloud services from AWS, Azure, and/or GCP that best match the requirements. For each recommendation, provide:

1. **Service Details**:
   - Cloud provider (AWS/Azure/GCP)
   - Service name and type
   - Specific configuration recommendations

2. **Justification**:
   - Why this service fits the requirements
   - Key benefits and features
   - Performance characteristics

3. **Cost Considerations**:
   - Estimated pricing model
   - Cost optimization opportunities
   - Scaling cost implications

4. **Implementation**:
   - Setup complexity (low/medium/high)
   - Implementation timeline
   - Prerequisites and dependencies

5. **Alternatives**:
   - Alternative services from same or different providers
   - Trade-offs between options

Please focus on practical, production-ready solutions and provide at least 3-5 key service recommendations covering compute, storage, database, and networking needs.

Respond in JSON format with an array of recommendations."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a Cloud Engineer expert in AWS, Azure, and GCP services. Provide specific, actionable service recommendations with detailed justification.",
                temperature=0.2,
                max_tokens=2500
            )
            
            # Parse recommendations
            import json
            try:
                recommendations = json.loads(response)
                if isinstance(recommendations, list):
                    return recommendations
                elif isinstance(recommendations, dict) and "recommendations" in recommendations:
                    return recommendations["recommendations"]
                else:
                    return [recommendations]
            except json.JSONDecodeError:
                return self._parse_llm_recommendations_response(response)
            
        except Exception as e:
            logger.error(f"LLM service recommendations failed: {e}")
            return self._get_fallback_service_recommendations(assessment_data)
    
    async def _llm_create_implementation_guidance(
        self, 
        recommendations: List[Dict[str, Any]], 
        cost_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to create detailed implementation guidance."""
        
        prompt = f"""Create a comprehensive implementation roadmap for the following cloud service recommendations:

RECOMMENDED SERVICES:
{json.dumps(recommendations, indent=2)}

COST ANALYSIS:
{json.dumps(cost_analysis, indent=2)}

Please provide detailed implementation guidance including:

1. **Deployment Roadmap**:
   - Implementation phases with timelines
   - Dependencies between services
   - Critical path items
   - Risk mitigation strategies

2. **Best Practices**:
   - Security best practices for each service
   - Performance optimization guidelines
   - Cost management strategies
   - Monitoring and alerting setup

3. **Step-by-Step Implementation**:
   - Detailed setup instructions for each phase
   - Configuration recommendations
   - Testing and validation procedures
   - Rollback procedures

4. **Operational Considerations**:
   - Day-to-day operations guidance
   - Maintenance procedures
   - Scaling operations
   - Disaster recovery planning

5. **Success Metrics**:
   - Key performance indicators
   - Cost tracking metrics
   - Performance benchmarks
   - Compliance checkpoints

Respond in JSON format with structured guidance for each section."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a senior Cloud Engineer with extensive experience in large-scale cloud implementations. Provide practical, actionable implementation guidance.",
                temperature=0.3,
                max_tokens=2000
            )
            
            import json
            try:
                guidance = json.loads(response)
                return guidance
            except json.JSONDecodeError:
                return self._parse_llm_guidance_response(response)
            
        except Exception as e:
            logger.error(f"LLM implementation guidance failed: {e}")
            return self._get_fallback_implementation_guidance()
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements dictionary for LLM prompt."""
        if not requirements:
            return "No specific requirements provided"
        
        formatted = []
        for key, value in requirements.items():
            if isinstance(value, dict):
                formatted.append(f"- {key.replace('_', ' ').title()}:")
                for subkey, subvalue in value.items():
                    formatted.append(f"  - {subkey.replace('_', ' ').title()}: {subvalue}")
            elif isinstance(value, list):
                formatted.append(f"- {key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
            else:
                formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        return '\n'.join(formatted)
    
    def _format_service_data_for_llm(self, service_data: Dict[str, Any]) -> str:
        """Format service data for LLM consumption."""
        if not service_data or not service_data.get("providers"):
            return "Limited service data available - using general cloud service knowledge"
        
        formatted = []
        for provider, provider_data in service_data.get("providers", {}).items():
            if "error" in provider_data:
                formatted.append(f"{provider.upper()}: Service data unavailable")
                continue
            
            formatted.append(f"{provider.upper()} Services:")
            for category, category_data in provider_data.items():
                if isinstance(category_data, dict) and "services" in category_data:
                    services = category_data["services"][:3]  # Limit to top 3 per category
                    formatted.append(f"  {category.title()}:")
                    for service in services:
                        name = service.get("name", "Unknown")
                        specs = service.get("specifications", {})
                        pricing = service.get("pricing", {})
                        formatted.append(f"    - {name}: {specs} (${pricing})")
        
        return '\n'.join(formatted) if formatted else "General cloud services available"
    
    async def _perform_real_cost_analysis(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform real cost analysis using cloud provider APIs."""
        try:
            total_monthly_cost = 0
            cost_breakdown = {}
            
            for rec in recommendations:
                service_name = rec.get("service_name", "Unknown")
                provider = rec.get("provider", "unknown")
                
                # Use cloud API tool to get real pricing data
                try:
                    cost_result = await self._use_tool(
                        "cloud_api",
                        provider=provider,
                        service="pricing",
                        operation="estimate_cost",
                        service_config=rec.get("configuration", {}),
                        usage_patterns=rec.get("usage_patterns", {})
                    )
                    
                    if cost_result.is_success:
                        monthly_cost = cost_result.data.get("monthly_cost", 0)
                        total_monthly_cost += monthly_cost
                        cost_breakdown[service_name] = {
                            "monthly_cost": monthly_cost,
                            "provider": provider,
                            "cost_details": cost_result.data
                        }
                    else:
                        # Fallback to estimation
                        estimated_cost = self._estimate_service_cost(rec)
                        total_monthly_cost += estimated_cost
                        cost_breakdown[service_name] = {
                            "monthly_cost": estimated_cost,
                            "provider": provider,
                            "estimated": True
                        }
                        
                except Exception as e:
                    logger.warning(f"Cost analysis failed for {service_name}: {e}")
                    # Use fallback estimation
                    estimated_cost = self._estimate_service_cost(rec)
                    total_monthly_cost += estimated_cost
                    cost_breakdown[service_name] = {
                        "monthly_cost": estimated_cost,
                        "provider": provider,
                        "estimated": True,
                        "error": str(e)
                    }
            
            return {
                "total_monthly_cost": total_monthly_cost,
                "total_annual_cost": total_monthly_cost * 12,
                "cost_breakdown": cost_breakdown,
                "currency": "USD",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "optimization_opportunities": self._identify_cost_optimizations(cost_breakdown)
            }
            
        except Exception as e:
            logger.error(f"Real cost analysis failed: {e}")
            return self._get_fallback_cost_analysis()
    
    def _estimate_service_cost(self, recommendation: Dict[str, Any]) -> float:
        """Estimate service cost based on recommendation details."""
        provider = recommendation.get("provider", "aws").lower()
        category = recommendation.get("category", "compute").lower()
        
        # Basic cost estimation based on service type and provider
        base_costs = {
            "aws": {"compute": 50, "storage": 20, "database": 100, "networking": 30},
            "azure": {"compute": 45, "storage": 18, "database": 95, "networking": 28},
            "gcp": {"compute": 40, "storage": 15, "database": 85, "networking": 25}
        }
        
        return base_costs.get(provider, base_costs["aws"]).get(category, 50)
    
    async def _store_recommendations_in_database(
        self, 
        recommendations: List[Dict[str, Any]], 
        cost_analysis: Dict[str, Any]
    ) -> List[str]:
        """Store recommendations in the database."""
        try:
            from ..models.recommendation import Recommendation, ServiceRecommendation
            from ..schemas.base import RecommendationConfidence, CloudProvider
            
            stored_ids = []
            
            for rec_data in recommendations:
                # Create service recommendations
                service_recs = []
                for service in rec_data.get("services", []):
                    try:
                        provider_str = service.get("provider", "aws").lower()
                        provider = CloudProvider.AWS if provider_str == "aws" else CloudProvider.AZURE if provider_str == "azure" else CloudProvider.GCP
                        
                        service_rec = ServiceRecommendation(
                            service_name=service.get("name", "Unknown"),
                            provider=provider,
                            service_category=service.get("category", "general"),
                            estimated_monthly_cost=service.get("estimated_cost", 0),
                            configuration=service.get("configuration", {}),
                            reasons=service.get("reasons", []),
                            setup_complexity=service.get("complexity", "medium")
                        )
                        service_recs.append(service_rec)
                    except Exception as e:
                        logger.warning(f"Failed to create service recommendation: {e}")
                
                # Determine confidence level
                confidence_score = rec_data.get("confidence_score", 0.7)
                if confidence_score >= 0.8:
                    confidence_level = RecommendationConfidence.HIGH
                elif confidence_score >= 0.6:
                    confidence_level = RecommendationConfidence.MEDIUM
                else:
                    confidence_level = RecommendationConfidence.LOW
                
                # Create main recommendation
                recommendation = Recommendation(
                    assessment_id=str(self.current_assessment.id) if self.current_assessment else "unknown",
                    agent_name=self.config.name,
                    agent_version=self.config.version,
                    title=rec_data.get("title", "Cloud Service Recommendation"),
                    summary=rec_data.get("description", "")[:500],
                    confidence_level=confidence_level,
                    confidence_score=confidence_score,
                    recommendation_data=rec_data,
                    recommended_services=service_recs,
                    cost_estimates=cost_analysis,
                    total_estimated_monthly_cost=rec_data.get("estimated_monthly_cost", 0),
                    implementation_steps=rec_data.get("implementation_steps", []),
                    category=rec_data.get("category", "infrastructure"),
                    business_impact=rec_data.get("priority", "medium")
                )
                
                # Save to database
                await recommendation.insert()
                stored_ids.append(str(recommendation.id))
                
                logger.info(f"Stored recommendation: {recommendation.title}")
            
            return stored_ids
            
        except Exception as e:
            logger.error(f"Failed to store recommendations in database: {e}")
            return []
    
    async def _fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when LLM processing fails."""
        logger.warning("Using fallback analysis due to LLM failure")
        
        return {
            "recommendations": [
                {
                    "category": "infrastructure",
                    "title": "Basic Cloud Infrastructure Setup",
                    "description": "Set up basic cloud infrastructure with compute, storage, and networking",
                    "priority": "high",
                    "services": ["Compute Instances", "Block Storage", "Load Balancer"],
                    "estimated_monthly_cost": 500,
                    "implementation_steps": [
                        "Set up virtual network",
                        "Deploy compute instances",
                        "Configure storage",
                        "Set up load balancing"
                    ]
                }
            ],
            "data": {
                "fallback_mode": True,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "llm_powered": False
            }
        }   
 
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
    
    # Helper methods for LLM response parsing and fallbacks
    
    def _parse_llm_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse non-JSON LLM analysis response into structured format."""
        try:
            # Extract key sections from text response
            analysis = {
                "workload_characteristics": {},
                "infrastructure_needs": {},
                "architecture_recommendations": {},
                "security_compliance": {},
                "technology_stack": {}
            }
            
            # Simple text parsing to extract information
            if "workload" in response.lower():
                analysis["workload_characteristics"]["detected"] = True
            if "compute" in response.lower():
                analysis["infrastructure_needs"]["compute"] = "required"
            if "microservices" in response.lower():
                analysis["architecture_recommendations"]["pattern"] = "microservices"
            elif "serverless" in response.lower():
                analysis["architecture_recommendations"]["pattern"] = "serverless"
            else:
                analysis["architecture_recommendations"]["pattern"] = "traditional"
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM analysis response: {e}")
            return self._get_fallback_technical_analysis({})
    
    def _parse_llm_recommendations_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse non-JSON LLM recommendations response."""
        try:
            # Extract service mentions from text
            recommendations = []
            
            # Common cloud services to look for
            services = {
                "EC2": {"provider": "aws", "category": "compute"},
                "S3": {"provider": "aws", "category": "storage"},
                "RDS": {"provider": "aws", "category": "database"},
                "Lambda": {"provider": "aws", "category": "compute"},
                "Azure VM": {"provider": "azure", "category": "compute"},
                "Blob Storage": {"provider": "azure", "category": "storage"},
                "Compute Engine": {"provider": "gcp", "category": "compute"},
                "Cloud Storage": {"provider": "gcp", "category": "storage"}
            }
            
            for service_name, service_info in services.items():
                if service_name.lower() in response.lower():
                    recommendations.append({
                        "title": f"{service_name} Recommendation",
                        "description": f"Use {service_name} for {service_info['category']} needs",
                        "provider": service_info["provider"],
                        "category": service_info["category"],
                        "priority": "medium",
                        "estimated_monthly_cost": 100
                    })
            
            return recommendations if recommendations else self._get_fallback_service_recommendations({})
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM recommendations response: {e}")
            return self._get_fallback_service_recommendations({})
    
    def _parse_llm_guidance_response(self, response: str) -> Dict[str, Any]:
        """Parse non-JSON LLM guidance response."""
        try:
            return {
                "deployment_roadmap": {
                    "phases": ["Setup", "Deploy", "Test", "Go-Live"],
                    "timeline": "4-6 weeks"
                },
                "best_practices": [
                    "Enable encryption",
                    "Set up monitoring",
                    "Implement backups",
                    "Configure access controls"
                ],
                "implementation_steps": [
                    "Plan infrastructure",
                    "Set up networking",
                    "Deploy services",
                    "Configure monitoring"
                ],
                "success_metrics": [
                    "System availability > 99%",
                    "Response time < 200ms",
                    "Cost within budget"
                ]
            }
        except Exception as e:
            logger.warning(f"Failed to parse LLM guidance response: {e}")
            return self._get_fallback_implementation_guidance()
    
    def _get_fallback_technical_analysis(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback technical analysis when LLM fails."""
        return {
            "workload_characteristics": {
                "primary_workload": "web_application",
                "expected_users": 1000,
                "traffic_pattern": "standard_business_hours"
            },
            "infrastructure_needs": {
                "compute": "medium",
                "storage": "standard",
                "database": "relational",
                "networking": "standard"
            },
            "architecture_recommendations": {
                "pattern": "microservices",
                "deployment": "containerized",
                "scalability": "horizontal"
            },
            "security_compliance": {
                "encryption": "required",
                "monitoring": "comprehensive",
                "access_control": "rbac"
            },
            "fallback_mode": True
        }
    
    def _get_fallback_service_recommendations(self, assessment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get fallback service recommendations when LLM fails."""
        return [
            {
                "title": "Compute Infrastructure",
                "description": "Set up scalable compute infrastructure",
                "provider": "aws",
                "category": "compute",
                "services": ["EC2", "Auto Scaling"],
                "priority": "high",
                "estimated_monthly_cost": 200,
                "implementation_steps": [
                    "Create VPC",
                    "Launch EC2 instances",
                    "Configure auto scaling"
                ]
            },
            {
                "title": "Storage Solution",
                "description": "Implement secure and scalable storage",
                "provider": "aws",
                "category": "storage", 
                "services": ["S3", "EBS"],
                "priority": "high",
                "estimated_monthly_cost": 50,
                "implementation_steps": [
                    "Create S3 buckets",
                    "Set up lifecycle policies",
                    "Configure encryption"
                ]
            },
            {
                "title": "Database Services",
                "description": "Deploy managed database solution",
                "provider": "aws",
                "category": "database",
                "services": ["RDS"],
                "priority": "high",
                "estimated_monthly_cost": 150,
                "implementation_steps": [
                    "Create RDS instance",
                    "Configure backups",
                    "Set up monitoring"
                ]
            }
        ]
    
    def _get_fallback_implementation_guidance(self) -> Dict[str, Any]:
        """Get fallback implementation guidance when LLM fails."""
        return {
            "deployment_roadmap": {
                "phases": [
                    {
                        "name": "Foundation",
                        "duration": "1-2 weeks",
                        "tasks": ["Network setup", "Security configuration"]
                    },
                    {
                        "name": "Core Services",
                        "duration": "2-3 weeks", 
                        "tasks": ["Compute deployment", "Database setup"]
                    },
                    {
                        "name": "Optimization",
                        "duration": "1 week",
                        "tasks": ["Performance tuning", "Cost optimization"]
                    }
                ]
            },
            "best_practices": [
                "Use Infrastructure as Code",
                "Implement monitoring and alerting",
                "Follow security best practices",
                "Plan for disaster recovery",
                "Regular cost optimization reviews"
            ],
            "operational_considerations": [
                "24/7 monitoring setup",
                "Automated backup procedures",
                "Scaling policies configuration",
                "Security patch management"
            ],
            "success_metrics": [
                "99.9% uptime target",
                "Sub-second response times",
                "Cost efficiency metrics",
                "Security compliance scores"
            ],
            "fallback_mode": True
        }
    
    def _get_fallback_cost_analysis(self) -> Dict[str, Any]:
        """Get fallback cost analysis when real API calls fail."""
        return {
            "total_monthly_cost": 500,
            "total_annual_cost": 6000,
            "cost_breakdown": {
                "compute": {"monthly_cost": 200, "percentage": 40},
                "storage": {"monthly_cost": 50, "percentage": 10},
                "database": {"monthly_cost": 150, "percentage": 30},
                "networking": {"monthly_cost": 100, "percentage": 20}
            },
            "currency": "USD",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "optimization_opportunities": [
                "Consider reserved instances for 20% savings",
                "Optimize storage tiers for cost reduction",
                "Review instance sizing for right-sizing opportunities"
            ],
            "estimated": True,
            "fallback_mode": True
        }
    
    def _identify_cost_optimizations(self, cost_breakdown: Dict[str, Any]) -> List[str]:
        """Identify cost optimization opportunities from cost breakdown."""
        optimizations = []
        
        for service, cost_data in cost_breakdown.items():
            monthly_cost = cost_data.get("monthly_cost", 0)
            
            if monthly_cost > 200:
                optimizations.append(f"Consider reserved instances for {service} to reduce costs by up to 30%")
            
            if monthly_cost > 100:
                optimizations.append(f"Review {service} sizing and usage patterns for optimization")
            
            if cost_data.get("estimated"):
                optimizations.append(f"Get precise pricing for {service} to better optimize costs")
        
        if not optimizations:
            optimizations.append("Regular cost review and optimization recommended")
        
        return optimizations