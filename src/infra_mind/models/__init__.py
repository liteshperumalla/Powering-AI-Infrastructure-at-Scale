"""
Data models package for Infra Mind.

Contains all Beanie document models for MongoDB.
"""

from .assessment import Assessment
from .recommendation import Recommendation, ServiceRecommendation
from .user import User
from .report import Report, ReportSection
from .metrics import Metric, AgentMetrics
from .conversation import Conversation, ConversationSummary, ChatAnalytics
from .compliance import (
    ComplianceFramework,
    AutomatedCheck,
    CheckExecution,
    EvidenceRequirement,
    ComplianceEvidence,
    RemediationAction,
    ComplianceAudit,
    ComplianceAlert,
    ComplianceDashboardMetrics
)
from .experiment import (
    Experiment,
    ExperimentVariant,
    ExperimentResult,
    ExperimentEvent,
    ExperimentStatus,
    VariantType
)
from .feedback import (
    UserFeedback,
    FeedbackAnalytics,
    QualityMetric,
    FeedbackType,
    FeedbackChannel,
    SentimentScore
)

# List of all document models for Beanie initialization
__all__ = [
    "Assessment",
    "Recommendation", 
    "ServiceRecommendation",
    "User",
    "Report",
    "ReportSection", 
    "Metric",
    "AgentMetrics",
    "Conversation",
    "ConversationSummary",
    "ChatAnalytics",
    "ComplianceFramework",
    "AutomatedCheck",
    "CheckExecution", 
    "EvidenceRequirement",
    "ComplianceEvidence",
    "RemediationAction",
    "ComplianceAudit",
    "ComplianceAlert",
    "ComplianceDashboardMetrics",
    "Experiment",
    "ExperimentVariant",
    "ExperimentResult", 
    "ExperimentEvent",
    "ExperimentStatus",
    "VariantType",
    "UserFeedback",
    "FeedbackAnalytics",
    "QualityMetric",
    "FeedbackType",
    "FeedbackChannel",
    "SentimentScore"
]

# Document models list for Beanie
DOCUMENT_MODELS = [
    Assessment,
    Recommendation,
    ServiceRecommendation,
    User,
    Report,
    ReportSection,
    Metric,
    AgentMetrics,
    Conversation,
    ConversationSummary,
    ChatAnalytics,
    ComplianceFramework,
    AutomatedCheck,
    CheckExecution,
    EvidenceRequirement,
    ComplianceEvidence,
    RemediationAction,
    ComplianceAudit,
    ComplianceAlert,
    ComplianceDashboardMetrics,
    Experiment,
    ExperimentVariant,
    ExperimentResult,
    ExperimentEvent,
    UserFeedback,
    FeedbackAnalytics,
    QualityMetric
]