"""
Comprehensive User Feedback and Quality Validation System.

This module provides enterprise-grade feedback collection, analysis,
and quality validation capabilities for infrastructure assessments.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of user feedback."""
    RATING = "rating"
    COMMENT = "comment"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    QUALITY_ASSESSMENT = "quality_assessment"
    USER_EXPERIENCE = "user_experience"


class FeedbackCategory(str, Enum):
    """Categories for feedback classification."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    USABILITY = "usability"
    PERFORMANCE = "performance"
    DESIGN = "design"
    CONTENT_QUALITY = "content_quality"
    FUNCTIONALITY = "functionality"


class SentimentScore(str, Enum):
    """Sentiment classification scores."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class FeedbackChannel(str, Enum):
    """Channels through which feedback is collected."""
    WEB_FORM = "web_form"
    EMAIL = "email"
    CHAT_INTERFACE = "chat_interface"
    API = "api"
    MOBILE_APP = "mobile_app"
    SURVEY = "survey"
    INTERVIEW = "interview"


@dataclass
class UserFeedback:
    """Individual user feedback entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    assessment_id: Optional[str] = None
    feedback_type: FeedbackType = FeedbackType.COMMENT
    category: FeedbackCategory = FeedbackCategory.CONTENT_QUALITY
    channel: FeedbackChannel = FeedbackChannel.WEB_FORM
    
    # Feedback content
    rating: Optional[int] = None  # 1-5 or 1-10 scale
    comment: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    
    # Context
    page_url: Optional[str] = None
    feature_name: Optional[str] = None
    component_id: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Analysis results
    sentiment_score: Optional[SentimentScore] = None
    confidence_level: float = 0.0
    keywords: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    device_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "assessment_id": self.assessment_id,
            "feedback_type": self.feedback_type.value,
            "category": self.category.value,
            "channel": self.channel.value,
            "rating": self.rating,
            "comment": self.comment,
            "suggestions": self.suggestions,
            "page_url": self.page_url,
            "feature_name": self.feature_name,
            "component_id": self.component_id,
            "sentiment_score": self.sentiment_score.value if self.sentiment_score else None,
            "confidence_level": self.confidence_level,
            "keywords": self.keywords,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "device_info": self.device_info
        }


@dataclass
class QualityMetrics:
    """Quality metrics derived from feedback."""
    average_rating: float = 0.0
    total_feedback_count: int = 0
    positive_feedback_rate: float = 0.0
    negative_feedback_rate: float = 0.0
    response_rate: float = 0.0
    satisfaction_score: float = 0.0
    nps_score: float = 0.0  # Net Promoter Score
    quality_trend: str = "stable"  # improving, stable, declining
    
    # Category-specific scores
    category_scores: Dict[str, float] = field(default_factory=dict)
    
    # Time-based metrics
    weekly_trend: List[float] = field(default_factory=list)
    monthly_trend: List[float] = field(default_factory=list)


class FeedbackCollector:
    """
    Multi-channel feedback collection system.
    
    Collects feedback from various channels and provides
    standardized processing and storage.
    """
    
    def __init__(self):
        """Initialize feedback collector."""
        self.feedback_storage: List[UserFeedback] = []
        self.collection_handlers: Dict[FeedbackChannel, Callable] = {}
        self.validation_rules: List[Callable] = []
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        
        logger.info("Feedback collector initialized")
    
    def register_channel_handler(self, channel: FeedbackChannel, handler: Callable) -> None:
        """
        Register a handler for a specific feedback channel.
        
        Args:
            channel: Feedback channel
            handler: Handler function for processing feedback from this channel
        """
        self.collection_handlers[channel] = handler
        logger.info(f"Registered handler for channel: {channel.value}")
    
    def add_validation_rule(self, rule: Callable[[UserFeedback], bool]) -> None:
        """
        Add a validation rule for feedback.
        
        Args:
            rule: Validation function that returns True if feedback is valid
        """
        self.validation_rules.append(rule)
    
    async def collect_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """
        Collect feedback from any channel.
        
        Args:
            feedback_data: Raw feedback data
            
        Returns:
            Feedback ID
        """
        try:
            # Convert raw data to UserFeedback
            feedback = self._parse_feedback_data(feedback_data)
            
            # Validate feedback
            if not self._validate_feedback(feedback):
                raise ValueError("Feedback validation failed")
            
            # Add to processing queue
            await self.processing_queue.put(feedback)
            
            logger.info(f"Collected feedback: {feedback.id}")
            return feedback.id
            
        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            raise
    
    def _parse_feedback_data(self, data: Dict[str, Any]) -> UserFeedback:
        """Parse raw feedback data into UserFeedback object."""
        feedback = UserFeedback()
        
        # Map common fields
        if "user_id" in data:
            feedback.user_id = data["user_id"]
        if "session_id" in data:
            feedback.session_id = data["session_id"]
        if "assessment_id" in data:
            feedback.assessment_id = data["assessment_id"]
        if "rating" in data:
            feedback.rating = int(data["rating"])
        if "comment" in data:
            feedback.comment = data["comment"]
        if "suggestions" in data:
            feedback.suggestions = data["suggestions"] if isinstance(data["suggestions"], list) else [data["suggestions"]]
        
        # Map enums with defaults
        if "feedback_type" in data:
            try:
                feedback.feedback_type = FeedbackType(data["feedback_type"])
            except ValueError:
                feedback.feedback_type = FeedbackType.COMMENT
        
        if "category" in data:
            try:
                feedback.category = FeedbackCategory(data["category"])
            except ValueError:
                feedback.category = FeedbackCategory.CONTENT_QUALITY
        
        if "channel" in data:
            try:
                feedback.channel = FeedbackChannel(data["channel"])
            except ValueError:
                feedback.channel = FeedbackChannel.WEB_FORM
        
        # Context information
        if "page_url" in data:
            feedback.page_url = data["page_url"]
        if "feature_name" in data:
            feedback.feature_name = data["feature_name"]
        if "component_id" in data:
            feedback.component_id = data["component_id"]
        if "user_agent" in data:
            feedback.user_agent = data["user_agent"]
        if "device_info" in data:
            feedback.device_info = data["device_info"]
        if "ip_address" in data:
            feedback.ip_address = data["ip_address"]
        
        return feedback
    
    def _validate_feedback(self, feedback: UserFeedback) -> bool:
        """Validate feedback against registered rules."""
        # Basic validation
        if not feedback.comment and feedback.rating is None:
            return False
        
        if feedback.rating is not None and (feedback.rating < 1 or feedback.rating > 10):
            return False
        
        # Apply custom validation rules
        for rule in self.validation_rules:
            try:
                if not rule(feedback):
                    return False
            except Exception as e:
                logger.error(f"Validation rule error: {e}")
                return False
        
        return True
    
    async def start_processing(self) -> None:
        """Start background processing of feedback."""
        if self.processing_task and not self.processing_task.done():
            return
        
        self.processing_task = asyncio.create_task(self._process_feedback_loop())
        logger.info("Started feedback processing")
    
    async def stop_processing(self) -> None:
        """Stop feedback processing."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped feedback processing")
    
    async def _process_feedback_loop(self) -> None:
        """Background loop for processing feedback."""
        while True:
            try:
                # Get feedback from queue (wait up to 1 second)
                feedback = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                # Process the feedback
                await self._process_feedback(feedback)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue  # No feedback to process, continue loop
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing feedback: {e}")
    
    async def _process_feedback(self, feedback: UserFeedback) -> None:
        """Process individual feedback entry."""
        try:
            # Perform sentiment analysis
            await self._analyze_sentiment(feedback)
            
            # Extract keywords
            await self._extract_keywords(feedback)
            
            # Calculate quality score
            await self._calculate_quality_score(feedback)
            
            # Mark as processed
            feedback.processed_at = datetime.now(timezone.utc)
            
            # Store feedback
            self.feedback_storage.append(feedback)
            
            logger.debug(f"Processed feedback: {feedback.id}")
            
        except Exception as e:
            logger.error(f"Failed to process feedback {feedback.id}: {e}")
    
    async def _analyze_sentiment(self, feedback: UserFeedback) -> None:
        """Analyze sentiment of feedback comment."""
        if not feedback.comment:
            return
        
        # Simple sentiment analysis based on keywords
        # In production, this would use a proper NLP library
        comment_lower = feedback.comment.lower()
        
        positive_words = ["good", "great", "excellent", "amazing", "helpful", "useful", "love", "perfect"]
        negative_words = ["bad", "terrible", "awful", "useless", "hate", "horrible", "disappointing", "worst"]
        
        positive_count = sum(1 for word in positive_words if word in comment_lower)
        negative_count = sum(1 for word in negative_words if word in comment_lower)
        
        if positive_count > negative_count + 1:
            feedback.sentiment_score = SentimentScore.POSITIVE
            feedback.confidence_level = 0.7
        elif negative_count > positive_count + 1:
            feedback.sentiment_score = SentimentScore.NEGATIVE
            feedback.confidence_level = 0.7
        else:
            feedback.sentiment_score = SentimentScore.NEUTRAL
            feedback.confidence_level = 0.5
        
        # Adjust based on rating if available
        if feedback.rating:
            if feedback.rating >= 4:
                if feedback.sentiment_score == SentimentScore.NEGATIVE:
                    feedback.sentiment_score = SentimentScore.NEUTRAL
                elif feedback.sentiment_score == SentimentScore.POSITIVE:
                    feedback.confidence_level = 0.9
            elif feedback.rating <= 2:
                if feedback.sentiment_score == SentimentScore.POSITIVE:
                    feedback.sentiment_score = SentimentScore.NEUTRAL
                elif feedback.sentiment_score == SentimentScore.NEGATIVE:
                    feedback.confidence_level = 0.9
    
    async def _extract_keywords(self, feedback: UserFeedback) -> None:
        """Extract keywords from feedback comment."""
        if not feedback.comment:
            return
        
        # Simple keyword extraction
        comment_lower = feedback.comment.lower()
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = [word.strip(".,!?;:") for word in comment_lower.split()]
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Get top keywords by frequency (simplified)
        word_counts = Counter(keywords)
        feedback.keywords = [word for word, count in word_counts.most_common(5)]
    
    async def _calculate_quality_score(self, feedback: UserFeedback) -> None:
        """Calculate quality score for feedback."""
        score = 0.0
        
        # Base score from rating
        if feedback.rating:
            score = feedback.rating / 5.0 if feedback.rating <= 5 else feedback.rating / 10.0
        else:
            # Use sentiment as fallback
            if feedback.sentiment_score == SentimentScore.VERY_POSITIVE:
                score = 1.0
            elif feedback.sentiment_score == SentimentScore.POSITIVE:
                score = 0.8
            elif feedback.sentiment_score == SentimentScore.NEUTRAL:
                score = 0.6
            elif feedback.sentiment_score == SentimentScore.NEGATIVE:
                score = 0.4
            else:
                score = 0.2
        
        # Adjust based on comment quality
        if feedback.comment:
            comment_length = len(feedback.comment.strip())
            if comment_length > 100:
                score += 0.1  # Detailed feedback bonus
            elif comment_length < 10:
                score -= 0.1  # Too brief penalty
        
        # Ensure score is within bounds
        feedback.quality_score = max(0.0, min(1.0, score))
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[UserFeedback]:
        """Get feedback by ID."""
        return next((f for f in self.feedback_storage if f.id == feedback_id), None)
    
    def get_feedback_by_assessment(self, assessment_id: str) -> List[UserFeedback]:
        """Get all feedback for a specific assessment."""
        return [f for f in self.feedback_storage if f.assessment_id == assessment_id]
    
    def get_feedback_by_user(self, user_id: str) -> List[UserFeedback]:
        """Get all feedback from a specific user."""
        return [f for f in self.feedback_storage if f.user_id == user_id]
    
    def get_recent_feedback(self, hours: int = 24) -> List[UserFeedback]:
        """Get recent feedback within specified hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [f for f in self.feedback_storage if f.created_at >= cutoff]


class FeedbackAnalyzer:
    """
    Advanced analytics for user feedback.
    
    Provides insights, trends, and quality metrics
    based on collected feedback data.
    """
    
    def __init__(self, collector: FeedbackCollector):
        """Initialize feedback analyzer."""
        self.collector = collector
        logger.info("Feedback analyzer initialized")
    
    def calculate_quality_metrics(self, days: int = 30) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Quality metrics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        feedback_data = [
            f for f in self.collector.feedback_storage
            if f.created_at >= cutoff_date
        ]
        
        if not feedback_data:
            return QualityMetrics()
        
        metrics = QualityMetrics()
        metrics.total_feedback_count = len(feedback_data)
        
        # Rating-based metrics
        ratings = [f.rating for f in feedback_data if f.rating is not None]
        if ratings:
            metrics.average_rating = statistics.mean(ratings)
        
        # Sentiment-based metrics
        sentiment_counts = Counter(f.sentiment_score for f in feedback_data if f.sentiment_score)
        total_with_sentiment = sum(sentiment_counts.values())
        
        if total_with_sentiment > 0:
            positive_count = (
                sentiment_counts.get(SentimentScore.POSITIVE, 0) +
                sentiment_counts.get(SentimentScore.VERY_POSITIVE, 0)
            )
            negative_count = (
                sentiment_counts.get(SentimentScore.NEGATIVE, 0) +
                sentiment_counts.get(SentimentScore.VERY_NEGATIVE, 0)
            )
            
            metrics.positive_feedback_rate = positive_count / total_with_sentiment
            metrics.negative_feedback_rate = negative_count / total_with_sentiment
        
        # Category-specific scores
        for category in FeedbackCategory:
            category_feedback = [f for f in feedback_data if f.category == category]
            if category_feedback:
                category_scores = [f.quality_score for f in category_feedback if f.quality_score is not None]
                if category_scores:
                    metrics.category_scores[category.value] = statistics.mean(category_scores)
        
        # Satisfaction score (0-1 scale)
        quality_scores = [f.quality_score for f in feedback_data if f.quality_score is not None]
        if quality_scores:
            metrics.satisfaction_score = statistics.mean(quality_scores)
        
        # NPS calculation (simplified)
        if ratings:
            promoters = sum(1 for r in ratings if r >= 9)
            detractors = sum(1 for r in ratings if r <= 6)
            metrics.nps_score = ((promoters - detractors) / len(ratings)) * 100
        
        # Trend analysis
        metrics.quality_trend = self._analyze_trend(feedback_data)
        
        return metrics
    
    def _analyze_trend(self, feedback_data: List[UserFeedback]) -> str:
        """Analyze quality trend over time."""
        if len(feedback_data) < 10:
            return "insufficient_data"
        
        # Sort by date
        sorted_feedback = sorted(feedback_data, key=lambda f: f.created_at)
        
        # Split into two halves
        mid_point = len(sorted_feedback) // 2
        earlier_half = sorted_feedback[:mid_point]
        recent_half = sorted_feedback[mid_point:]
        
        # Calculate average quality scores
        earlier_scores = [f.quality_score for f in earlier_half if f.quality_score is not None]
        recent_scores = [f.quality_score for f in recent_half if f.quality_score is not None]
        
        if not earlier_scores or not recent_scores:
            return "insufficient_data"
        
        earlier_avg = statistics.mean(earlier_scores)
        recent_avg = statistics.mean(recent_scores)
        
        if recent_avg > earlier_avg + 0.05:
            return "improving"
        elif recent_avg < earlier_avg - 0.05:
            return "declining"
        else:
            return "stable"
    
    def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive feedback summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Feedback summary and analytics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        feedback_data = [
            f for f in self.collector.feedback_storage
            if f.created_at >= cutoff_date
        ]
        
        # Basic counts
        total_feedback = len(feedback_data)
        feedback_by_type = Counter(f.feedback_type for f in feedback_data)
        feedback_by_category = Counter(f.category for f in feedback_data)
        feedback_by_channel = Counter(f.channel for f in feedback_data)
        
        # Top keywords
        all_keywords = []
        for feedback in feedback_data:
            all_keywords.extend(feedback.keywords)
        top_keywords = Counter(all_keywords).most_common(10)
        
        # Recent issues (negative feedback)
        negative_feedback = [
            f for f in feedback_data
            if f.sentiment_score in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]
        ]
        
        return {
            "period_days": days,
            "summary": {
                "total_feedback": total_feedback,
                "feedback_by_type": dict(feedback_by_type),
                "feedback_by_category": dict(feedback_by_category),
                "feedback_by_channel": dict(feedback_by_channel)
            },
            "quality_metrics": self.calculate_quality_metrics(days).to_dict() if hasattr(QualityMetrics, 'to_dict') else "metrics_calculated",
            "insights": {
                "top_keywords": top_keywords,
                "negative_feedback_count": len(negative_feedback),
                "most_common_issues": [f.comment[:100] + "..." if f.comment and len(f.comment) > 100 else f.comment for f in negative_feedback[:5]]
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data."""
        # Multi-period analysis
        daily_metrics = self.calculate_quality_metrics(days=1)
        weekly_metrics = self.calculate_quality_metrics(days=7)
        monthly_metrics = self.calculate_quality_metrics(days=30)
        
        # Channel performance
        all_feedback = self.collector.feedback_storage
        channel_performance = {}
        for channel in FeedbackChannel:
            channel_feedback = [f for f in all_feedback if f.channel == channel]
            if channel_feedback:
                avg_quality = statistics.mean([
                    f.quality_score for f in channel_feedback 
                    if f.quality_score is not None
                ])
                channel_performance[channel.value] = {
                    "count": len(channel_feedback),
                    "average_quality": avg_quality
                }
        
        return {
            "overview": {
                "total_feedback": len(all_feedback),
                "processed_feedback": len([f for f in all_feedback if f.processed_at]),
                "channels_active": len([ch for ch, perf in channel_performance.items() if perf["count"] > 0])
            },
            "quality_trends": {
                "daily": {
                    "satisfaction_score": daily_metrics.satisfaction_score,
                    "positive_rate": daily_metrics.positive_feedback_rate,
                    "trend": daily_metrics.quality_trend
                },
                "weekly": {
                    "satisfaction_score": weekly_metrics.satisfaction_score,
                    "positive_rate": weekly_metrics.positive_feedback_rate,
                    "trend": weekly_metrics.quality_trend
                },
                "monthly": {
                    "satisfaction_score": monthly_metrics.satisfaction_score,
                    "positive_rate": monthly_metrics.positive_feedback_rate,
                    "trend": monthly_metrics.quality_trend
                }
            },
            "channel_performance": channel_performance,
            "category_scores": monthly_metrics.category_scores,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# Global feedback system instances
feedback_collector = FeedbackCollector()
feedback_analyzer = FeedbackAnalyzer(feedback_collector)