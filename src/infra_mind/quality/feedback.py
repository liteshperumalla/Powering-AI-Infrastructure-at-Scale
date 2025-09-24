"""
User feedback collection and quality scoring mechanisms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

from ..models.recommendation import Recommendation
from ..models.assessment import Assessment
from ..models.user import User
from ..core.database import get_database
from ..core.cache import CacheManager


class FeedbackType(Enum):
    RATING = "rating"
    COMMENT = "comment"
    IMPLEMENTATION_RESULT = "implementation_result"
    ACCURACY_REPORT = "accuracy_report"
    SUGGESTION = "suggestion"


class FeedbackSentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class UserFeedback:
    """User feedback on recommendations."""
    feedback_id: str
    user_id: str
    assessment_id: str
    recommendation_id: str
    agent_name: str
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    implementation_success: Optional[bool] = None
    cost_accuracy: Optional[float] = None  # Actual vs predicted cost ratio
    time_to_implement: Optional[int] = None  # Days
    business_value_realized: Optional[int] = None  # 1-5 scale
    technical_accuracy: Optional[int] = None  # 1-5 scale
    ease_of_implementation: Optional[int] = None  # 1-5 scale
    would_recommend: Optional[bool] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


@dataclass
class QualityScore:
    """Quality score for recommendations."""
    recommendation_id: str
    agent_name: str
    overall_score: float
    accuracy_score: float
    usefulness_score: float
    implementation_score: float
    business_value_score: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    last_updated: datetime
    score_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents."""
    agent_name: str
    total_recommendations: int
    average_rating: float
    accuracy_score: float
    implementation_success_rate: float
    user_satisfaction_score: float
    business_value_score: float
    improvement_trend: float  # Positive = improving, negative = declining
    last_30_days_performance: Dict[str, float]
    strengths: List[str]
    improvement_areas: List[str]
    last_updated: datetime


class FeedbackCollector:
    """System for collecting and processing user feedback."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        self.db = None
    
    async def initialize(self):
        """Initialize database connection."""
        self.db = await get_database()
    
    async def collect_feedback(self, feedback: UserFeedback) -> bool:
        """
        Collect user feedback on recommendations.
        
        Args:
            feedback: User feedback data
            
        Returns:
            Success status
        """
        try:
            if not self.db:
                await self.initialize()
            
            # Store feedback in database
            feedback_doc = {
                "feedback_id": feedback.feedback_id,
                "user_id": feedback.user_id,
                "assessment_id": feedback.assessment_id,
                "recommendation_id": feedback.recommendation_id,
                "agent_name": feedback.agent_name,
                "feedback_type": feedback.feedback_type.value,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "implementation_success": feedback.implementation_success,
                "cost_accuracy": feedback.cost_accuracy,
                "time_to_implement": feedback.time_to_implement,
                "business_value_realized": feedback.business_value_realized,
                "technical_accuracy": feedback.technical_accuracy,
                "ease_of_implementation": feedback.ease_of_implementation,
                "would_recommend": feedback.would_recommend,
                "tags": feedback.tags,
                "metadata": feedback.metadata,
                "created_at": feedback.created_at,
                "processed": feedback.processed
            }
            
            await self.db.feedback.insert_one(feedback_doc)
            
            # Trigger async processing
            asyncio.create_task(self._process_feedback_async(feedback))
            
            self.logger.info(f"Feedback collected for recommendation {feedback.recommendation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to collect feedback: {e}")
            return False
    
    async def get_feedback_summary(self, recommendation_id: str) -> Dict[str, Any]:
        """Get feedback summary for a recommendation."""
        try:
            if not self.db:
                await self.initialize()
            
            # Get all feedback for recommendation
            feedback_cursor = self.db.feedback.find({"recommendation_id": recommendation_id})
            feedback_list = await feedback_cursor.to_list(length=None)
            
            if not feedback_list:
                return {"total_feedback": 0, "summary": "No feedback available"}
            
            # Calculate summary statistics
            ratings = [f["rating"] for f in feedback_list if f.get("rating")]
            implementation_successes = [f["implementation_success"] for f in feedback_list 
                                      if f.get("implementation_success") is not None]
            
            summary = {
                "total_feedback": len(feedback_list),
                "average_rating": statistics.mean(ratings) if ratings else None,
                "rating_distribution": self._calculate_rating_distribution(ratings),
                "implementation_success_rate": (
                    sum(implementation_successes) / len(implementation_successes) 
                    if implementation_successes else None
                ),
                "common_tags": self._get_common_tags(feedback_list),
                "sentiment_analysis": await self._analyze_sentiment(feedback_list),
                "recent_feedback": sorted(feedback_list, key=lambda x: x["created_at"], reverse=True)[:5]
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get feedback summary: {e}")
            return {"error": str(e)}
    
    async def _process_feedback_async(self, feedback: UserFeedback):
        """Process feedback asynchronously."""
        try:
            # Update quality scores
            await self._update_quality_scores(feedback)
            
            # Update agent performance metrics
            await self._update_agent_metrics(feedback)
            
            # Trigger learning updates if needed
            if feedback.rating and feedback.rating <= 2:
                await self._trigger_improvement_analysis(feedback)
            
            # Mark feedback as processed
            await self.db.feedback.update_one(
                {"feedback_id": feedback.feedback_id},
                {"$set": {"processed": True}}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback: {e}")
    
    async def _update_quality_scores(self, feedback: UserFeedback):
        """Update quality scores based on feedback."""
        try:
            # Get existing quality score
            existing_score = await self.db.quality_scores.find_one(
                {"recommendation_id": feedback.recommendation_id}
            )
            
            if existing_score:
                # Update existing score
                updated_score = await self._recalculate_quality_score(
                    feedback.recommendation_id, feedback
                )
            else:
                # Create new quality score
                updated_score = await self._calculate_initial_quality_score(
                    feedback.recommendation_id, feedback
                )
            
            # Store updated score
            await self.db.quality_scores.replace_one(
                {"recommendation_id": feedback.recommendation_id},
                updated_score.__dict__,
                upsert=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update quality scores: {e}")
    
    async def _update_agent_metrics(self, feedback: UserFeedback):
        """Update agent performance metrics."""
        try:
            # Get all feedback for this agent
            agent_feedback = await self.db.feedback.find(
                {"agent_name": feedback.agent_name}
            ).to_list(length=None)
            
            # Calculate performance metrics
            metrics = await self._calculate_agent_metrics(feedback.agent_name, agent_feedback)
            
            # Store metrics
            await self.db.agent_metrics.replace_one(
                {"agent_name": feedback.agent_name},
                metrics.__dict__,
                upsert=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update agent metrics: {e}")
    
    def _calculate_rating_distribution(self, ratings: List[int]) -> Dict[int, int]:
        """Calculate distribution of ratings."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            if 1 <= rating <= 5:
                distribution[rating] += 1
        return distribution
    
    def _get_common_tags(self, feedback_list: List[Dict]) -> List[str]:
        """Get most common tags from feedback."""
        tag_counts = {}
        for feedback in feedback_list:
            for tag in feedback.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Return top 5 most common tags
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    async def _analyze_sentiment(self, feedback_list: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of feedback comments."""
        comments = [f["comment"] for f in feedback_list if f.get("comment")]
        
        if not comments:
            return {"sentiment": "neutral", "confidence": 0.0}
        
        # Simple sentiment analysis based on keywords
        positive_keywords = ["good", "great", "excellent", "helpful", "accurate", "useful"]
        negative_keywords = ["bad", "poor", "wrong", "inaccurate", "useless", "terrible"]
        
        positive_count = 0
        negative_count = 0
        
        for comment in comments:
            comment_lower = comment.lower()
            positive_count += sum(1 for word in positive_keywords if word in comment_lower)
            negative_count += sum(1 for word in negative_keywords if word in comment_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = positive_count / (positive_count + negative_count)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = negative_count / (positive_count + negative_count)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
            "total_comments": len(comments)
        }
    
    async def _recalculate_quality_score(self, recommendation_id: str, 
                                       new_feedback: UserFeedback) -> QualityScore:
        """Recalculate quality score with new feedback."""
        # Get all feedback for this recommendation
        all_feedback = await self.db.feedback.find(
            {"recommendation_id": recommendation_id}
        ).to_list(length=None)
        
        return await self._calculate_quality_score_from_feedback(
            recommendation_id, all_feedback
        )
    
    async def _calculate_initial_quality_score(self, recommendation_id: str, 
                                             feedback: UserFeedback) -> QualityScore:
        """Calculate initial quality score from first feedback."""
        return await self._calculate_quality_score_from_feedback(
            recommendation_id, [feedback.__dict__]
        )
    
    async def _calculate_quality_score_from_feedback(self, recommendation_id: str, 
                                                   feedback_list: List[Dict]) -> QualityScore:
        """Calculate quality score from feedback list."""
        if not feedback_list:
            return QualityScore(
                recommendation_id=recommendation_id,
                agent_name="unknown",
                overall_score=0.0,
                accuracy_score=0.0,
                usefulness_score=0.0,
                implementation_score=0.0,
                business_value_score=0.0,
                confidence_interval=(0.0, 0.0),
                sample_size=0,
                last_updated=datetime.utcnow()
            )
        
        # Extract scores from feedback
        ratings = [f["rating"] for f in feedback_list if f.get("rating")]
        technical_accuracy = [f["technical_accuracy"] for f in feedback_list 
                            if f.get("technical_accuracy")]
        business_value = [f["business_value_realized"] for f in feedback_list 
                         if f.get("business_value_realized")]
        implementation_ease = [f["ease_of_implementation"] for f in feedback_list 
                             if f.get("ease_of_implementation")]
        
        # Calculate component scores
        accuracy_score = statistics.mean(technical_accuracy) / 5.0 if technical_accuracy else 0.0
        usefulness_score = statistics.mean(ratings) / 5.0 if ratings else 0.0
        implementation_score = statistics.mean(implementation_ease) / 5.0 if implementation_ease else 0.0
        business_value_score = statistics.mean(business_value) / 5.0 if business_value else 0.0
        
        # Calculate overall score (weighted average)
        weights = {"accuracy": 0.3, "usefulness": 0.25, "implementation": 0.25, "business_value": 0.2}
        overall_score = (
            accuracy_score * weights["accuracy"] +
            usefulness_score * weights["usefulness"] +
            implementation_score * weights["implementation"] +
            business_value_score * weights["business_value"]
        )
        
        # Calculate confidence interval (simplified)
        sample_size = len(feedback_list)
        margin_of_error = 0.1 / (sample_size ** 0.5) if sample_size > 0 else 0.5
        confidence_interval = (
            max(0.0, overall_score - margin_of_error),
            min(1.0, overall_score + margin_of_error)
        )
        
        return QualityScore(
            recommendation_id=recommendation_id,
            agent_name=feedback_list[0]smart_get("agent_name"),
            overall_score=overall_score,
            accuracy_score=accuracy_score,
            usefulness_score=usefulness_score,
            implementation_score=implementation_score,
            business_value_score=business_value_score,
            confidence_interval=confidence_interval,
            sample_size=sample_size,
            last_updated=datetime.utcnow(),
            score_breakdown={
                "accuracy": accuracy_score,
                "usefulness": usefulness_score,
                "implementation": implementation_score,
                "business_value": business_value_score
            }
        )
    
    async def _calculate_agent_metrics(self, agent_name: str, 
                                     feedback_list: List[Dict]) -> AgentPerformanceMetrics:
        """Calculate performance metrics for an agent."""
        if not feedback_list:
            return AgentPerformanceMetrics(
                agent_name=agent_name,
                total_recommendations=0,
                average_rating=0.0,
                accuracy_score=0.0,
                implementation_success_rate=0.0,
                user_satisfaction_score=0.0,
                business_value_score=0.0,
                improvement_trend=0.0,
                last_30_days_performance={},
                strengths=[],
                improvement_areas=[],
                last_updated=datetime.utcnow()
            )
        
        # Calculate basic metrics
        ratings = [f["rating"] for f in feedback_list if f.get("rating")]
        technical_accuracy = [f["technical_accuracy"] for f in feedback_list 
                            if f.get("technical_accuracy")]
        implementation_successes = [f["implementation_success"] for f in feedback_list 
                                  if f.get("implementation_success") is not None]
        business_values = [f["business_value_realized"] for f in feedback_list 
                         if f.get("business_value_realized")]
        
        # Calculate performance metrics
        average_rating = statistics.mean(ratings) if ratings else 0.0
        accuracy_score = statistics.mean(technical_accuracy) / 5.0 if technical_accuracy else 0.0
        implementation_success_rate = (
            sum(implementation_successes) / len(implementation_successes) 
            if implementation_successes else 0.0
        )
        user_satisfaction_score = average_rating / 5.0
        business_value_score = statistics.mean(business_values) / 5.0 if business_values else 0.0
        
        # Calculate improvement trend (last 30 days vs previous 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        
        recent_feedback = [f for f in feedback_list 
                          if datetime.fromisoformat(f["created_at"]) > thirty_days_ago]
        previous_feedback = [f for f in feedback_list 
                           if sixty_days_ago < datetime.fromisoformat(f["created_at"]) <= thirty_days_ago]
        
        recent_avg = statistics.mean([f["rating"] for f in recent_feedback if f.get("rating")]) if recent_feedback else 0
        previous_avg = statistics.mean([f["rating"] for f in previous_feedback if f.get("rating")]) if previous_feedback else 0
        
        improvement_trend = recent_avg - previous_avg if previous_avg > 0 else 0.0
        
        # Identify strengths and improvement areas
        strengths, improvement_areas = self._identify_strengths_and_improvements(feedback_list)
        
        return AgentPerformanceMetrics(
            agent_name=agent_name,
            total_recommendations=len(feedback_list),
            average_rating=average_rating,
            accuracy_score=accuracy_score,
            implementation_success_rate=implementation_success_rate,
            user_satisfaction_score=user_satisfaction_score,
            business_value_score=business_value_score,
            improvement_trend=improvement_trend,
            last_30_days_performance={
                "average_rating": recent_avg,
                "total_feedback": len(recent_feedback),
                "implementation_success_rate": sum([f["implementation_success"] for f in recent_feedback 
                                                   if f.get("implementation_success")]) / len(recent_feedback) if recent_feedback else 0
            },
            strengths=strengths,
            improvement_areas=improvement_areas,
            last_updated=datetime.utcnow()
        )
    
    def _identify_strengths_and_improvements(self, feedback_list: List[Dict]) -> Tuple[List[str], List[str]]:
        """Identify agent strengths and improvement areas from feedback."""
        strengths = []
        improvement_areas = []
        
        # Analyze ratings by category
        categories = {
            "technical_accuracy": "Technical Accuracy",
            "business_value_realized": "Business Value",
            "ease_of_implementation": "Implementation Ease"
        }
        
        for field, category in categories.items():
            scores = [f[field] for f in feedback_list if f.get(field)]
            if scores:
                avg_score = statistics.mean(scores)
                if avg_score >= 4.0:
                    strengths.append(category)
                elif avg_score <= 2.5:
                    improvement_areas.append(category)
        
        # Analyze common tags
        positive_tags = ["accurate", "helpful", "clear", "comprehensive"]
        negative_tags = ["confusing", "incomplete", "expensive", "complex"]
        
        all_tags = []
        for feedback in feedback_list:
            all_tags.extend(feedback.get("tags", []))
        
        for tag in positive_tags:
            if tag in all_tags and all_tags.count(tag) >= 2:
                strengths.append(f"Consistently {tag}")
        
        for tag in negative_tags:
            if tag in all_tags and all_tags.count(tag) >= 2:
                improvement_areas.append(f"Often {tag}")
        
        return strengths[:5], improvement_areas[:5]  # Limit to top 5 each
    
    async def _trigger_improvement_analysis(self, feedback: UserFeedback):
        """Trigger improvement analysis for poor feedback."""
        try:
            # Log poor feedback for analysis
            self.logger.warning(f"Poor feedback received for {feedback.agent_name}: "
                              f"Rating {feedback.rating}, Comment: {feedback.comment}")
            
            # Store in improvement queue for manual review
            improvement_item = {
                "feedback_id": feedback.feedback_id,
                "agent_name": feedback.agent_name,
                "recommendation_id": feedback.recommendation_id,
                "issue_type": "poor_rating",
                "priority": "high" if feedback.rating == 1 else "medium",
                "created_at": datetime.utcnow(),
                "status": "pending_review"
            }
            
            await self.db.improvement_queue.insert_one(improvement_item)
            
        except Exception as e:
            self.logger.error(f"Failed to trigger improvement analysis: {e}")


class QualityScoreManager:
    """Manager for quality scores and performance tracking."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        self.db = None
    
    async def initialize(self):
        """Initialize database connection."""
        self.db = await get_database()
    
    async def get_quality_score(self, recommendation_id: str) -> Optional[QualityScore]:
        """Get quality score for a recommendation."""
        try:
            if not self.db:
                await self.initialize()
            
            # Check cache first
            cache_key = f"quality_score_{recommendation_id}"
            cached_score = await self.cache_manager.get(cache_key)
            if cached_score:
                return QualityScore(**cached_score)
            
            # Get from database
            score_doc = await self.db.quality_scores.find_one(
                {"recommendation_id": recommendation_id}
            )
            
            if score_doc:
                score = QualityScore(**score_doc)
                # Cache for 1 hour
                await self.cache_manager.set(cache_key, score.__dict__, ttl=3600)
                return score
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get quality score: {e}")
            return None
    
    async def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformanceMetrics]:
        """Get performance metrics for an agent."""
        try:
            if not self.db:
                await self.initialize()
            
            # Check cache first
            cache_key = f"agent_performance_{agent_name}"
            cached_metrics = await self.cache_manager.get(cache_key)
            if cached_metrics:
                return AgentPerformanceMetrics(**cached_metrics)
            
            # Get from database
            metrics_doc = await self.db.agent_metrics.find_one(
                {"agent_name": agent_name}
            )
            
            if metrics_doc:
                metrics = AgentPerformanceMetrics(**metrics_doc)
                # Cache for 30 minutes
                await self.cache_manager.set(cache_key, metrics.__dict__, ttl=1800)
                return metrics
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get agent performance: {e}")
            return None
    
    async def get_system_quality_overview(self) -> Dict[str, Any]:
        """Get overall system quality metrics."""
        try:
            if not self.db:
                await self.initialize()
            
            # Get all quality scores
            quality_scores = await self.db.quality_scores.find().to_list(length=None)
            
            if not quality_scores:
                return {"message": "No quality data available"}
            
            # Calculate system-wide metrics
            overall_scores = [score["overall_score"] for score in quality_scores]
            accuracy_scores = [score["accuracy_score"] for score in quality_scores]
            usefulness_scores = [score["usefulness_score"] for score in quality_scores]
            
            # Get agent performance summary
            agent_metrics = await self.db.agent_metrics.find().to_list(length=None)
            
            overview = {
                "system_metrics": {
                    "total_recommendations": len(quality_scores),
                    "average_quality_score": statistics.mean(overall_scores),
                    "average_accuracy_score": statistics.mean(accuracy_scores),
                    "average_usefulness_score": statistics.mean(usefulness_scores),
                    "quality_distribution": self._calculate_score_distribution(overall_scores)
                },
                "agent_performance": {
                    "total_agents": len(agent_metrics),
                    "top_performing_agents": sorted(
                        agent_metrics, 
                        key=lambda x: x["average_rating"], 
                        reverse=True
                    )[:5],
                    "agents_needing_improvement": [
                        agent for agent in agent_metrics 
                        if agent["average_rating"] < 3.0
                    ]
                },
                "trends": {
                    "improving_agents": [
                        agent for agent in agent_metrics 
                        if agent["improvement_trend"] > 0.1
                    ],
                    "declining_agents": [
                        agent for agent in agent_metrics 
                        if agent["improvement_trend"] < -0.1
                    ]
                },
                "last_updated": datetime.utcnow()
            }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get system quality overview: {e}")
            return {"error": str(e)}
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of quality scores."""
        distribution = {
            "excellent": 0,  # 0.8-1.0
            "good": 0,       # 0.6-0.8
            "fair": 0,       # 0.4-0.6
            "poor": 0        # 0.0-0.4
        }
        
        for score in scores:
            if score >= 0.8:
                distribution["excellent"] += 1
            elif score >= 0.6:
                distribution["good"] += 1
            elif score >= 0.4:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1
        
        return distribution