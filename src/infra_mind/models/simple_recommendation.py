"""
Simplified recommendation model for testing quality assurance.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class Recommendation:
    """Simplified recommendation model for testing."""
    recommendation_id: str
    service_name: str
    provider: str
    cost_estimate: float
    configuration: Dict[str, Any]
    features: List[str]
    confidence_score: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Assessment:
    """Simplified assessment model for testing."""
    assessment_id: str
    business_requirements: Dict[str, Any]
    technical_requirements: Dict[str, Any]
    compliance_requirements: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class User:
    """Simplified user model for testing."""
    user_id: str
    email: str
    full_name: str
    role: str = "user"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()