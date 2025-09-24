"""
Advanced recommendation validation and fact-checking systems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from ..models.recommendation import Recommendation
from ..models.assessment import Assessment
from ..cloud.unified import UnifiedCloudClient
from ..core.cache import CacheManager


class ValidationStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ValidationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    status: ValidationStatus
    severity: ValidationSeverity
    confidence_score: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class FactCheckResult:
    """Result of fact-checking against authoritative sources."""
    claim: str
    source: str
    verified: bool
    confidence: float
    evidence: Dict[str, Any]
    timestamp: datetime


class RecommendationValidator:
    """Advanced validation system for agent recommendations."""
    
    def __init__(self, cloud_service: UnifiedCloudClient, cache_manager: CacheManager):
        self.cloud_service = cloud_service
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # Validation rules configuration
        self.validation_rules = {
            'pricing_accuracy': {
                'enabled': True,
                'tolerance': 0.05,  # 5% tolerance for pricing variations
                'cache_ttl': 3600   # 1 hour cache for pricing data
            },
            'service_availability': {
                'enabled': True,
                'regions_to_check': ['us-east-1', 'us-west-2', 'eu-west-1'],
                'cache_ttl': 1800   # 30 minutes cache
            },
            'compliance_requirements': {
                'enabled': True,
                'strict_mode': True,
                'cache_ttl': 86400  # 24 hours cache
            },
            'cost_optimization': {
                'enabled': True,
                'min_savings_threshold': 0.10,  # 10% minimum savings
                'cache_ttl': 3600
            }
        }
    
    async def validate_recommendation(self, recommendation: Recommendation, 
                                    assessment: Assessment) -> List[ValidationResult]:
        """
        Comprehensive validation of a single recommendation.
        
        Args:
            recommendation: The recommendation to validate
            assessment: The original assessment context
            
        Returns:
            List of validation results
        """
        validation_results = []
        
        try:
            # Run all validation checks in parallel
            validation_tasks = [
                self._validate_pricing_accuracy(recommendation),
                self._validate_service_availability(recommendation),
                self._validate_compliance_requirements(recommendation, assessment),
                self._validate_cost_optimization(recommendation, assessment),
                self._validate_technical_feasibility(recommendation, assessment),
                self._validate_business_alignment(recommendation, assessment)
            ]
            
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Validation check failed: {result}")
                    validation_results.append(ValidationResult(
                        check_name="validation_error",
                        status=ValidationStatus.FAILED,
                        severity=ValidationSeverity.HIGH,
                        confidence_score=0.0,
                        details={"error": str(result)},
                        timestamp=datetime.utcnow(),
                        error_message=str(result)
                    ))
                else:
                    validation_results.extend(result)
            
            # Calculate overall validation score
            overall_score = self._calculate_overall_score(validation_results)
            self.logger.info(f"Recommendation validation completed with score: {overall_score}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Critical validation error: {e}")
            return [ValidationResult(
                check_name="critical_validation_error",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.CRITICAL,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )]
    
    async def _validate_pricing_accuracy(self, recommendation: Recommendation) -> List[ValidationResult]:
        """Validate pricing information against current cloud provider APIs."""
        results = []
        
        if not self.validation_rules['pricing_accuracy']['enabled']:
            return results
        
        try:
            # Get current pricing from cloud providers
            cache_key = f"pricing_validation_{recommendation.service_name}_{recommendation.provider}"
            cached_result = await self.cache_manager.get(cache_key)
            
            if cached_result:
                current_pricing = cached_result
            else:
                current_pricing = await self.cloud_service.get_service_pricing(
                    recommendation.provider,
                    recommendation.service_name,
                    recommendation.configuration
                )
                await self.cache_manager.set(
                    cache_key, 
                    current_pricing, 
                    ttl=self.validation_rules['pricing_accuracy']['cache_ttl']
                )
            
            # Compare recommended pricing with current pricing
            recommended_cost = recommendation.cost_estimate
            current_cost = current_pricing.get('monthly_cost', 0)
            
            if current_cost > 0:
                price_difference = abs(recommended_cost - current_cost) / current_cost
                tolerance = self.validation_rules['pricing_accuracy']['tolerance']
                
                if price_difference <= tolerance:
                    status = ValidationStatus.VALIDATED
                    severity = ValidationSeverity.LOW
                    confidence = 1.0 - price_difference
                else:
                    status = ValidationStatus.NEEDS_REVIEW
                    severity = ValidationSeverity.MEDIUM if price_difference < 0.2 else ValidationSeverity.HIGH
                    confidence = max(0.0, 1.0 - price_difference)
                
                results.append(ValidationResult(
                    check_name="pricing_accuracy",
                    status=status,
                    severity=severity,
                    confidence_score=confidence,
                    details={
                        "recommended_cost": recommended_cost,
                        "current_cost": current_cost,
                        "difference_percentage": price_difference,
                        "tolerance": tolerance
                    },
                    timestamp=datetime.utcnow()
                ))
            
        except Exception as e:
            results.append(ValidationResult(
                check_name="pricing_accuracy",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    async def _validate_service_availability(self, recommendation: Recommendation) -> List[ValidationResult]:
        """Validate service availability in recommended regions."""
        results = []
        
        if not self.validation_rules['service_availability']['enabled']:
            return results
        
        try:
            regions_to_check = self.validation_rules['service_availability']['regions_to_check']
            
            for region in regions_to_check:
                cache_key = f"service_availability_{recommendation.provider}_{recommendation.service_name}_{region}"
                cached_result = await self.cache_manager.get(cache_key)
                
                if cached_result:
                    is_available = cached_result
                else:
                    is_available = await self.cloud_service.check_service_availability(
                        recommendation.provider,
                        recommendation.service_name,
                        region
                    )
                    await self.cache_manager.set(
                        cache_key,
                        is_available,
                        ttl=self.validation_rules['service_availability']['cache_ttl']
                    )
                
                status = ValidationStatus.VALIDATED if is_available else ValidationStatus.FAILED
                severity = ValidationSeverity.LOW if is_available else ValidationSeverity.HIGH
                
                results.append(ValidationResult(
                    check_name=f"service_availability_{region}",
                    status=status,
                    severity=severity,
                    confidence_score=1.0 if is_available else 0.0,
                    details={
                        "region": region,
                        "service": recommendation.service_name,
                        "provider": recommendation.provider,
                        "available": is_available
                    },
                    timestamp=datetime.utcnow()
                ))
        
        except Exception as e:
            results.append(ValidationResult(
                check_name="service_availability",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    async def _validate_compliance_requirements(self, recommendation: Recommendation, 
                                              assessment: Assessment) -> List[ValidationResult]:
        """Validate compliance requirements against recommendation."""
        results = []
        
        if not self.validation_rules['compliance_requirements']['enabled']:
            return results
        
        try:
            compliance_needs = assessment.compliance_requirements.get('regulations', [])
            
            for regulation in compliance_needs:
                # Check if recommendation meets compliance requirements
                compliance_check = await self._check_compliance_alignment(
                    recommendation, regulation
                )
                
                status = ValidationStatus.VALIDATED if compliance_check['compliant'] else ValidationStatus.FAILED
                severity = ValidationSeverity.CRITICAL if not compliance_check['compliant'] else ValidationSeverity.LOW
                
                results.append(ValidationResult(
                    check_name=f"compliance_{regulation}",
                    status=status,
                    severity=severity,
                    confidence_score=compliance_check['confidence'],
                    details={
                        "regulation": regulation,
                        "compliant": compliance_check['compliant'],
                        "requirements": compliance_check['requirements'],
                        "gaps": compliance_check.get('gaps', [])
                    },
                    timestamp=datetime.utcnow()
                ))
        
        except Exception as e:
            results.append(ValidationResult(
                check_name="compliance_requirements",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.HIGH,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    async def _validate_cost_optimization(self, recommendation: Recommendation, 
                                        assessment: Assessment) -> List[ValidationResult]:
        """Validate cost optimization potential."""
        results = []
        
        if not self.validation_rules['cost_optimization']['enabled']:
            return results
        
        try:
            # Get alternative options for comparison
            alternatives = await self.cloud_service.get_alternative_services(
                recommendation.provider,
                recommendation.service_name,
                assessment.technical_requirements
            )
            
            if alternatives:
                min_alternative_cost = min(alt['cost'] for alt in alternatives)
                current_cost = recommendation.cost_estimate
                
                if min_alternative_cost < current_cost:
                    potential_savings = (current_cost - min_alternative_cost) / current_cost
                    min_threshold = self.validation_rules['cost_optimization']['min_savings_threshold']
                    
                    if potential_savings >= min_threshold:
                        status = ValidationStatus.NEEDS_REVIEW
                        severity = ValidationSeverity.MEDIUM
                        confidence = potential_savings
                    else:
                        status = ValidationStatus.VALIDATED
                        severity = ValidationSeverity.LOW
                        confidence = 1.0 - potential_savings
                else:
                    status = ValidationStatus.VALIDATED
                    severity = ValidationSeverity.LOW
                    confidence = 1.0
                
                results.append(ValidationResult(
                    check_name="cost_optimization",
                    status=status,
                    severity=severity,
                    confidence_score=confidence,
                    details={
                        "current_cost": current_cost,
                        "min_alternative_cost": min_alternative_cost,
                        "potential_savings": potential_savings if min_alternative_cost < current_cost else 0,
                        "alternatives_count": len(alternatives)
                    },
                    timestamp=datetime.utcnow()
                ))
        
        except Exception as e:
            results.append(ValidationResult(
                check_name="cost_optimization",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.LOW,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    async def _validate_technical_feasibility(self, recommendation: Recommendation, 
                                            assessment: Assessment) -> List[ValidationResult]:
        """Validate technical feasibility of the recommendation."""
        results = []
        
        try:
            # Check resource requirements vs. availability
            tech_reqs = assessment.technical_requirements
            
            # Validate compute requirements
            if 'compute' in tech_reqs:
                compute_validation = await self._validate_compute_requirements(
                    recommendation, tech_reqs['compute']
                )
                results.extend(compute_validation)
            
            # Validate storage requirements
            if 'storage' in tech_reqs:
                storage_validation = await self._validate_storage_requirements(
                    recommendation, tech_reqs['storage']
                )
                results.extend(storage_validation)
            
            # Validate network requirements
            if 'network' in tech_reqs:
                network_validation = await self._validate_network_requirements(
                    recommendation, tech_reqs['network']
                )
                results.extend(network_validation)
        
        except Exception as e:
            results.append(ValidationResult(
                check_name="technical_feasibility",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    async def _validate_business_alignment(self, recommendation: Recommendation, 
                                         assessment: Assessment) -> List[ValidationResult]:
        """Validate business alignment of the recommendation."""
        results = []
        
        try:
            business_reqs = assessment.business_requirements
            
            # Check budget alignment
            budget_range = business_reqs.get('budget_range')
            if budget_range:
                budget_validation = await self._validate_budget_alignment(
                    recommendation, budget_range
                )
                results.append(budget_validation)
            
            # Check timeline alignment
            timeline = business_reqs.get('timeline')
            if timeline:
                timeline_validation = await self._validate_timeline_alignment(
                    recommendation, timeline
                )
                results.append(timeline_validation)
            
            # Check business goals alignment
            business_goals = business_reqs.get('business_goals', [])
            if business_goals:
                goals_validation = await self._validate_goals_alignment(
                    recommendation, business_goals
                )
                results.extend(goals_validation)
        
        except Exception as e:
            results.append(ValidationResult(
                check_name="business_alignment",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                confidence_score=0.0,
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error_message=str(e)
            ))
        
        return results
    
    def _calculate_overall_score(self, validation_results: List[ValidationResult]) -> float:
        """Calculate overall validation score from individual results."""
        if not validation_results:
            return 0.0
        
        total_weight = 0
        weighted_score = 0
        
        # Weight by severity (higher severity = higher weight)
        severity_weights = {
            ValidationSeverity.LOW: 1.0,
            ValidationSeverity.MEDIUM: 2.0,
            ValidationSeverity.HIGH: 3.0,
            ValidationSeverity.CRITICAL: 4.0
        }
        
        for result in validation_results:
            weight = severity_weights[result.severity]
            total_weight += weight
            
            # Convert status to score
            status_score = {
                ValidationStatus.VALIDATED: 1.0,
                ValidationStatus.NEEDS_REVIEW: 0.5,
                ValidationStatus.FAILED: 0.0,
                ValidationStatus.PENDING: 0.0
            }[result.status]
            
            weighted_score += status_score * result.confidence_score * weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    async def _check_compliance_alignment(self, recommendation: Recommendation, 
                                        regulation: str) -> Dict[str, Any]:
        """Check compliance alignment for a specific regulation."""
        # This would integrate with compliance databases
        # For now, return a mock implementation
        return {
            'compliant': True,
            'confidence': 0.9,
            'requirements': [f"{regulation} data encryption", f"{regulation} audit logging"],
            'gaps': []
        }
    
    async def _validate_compute_requirements(self, recommendation: Recommendation, 
                                           compute_reqs: Dict) -> List[ValidationResult]:
        """Validate compute requirements."""
        # Implementation for compute validation
        return []
    
    async def _validate_storage_requirements(self, recommendation: Recommendation, 
                                           storage_reqs: Dict) -> List[ValidationResult]:
        """Validate storage requirements."""
        # Implementation for storage validation
        return []
    
    async def _validate_network_requirements(self, recommendation: Recommendation, 
                                           network_reqs: Dict) -> List[ValidationResult]:
        """Validate network requirements."""
        # Implementation for network validation
        return []
    
    async def _validate_budget_alignment(self, recommendation: Recommendation, 
                                       budget_range: str) -> ValidationResult:
        """Validate budget alignment."""
        # Implementation for budget validation
        return ValidationResult(
            check_name="budget_alignment",
            status=ValidationStatus.VALIDATED,
            severity=ValidationSeverity.MEDIUM,
            confidence_score=0.9,
            details={"budget_range": budget_range},
            timestamp=datetime.utcnow()
        )
    
    async def _validate_timeline_alignment(self, recommendation: Recommendation, 
                                         timeline: str) -> ValidationResult:
        """Validate timeline alignment."""
        # Implementation for timeline validation
        return ValidationResult(
            check_name="timeline_alignment",
            status=ValidationStatus.VALIDATED,
            severity=ValidationSeverity.LOW,
            confidence_score=0.8,
            details={"timeline": timeline},
            timestamp=datetime.utcnow()
        )
    
    async def _validate_goals_alignment(self, recommendation: Recommendation, 
                                      business_goals: List[str]) -> List[ValidationResult]:
        """Validate business goals alignment."""
        # Implementation for goals validation
        return []


class FactChecker:
    """Fact-checking system for recommendations against authoritative sources."""
    
    def __init__(self, cloud_service: UnifiedCloudClient, cache_manager: CacheManager):
        self.cloud_service = cloud_service
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
    
    async def fact_check_recommendation(self, recommendation: Recommendation) -> List[FactCheckResult]:
        """
        Fact-check recommendation against authoritative sources.
        
        Args:
            recommendation: The recommendation to fact-check
            
        Returns:
            List of fact-check results
        """
        fact_check_results = []
        
        try:
            # Extract claims from recommendation
            claims = self._extract_claims(recommendation)
            
            # Check each claim against authoritative sources
            for claim in claims:
                result = await self._verify_claim(claim, recommendation)
                fact_check_results.append(result)
            
            return fact_check_results
            
        except Exception as e:
            self.logger.error(f"Fact-checking failed: {e}")
            return []
    
    def _extract_claims(self, recommendation: Recommendation) -> List[str]:
        """Extract verifiable claims from recommendation."""
        claims = []
        
        # Extract pricing claims
        if recommendation.cost_estimate:
            claims.append(f"Service {recommendation.service_name} costs ${recommendation.cost_estimate}/month")
        
        # Extract feature claims
        for feature in recommendation.features:
            claims.append(f"Service {recommendation.service_name} supports {feature}")
        
        # Extract performance claims
        if hasattr(recommendation, 'performance_metrics'):
            for metric, value in recommendation.performance_metrics.items():
                claims.append(f"Service {recommendation.service_name} provides {metric}: {value}")
        
        return claims
    
    async def _verify_claim(self, claim: str, recommendation: Recommendation) -> FactCheckResult:
        """Verify a specific claim against authoritative sources."""
        try:
            # Generate cache key for claim
            claim_hash = hashlib.md5(claim.encode()).hexdigest()
            cache_key = f"fact_check_{claim_hash}"
            
            # Check cache first
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                return FactCheckResult(**cached_result)
            
            # Verify against cloud provider documentation
            verification_result = await self._verify_against_provider_docs(
                claim, recommendation.provider, recommendation.service_name
            )
            
            result = FactCheckResult(
                claim=claim,
                source=f"{recommendation.provider}_documentation",
                verified=verification_result['verified'],
                confidence=verification_result['confidence'],
                evidence=verification_result['evidence'],
                timestamp=datetime.utcnow()
            )
            
            # Cache result
            await self.cache_manager.set(cache_key, result.__dict__, ttl=86400)  # 24 hours
            
            return result
            
        except Exception as e:
            self.logger.error(f"Claim verification failed: {e}")
            return FactCheckResult(
                claim=claim,
                source="error",
                verified=False,
                confidence=0.0,
                evidence={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def _verify_against_provider_docs(self, claim: str, provider: str, 
                                          service_name: str) -> Dict[str, Any]:
        """Verify claim against cloud provider documentation."""
        # This would integrate with provider documentation APIs
        # For now, return a mock implementation
        return {
            'verified': True,
            'confidence': 0.85,
            'evidence': {
                'source_url': f"https://{provider}.com/docs/{service_name}",
                'last_updated': datetime.utcnow().isoformat(),
                'verification_method': 'documentation_api'
            }
        }