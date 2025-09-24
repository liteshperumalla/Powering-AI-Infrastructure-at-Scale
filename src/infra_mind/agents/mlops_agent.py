"""
MLOps Agent for Infra Mind.

Provides ML pipeline optimization expertise, MLOps platform integration,
and CI/CD pipeline recommendations for ML workloads.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base import BaseAgent, AgentConfig, AgentRole
from .tools import ToolResult
from .web_search import get_web_search_client
from ..models.assessment import Assessment
from ..llm.manager import LLMManager

logger = logging.getLogger(__name__)


class MLOpsAgent(BaseAgent):
    """
    MLOps Agent for ML pipeline optimization and deployment strategies.
    
    This agent focuses on:
    - ML pipeline optimization and best practices
    - MLOps platform recommendations and integration
    - CI/CD pipeline design for ML workloads
    - Model deployment and serving strategies
    - ML infrastructure scaling and monitoring
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize MLOps Agent.
        
        Args:
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="MLOps Agent",
                role=AgentRole.MLOPS,
                tools_enabled=["cloud_api", "calculator", "data_processor"],
                temperature=0.2,  # Lower temperature for more consistent technical recommendations
                max_tokens=2500,
                custom_config={
                    "focus_areas": [
                        "ml_pipeline_optimization",
                        "model_deployment",
                        "ci_cd_integration",
                        "mlops_platforms",
                        "monitoring_observability"
                    ],
                    "mlops_platforms": [
                        "kubeflow", "mlflow", "sagemaker", "azure_ml", 
                        "vertex_ai", "databricks", "weights_biases"
                    ],
                    "deployment_strategies": [
                        "batch_inference", "real_time_serving", 
                        "edge_deployment", "serverless_ml"
                    ]
                }
            )
        
        super().__init__(config)
        
        # Initialize client attributes
        self.web_search_client = None
        self.llm_client = None
        
        # MLOps-specific attributes
        self.mlops_platforms = [
            "kubeflow", "mlflow", "sagemaker", "azure_ml", 
            "vertex_ai", "databricks", "weights_biases"
        ]
        
        self.deployment_patterns = [
            "batch_inference", "real_time_serving", 
            "edge_deployment", "serverless_ml", "streaming_ml"
        ]
        
        self.ml_lifecycle_stages = [
            "data_ingestion", "data_preprocessing", "feature_engineering",
            "model_training", "model_validation", "model_deployment",
            "model_monitoring", "model_retraining"
        ]
        
        # MLOps best practices
        self.best_practices = [
            "version_control_for_data_and_models",
            "automated_testing_for_ml_code",
            "continuous_integration_for_ml",
            "model_versioning_and_registry",
            "automated_model_validation",
            "monitoring_and_alerting",
            "reproducible_experiments",
            "feature_store_management"
        ]
        
        logger.info("MLOps Agent initialized with ML pipeline optimization capabilities")
    
    async def _execute_main_logic(self) -> Dict[str, Any]:
        """
        Execute MLOps agent's main pipeline optimization logic.
        
        Returns:
            Dictionary with MLOps recommendations and analysis
        """
        logger.info("MLOps Agent starting ML pipeline analysis")
        
        try:
            # Initialize clients for real data collection
            if not self.web_search_client:
                self.web_search_client = await get_web_search_client()
            if not self.llm_client:
                self.llm_client = LLMManager()
            
            # Step 1: Analyze ML workload requirements with LLM enhancement
            ml_analysis = await self._analyze_ml_requirements_with_llm()
            
            # Step 2: Assess current ML maturity and gaps
            maturity_assessment = await self._assess_ml_maturity()
            
            # Step 3: Recommend MLOps platforms and tools
            platform_recommendations = await self._recommend_mlops_platforms(ml_analysis)
            
            # Step 4: Design CI/CD pipeline for ML
            cicd_design = await self._design_ml_cicd_pipeline(ml_analysis, platform_recommendations)
            
            # Step 5: Create deployment strategy
            deployment_strategy = await self._create_deployment_strategy(ml_analysis)
            
            # Step 6: Generate monitoring and observability plan
            monitoring_plan = await self._create_monitoring_plan(deployment_strategy)
            
            # Step 7: Generate MLOps recommendations
            mlops_recommendations = await self._generate_mlops_recommendations(
                ml_analysis, maturity_assessment, platform_recommendations, 
                cicd_design, deployment_strategy, monitoring_plan
            )
            
            result = {
                "recommendations": mlops_recommendations,
                "data": {
                    "ml_analysis": ml_analysis,
                    "maturity_assessment": maturity_assessment,
                    "platform_recommendations": platform_recommendations,
                    "cicd_design": cicd_design,
                    "deployment_strategy": deployment_strategy,
                    "monitoring_plan": monitoring_plan,
                    "best_practices": self.best_practices,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            logger.info("MLOps Agent completed ML pipeline analysis successfully")
            return result
            
        except Exception as e:
            logger.error(f"MLOps Agent analysis failed: {str(e)}")
            raise
    
    async def _analyze_ml_requirements(self) -> Dict[str, Any]:
        """Analyze ML workload requirements and characteristics."""
        logger.debug("Analyzing ML workload requirements")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        technical_req = assessment_data.get("technical_requirements", {})
        business_req = assessment_data.get("business_requirements", {})
        
        # Use data processing tool to analyze requirements
        analysis_result = await self._use_tool(
            "data_processor",
            data=assessment_data,
            operation="analyze"
        )
        
        # Extract ML-specific information
        workload_types = technical_req.get("workload_types", [])
        ml_workloads = [wl for wl in workload_types if "ml" in wl.lower() or "ai" in wl.lower()]
        
        # Determine ML use cases
        ml_use_cases = self._identify_ml_use_cases(technical_req, business_req)
        
        # Assess data characteristics
        data_characteristics = self._assess_data_characteristics(technical_req)
        
        # Determine model complexity
        model_complexity = self._assess_model_complexity(ml_use_cases, data_characteristics)
        
        # Assess performance requirements
        performance_requirements = self._assess_ml_performance_requirements(technical_req)
        
        return {
            "ml_workloads": ml_workloads,
            "ml_use_cases": ml_use_cases,
            "data_characteristics": data_characteristics,
            "model_complexity": model_complexity,
            "performance_requirements": performance_requirements,
            "expected_users": technical_req.get("expected_users", 1000),
            "data_insights": analysis_result.data if analysis_result.is_success else {},
            "ml_lifecycle_needs": self._assess_lifecycle_needs(ml_use_cases)
        }
    
    async def _assess_ml_maturity(self) -> Dict[str, Any]:
        """Assess current ML maturity level and identify gaps."""
        logger.debug("Assessing ML maturity level")
        
        assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
        business_req = assessment_data.get("business_requirements", {})
        technical_req = assessment_data.get("technical_requirements", {})
        
        # Assess maturity indicators
        maturity_indicators = {
            "data_management": self._assess_data_management_maturity(technical_req),
            "model_development": self._assess_model_development_maturity(technical_req),
            "deployment_automation": self._assess_deployment_maturity(technical_req),
            "monitoring_observability": self._assess_monitoring_maturity(technical_req),
            "governance_compliance": self._assess_governance_maturity(business_req)
        }
        
        # Calculate overall maturity score
        maturity_scores = [indicator["score"] for indicator in maturity_indicators.values()]
        overall_maturity = sum(maturity_scores) / len(maturity_scores) if maturity_scores else 0
        
        # Determine maturity level
        maturity_level = self._categorize_maturity_level(overall_maturity)
        
        # Identify key gaps
        gaps = self._identify_maturity_gaps(maturity_indicators)
        
        return {
            "overall_maturity_score": overall_maturity,
            "maturity_level": maturity_level,
            "maturity_indicators": maturity_indicators,
            "key_gaps": gaps,
            "improvement_priorities": self._prioritize_improvements(gaps)
        }
    
    async def _recommend_mlops_platforms(self, ml_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend MLOps platforms based on requirements."""
        logger.debug("Recommending MLOps platforms")
        
        ml_use_cases = ml_analysis.get("ml_use_cases", [])
        model_complexity = ml_analysis.get("model_complexity", {})
        expected_users = ml_analysis.get("expected_users", 1000)
        
        # Evaluate platforms for different use cases
        platform_evaluations = {}
        
        for platform in self.mlops_platforms:
            evaluation = await self._evaluate_mlops_platform(
                platform, ml_use_cases, model_complexity, expected_users
            )
            platform_evaluations[platform] = evaluation
        
        # Rank platforms
        ranked_platforms = self._rank_mlops_platforms(platform_evaluations)
        
        # Generate platform recommendations
        recommendations = self._generate_platform_recommendations(ranked_platforms, ml_analysis)
        
        return {
            "platform_evaluations": platform_evaluations,
            "ranked_platforms": ranked_platforms,
            "recommendations": recommendations,
            "selection_criteria": [
                "ease_of_use", "scalability", "integration_capabilities",
                "cost_effectiveness", "community_support", "vendor_lock_in_risk"
            ]
        }
    
    async def _design_ml_cicd_pipeline(self, ml_analysis: Dict[str, Any], 
                                      platform_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Design CI/CD pipeline for ML workloads."""
        logger.debug("Designing ML CI/CD pipeline")
        
        ml_use_cases = ml_analysis.get("ml_use_cases", [])
        recommended_platform = platform_recommendations.get("recommendations", [{}])[0].get("platform", "mlflow")
        
        # Design pipeline stages
        pipeline_stages = self._design_pipeline_stages(ml_use_cases, recommended_platform)
        
        # Define automation strategies
        automation_strategies = self._define_automation_strategies(ml_analysis)
        
        # Create testing strategy
        testing_strategy = self._create_ml_testing_strategy(ml_use_cases)
        
        # Design deployment pipeline
        deployment_pipeline = self._design_deployment_pipeline(ml_analysis, recommended_platform)
        
        return {
            "pipeline_stages": pipeline_stages,
            "automation_strategies": automation_strategies,
            "testing_strategy": testing_strategy,
            "deployment_pipeline": deployment_pipeline,
            "recommended_tools": self._recommend_cicd_tools(recommended_platform),
            "implementation_timeline": self._estimate_cicd_implementation_time(pipeline_stages)
        }
    
    async def _create_deployment_strategy(self, ml_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create ML model deployment strategy."""
        logger.debug("Creating ML deployment strategy")
        
        ml_use_cases = ml_analysis.get("ml_use_cases", [])
        performance_req = ml_analysis.get("performance_requirements", {})
        expected_users = ml_analysis.get("expected_users", 1000)
        
        # Determine deployment patterns
        deployment_patterns = self._select_deployment_patterns(ml_use_cases, performance_req, expected_users)
        
        # Design serving infrastructure
        serving_infrastructure = self._design_serving_infrastructure(deployment_patterns, expected_users)
        
        # Create scaling strategy
        scaling_strategy = self._create_ml_scaling_strategy(deployment_patterns, expected_users)
        
        # Design rollout strategy
        rollout_strategy = self._design_rollout_strategy(deployment_patterns)
        
        return {
            "deployment_patterns": deployment_patterns,
            "serving_infrastructure": serving_infrastructure,
            "scaling_strategy": scaling_strategy,
            "rollout_strategy": rollout_strategy,
            "cost_optimization": self._create_deployment_cost_optimization(deployment_patterns)
        }
    
    async def _create_monitoring_plan(self, deployment_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring and observability plan for ML systems."""
        logger.debug("Creating ML monitoring plan")
        
        deployment_patterns = deployment_strategy.get("deployment_patterns", [])
        
        # Define monitoring metrics
        monitoring_metrics = self._define_ml_monitoring_metrics(deployment_patterns)
        
        # Create alerting strategy
        alerting_strategy = self._create_ml_alerting_strategy(monitoring_metrics)
        
        # Design model performance tracking
        performance_tracking = self._design_model_performance_tracking(deployment_patterns)
        
        # Create data drift detection
        drift_detection = self._create_drift_detection_strategy(deployment_patterns)
        
        return {
            "monitoring_metrics": monitoring_metrics,
            "alerting_strategy": alerting_strategy,
            "performance_tracking": performance_tracking,
            "drift_detection": drift_detection,
            "recommended_tools": self._recommend_monitoring_tools(deployment_patterns)
        }
    
    async def _generate_mlops_recommendations(self, ml_analysis: Dict[str, Any],
                                            maturity_assessment: Dict[str, Any],
                                            platform_recommendations: Dict[str, Any],
                                            cicd_design: Dict[str, Any],
                                            deployment_strategy: Dict[str, Any],
                                            monitoring_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate final MLOps recommendations."""
        logger.debug("Generating MLOps recommendations")
        
        recommendations = []
        
        # Platform recommendation
        top_platform = platform_recommendations.get("recommendations", [{}])[0]
        if top_platform:
            recommendations.append({
                "category": "mlops_platform",
                "priority": "high",
                "title": f"Implement {top_platform.get('platform', 'MLOps').title()} Platform",
                "description": f"Deploy {top_platform.get('platform', 'MLOps')} as your primary MLOps platform",
                "rationale": top_platform.get("rationale", "Best fit for your ML requirements"),
                "implementation_steps": top_platform.get("implementation_steps", []),
                "business_impact": "Streamlines ML development and deployment processes",
                "timeline": "4-8 weeks",
                "investment_required": "Medium (platform setup and training)"
            })
        
        # CI/CD Pipeline recommendation
        pipeline_stages = cicd_design.get("pipeline_stages", [])
        if pipeline_stages:
            recommendations.append({
                "category": "cicd_pipeline",
                "priority": "high",
                "title": "Implement ML CI/CD Pipeline",
                "description": "Set up automated CI/CD pipeline for ML model development and deployment",
                "rationale": "Ensures consistent, reliable, and automated ML model deployments",
                "implementation_steps": [
                    "Set up version control for ML code and data",
                    "Implement automated testing for ML models",
                    "Create automated model validation pipeline",
                    "Set up automated deployment to staging and production"
                ],
                "business_impact": "Reduces deployment time and improves model reliability",
                "timeline": "6-10 weeks",
                "investment_required": "Medium (development and tooling)"
            })
        
        # Deployment strategy recommendation
        deployment_patterns = deployment_strategy.get("deployment_patterns", [])
        if deployment_patterns:
            primary_pattern = deployment_patterns[0] if deployment_patterns else {}
            recommendations.append({
                "category": "deployment_strategy",
                "priority": "high",
                "title": f"Implement {primary_pattern.get('pattern', 'Model').title()} Deployment",
                "description": f"Deploy ML models using {primary_pattern.get('pattern', 'recommended')} pattern",
                "rationale": primary_pattern.get("rationale", "Optimal for your use case requirements"),
                "implementation_steps": primary_pattern.get("implementation_steps", []),
                "business_impact": "Enables scalable and reliable ML model serving",
                "timeline": "3-6 weeks",
                "investment_required": "Medium (infrastructure and development)"
            })
        
        # Monitoring recommendation
        monitoring_metrics = monitoring_plan.get("monitoring_metrics", {})
        if monitoring_metrics:
            recommendations.append({
                "category": "monitoring_observability",
                "priority": "medium",
                "title": "Implement ML Model Monitoring",
                "description": "Set up comprehensive monitoring for ML model performance and data quality",
                "rationale": "Essential for maintaining model performance and detecting issues early",
                "implementation_steps": [
                    "Set up model performance metrics tracking",
                    "Implement data drift detection",
                    "Create alerting for model degradation",
                    "Set up automated retraining triggers"
                ],
                "business_impact": "Maintains model accuracy and prevents performance degradation",
                "timeline": "4-6 weeks",
                "investment_required": "Low-Medium (monitoring tools and setup)"
            })
        
        # Maturity improvement recommendations
        maturity_level = maturity_assessment.get("maturity_level", "basic")
        if maturity_level in ["basic", "developing"]:
            key_gaps = maturity_assessment.get("key_gaps", [])
            if key_gaps:
                recommendations.append({
                    "category": "maturity_improvement",
                    "priority": "medium",
                    "title": "Improve MLOps Maturity",
                    "description": f"Address key gaps to advance from {maturity_level} to advanced MLOps maturity",
                    "rationale": "Higher MLOps maturity leads to more reliable and efficient ML operations",
                    "implementation_steps": [
                        f"Address {gap}" for gap in key_gaps[:3]
                    ],
                    "business_impact": "Improves ML development efficiency and model reliability",
                    "timeline": "8-12 weeks",
                    "investment_required": "Medium (process improvement and training)"
                })
        
        return recommendations
    
    # Helper methods
    
    def _identify_ml_use_cases(self, technical_req: Dict[str, Any], 
                              business_req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify ML use cases from requirements."""
        use_cases = []
        
        workload_types = technical_req.get("workload_types", [])
        industry = business_req.get("industry")
        
        # Common ML use cases by workload type
        if "ai_ml" in workload_types or "machine_learning" in workload_types:
            use_cases.append({
                "type": "predictive_analytics",
                "description": "Predictive modeling and analytics",
                "complexity": "medium",
                "data_requirements": "structured_data"
            })
        
        if "data_processing" in workload_types:
            use_cases.append({
                "type": "data_pipeline",
                "description": "Automated data processing and feature engineering",
                "complexity": "low",
                "data_requirements": "batch_data"
            })
        
        # Industry-specific use cases
        if industry == "healthcare":
            use_cases.append({
                "type": "medical_diagnosis",
                "description": "Medical image analysis or diagnostic support",
                "complexity": "high",
                "data_requirements": "image_data"
            })
        elif industry == "finance" or industry == "fintech":
            use_cases.append({
                "type": "fraud_detection",
                "description": "Real-time fraud detection and risk assessment",
                "complexity": "high",
                "data_requirements": "streaming_data"
            })
        elif industry == "retail" or industry == "ecommerce":
            use_cases.append({
                "type": "recommendation_system",
                "description": "Product recommendation and personalization",
                "complexity": "medium",
                "data_requirements": "user_behavior_data"
            })
        
        # Default use case if none identified
        if not use_cases:
            use_cases.append({
                "type": "general_ml",
                "description": "General machine learning applications",
                "complexity": "medium",
                "data_requirements": "structured_data"
            })
        
        return use_cases
    
    def _assess_data_characteristics(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data characteristics for ML workloads."""
        expected_users = technical_req.get("expected_users", 1000)
        
        # Estimate data volume based on users
        if expected_users < 1000:
            data_volume = "small"
            estimated_records = "< 100K"
        elif expected_users < 10000:
            data_volume = "medium"
            estimated_records = "100K - 1M"
        else:
            data_volume = "large"
            estimated_records = "> 1M"
        
        return {
            "volume": data_volume,
            "estimated_records": estimated_records,
            "velocity": "batch" if expected_users < 5000 else "streaming",
            "variety": "structured",  # Default assumption
            "quality_requirements": "high" if expected_users > 10000 else "medium"
        }
    
    def _assess_model_complexity(self, ml_use_cases: List[Dict[str, Any]], 
                                data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess model complexity requirements."""
        complexity_scores = []
        
        for use_case in ml_use_cases:
            complexity = use_case.get("complexity", "medium")
            if complexity == "high":
                complexity_scores.append(3)
            elif complexity == "medium":
                complexity_scores.append(2)
            else:
                complexity_scores.append(1)
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 2
        
        if avg_complexity >= 2.5:
            overall_complexity = "high"
            compute_requirements = "gpu_required"
        elif avg_complexity >= 1.5:
            overall_complexity = "medium"
            compute_requirements = "cpu_intensive"
        else:
            overall_complexity = "low"
            compute_requirements = "cpu_light"
        
        return {
            "overall_complexity": overall_complexity,
            "compute_requirements": compute_requirements,
            "training_time_estimate": self._estimate_training_time(overall_complexity),
            "model_size_estimate": self._estimate_model_size(overall_complexity)
        }
    
    def _assess_ml_performance_requirements(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess ML performance requirements."""
        expected_users = technical_req.get("expected_users", 1000)
        performance_req = technical_req.get("performance_requirements", {})
        
        # Infer latency requirements
        if expected_users > 10000:
            latency_requirement = "low"  # < 100ms
            throughput_requirement = "high"  # > 1000 requests/sec
        elif expected_users > 1000:
            latency_requirement = "medium"  # < 500ms
            throughput_requirement = "medium"  # 100-1000 requests/sec
        else:
            latency_requirement = "high"  # < 1s
            throughput_requirement = "low"  # < 100 requests/sec
        
        return {
            "latency_requirement": latency_requirement,
            "throughput_requirement": throughput_requirement,
            "availability_requirement": "99.9%" if expected_users > 5000 else "99%",
            "scalability_requirement": "auto_scaling" if expected_users > 1000 else "manual_scaling"
        }
    
    def _assess_lifecycle_needs(self, ml_use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess ML lifecycle stage needs."""
        needs = {}
        
        for stage in self.ml_lifecycle_stages:
            if stage == "data_ingestion":
                needs[stage] = {"priority": "high", "automation_level": "medium"}
            elif stage == "model_training":
                needs[stage] = {"priority": "high", "automation_level": "high"}
            elif stage == "model_deployment":
                needs[stage] = {"priority": "high", "automation_level": "high"}
            elif stage == "model_monitoring":
                needs[stage] = {"priority": "medium", "automation_level": "medium"}
            else:
                needs[stage] = {"priority": "medium", "automation_level": "low"}
        
        return needs
    
    def _assess_data_management_maturity(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data management maturity."""
        # Simple assessment based on available information
        score = 0.3  # Basic assumption
        
        gaps = [
            "Implement data versioning",
            "Set up data quality monitoring",
            "Create feature store"
        ]
        
        return {
            "score": score,
            "level": "developing",
            "gaps": gaps
        }
    
    def _assess_model_development_maturity(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess model development maturity."""
        score = 0.4  # Basic assumption
        
        gaps = [
            "Implement experiment tracking",
            "Set up model versioning",
            "Create automated model validation"
        ]
        
        return {
            "score": score,
            "level": "developing",
            "gaps": gaps
        }
    
    def _assess_deployment_maturity(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess deployment maturity."""
        score = 0.2  # Basic assumption
        
        gaps = [
            "Implement automated deployment",
            "Set up blue-green deployments",
            "Create rollback mechanisms"
        ]
        
        return {
            "score": score,
            "level": "basic",
            "gaps": gaps
        }
    
    def _assess_monitoring_maturity(self, technical_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess monitoring maturity."""
        score = 0.3  # Basic assumption
        
        gaps = [
            "Implement model performance monitoring",
            "Set up data drift detection",
            "Create automated alerting"
        ]
        
        return {
            "score": score,
            "level": "developing",
            "gaps": gaps
        }
    
    def _assess_governance_maturity(self, business_req: Dict[str, Any]) -> Dict[str, Any]:
        """Assess governance maturity."""
        score = 0.4  # Basic assumption
        
        gaps = [
            "Implement model governance policies",
            "Set up compliance tracking",
            "Create audit trails"
        ]
        
        return {
            "score": score,
            "level": "developing",
            "gaps": gaps
        }
    
    def _categorize_maturity_level(self, score: float) -> str:
        """Categorize maturity level based on score."""
        if score >= 0.8:
            return "advanced"
        elif score >= 0.6:
            return "intermediate"
        elif score >= 0.4:
            return "developing"
        else:
            return "basic"
    
    def _identify_maturity_gaps(self, maturity_indicators: Dict[str, Any]) -> List[str]:
        """Identify key maturity gaps."""
        all_gaps = []
        
        for indicator, data in maturity_indicators.items():
            gaps = data.get("gaps", [])
            all_gaps.extend(gaps)
        
        # Return top 5 gaps
        return all_gaps[:5]
    
    def _prioritize_improvements(self, gaps: List[str]) -> List[Dict[str, Any]]:
        """Prioritize improvement areas."""
        priorities = []
        
        for i, gap in enumerate(gaps[:3]):  # Top 3 priorities
            priority = "high" if i == 0 else "medium" if i == 1 else "low"
            priorities.append({
                "gap": gap,
                "priority": priority,
                "estimated_effort": "medium"
            })
        
        return priorities
    
    async def _evaluate_mlops_platform(self, platform: str, ml_use_cases: List[Dict[str, Any]],
                                      model_complexity: Dict[str, Any], expected_users: int) -> Dict[str, Any]:
        """Evaluate a specific MLOps platform."""
        # Platform characteristics (simplified)
        platform_info = {
            "kubeflow": {
                "ease_of_use": 0.6,
                "scalability": 0.9,
                "cost": 0.7,
                "integration": 0.8,
                "description": "Open-source ML platform for Kubernetes"
            },
            "mlflow": {
                "ease_of_use": 0.8,
                "scalability": 0.7,
                "cost": 0.9,
                "integration": 0.8,
                "description": "Open-source ML lifecycle management"
            },
            "sagemaker": {
                "ease_of_use": 0.9,
                "scalability": 0.9,
                "cost": 0.6,
                "integration": 0.7,
                "description": "AWS managed ML service"
            },
            "azure_ml": {
                "ease_of_use": 0.8,
                "scalability": 0.8,
                "cost": 0.7,
                "integration": 0.8,
                "description": "Azure Machine Learning service"
            },
            "vertex_ai": {
                "ease_of_use": 0.8,
                "scalability": 0.9,
                "cost": 0.7,
                "integration": 0.7,
                "description": "Google Cloud ML platform"
            }
        }
        
        info = platform_info.get(platform, {
            "ease_of_use": 0.5,
            "scalability": 0.5,
            "cost": 0.5,
            "integration": 0.5,
            "description": f"{platform} MLOps platform"
        })
        
        # Calculate suitability score
        score = (
            info["ease_of_use"] * 0.3 +
            info["scalability"] * 0.3 +
            info["cost"] * 0.2 +
            info["integration"] * 0.2
        )
        
        return {
            "platform": platform,
            "suitability_score": score,
            "characteristics": info,
            "pros": self._get_platform_pros(platform),
            "cons": self._get_platform_cons(platform)
        }
    
    def _get_platform_pros(self, platform: str) -> List[str]:
        """Get platform advantages."""
        pros_map = {
            "kubeflow": ["Highly scalable", "Kubernetes native", "Open source"],
            "mlflow": ["Easy to use", "Language agnostic", "Open source"],
            "sagemaker": ["Fully managed", "AWS integration", "Auto-scaling"],
            "azure_ml": ["Azure integration", "Enterprise features", "Hybrid cloud"],
            "vertex_ai": ["Google Cloud integration", "AutoML capabilities", "Scalable"]
        }
        return pros_map.get(platform, ["Platform specific advantages"])
    
    def _get_platform_cons(self, platform: str) -> List[str]:
        """Get platform disadvantages."""
        cons_map = {
            "kubeflow": ["Complex setup", "Requires Kubernetes expertise"],
            "mlflow": ["Limited managed services", "Requires infrastructure setup"],
            "sagemaker": ["AWS vendor lock-in", "Can be expensive"],
            "azure_ml": ["Azure vendor lock-in", "Learning curve"],
            "vertex_ai": ["GCP vendor lock-in", "Limited customization"]
        }
        return cons_map.get(platform, ["Platform specific limitations"])
    
    def _rank_mlops_platforms(self, evaluations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank MLOps platforms by suitability."""
        ranked = sorted(
            evaluations.values(),
            key=lambda x: x["suitability_score"],
            reverse=True
        )
        return ranked
    
    def _generate_platform_recommendations(self, ranked_platforms: List[Dict[str, Any]],
                                         ml_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate platform recommendations."""
        recommendations = []
        
        for i, platform in enumerate(ranked_platforms[:3]):  # Top 3 platforms
            recommendation = {
                "rank": i + 1,
                "platform": platform["platform"],
                "suitability_score": platform["suitability_score"],
                "rationale": f"Scored {platform['suitability_score']:.2f} based on ease of use, scalability, and cost",
                "implementation_steps": [
                    f"Set up {platform['platform']} environment",
                    "Configure ML pipeline templates",
                    "Integrate with existing infrastructure",
                    "Train team on platform usage"
                ],
                "pros": platform.get("pros", []),
                "cons": platform.get("cons", [])
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _design_pipeline_stages(self, ml_use_cases: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Design ML pipeline stages."""
        stages = [
            {
                "stage": "data_validation",
                "description": "Validate input data quality and schema",
                "tools": ["great_expectations", "tensorflow_data_validation"],
                "automation_level": "high"
            },
            {
                "stage": "feature_engineering",
                "description": "Transform raw data into ML features",
                "tools": ["pandas", "scikit_learn", "feature_store"],
                "automation_level": "medium"
            },
            {
                "stage": "model_training",
                "description": "Train ML models with hyperparameter tuning",
                "tools": [platform, "optuna", "ray_tune"],
                "automation_level": "high"
            },
            {
                "stage": "model_validation",
                "description": "Validate model performance and quality",
                "tools": ["mlflow", "model_validator", "fairness_indicators"],
                "automation_level": "high"
            },
            {
                "stage": "model_deployment",
                "description": "Deploy validated models to production",
                "tools": ["kubernetes", "docker", "model_server"],
                "automation_level": "high"
            }
        ]
        
        return stages
    
    def _define_automation_strategies(self, ml_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Define automation strategies for ML pipeline."""
        return {
            "trigger_strategies": [
                "scheduled_retraining",
                "data_drift_detection",
                "performance_degradation"
            ],
            "testing_automation": [
                "unit_tests_for_ml_code",
                "integration_tests_for_pipeline",
                "model_performance_tests"
            ],
            "deployment_automation": [
                "automated_staging_deployment",
                "canary_deployments",
                "blue_green_deployments"
            ]
        }
    
    def _create_ml_testing_strategy(self, ml_use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create testing strategy for ML systems."""
        return {
            "data_testing": [
                "Schema validation",
                "Data quality checks",
                "Data drift detection"
            ],
            "model_testing": [
                "Model performance validation",
                "Bias and fairness testing",
                "Model explainability tests"
            ],
            "integration_testing": [
                "End-to-end pipeline testing",
                "API integration testing",
                "Load testing for model serving"
            ],
            "recommended_tools": [
                "pytest", "great_expectations", "deepchecks", "evidently"
            ]
        }
    
    def _design_deployment_pipeline(self, ml_analysis: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Design deployment pipeline for ML models."""
        return {
            "stages": [
                {
                    "name": "staging_deployment",
                    "description": "Deploy to staging environment for testing",
                    "validation_steps": ["smoke_tests", "integration_tests"]
                },
                {
                    "name": "canary_deployment",
                    "description": "Deploy to small subset of production traffic",
                    "validation_steps": ["performance_monitoring", "error_rate_monitoring"]
                },
                {
                    "name": "full_deployment",
                    "description": "Deploy to full production traffic",
                    "validation_steps": ["comprehensive_monitoring", "rollback_readiness"]
                }
            ],
            "rollback_strategy": {
                "trigger_conditions": ["error_rate_spike", "performance_degradation"],
                "rollback_time": "< 5 minutes",
                "validation_steps": ["health_checks", "traffic_validation"]
            }
        }
    
    def _recommend_cicd_tools(self, platform: str) -> List[Dict[str, Any]]:
        """Recommend CI/CD tools for ML platform."""
        return [
            {
                "category": "version_control",
                "tools": ["git", "dvc", "git_lfs"],
                "purpose": "Version control for code, data, and models"
            },
            {
                "category": "ci_cd",
                "tools": ["github_actions", "jenkins", "gitlab_ci"],
                "purpose": "Continuous integration and deployment"
            },
            {
                "category": "containerization",
                "tools": ["docker", "kubernetes", "helm"],
                "purpose": "Containerization and orchestration"
            },
            {
                "category": "monitoring",
                "tools": ["prometheus", "grafana", "datadog"],
                "purpose": "System and model monitoring"
            }
        ]
    
    def _estimate_cicd_implementation_time(self, pipeline_stages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate CI/CD implementation timeline."""
        base_time = len(pipeline_stages) * 2  # 2 weeks per stage
        
        return {
            "total_weeks": base_time,
            "phases": [
                {"phase": "setup_and_planning", "weeks": 2},
                {"phase": "pipeline_development", "weeks": base_time - 4},
                {"phase": "testing_and_validation", "weeks": 2}
            ]
        }
    
    def _select_deployment_patterns(self, ml_use_cases: List[Dict[str, Any]],
                                   performance_req: Dict[str, Any], expected_users: int) -> List[Dict[str, Any]]:
        """Select appropriate deployment patterns."""
        patterns = []
        
        latency_req = performance_req.get("latency_requirement", "medium")
        
        if latency_req == "low" or expected_users > 10000:
            patterns.append({
                "pattern": "real_time_serving",
                "description": "Low-latency real-time model serving",
                "use_case": "Interactive applications requiring immediate responses",
                "infrastructure": ["model_server", "load_balancer", "caching"],
                "rationale": "Required for low-latency, high-throughput applications"
            })
        
        if any(uc.get("data_requirements") == "batch_data" for uc in ml_use_cases):
            patterns.append({
                "pattern": "batch_inference",
                "description": "Scheduled batch processing of predictions",
                "use_case": "Periodic processing of large datasets",
                "infrastructure": ["batch_processor", "data_pipeline", "storage"],
                "rationale": "Efficient for processing large volumes of data periodically"
            })
        
        if expected_users < 1000:
            patterns.append({
                "pattern": "serverless_ml",
                "description": "Serverless model deployment for variable workloads",
                "use_case": "Variable or unpredictable traffic patterns",
                "infrastructure": ["serverless_functions", "api_gateway", "auto_scaling"],
                "rationale": "Cost-effective for variable or low-volume workloads"
            })
        
        return patterns or [{
            "pattern": "real_time_serving",
            "description": "Standard real-time model serving",
            "use_case": "General purpose model serving",
            "infrastructure": ["model_server", "api_gateway"],
            "rationale": "Standard deployment pattern for most use cases"
        }]
    
    def _design_serving_infrastructure(self, deployment_patterns: List[Dict[str, Any]], 
                                     expected_users: int) -> Dict[str, Any]:
        """Design serving infrastructure for ML models."""
        primary_pattern = deployment_patterns[0] if deployment_patterns else {}
        
        if primary_pattern.get("pattern") == "real_time_serving":
            infrastructure = {
                "compute": {
                    "type": "container_based",
                    "scaling": "horizontal_auto_scaling",
                    "resources": self._calculate_serving_resources(expected_users)
                },
                "networking": {
                    "load_balancer": True,
                    "api_gateway": True,
                    "cdn": expected_users > 5000
                },
                "storage": {
                    "model_storage": "object_storage",
                    "cache": "redis" if expected_users > 1000 else "in_memory"
                }
            }
        else:
            infrastructure = {
                "compute": {
                    "type": "batch_processing",
                    "scaling": "scheduled_scaling",
                    "resources": {"cpu": "4 cores", "memory": "16GB"}
                },
                "storage": {
                    "input_data": "data_lake",
                    "output_data": "data_warehouse",
                    "model_storage": "object_storage"
                }
            }
        
        return infrastructure
    
    def _calculate_serving_resources(self, expected_users: int) -> Dict[str, Any]:
        """Calculate serving resource requirements."""
        if expected_users < 1000:
            return {"cpu": "2 cores", "memory": "4GB", "replicas": 2}
        elif expected_users < 10000:
            return {"cpu": "4 cores", "memory": "8GB", "replicas": 3}
        else:
            return {"cpu": "8 cores", "memory": "16GB", "replicas": 5}
    
    def _create_ml_scaling_strategy(self, deployment_patterns: List[Dict[str, Any]], 
                                   expected_users: int) -> Dict[str, Any]:
        """Create scaling strategy for ML deployments."""
        return {
            "horizontal_scaling": {
                "enabled": expected_users > 1000,
                "min_replicas": 2,
                "max_replicas": 10,
                "target_cpu_utilization": 70
            },
            "vertical_scaling": {
                "enabled": True,
                "resource_limits": {
                    "cpu": "8 cores",
                    "memory": "32GB"
                }
            },
            "auto_scaling_triggers": [
                "cpu_utilization > 70%",
                "memory_utilization > 80%",
                "request_latency > 500ms"
            ]
        }
    
    def _design_rollout_strategy(self, deployment_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Design rollout strategy for ML deployments."""
        return {
            "strategy": "blue_green",
            "phases": [
                {
                    "phase": "canary",
                    "traffic_percentage": 5,
                    "duration": "30 minutes",
                    "success_criteria": ["error_rate < 1%", "latency < 200ms"]
                },
                {
                    "phase": "gradual_rollout",
                    "traffic_percentage": 50,
                    "duration": "2 hours",
                    "success_criteria": ["error_rate < 0.5%", "latency < 150ms"]
                },
                {
                    "phase": "full_rollout",
                    "traffic_percentage": 100,
                    "duration": "ongoing",
                    "success_criteria": ["system_stability"]
                }
            ]
        }
    
    def _create_deployment_cost_optimization(self, deployment_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create cost optimization strategies for deployments."""
        return {
            "strategies": [
                {
                    "strategy": "right_sizing",
                    "description": "Optimize resource allocation based on actual usage",
                    "potential_savings": "20-30%"
                },
                {
                    "strategy": "spot_instances",
                    "description": "Use spot instances for batch processing workloads",
                    "potential_savings": "50-70%"
                },
                {
                    "strategy": "auto_scaling",
                    "description": "Scale resources based on demand",
                    "potential_savings": "30-40%"
                }
            ],
            "monitoring_metrics": [
                "cost_per_prediction",
                "resource_utilization",
                "idle_time_percentage"
            ]
        }
    
    def _define_ml_monitoring_metrics(self, deployment_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Define monitoring metrics for ML systems."""
        return {
            "model_performance": [
                "prediction_accuracy",
                "precision_recall",
                "f1_score",
                "auc_roc"
            ],
            "system_performance": [
                "prediction_latency",
                "throughput_rps",
                "error_rate",
                "availability"
            ],
            "data_quality": [
                "data_drift_score",
                "feature_distribution_shift",
                "missing_values_percentage",
                "outlier_detection"
            ],
            "business_metrics": [
                "prediction_volume",
                "user_satisfaction",
                "business_impact",
                "cost_per_prediction"
            ]
        }
    
    def _create_ml_alerting_strategy(self, monitoring_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create alerting strategy for ML systems."""
        return {
            "critical_alerts": [
                {
                    "metric": "model_accuracy",
                    "threshold": "< 85%",
                    "action": "immediate_investigation"
                },
                {
                    "metric": "prediction_latency",
                    "threshold": "> 1000ms",
                    "action": "scale_up_resources"
                },
                {
                    "metric": "error_rate",
                    "threshold": "> 5%",
                    "action": "rollback_deployment"
                }
            ],
            "warning_alerts": [
                {
                    "metric": "data_drift_score",
                    "threshold": "> 0.3",
                    "action": "schedule_retraining"
                },
                {
                    "metric": "resource_utilization",
                    "threshold": "> 80%",
                    "action": "consider_scaling"
                }
            ]
        }
    
    def _design_model_performance_tracking(self, deployment_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Design model performance tracking system."""
        return {
            "tracking_methods": [
                "online_evaluation",
                "offline_evaluation",
                "a_b_testing"
            ],
            "evaluation_frequency": {
                "real_time_metrics": "continuous",
                "batch_evaluation": "daily",
                "comprehensive_review": "weekly"
            },
            "performance_baselines": {
                "accuracy_baseline": "90%",
                "latency_baseline": "100ms",
                "throughput_baseline": "1000 rps"
            }
        }
    
    def _create_drift_detection_strategy(self, deployment_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create data drift detection strategy."""
        return {
            "drift_types": [
                "feature_drift",
                "label_drift",
                "concept_drift"
            ],
            "detection_methods": [
                "statistical_tests",
                "distribution_comparison",
                "model_performance_degradation"
            ],
            "detection_frequency": "daily",
            "response_actions": [
                "alert_ml_team",
                "trigger_retraining",
                "update_feature_pipeline"
            ]
        }
    
    def _recommend_monitoring_tools(self, deployment_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recommend monitoring tools for ML systems."""
        return [
            {
                "category": "model_monitoring",
                "tools": ["evidently", "whylabs", "arize"],
                "purpose": "Monitor model performance and data drift"
            },
            {
                "category": "system_monitoring",
                "tools": ["prometheus", "grafana", "datadog"],
                "purpose": "Monitor system performance and infrastructure"
            },
            {
                "category": "logging",
                "tools": ["elasticsearch", "fluentd", "kibana"],
                "purpose": "Centralized logging and log analysis"
            },
            {
                "category": "alerting",
                "tools": ["pagerduty", "slack", "email"],
                "purpose": "Alert notification and escalation"
            }
        ]
    
    def _estimate_training_time(self, complexity: str) -> str:
        """Estimate model training time based on complexity."""
        if complexity == "high":
            return "4-12 hours"
        elif complexity == "medium":
            return "1-4 hours"
        else:
            return "< 1 hour"
    
    def _estimate_model_size(self, complexity: str) -> str:
        """Estimate model size based on complexity."""
        if complexity == "high":
            return "> 1GB"
        elif complexity == "medium":
            return "100MB - 1GB"
        else:
            return "< 100MB"
    
    async def _analyze_ml_requirements_with_llm(self) -> Dict[str, Any]:
        """
        Analyze ML requirements using LLM analysis and real MLOps research.
        
        Returns:
            Dictionary containing enhanced ML analysis
        """
        try:
            # Get base analysis first
            base_analysis = await self._analyze_ml_requirements()
            
            assessment_data = self.current_assessment.model_dump() if self.current_assessment else {}
            technical_req = assessment_data.get("technical_requirements", {})
            business_req = assessment_data.get("business_requirements", {})
            
            # Research latest MLOps trends and tools
            mlops_trends = await self.web_search_client.search(
                "MLOps trends 2024 2025 machine learning operations best practices tools platforms",
                max_results=5
            )
            
            # Prepare context for LLM analysis
            mlops_context = f"""
            BUSINESS AND ML CONTEXT:
            - Industry: {business_req.get('industry', 'Not specified')}
            - Data Types: {technical_req.get('data_types', [])}
            - Workload Types: {technical_req.get('workload_types', [])}
            - Expected Users: {technical_req.get('expected_users', 'Not specified')}
            - Performance Requirements: {technical_req.get('performance_requirements', {})}
            - Budget Constraints: {business_req.get('budget_range', 'Not specified')}
            - Existing Infrastructure: {technical_req.get('existing_infrastructure', 'None specified')}
            - Team Size: {business_req.get('team_size', 'Not specified')}
            
            CURRENT MLOPS TRENDS (2024-2025):
            """
            
            for result in mlops_trends.get("results", [])[:3]:
                mlops_context += f"- {result.get('title')}: {result.get('snippet')[:200]}...\n"
            
            analysis_prompt = f"""
            Analyze ML/AI requirements and provide comprehensive MLOps recommendations:
            
            {mlops_context}
            
            Based on this information, provide detailed analysis:
            1. ML workload classification and requirements
            2. Recommended MLOps platform architecture
            3. CI/CD pipeline design for ML workflows
            4. Model deployment and serving strategies
            5. Data pipeline and feature store requirements  
            6. Model monitoring and observability needs
            7. Team workflow and collaboration tools
            8. Scalability and performance optimization
            9. Cost optimization strategies for ML infrastructure
            10. Risk mitigation and ML governance
            
            Consider modern MLOps practices including:
            - Model versioning and experiment tracking
            - Automated testing for ML pipelines
            - Feature stores and data versioning
            - Model drift detection and retraining
            - A/B testing for models
            - Explainability and compliance
            
            Return in JSON format with: workload_classification, platform_architecture, cicd_design, deployment_strategy, data_pipeline, monitoring_strategy, collaboration_tools, scalability_plan, cost_optimization, governance_framework.
            """
            
            llm_response = await self._call_llm(
                prompt=analysis_prompt,
                system_prompt="You are an MLOps expert with deep knowledge of machine learning operations, data engineering, and ML infrastructure at scale.",
                temperature=0.1,
                max_tokens=2500
            )
            
            llm_analysis = self._parse_llm_response(llm_response)
            
            # Enhance base analysis with LLM insights
            enhanced_analysis = {
                **base_analysis,
                "workload_classification": llm_analysis.get("workload_classification", {}),
                "platform_architecture": llm_analysis.get("platform_architecture", {}),
                "cicd_design": llm_analysis.get("cicd_design", {}),
                "deployment_strategy": llm_analysis.get("deployment_strategy", {}),
                "data_pipeline": llm_analysis.get("data_pipeline", {}),
                "monitoring_strategy": llm_analysis.get("monitoring_strategy", {}),
                "collaboration_tools": llm_analysis.get("collaboration_tools", {}),
                "scalability_plan": llm_analysis.get("scalability_plan", {}),
                "cost_optimization": llm_analysis.get("cost_optimization", {}),
                "governance_framework": llm_analysis.get("governance_framework", {}),
                "mlops_trends": mlops_trends.get("results", []),
                "llm_insights": llm_analysis.get("analysis"),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.warning(f"LLM-enhanced ML requirements analysis failed: {str(e)}")
            return await self._analyze_ml_requirements()
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response, handling both JSON and text formats with robust error handling."""
        import json
        import re
        
        try:
            # Clean the response
            response = response.strip()
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            # Try to parse as JSON first
            result = json.loads(response)
            
            # Validate result is a dictionary
            if not isinstance(result, dict):
                return {
                    "analysis": str(response),
                    "extracted_points": self._extract_key_points_from_text(str(response))
                }
                
            return result
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fallback to extracting structured information from text
            return {
                "analysis": response,
                "extracted_points": self._extract_key_points_from_text(response)
            }
    
    def _extract_key_points_from_text(self, text: str) -> List[str]:
        """Extract key points from text when JSON parsing fails."""
        points = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*'))):
                points.append(line)
        return points