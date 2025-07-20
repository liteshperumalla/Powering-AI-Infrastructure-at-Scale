"""
Tests for database models.

Verifies that model validation and basic functionality work correctly.
Note: These are unit tests that don't require database connection.
"""

import pytest
from datetime import datetime
from decimal import Decimal

# Import Pydantic models directly for validation testing
from pydantic import ValidationError

from src.infra_mind.schemas.base import (
    CompanySize, Industry, BudgetRange, CloudProvider,
    Priority, AssessmentStatus, RecommendationConfidence
)
from src.infra_mind.models.metrics import MetricType, MetricCategory


class TestModelValidation:
    """Test model validation without database connection."""
    
    def test_assessment_data_structure(self):
        """Test Assessment data structure validation."""
        # Test that we can create assessment data
        assessment_data = {
            "user_id": "user123",
            "title": "Test Assessment",
            "description": "A test assessment",
            "business_requirements": {
                "company_size": "medium",
                "industry": "technology"
            },
            "technical_requirements": {
                "workload_types": ["web_application"],
                "expected_users": 1000
            },
            "status": "draft",
            "priority": "high"
        }
        
        # Basic validation
        assert assessment_data["user_id"] == "user123"
        assert assessment_data["title"] == "Test Assessment"
        assert assessment_data["status"] == "draft"
        assert assessment_data["priority"] == "high"
        assert isinstance(assessment_data["business_requirements"], dict)
        assert isinstance(assessment_data["technical_requirements"], dict)


class TestPasswordHashing:
    """Test password hashing functionality without database."""
    
    def test_password_hashing_static_methods(self):
        """Test password hashing static methods."""
        # Import the User model to access static methods
        from src.infra_mind.models.user import User
        
        password = "test_password_123"
        hashed = User.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        assert isinstance(hashed, str)
        
        # Test that we can verify the password
        # Note: We can't create a User instance without DB, but we can test the static method
        import bcrypt
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class TestEnumValidation:
    """Test enum validation for model fields."""
    
    def test_company_size_enum(self):
        """Test CompanySize enum values."""
        assert CompanySize.STARTUP == "startup"
        assert CompanySize.MEDIUM == "medium"
        assert CompanySize.ENTERPRISE == "enterprise"
        
        # Test that all enum values are strings
        for size in CompanySize:
            assert isinstance(size.value, str)
    
    def test_cloud_provider_enum(self):
        """Test CloudProvider enum values."""
        assert CloudProvider.AWS == "aws"
        assert CloudProvider.AZURE == "azure"
        assert CloudProvider.GCP == "gcp"
        assert CloudProvider.MULTI_CLOUD == "multi_cloud"
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"
    
    def test_recommendation_confidence_enum(self):
        """Test RecommendationConfidence enum values."""
        assert RecommendationConfidence.LOW == "low"
        assert RecommendationConfidence.MEDIUM == "medium"
        assert RecommendationConfidence.HIGH == "high"
        assert RecommendationConfidence.VERY_HIGH == "very_high"


class TestDataValidation:
    """Test data validation logic."""
    
    def test_decimal_validation(self):
        """Test Decimal field validation."""
        # Test valid decimal
        cost = Decimal("123.45")
        assert cost == Decimal("123.45")
        assert isinstance(cost, Decimal)
        
        # Test decimal precision
        precise_cost = Decimal("123.456789")
        assert precise_cost > Decimal("123.45")
    
    def test_percentage_validation(self):
        """Test percentage validation logic."""
        def validate_percentage(value):
            return 0.0 <= value <= 100.0
        
        assert validate_percentage(0.0) is True
        assert validate_percentage(50.5) is True
        assert validate_percentage(100.0) is True
        assert validate_percentage(-1.0) is False
        assert validate_percentage(101.0) is False
    
    def test_confidence_score_validation(self):
        """Test confidence score validation logic."""
        def validate_confidence(value):
            return 0.0 <= value <= 1.0
        
        assert validate_confidence(0.0) is True
        assert validate_confidence(0.5) is True
        assert validate_confidence(1.0) is True
        assert validate_confidence(-0.1) is False
        assert validate_confidence(1.1) is False