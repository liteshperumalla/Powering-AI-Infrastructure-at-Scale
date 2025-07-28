"""
Quality assurance module for Infra Mind.

This module provides comprehensive quality assurance capabilities including:
- Advanced recommendation validation and fact-checking
- User feedback collection and quality scoring
- A/B testing framework for recommendation strategies
- Continuous monitoring and quality improvement processes
"""

from .validation import (
    RecommendationValidator,
    FactChecker,
    ValidationResult,
    ValidationStatus,
    ValidationSeverity,
    FactCheckResult
)

from .feedback import (
    FeedbackCollector,
    QualityScoreManager,
    UserFeedback,
    QualityScore,
    AgentPerformanceMetrics,
    FeedbackType,
    FeedbackSentiment
)

from .ab_testing import (
    ABTestingFramework,
    Experiment,
    ExperimentVariant,
    ExperimentMetric,
    ExperimentResult,
    ExperimentAssignment,
    ExperimentStatus,
    ExperimentType,
    StatisticalSignificance
)

from .continuous_improvement import (
    ContinuousImprovementSystem,
    QualityAlert,
    ImprovementAction,
    QualityTrend,
    AlertSeverity,
    ImprovementActionType
)

__all__ = [
    # Validation
    'RecommendationValidator',
    'FactChecker',
    'ValidationResult',
    'ValidationStatus',
    'ValidationSeverity',
    'FactCheckResult',
    
    # Feedback
    'FeedbackCollector',
    'QualityScoreManager',
    'UserFeedback',
    'QualityScore',
    'AgentPerformanceMetrics',
    'FeedbackType',
    'FeedbackSentiment',
    
    # A/B Testing
    'ABTestingFramework',
    'Experiment',
    'ExperimentVariant',
    'ExperimentMetric',
    'ExperimentResult',
    'ExperimentAssignment',
    'ExperimentStatus',
    'ExperimentType',
    'StatisticalSignificance',
    
    # Continuous Improvement
    'ContinuousImprovementSystem',
    'QualityAlert',
    'ImprovementAction',
    'QualityTrend',
    'AlertSeverity',
    'ImprovementActionType'
]