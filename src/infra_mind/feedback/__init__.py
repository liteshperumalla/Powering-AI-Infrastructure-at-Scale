"""
User Feedback and Quality Validation System.

This package provides comprehensive user feedback capabilities including:
- Multi-channel feedback collection
- Sentiment analysis and categorization
- Quality scoring and validation
- Feedback analytics and reporting
- Automated improvement suggestions
"""

from .system import (
    FeedbackCollector, FeedbackAnalyzer, UserFeedback,
    FeedbackType, FeedbackCategory, FeedbackChannel
)

__all__ = [
    'FeedbackCollector',
    'FeedbackAnalyzer',
    'UserFeedback',
    'FeedbackType',
    'FeedbackCategory',
    'FeedbackChannel'
]