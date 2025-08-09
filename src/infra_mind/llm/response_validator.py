"""
Response validation and quality checks for LLM responses.

Provides comprehensive validation of LLM responses including
content quality, format validation, and safety checks.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .interface import LLMResponse, LLMValidationError

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Validation issue found in LLM response."""
    severity: ValidationSeverity
    category: str
    message: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                  for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "quality_score": round(self.quality_score, 3),
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": self.metadata
        }


class ResponseValidator:
    """
    Comprehensive LLM response validator.
    
    Features:
    - Content quality assessment
    - Format validation
    - Safety and appropriateness checks
    - Business logic validation
    - Customizable validation rules
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize response validator.
        
        Args:
            config: Validation configuration
        """
        self.config = config or {}
        
        # Default validation settings
        self.min_length = self.config.get("min_length", 10)
        self.max_length = self.config.get("max_length", 10000)
        self.require_complete_sentences = self.config.get("require_complete_sentences", True)
        self.check_profanity = self.config.get("check_profanity", True)
        self.check_safety = self.config.get("check_safety", True)
        
        # Custom validation rules
        self.custom_validators: List[Callable[[str], ValidationIssue]] = []
        
        # Profanity filter (basic implementation)
        self.profanity_words = {
            # Add profanity words here - keeping minimal for example
            "inappropriate", "offensive"  # Placeholder words
        }
        
        # Safety keywords to flag
        self.safety_keywords = {
            "violence", "harm", "illegal", "dangerous", "weapon", "drug"
        }
        
        logger.info("Response validator initialized")
    
    def validate_response(self, response: LLMResponse, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate LLM response comprehensively.
        
        Args:
            response: LLM response to validate
            context: Additional context for validation
            
        Returns:
            Validation result with issues and quality score
        """
        issues = []
        metadata = {
            "response_length": len(response.content),
            "model": response.model,
            "provider": response.provider.value,
            "token_usage": response.token_usage.total_tokens
        }
        
        # Basic content validation
        issues.extend(self._validate_basic_content(response.content))
        
        # Format validation
        issues.extend(self._validate_format(response.content, context))
        
        # Quality assessment
        issues.extend(self._assess_quality(response.content))
        
        # Safety checks
        if self.check_safety:
            issues.extend(self._check_safety(response.content))
        
        # Profanity check
        if self.check_profanity:
            issues.extend(self._check_profanity(response.content))
        
        # Business logic validation
        issues.extend(self._validate_business_logic(response.content, context))
        
        # Custom validation rules
        for validator in self.custom_validators:
            try:
                issue = validator(response.content)
                if issue:
                    issues.append(issue)
            except Exception as e:
                logger.warning(f"Custom validator failed: {str(e)}")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(response.content, issues)
        
        # Determine if response is valid
        is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                          for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            metadata=metadata
        )
    
    def _validate_basic_content(self, content: str) -> List[ValidationIssue]:
        """Validate basic content requirements."""
        issues = []
        
        # Check if content exists
        if not content or not content.strip():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="content",
                message="Response is empty or contains only whitespace",
                suggestion="Ensure the LLM generates meaningful content"
            ))
            return issues
        
        # Check length requirements
        content_length = len(content.strip())
        
        if content_length < self.min_length:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="content",
                message=f"Response is too short ({content_length} chars, minimum {self.min_length})",
                suggestion="Consider adjusting max_tokens or prompt to encourage longer responses"
            ))
        
        if content_length > self.max_length:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="content",
                message=f"Response is too long ({content_length} chars, maximum {self.max_length})",
                suggestion="Consider reducing max_tokens or adding length constraints to prompt"
            ))
        
        # Check for complete sentences
        if self.require_complete_sentences:
            if not self._has_complete_sentences(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="format",
                    message="Response does not contain complete sentences",
                    suggestion="Adjust prompt to encourage complete, well-formed sentences"
                ))
        
        return issues
    
    def _validate_format(self, content: str, context: Optional[Dict[str, Any]]) -> List[ValidationIssue]:
        """Validate response format based on context."""
        issues = []
        
        if not context:
            return issues
        
        expected_format = context.get("expected_format")
        if not expected_format:
            return issues
        
        # JSON format validation
        if expected_format == "json":
            if not self._is_valid_json_format(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="format",
                    message="Response is not in valid JSON format",
                    suggestion="Ensure prompt specifies JSON format requirements clearly"
                ))
        
        # Markdown format validation
        elif expected_format == "markdown":
            if not self._has_markdown_structure(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="format",
                    message="Response lacks proper Markdown structure",
                    suggestion="Include Markdown formatting examples in prompt"
                ))
        
        # List format validation
        elif expected_format == "list":
            if not self._is_list_format(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="format",
                    message="Response is not in list format",
                    suggestion="Specify list format requirements in prompt"
                ))
        
        return issues
    
    def _assess_quality(self, content: str) -> List[ValidationIssue]:
        """Assess content quality."""
        issues = []
        
        # Check for repetition
        repetition_score = self._calculate_repetition_score(content)
        if repetition_score > 0.3:  # More than 30% repetitive
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="quality",
                message=f"High repetition detected (score: {repetition_score:.2f})",
                suggestion="Adjust temperature or use different prompting techniques"
            ))
        
        # Check for coherence
        if not self._is_coherent(content):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="quality",
                message="Response lacks coherence or logical flow",
                suggestion="Improve prompt structure or use system prompts for better guidance"
            ))
        
        # Check for completeness
        if self._appears_truncated(content):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="quality",
                message="Response appears to be truncated or incomplete",
                suggestion="Increase max_tokens or check for token limits"
            ))
        
        return issues
    
    def _check_safety(self, content: str) -> List[ValidationIssue]:
        """Check for safety issues."""
        issues = []
        
        # Handle None content gracefully
        if not content:
            return issues
            
        content_lower = content.lower()
        
        # Check for safety keywords
        found_keywords = [keyword for keyword in self.safety_keywords 
                         if keyword in content_lower]
        
        if found_keywords:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="safety",
                message=f"Potentially unsafe content detected: {', '.join(found_keywords)}",
                suggestion="Review content for safety and appropriateness"
            ))
        
        # Check for personal information patterns
        if self._contains_personal_info(content):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="safety",
                message="Response may contain personal information",
                suggestion="Ensure no sensitive data is included in responses"
            ))
        
        return issues
    
    def _check_profanity(self, content: str) -> List[ValidationIssue]:
        """Check for profanity."""
        issues = []
        
        # Handle None content gracefully
        if not content:
            return issues
            
        content_lower = content.lower()
        found_profanity = [word for word in self.profanity_words 
                          if word in content_lower]
        
        if found_profanity:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="profanity",
                message=f"Inappropriate language detected: {', '.join(found_profanity)}",
                suggestion="Regenerate response with content filtering"
            ))
        
        return issues
    
    def _validate_business_logic(self, content: str, context: Optional[Dict[str, Any]]) -> List[ValidationIssue]:
        """Validate business logic specific to Infra Mind."""
        issues = []
        
        if not context:
            return issues
        
        agent_name = context.get("agent_name", "") or ""
        
        # CTO Agent specific validation
        if agent_name and "cto" in agent_name.lower():
            if not self._contains_business_terms(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_logic",
                    message="CTO response lacks business-focused terminology",
                    suggestion="Ensure response includes ROI, budget, or strategic considerations"
                ))
        
        # Cloud Engineer Agent specific validation
        elif agent_name and ("cloud" in agent_name.lower() or "engineer" in agent_name.lower()):
            if not self._contains_technical_terms(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_logic",
                    message="Cloud Engineer response lacks technical details",
                    suggestion="Include specific cloud services, architectures, or technical recommendations"
                ))
        
        # Research Agent specific validation
        elif agent_name and "research" in agent_name.lower():
            if not self._contains_research_elements(content):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="business_logic",
                    message="Research response lacks analytical elements",
                    suggestion="Include data sources, comparisons, or analytical insights"
                ))
        
        return issues
    
    def _calculate_quality_score(self, content: str, issues: List[ValidationIssue]) -> float:
        """Calculate overall quality score."""
        base_score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                base_score -= 0.4
            elif issue.severity == ValidationSeverity.ERROR:
                base_score -= 0.2
            elif issue.severity == ValidationSeverity.WARNING:
                base_score -= 0.1
            elif issue.severity == ValidationSeverity.INFO:
                base_score -= 0.05
        
        # Bonus points for quality indicators
        if self._has_good_structure(content):
            base_score += 0.1
        
        if self._has_specific_details(content):
            base_score += 0.1
        
        if self._has_actionable_content(content):
            base_score += 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    # Helper methods for validation checks
    
    def _has_complete_sentences(self, content: str) -> bool:
        """Check if content has complete sentences."""
        sentences = re.split(r'[.!?]+', content.strip())
        complete_sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        return len(complete_sentences) > 0
    
    def _is_valid_json_format(self, content: str) -> bool:
        """Check if content is valid JSON format."""
        import json
        try:
            json.loads(content.strip())
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def _has_markdown_structure(self, content: str) -> bool:
        """Check if content has Markdown structure."""
        markdown_patterns = [
            r'^#+\s',  # Headers
            r'^\*\s',  # Bullet points
            r'^\d+\.\s',  # Numbered lists
            r'\*\*.*\*\*',  # Bold text
            r'`.*`',  # Code
        ]
        
        for pattern in markdown_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False
    
    def _is_list_format(self, content: str) -> bool:
        """Check if content is in list format."""
        lines = content.strip().split('\n')
        list_lines = [line for line in lines 
                     if re.match(r'^\s*[-*•]\s|^\s*\d+\.\s', line.strip())]
        return len(list_lines) >= 2
    
    def _calculate_repetition_score(self, content: str) -> float:
        """Calculate repetition score (0.0 to 1.0)."""
        words = content.lower().split()
        if len(words) < 10:
            return 0.0
        
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Calculate repetition based on most frequent words
        max_count = max(word_counts.values())
        repetition_score = (max_count - 1) / len(words)
        
        return min(1.0, repetition_score * 3)  # Scale up for visibility
    
    def _is_coherent(self, content: str) -> bool:
        """Check if content is coherent."""
        # Simple coherence check based on sentence transitions
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) < 2:
            return True
        
        # Check for transition words/phrases
        transition_words = {
            'however', 'therefore', 'furthermore', 'additionally', 'moreover',
            'consequently', 'meanwhile', 'similarly', 'in contrast', 'for example'
        }
        

        # Handle None content gracefully
        if not content:
            return False
        content_lower = content.lower()
        transition_count = sum(1 for word in transition_words if word in content_lower)
        
        # Coherent if has some transitions or is short
        return transition_count > 0 or len(sentences) <= 3
    
    def _appears_truncated(self, content: str) -> bool:
        """Check if content appears truncated."""
        # Check if ends abruptly without proper punctuation
        content = content.strip()
        if not content:
            return True
        
        last_char = content[-1]
        if last_char not in '.!?':
            # Check if last sentence seems incomplete
            last_sentence = content.split('.')[-1].strip()
            if len(last_sentence) > 20 and not last_sentence.endswith((':', ',')):
                return True
        
        return False
    
    def _contains_personal_info(self, content: str) -> bool:
        """Check for personal information patterns."""
        # Simple patterns for common personal info
        patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def _contains_business_terms(self, content: str) -> bool:
        """Check for business-focused terminology."""
        business_terms = {
            'roi', 'budget', 'cost', 'investment', 'revenue', 'profit',
            'strategy', 'strategic', 'business', 'stakeholder', 'executive'
        }
        

        # Handle None content gracefully
        if not content:
            return False
        content_lower = content.lower()
        return any(term in content_lower for term in business_terms)
    
    def _contains_technical_terms(self, content: str) -> bool:
        """Check for technical terminology."""
        technical_terms = {
            'aws', 'azure', 'gcp', 'cloud', 'server', 'database',
            'api', 'microservice', 'container', 'kubernetes', 'docker'
        }
        

        # Handle None content gracefully
        if not content:
            return False
        content_lower = content.lower()
        return any(term in content_lower for term in technical_terms)
    
    def _contains_research_elements(self, content: str) -> bool:
        """Check for research-focused elements."""
        research_terms = {
            'analysis', 'data', 'research', 'study', 'comparison',
            'trend', 'market', 'industry', 'benchmark', 'metric'
        }
        

        # Handle None content gracefully
        if not content:
            return False
        content_lower = content.lower()
        return any(term in content_lower for term in research_terms)
    
    def _has_good_structure(self, content: str) -> bool:
        """Check for good content structure."""
        # Look for headers, lists, or clear paragraphs
        return (
            self._has_markdown_structure(content) or
            self._is_list_format(content) or
            len(content.split('\n\n')) > 1  # Multiple paragraphs
        )
    
    def _has_specific_details(self, content: str) -> bool:
        """Check for specific details."""
        # Look for numbers, specific terms, examples
        has_numbers = bool(re.search(r'\d+', content))
        has_examples = 'example' in content.lower() or 'for instance' in content.lower()
        has_specifics = any(word in content.lower() for word in ['specific', 'particular', 'exactly'])
        
        return has_numbers or has_examples or has_specifics
    
    def _has_actionable_content(self, content: str) -> bool:
        """Check for actionable content."""
        action_words = {
            'should', 'recommend', 'suggest', 'implement', 'consider',
            'action', 'step', 'next', 'plan', 'strategy'
        }
        

        # Handle None content gracefully
        if not content:
            return False
        content_lower = content.lower()
        return any(word in content_lower for word in action_words)
    
    def add_custom_validator(self, validator: Callable[[str], Optional[ValidationIssue]]) -> None:
        """
        Add custom validation rule.
        
        Args:
            validator: Function that takes content string and returns ValidationIssue or None
        """
        self.custom_validators.append(validator)
        logger.info("Added custom validation rule")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Validation configuration and statistics
        """
        return {
            "config": {
                "min_length": self.min_length,
                "max_length": self.max_length,
                "require_complete_sentences": self.require_complete_sentences,
                "check_profanity": self.check_profanity,
                "check_safety": self.check_safety
            },
            "custom_validators": len(self.custom_validators),
            "profanity_words": len(self.profanity_words),
            "safety_keywords": len(self.safety_keywords)
        }