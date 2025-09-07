"""
Feedback model for user feedback collection and analysis.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field
from enum import Enum


class FeedbackType(str, Enum):
    ASSESSMENT_QUALITY = "assessment_quality"
    UI_EXPERIENCE = "ui_experience"
    PERFORMANCE = "performance"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL = "general"


class FeedbackChannel(str, Enum):
    ASSESSMENT_INTERFACE = "assessment_interface"
    EMAIL_SURVEY = "email_survey"
    IN_APP_PROMPT = "in_app_prompt"
    SUPPORT_CHAT = "support_chat"
    API = "api"
    WEB = "web"


class SentimentScore(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class UserFeedback(Document):
    """User feedback collection model."""
    
    # Basic info
    user_id: str = Field(description="User who submitted feedback")
    assessment_id: Optional[str] = Field(default=None, description="Related assessment ID")
    
    # Feedback content
    feedback_type: FeedbackType = Field(description="Type of feedback")
    channel: FeedbackChannel = Field(description="Channel through which feedback was submitted")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating (1-5)")
    title: Optional[str] = Field(default=None, description="Feedback title")
    comments: Optional[str] = Field(default=None, description="Detailed comments")
    
    # Analysis
    sentiment: Optional[SentimentScore] = Field(default=None, description="Sentiment analysis")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    category_confidence: Optional[float] = Field(default=None, description="Category classification confidence")
    
    # Context
    user_attributes: Dict[str, Any] = Field(default_factory=dict, description="User context")
    session_id: Optional[str] = Field(default=None, description="User session ID")
    page_url: Optional[str] = Field(default=None, description="Page where feedback was submitted")
    
    # Processing
    processed: bool = Field(default=False, description="Whether feedback has been processed")
    processed_at: Optional[datetime] = Field(default=None, description="When feedback was processed")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    priority: Optional[str] = Field(default="medium", description="Priority level")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_feedback"
        indexes = [
            "user_id",
            "assessment_id", 
            "feedback_type",
            "channel",
            "sentiment",
            "processed",
            [("feedback_type", 1), ("created_at", -1)],
            [("user_id", 1), ("created_at", -1)],
            [("assessment_id", 1), ("created_at", -1)],
            [("processed", 1), ("created_at", -1)],
            [("sentiment", 1), ("rating", -1)],
        ]


class FeedbackAnalytics(Document):
    """Aggregated feedback analytics."""
    
    # Time period
    period_start: datetime = Field(description="Analytics period start")
    period_end: datetime = Field(description="Analytics period end")
    period_type: str = Field(description="Period type (daily, weekly, monthly)")
    
    # Overall metrics
    total_feedback: int = Field(default=0)
    avg_rating: Optional[float] = Field(default=None)
    response_rate: Optional[float] = Field(default=None)
    
    # Sentiment breakdown
    sentiment_breakdown: Dict[str, int] = Field(default_factory=dict)
    sentiment_score: Optional[float] = Field(default=None, description="Overall sentiment score")
    
    # Category breakdown
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    category_ratings: Dict[str, float] = Field(default_factory=dict)
    
    # Channel performance
    channel_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Trends
    trend_direction: Optional[str] = Field(default=None, description="improving, declining, stable")
    trend_percentage: Optional[float] = Field(default=None)
    
    # Top keywords and themes
    top_keywords: List[Dict[str, Any]] = Field(default_factory=list)
    common_themes: List[str] = Field(default_factory=list)
    
    # Action items
    improvement_opportunities: List[str] = Field(default_factory=list)
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "feedback_analytics"
        indexes = [
            [("period_start", 1), ("period_end", 1)],
            [("period_type", 1), ("calculated_at", -1)],
            "calculated_at",
        ]


class QualityMetric(Document):
    """Quality metrics for assessments and system components."""
    
    # Target identification
    target_type: str = Field(description="Type of target (assessment, user, system)")
    target_id: str = Field(description="ID of the target")
    
    # Metric details
    metric_name: str = Field(description="Name of the quality metric")
    metric_value: float = Field(description="Metric value")
    metric_unit: Optional[str] = Field(default=None, description="Unit of measurement")
    
    # Context
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Metric dimensions")
    tags: List[str] = Field(default_factory=list)
    
    # Quality scoring
    quality_score: Optional[float] = Field(default=None, ge=0, le=100, description="Overall quality score")
    sub_scores: Dict[str, float] = Field(default_factory=dict, description="Sub-component scores")
    
    # Thresholds and alerts
    threshold_min: Optional[float] = Field(default=None)
    threshold_max: Optional[float] = Field(default=None)
    alert_triggered: bool = Field(default=False)
    
    # Timestamps
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "quality_metrics"
        indexes = [
            "target_type",
            "target_id",
            "metric_name",
            [("target_type", 1), ("target_id", 1)],
            [("metric_name", 1), ("measured_at", -1)],
            [("target_id", 1), ("measured_at", -1)],
            [("alert_triggered", 1), ("measured_at", -1)],
        ]