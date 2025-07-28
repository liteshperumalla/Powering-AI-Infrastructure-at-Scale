"""
Tests for compliance features including data retention, consent management,
data export/portability, and audit trail functionality.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId

from src.infra_mind.core.compliance import (
    ComplianceManager,
    DataCategory,
    RetentionPeriod,
    ConsentType,
    ConsentStatus,
    DataRetentionPolicy,
    UserConsent,
    compliance_manager,
    record_user_consent,
    export_user_data_request,
    delete_user_data_request
)
from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment


class TestDataRetentionPolicy:
    """Test data retention policy functionality."""
    
    def test_policy_creation(self):
        """Test creating a data retention policy."""
        policy = DataRetentionPolicy(
            data_category=DataCategory.PERSONAL_DATA,
            retention_period=RetentionPeriod.YEARS_3,
            legal_basis="GDPR compliance",
            description="Personal data retention",
            auto_delete=True,
            exceptions=["Active accounts"]
        )
        
        assert policy.data_category == DataCategory.PERSONAL_DATA
        assert policy.retention_period == RetentionPeriod.YEARS_3
        assert policy.auto_delete is True
        assert "Active accounts" in policy.exceptions
    
    def test_expiry_date_calculation(self):
        """Test expiry date calculation for different retention periods."""
        policy = DataRetentionPolicy(
            data_category=DataCategory.PERSONAL_DATA,
            retention_period=RetentionPeriod.DAYS_30,
            legal_basis="Test",
            description="Test policy"
        )
        
        created_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        expiry_date = policy.get_expiry_date(created_date)
        
        expected_expiry = created_date + timedelta(days=30)
        assert expiry_date == expected_expiry
    
    def test_indefinite_retention(self):
        """Test indefinite retention policy."""
        policy = DataRetentionPolicy(
            data_category=DataCategory.AUDIT_DATA,
            retention_period=RetentionPeriod.INDEFINITE,
            legal_basis="Legal requirement",
            description="Audit data"
        )
        
        created_date = datetime.now(timezone.utc)
        expiry_date = policy.get_expiry_date(created_date)
        
        assert expiry_date is None


class TestUserConsent:
    """Test user consent functionality."""
    
    def test_consent_creation(self):
        """Test creating a user consent record."""
        consent = UserConsent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            status=ConsentStatus.GRANTED,
            legal_basis="User consent",
            purpose="Service provision",
            data_categories=[DataCategory.PERSONAL_DATA]
        )
        
        assert consent.user_id == "user123"
        assert consent.consent_type == ConsentType.DATA_PROCESSING
        assert consent.status == ConsentStatus.GRANTED
        assert DataCategory.PERSONAL_DATA in consent.data_categories


class TestComplianceManager:
    """Test compliance manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a compliance manager instance for testing."""
        return ComplianceManager()
    
    def test_initialization(self, manager):
        """Test compliance manager initialization."""
        assert manager.retention_policies is not None
        assert len(manager.retention_policies) > 0
        assert DataCategory.PERSONAL_DATA in manager.retention_policies
    
    def test_get_retention_policy(self, manager):
        """Test getting retention policy for a data category."""
        policy = manager.get_retention_policy(DataCategory.PERSONAL_DATA)
        
        assert policy is not None
        assert policy.data_category == DataCategory.PERSONAL_DATA
        assert policy.retention_period == RetentionPeriod.YEARS_3
    
    def test_update_retention_policy(self, manager):
        """Test updating a retention policy."""
        new_policy = DataRetentionPolicy(
            data_category=DataCategory.TECHNICAL_DATA,
            retention_period=RetentionPeriod.MONTHS_6,
            legal_basis="Updated requirement",
            description="Updated technical data policy",
            auto_delete=False
        )
        
        manager.update_retention_policy(new_policy)
        
        retrieved_policy = manager.get_retention_policy(DataCategory.TECHNICAL_DATA)
        assert retrieved_policy.retention_period == RetentionPeriod.MONTHS_6
        assert retrieved_policy.auto_delete is False
    
    @pytest.mark.asyncio
    async def test_check_data_expiry(self, manager):
        """Test checking data expiry status."""
        # Test with expired data
        old_date = datetime.now(timezone.utc) - timedelta(days=400)  # Older than 1 year
        
        result = await manager.check_data_expiry(DataCategory.TECHNICAL_DATA, old_date)
        
        assert "expired" in result
        assert "expiry_date" in result
        assert "policy" in result
    
    @pytest.mark.asyncio
    async def test_schedule_data_deletion(self, manager):
        """Test scheduling data deletion."""
        user_id = "user123"
        categories = [DataCategory.PERSONAL_DATA, DataCategory.ASSESSMENT_DATA]
        
        result = await manager.schedule_data_deletion(user_id, categories)
        
        assert result["user_id"] == user_id
        assert "deletion_schedule" in result
        assert "scheduled_at" in result
    
    def test_record_consent(self, manager):
        """Test recording user consent."""
        consent = UserConsent(
            user_id="user123",
            consent_type=ConsentType.MARKETING,
            status=ConsentStatus.GRANTED,
            legal_basis="User consent"
        )
        
        manager.record_consent(consent)
        
        assert "user123" in manager.consent_records
        assert len(manager.consent_records["user123"]) == 1
        assert manager.consent_records["user123"][0].consent_type == ConsentType.MARKETING
    
    def test_get_user_consent(self, manager):
        """Test getting user consent."""
        # Record initial consent
        consent = UserConsent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            status=ConsentStatus.GRANTED
        )
        manager.record_consent(consent)
        
        # Retrieve consent
        retrieved_consent = manager.get_user_consent("user123", ConsentType.ANALYTICS)
        
        assert retrieved_consent is not None
        assert retrieved_consent.status == ConsentStatus.GRANTED
    
    def test_check_consent_status(self, manager):
        """Test checking consent status."""
        # Test with no consent recorded
        status = manager.check_consent_status("user123", ConsentType.COOKIES)
        assert status == ConsentStatus.PENDING
        
        # Record consent and test again
        consent = UserConsent(
            user_id="user123",
            consent_type=ConsentType.COOKIES,
            status=ConsentStatus.DENIED
        )
        manager.record_consent(consent)
        
        status = manager.check_consent_status("user123", ConsentType.COOKIES)
        assert status == ConsentStatus.DENIED
    
    def test_withdraw_consent(self, manager):
        """Test withdrawing user consent."""
        # First grant consent
        consent = UserConsent(
            user_id="user123",
            consent_type=ConsentType.PROFILING,
            status=ConsentStatus.GRANTED
        )
        manager.record_consent(consent)
        
        # Then withdraw it
        success = manager.withdraw_consent("user123", ConsentType.PROFILING)
        
        assert success is True
        
        # Check that consent is now withdrawn
        status = manager.check_consent_status("user123", ConsentType.PROFILING)
        assert status == ConsentStatus.WITHDRAWN
    
    def test_get_consent_summary(self, manager):
        """Test getting consent summary for a user."""
        user_id = "user123"
        
        # Record some consents
        consents = [
            UserConsent(user_id=user_id, consent_type=ConsentType.DATA_PROCESSING, status=ConsentStatus.GRANTED),
            UserConsent(user_id=user_id, consent_type=ConsentType.MARKETING, status=ConsentStatus.DENIED),
        ]
        
        for consent in consents:
            manager.record_consent(consent)
        
        summary = manager.get_consent_summary(user_id)
        
        assert summary["user_id"] == user_id
        assert "consent_summary" in summary
        assert summary["consent_summary"]["data_processing"]["status"] == "granted"
        assert summary["consent_summary"]["marketing"]["status"] == "denied"
    
    @pytest.mark.asyncio
    async def test_export_user_data(self, manager):
        """Test exporting user data."""
        user_id = str(ObjectId())
        
        # Mock User.get to return a test user
        with patch('src.infra_mind.core.compliance.User.get') as mock_get:
            mock_user = Mock()
            mock_user.email = "test@example.com"
            mock_user.full_name = "Test User"
            mock_user.company_name = "Test Company"
            mock_user.company_size = None
            mock_user.industry = None
            mock_user.job_title = "Developer"
            mock_user.preferred_cloud_providers = ["aws"]
            mock_user.notification_preferences = {"email_reports": True}
            mock_user.created_at = datetime.now(timezone.utc)
            mock_user.last_login = None
            mock_get.return_value = mock_user
            
            # Mock Assessment.find to return test assessments
            with patch('src.infra_mind.core.compliance.Assessment.find') as mock_find:
                mock_assessment = Mock()
                mock_assessment.id = ObjectId()
                mock_assessment.title = "Test Assessment"
                mock_assessment.description = "Test Description"
                mock_assessment.business_requirements = {}
                mock_assessment.technical_requirements = {}
                mock_assessment.status.value = "completed"
                mock_assessment.priority.value = "medium"
                mock_assessment.created_at = datetime.now(timezone.utc)
                mock_assessment.completed_at = None
                
                mock_find.return_value.to_list = AsyncMock(return_value=[mock_assessment])
                
                # Test export
                result = await manager.export_user_data(user_id)
                
                assert result["user_id"] == user_id
                assert "export_timestamp" in result
                assert "data" in result
                assert "personal_data" in result["data"]
                assert result["data"]["personal_data"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_delete_user_data(self, manager):
        """Test deleting user data."""
        user_id = str(ObjectId())
        
        # Mock User.get to return a test user
        with patch('src.infra_mind.core.compliance.User.get') as mock_get:
            mock_user = Mock()
            mock_user.id = ObjectId(user_id)
            mock_user.email = "test@example.com"
            mock_user.save = AsyncMock()
            mock_get.return_value = mock_user
            
            # Mock Assessment.find to return test assessments
            with patch('src.infra_mind.core.compliance.Assessment.find') as mock_find:
                mock_assessment = Mock()
                mock_assessment.delete = AsyncMock()
                mock_find.return_value.to_list = AsyncMock(return_value=[mock_assessment])
                
                # Test deletion
                result = await manager.delete_user_data(user_id, reason="User request")
                
                assert result["user_id"] == user_id
                assert result["reason"] == "User request"
                assert "results" in result
                assert "personal_data" in result["results"]
    
    def test_generate_compliance_report(self, manager):
        """Test generating compliance report."""
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        report = manager.generate_compliance_report(start_date, end_date)
        
        assert report["report_type"] == "compliance_report"
        assert "period" in report
        assert "data_retention" in report
        assert "consent_management" in report
        assert "data_requests" in report
        assert "audit_summary" in report


class TestConvenienceFunctions:
    """Test convenience functions for compliance operations."""
    
    @pytest.mark.asyncio
    async def test_record_user_consent(self):
        """Test recording user consent convenience function."""
        with patch.object(compliance_manager, 'record_consent') as mock_record:
            await record_user_consent(
                user_id="user123",
                consent_type=ConsentType.DATA_PROCESSING,
                status=ConsentStatus.GRANTED,
                legal_basis="User consent"
            )
            
            mock_record.assert_called_once()
            call_args = mock_record.call_args[0][0]
            assert call_args.user_id == "user123"
            assert call_args.consent_type == ConsentType.DATA_PROCESSING
            assert call_args.status == ConsentStatus.GRANTED
    
    @pytest.mark.asyncio
    async def test_export_user_data_request(self):
        """Test export user data request convenience function."""
        with patch.object(compliance_manager, 'export_user_data') as mock_export:
            mock_export.return_value = {"user_id": "user123", "data": {}}
            
            result = await export_user_data_request("user123", "192.168.1.1")
            
            mock_export.assert_called_once_with("user123")
            assert result["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_delete_user_data_request(self):
        """Test delete user data request convenience function."""
        with patch.object(compliance_manager, 'delete_user_data') as mock_delete:
            mock_delete.return_value = {"user_id": "user123", "results": {}}
            
            result = await delete_user_data_request("user123", "User request", "192.168.1.1")
            
            mock_delete.assert_called_once_with("user123", reason="User request")
            assert result["user_id"] == "user123"


class TestComplianceIntegration:
    """Test integration between compliance features and other system components."""
    
    @pytest.mark.asyncio
    async def test_gdpr_compliance_workflow(self):
        """Test complete GDPR compliance workflow."""
        manager = ComplianceManager()
        user_id = "gdpr_user"
        
        # 1. Record consent for data processing
        consent = UserConsent(
            user_id=user_id,
            consent_type=ConsentType.DATA_PROCESSING,
            status=ConsentStatus.GRANTED,
            legal_basis="GDPR Article 6(1)(a) - Consent",
            purpose="Service provision"
        )
        manager.record_consent(consent)
        
        # 2. Check consent status
        status = manager.check_consent_status(user_id, ConsentType.DATA_PROCESSING)
        assert status == ConsentStatus.GRANTED
        
        # 3. Export user data (Right to portability)
        with patch('src.infra_mind.core.compliance.User.get') as mock_get, \
             patch('src.infra_mind.core.compliance.Assessment.find') as mock_find:
            
            mock_get.return_value = None  # User not found
            mock_find.return_value.to_list = AsyncMock(return_value=[])
            
            export_result = await manager.export_user_data(user_id)
            assert export_result["user_id"] == user_id
        
        # 4. Withdraw consent
        success = manager.withdraw_consent(user_id, ConsentType.DATA_PROCESSING)
        assert success is True
        
        # 5. Verify consent is withdrawn
        status = manager.check_consent_status(user_id, ConsentType.DATA_PROCESSING)
        assert status == ConsentStatus.WITHDRAWN
        
        # 6. Request data deletion (Right to erasure)
        with patch('src.infra_mind.core.compliance.User.get') as mock_get, \
             patch('src.infra_mind.core.compliance.Assessment.find') as mock_find:
            
            mock_get.return_value = None  # User not found
            mock_find.return_value.to_list = AsyncMock(return_value=[])
            
            deletion_result = await manager.delete_user_data(user_id, reason="GDPR erasure request")
            assert deletion_result["user_id"] == user_id
    
    def test_data_retention_compliance(self):
        """Test data retention compliance across different categories."""
        manager = ComplianceManager()
        
        # Test that all required data categories have retention policies
        required_categories = [
            DataCategory.PERSONAL_DATA,
            DataCategory.BUSINESS_DATA,
            DataCategory.ASSESSMENT_DATA,
            DataCategory.AUDIT_DATA
        ]
        
        for category in required_categories:
            policy = manager.get_retention_policy(category)
            assert policy is not None, f"Missing retention policy for {category}"
            assert policy.legal_basis is not None
            assert policy.description is not None
        
        # Test that audit data has longer retention than personal data
        personal_policy = manager.get_retention_policy(DataCategory.PERSONAL_DATA)
        audit_policy = manager.get_retention_policy(DataCategory.AUDIT_DATA)
        
        # Audit data should be retained longer for compliance
        assert audit_policy.retention_period == RetentionPeriod.YEARS_7
        assert personal_policy.retention_period == RetentionPeriod.YEARS_3
    
    def test_consent_management_completeness(self):
        """Test that consent management covers all required consent types."""
        manager = ComplianceManager()
        user_id = "test_user"
        
        # Test all consent types can be managed
        for consent_type in ConsentType:
            # Grant consent
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.GRANTED
            )
            manager.record_consent(consent)
            
            # Verify consent is recorded
            status = manager.check_consent_status(user_id, consent_type)
            assert status == ConsentStatus.GRANTED
            
            # Withdraw consent
            success = manager.withdraw_consent(user_id, consent_type)
            assert success is True
            
            # Verify consent is withdrawn
            status = manager.check_consent_status(user_id, consent_type)
            assert status == ConsentStatus.WITHDRAWN


if __name__ == "__main__":
    pytest.main([__file__])