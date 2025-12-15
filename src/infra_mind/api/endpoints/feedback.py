"""
User feedback collection and analysis API endpoints with real database functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timedelta, timezone
import uuid

from .auth import get_current_user, require_enterprise_access
from ...models.user import User
from ...models.feedback import (
    UserFeedback, FeedbackAnalytics, QualityMetric,
    FeedbackType, FeedbackChannel, SentimentScore
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


# Pydantic models for request/response
class SubmitFeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    assessment_id: Optional[str] = Field(None, description="Related assessment ID")
    feedback_type: str = Field(..., description="Type of feedback")
    channel: str = Field(default="assessment_interface", description="Feedback channel")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    title: Optional[str] = Field(None, description="Feedback title")
    comments: Optional[str] = Field(None, description="Detailed comments")
    tags: List[str] = Field(default_factory=list, description="Tags")


class FeedbackResponse(BaseModel):
    """Response model for feedback."""
    id: str
    user_id: str
    assessment_id: Optional[str]
    feedback_type: str
    channel: str
    rating: Optional[int]
    title: Optional[str]
    comments: Optional[str]
    sentiment: Optional[str]
    processed: bool
    created_at: str


@router.get("/health")
async def feedback_health_check():
    """Health check endpoint for feedback system."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "feedback_collection": "operational",
            "database": "operational",
            "analytics_engine": "operational"
        }
    }



@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: SubmitFeedbackRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit feedback (accessible to all authenticated users)."""
    try:
        # Validate feedback type
        try:
            feedback_type = FeedbackType(request.feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feedback type: {request.feedback_type}"
            )
        
        # Validate channel
        try:
            channel = FeedbackChannel(request.channel)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feedback channel: {request.channel}"
            )
        
        # Basic sentiment analysis (simplified)
        sentiment = None
        if request.rating:
            if request.rating >= 4:
                sentiment = SentimentScore.POSITIVE
            elif request.rating <= 2:
                sentiment = SentimentScore.NEGATIVE
            else:
                sentiment = SentimentScore.NEUTRAL
        
        # Create feedback record
        feedback = UserFeedback(
            user_id=str(current_user.id),
            assessment_id=request.assessment_id,
            feedback_type=feedback_type,
            channel=channel,
            rating=request.rating,
            title=request.title,
            comments=request.comments,
            sentiment=sentiment,
            tags=request.tags,
            processed=False
        )
        await feedback.insert()
        
        return {
            "feedback_id": str(feedback.id),
            "status": "submitted",
            "submitted_by": current_user.email,
            "submitted_at": feedback.created_at.isoformat(),
            "sentiment": sentiment.value if sentiment else None,
            "message": "Feedback submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum results"),
    current_user: User = Depends(require_enterprise_access)
):
    """List feedback entries with optional filters (admin only)."""
    try:
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        if assessment_id:
            query["assessment_id"] = assessment_id
        if feedback_type:
            try:
                query["feedback_type"] = FeedbackType(feedback_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid feedback type: {feedback_type}"
                )
        if channel:
            try:
                query["channel"] = FeedbackChannel(channel)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid channel: {channel}"
                )
        if sentiment:
            try:
                query["sentiment"] = SentimentScore(sentiment)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sentiment: {sentiment}"
                )
        if processed is not None:
            query["processed"] = processed
        
        # Fetch feedback from database
        feedback_list = await UserFeedback.find(query).sort(-UserFeedback.created_at).limit(limit).to_list()
        
        # Convert to response format
        result = []
        for fb in feedback_list:
            result.append(FeedbackResponse(
                id=str(fb.id),
                user_id=fb.user_id,
                assessment_id=fb.assessment_id,
                feedback_type=fb.feedback_type.value,
                channel=fb.channel.value,
                rating=fb.rating,
                title=fb.title,
                comments=fb.comments,
                sentiment=fb.sentiment.value if fb.sentiment else None,
                processed=fb.processed,
                created_at=fb.created_at.isoformat()
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list feedback: {str(e)}"
        )


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(require_enterprise_access)
):
    """Get feedback details (admin only)."""
    try:
        feedback = await UserFeedback.get(feedback_id)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return {
            "id": str(feedback.id),
            "user_id": feedback.user_id,
            "assessment_id": feedback.assessment_id,
            "feedback_type": feedback.feedback_type.value,
            "channel": feedback.channel.value,
            "rating": feedback.rating,
            "title": feedback.title,
            "comments": feedback.comments,
            "sentiment": feedback.sentiment.value if feedback.sentiment else None,
            "keywords": feedback.keywords,
            "tags": feedback.tags,
            "priority": feedback.priority,
            "processed": feedback.processed,
            "processed_at": feedback.processed_at.isoformat() if feedback.processed_at else None,
            "created_at": feedback.created_at.isoformat(),
            "updated_at": feedback.updated_at.isoformat(),
            "user_attributes": feedback.user_attributes,
            "session_id": feedback.session_id,
            "page_url": feedback.page_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


@router.get("/analytics/dashboard")
async def get_feedback_analytics(
    current_user: User = Depends(require_enterprise_access)
):
    """Get comprehensive feedback analytics dashboard (admin only)."""
    try:
        # Get basic counts
        total_feedback = await UserFeedback.find().count()
        processed_feedback = await UserFeedback.find(UserFeedback.processed == True).count()

        # Get average rating
        all_feedback = await UserFeedback.find(UserFeedback.rating != None).to_list()
        avg_rating = sum(fb.rating for fb in all_feedback if fb.rating) / len(all_feedback) if all_feedback else 0

        # Sentiment breakdown
        positive_count = await UserFeedback.find(UserFeedback.sentiment == SentimentScore.POSITIVE).count()
        neutral_count = await UserFeedback.find(UserFeedback.sentiment == SentimentScore.NEUTRAL).count()
        negative_count = await UserFeedback.find(UserFeedback.sentiment == SentimentScore.NEGATIVE).count()
        
        # Channel performance
        channel_stats = {}
        for channel in FeedbackChannel:
            count = await UserFeedback.find(UserFeedback.channel == channel).count()
            if count > 0:
                channel_feedback = await UserFeedback.find(
                    UserFeedback.channel == channel,
                    UserFeedback.rating != None
                ).to_list()
                avg_channel_rating = sum(fb.rating for fb in channel_feedback if fb.rating) / len(channel_feedback) if channel_feedback else 0

                channel_stats[channel.value] = {
                    "count": count,
                    "avg_rating": round(avg_channel_rating, 2)
                }

        # Category scores
        category_stats = {}
        for fb_type in FeedbackType:
            count = await UserFeedback.find(UserFeedback.feedback_type == fb_type).count()
            if count > 0:
                type_feedback = await UserFeedback.find(
                    UserFeedback.feedback_type == fb_type,
                    UserFeedback.rating != None
                ).to_list()
                avg_type_rating = sum(fb.rating for fb in type_feedback if fb.rating) / len(type_feedback) if type_feedback else 0

                category_stats[fb_type.value] = round(avg_type_rating, 2)
        
        # Calculate response rate (simplified - assume 100 total possible responses)
        response_rate = min(total_feedback / 100, 1.0) if total_feedback else 0
        
        # Calculate sentiment score
        total_sentiment_feedback = positive_count + neutral_count + negative_count
        sentiment_score = 0
        if total_sentiment_feedback > 0:
            sentiment_score = (positive_count * 1 + neutral_count * 0.5) / total_sentiment_feedback
        
        return {
            "overview": {
                "total_feedback": total_feedback,
                "processed_feedback": processed_feedback,
                "avg_rating": round(avg_rating, 2),
                "response_rate": round(response_rate, 3),
                "sentiment_score": round(sentiment_score, 3)
            },
            "sentiment_breakdown": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            },
            "channel_performance": channel_stats,
            "category_scores": category_stats,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback analytics: {str(e)}"
        )


@router.get("/summary/period")
async def get_feedback_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_enterprise_access)
):
    """Get feedback summary for specified period (admin only)."""
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get feedback within period
        period_feedback = await UserFeedback.find(
            UserFeedback.created_at >= start_date,
            UserFeedback.created_at <= end_date
        ).to_list()
        
        # Calculate metrics
        total_feedback = len(period_feedback)
        avg_rating = 0
        sentiment_breakdown = {"positive": 0, "neutral": 0, "negative": 0}
        category_breakdown = {}
        
        if total_feedback > 0:
            # Average rating
            ratings = [fb.rating for fb in period_feedback if fb.rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Sentiment breakdown
            for fb in period_feedback:
                if fb.sentiment:
                    sentiment_breakdown[fb.sentiment.value] += 1
            
            # Category breakdown
            for fb in period_feedback:
                category = fb.feedback_type.value
                if category not in category_breakdown:
                    category_breakdown[category] = {"count": 0, "ratings": []}
                category_breakdown[category]["count"] += 1
                if fb.rating:
                    category_breakdown[category]["ratings"].append(fb.rating)
        
        # Calculate category averages
        top_categories = []
        for category, data in category_breakdown.items():
            avg_category_rating = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 0
            top_categories.append({
                "category": category,
                "count": data["count"],
                "avg_rating": round(avg_category_rating, 2)
            })
        
        # Sort by count
        top_categories.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_feedback": total_feedback,
            "avg_rating": round(avg_rating, 2),
            "sentiment_breakdown": sentiment_breakdown,
            "top_categories": top_categories[:5],
            "improvement_opportunities": [
                "Increase feedback collection rate",
                "Address negative sentiment feedback",
                "Improve response to feature requests"
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback summary: {str(e)}"
        )
