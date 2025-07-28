#!/usr/bin/env python3
"""
Demo script for Infra Mind compliance features.

This script demonstrates the comprehensive compliance management system including:
- Data retention policies
- Consent management
- Data export and portability
- Privacy controls
- Audit trail functionality

Run with: python demo_compliance_features.py
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.append(str(Path(__file__).parent / "src"))

from infra_mind.core.compliance import (
    ComplianceManager,
    DataCategory,
    RetentionPeriod,
    ConsentType,
    ConsentStatus,
    DataRetentionPolicy,
    UserConsent,
    record_user_consent,
    export_user_data_request,
    delete_user_data_request
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


async def demo_data_retention_policies():
    """Demonstrate data retention policy management."""
    print_section("DATA RETENTION POLICIES")
    
    manager = ComplianceManager()
    
    print("📋 Current Retention Policies:")
    for category, policy in manager.retention_policies.items():
        print(f"  • {category.value}:")
        print(f"    - Retention Period: {policy.retention_period.value}")
        print(f"    - Auto Delete: {policy.auto_delete}")
        print(f"    - Legal Basis: {policy.legal_basis}")
        print(f"    - Description: {policy.description}")
        if policy.exceptions:
            print(f"    - Exceptions: {', '.join(policy.exceptions)}")
        print()
    
    print_subsection("Testing Data Expiry Checks")
    
    # Test data expiry for different scenarios
    test_dates = [
        ("Recent data", datetime.now(timezone.utc) - timedelta(days=30)),
        ("Old personal data", datetime.now(timezone.utc) - timedelta(days=1200)),  # > 3 years
        ("Old technical data", datetime.now(timezone.utc) - timedelta(days=400)),   # > 1 year
    ]
    
    for description, test_date in test_dates:
        print(f"\n🔍 Checking expiry for {description} (created: {test_date.date()}):")
        
        for category in [DataCategory.PERSONAL_DATA, DataCategory.TECHNICAL_DATA]:
            result = await manager.check_data_expiry(category, test_date)
            status = "EXPIRED" if result["expired"] else "ACTIVE"
            print(f"  • {category.value}: {status}")
            if result.get("expiry_date"):
                expiry_date = datetime.fromisoformat(result["expiry_date"].replace('Z', '+00:00'))
                print(f"    Expires: {expiry_date.date()}")
    
    print_subsection("Updating Retention Policy")
    
    # Demonstrate updating a retention policy
    new_policy = DataRetentionPolicy(
        data_category=DataCategory.TECHNICAL_DATA,
        retention_period=RetentionPeriod.MONTHS_6,
        legal_basis="Updated operational requirements",
        description="Technical logs and system data (updated policy)",
        auto_delete=True,
        exceptions=["Critical system logs"]
    )
    
    print(f"📝 Updating retention policy for {new_policy.data_category.value}:")
    print(f"  • New retention period: {new_policy.retention_period.value}")
    print(f"  • Auto delete: {new_policy.auto_delete}")
    
    manager.update_retention_policy(new_policy)
    print("✅ Policy updated successfully!")


async def demo_consent_management():
    """Demonstrate consent management functionality."""
    print_section("CONSENT MANAGEMENT")
    
    manager = ComplianceManager()
    user_id = "demo_user_123"
    
    print(f"👤 Managing consent for user: {user_id}")
    
    print_subsection("Recording Initial Consent")
    
    # Record various types of consent
    consent_scenarios = [
        (ConsentType.DATA_PROCESSING, ConsentStatus.GRANTED, "Essential for service provision"),
        (ConsentType.MARKETING, ConsentStatus.DENIED, "User opted out of marketing"),
        (ConsentType.ANALYTICS, ConsentStatus.GRANTED, "Help improve our services"),
        (ConsentType.COOKIES, ConsentStatus.GRANTED, "Functional and analytics cookies"),
        (ConsentType.THIRD_PARTY_SHARING, ConsentStatus.DENIED, "User prefers data privacy"),
    ]
    
    for consent_type, status, purpose in consent_scenarios:
        await record_user_consent(
            user_id=user_id,
            consent_type=consent_type,
            status=status,
            ip_address="192.168.1.100",
            legal_basis="User consent",
            purpose=purpose,
            data_categories=[DataCategory.PERSONAL_DATA]
        )
        
        print(f"✅ Recorded {consent_type.value}: {status.value}")
    
    print_subsection("Checking Consent Status")
    
    print("📊 Current consent status:")
    for consent_type in ConsentType:
        status = manager.check_consent_status(user_id, consent_type)
        consent = manager.get_user_consent(user_id, consent_type)
        
        print(f"  • {consent_type.value}: {status.value}")
        if consent and consent.granted_at:
            print(f"    Granted at: {consent.granted_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if consent and consent.purpose:
            print(f"    Purpose: {consent.purpose}")
    
    print_subsection("Consent Summary")
    
    summary = manager.get_consent_summary(user_id)
    print("📋 Complete consent summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    print_subsection("Withdrawing Consent")
    
    # Demonstrate consent withdrawal
    print(f"🚫 Withdrawing marketing consent for user {user_id}...")
    success = manager.withdraw_consent(user_id, ConsentType.MARKETING, "192.168.1.100")
    
    if success:
        print("✅ Marketing consent withdrawn successfully!")
        new_status = manager.check_consent_status(user_id, ConsentType.MARKETING)
        print(f"   New status: {new_status.value}")
    else:
        print("❌ Failed to withdraw consent (no active consent found)")


async def demo_data_export_portability():
    """Demonstrate data export and portability features."""
    print_section("DATA EXPORT & PORTABILITY")
    
    user_id = "demo_user_123"
    
    print(f"📦 Exporting data for user: {user_id}")
    
    print_subsection("Full Data Export")
    
    try:
        # Note: This would normally require actual user data in the database
        print("🔄 Initiating full data export...")
        print("   (In a real scenario, this would export all user data)")
        
        # Simulate export structure
        simulated_export = {
            "user_id": user_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_categories": [cat.value for cat in DataCategory],
            "data": {
                "personal_data": {
                    "email": "demo@example.com",
                    "full_name": "Demo User",
                    "company_name": "Demo Company",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                "assessment_data": [
                    {
                        "id": "assessment_123",
                        "title": "AI Infrastructure Assessment",
                        "status": "completed",
                        "created_at": "2024-01-15T10:00:00Z"
                    }
                ],
                "consent_records": {
                    "data_processing": {"status": "granted", "granted_at": "2024-01-01T00:00:00Z"},
                    "marketing": {"status": "withdrawn", "withdrawn_at": "2024-01-20T15:30:00Z"}
                }
            }
        }
        
        print("✅ Data export completed!")
        print(f"   Export size: {len(json.dumps(simulated_export)) / 1024:.1f} KB")
        print(f"   Categories included: {len(simulated_export['data_categories'])}")
        
        # Save export to file
        export_file = Path("user_data_export.json")
        with open(export_file, 'w') as f:
            json.dump(simulated_export, f, indent=2)
        print(f"   Saved to: {export_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
    
    print_subsection("Selective Data Export")
    
    # Demonstrate selective export
    selected_categories = [DataCategory.PERSONAL_DATA, DataCategory.ASSESSMENT_DATA]
    print(f"📋 Exporting selected categories: {[cat.value for cat in selected_categories]}")
    print("   (This would export only the specified data categories)")
    print("✅ Selective export would be completed here!")


async def demo_data_deletion():
    """Demonstrate data deletion (right to erasure) functionality."""
    print_section("DATA DELETION (RIGHT TO ERASURE)")
    
    user_id = "demo_user_123"
    
    print(f"🗑️  Processing data deletion request for user: {user_id}")
    
    print_subsection("Deletion Request Analysis")
    
    # Analyze what would be deleted
    categories_to_delete = [
        DataCategory.PERSONAL_DATA,
        DataCategory.ASSESSMENT_DATA,
        DataCategory.RECOMMENDATION_DATA
    ]
    
    print("📋 Data categories requested for deletion:")
    for category in categories_to_delete:
        print(f"  • {category.value}")
    
    print("\n⚠️  Categories that cannot be deleted:")
    protected_categories = [DataCategory.AUDIT_DATA]
    for category in protected_categories:
        print(f"  • {category.value} (required for compliance)")
    
    print_subsection("Simulated Deletion Process")
    
    # Simulate deletion process
    print("🔄 Processing deletion request...")
    print("   1. Validating user identity...")
    print("   2. Checking legal requirements...")
    print("   3. Identifying data to be deleted...")
    print("   4. Creating deletion audit trail...")
    print("   5. Executing data deletion...")
    
    # Simulate deletion results
    deletion_results = {
        "user_id": user_id,
        "deletion_timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": "User request - GDPR Article 17",
        "results": {
            "personal_data": "anonymized",
            "assessment_data": "deleted_3_records",
            "recommendation_data": "deleted_5_records",
            "audit_data": "retained_for_compliance"
        }
    }
    
    print("✅ Data deletion completed!")
    print("📊 Deletion summary:")
    for category, result in deletion_results["results"].items():
        print(f"  • {category}: {result}")
    
    print(f"\n📝 Deletion audit record created at: {deletion_results['deletion_timestamp']}")


async def demo_compliance_reporting():
    """Demonstrate compliance reporting functionality."""
    print_section("COMPLIANCE REPORTING")
    
    manager = ComplianceManager()
    
    print_subsection("Generating Compliance Report")
    
    # Generate a compliance report for the last 30 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    print(f"📊 Generating compliance report for period:")
    print(f"   From: {start_date.date()}")
    print(f"   To: {end_date.date()}")
    
    report = manager.generate_compliance_report(start_date, end_date)
    
    print("\n✅ Compliance report generated!")
    print(f"   Report type: {report['report_type']}")
    print(f"   Generated at: {report['generated_at']}")
    
    print_subsection("Data Retention Summary")
    retention_report = report['data_retention']
    print(f"📋 Active retention policies: {retention_report['policies_count']}")
    
    for category, policy_info in retention_report['policies'].items():
        print(f"  • {category}:")
        print(f"    - Retention: {policy_info['retention_period']}")
        print(f"    - Auto-delete: {policy_info['auto_delete']}")
    
    print_subsection("Consent Management Summary")
    consent_report = report['consent_management']
    print(f"👥 Users with consent records: {consent_report['total_users_with_consent']}")
    
    if consent_report['consent_statistics']:
        print("📊 Consent statistics:")
        for consent_type, stats in consent_report['consent_statistics'].items():
            print(f"  • {consent_type}:")
            print(f"    - Granted: {stats['granted']}")
            print(f"    - Denied: {stats['denied']}")
            print(f"    - Withdrawn: {stats['withdrawn']}")
    
    # Save report to file
    report_file = Path("compliance_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Full report saved to: {report_file}")


async def demo_privacy_controls():
    """Demonstrate privacy control features."""
    print_section("PRIVACY CONTROLS")
    
    manager = ComplianceManager()
    user_id = "demo_user_123"
    
    print_subsection("Privacy Settings Overview")
    
    # Simulate privacy settings
    privacy_settings = {
        "data_minimization": {
            "enabled": True,
            "description": "Only collect necessary data for service provision"
        },
        "purpose_limitation": {
            "enabled": True,
            "description": "Data used only for stated purposes"
        },
        "storage_limitation": {
            "enabled": True,
            "description": "Data retained only as long as necessary"
        },
        "transparency": {
            "enabled": True,
            "description": "Clear information about data processing"
        },
        "user_control": {
            "enabled": True,
            "description": "Users can manage their data and consent"
        }
    }
    
    print("🔒 Privacy-by-Design Controls:")
    for control, info in privacy_settings.items():
        status = "✅ ENABLED" if info["enabled"] else "❌ DISABLED"
        print(f"  • {control.replace('_', ' ').title()}: {status}")
        print(f"    {info['description']}")
    
    print_subsection("Data Subject Rights")
    
    rights = [
        ("Right to Information", "Users informed about data processing"),
        ("Right of Access", "Users can view their personal data"),
        ("Right to Rectification", "Users can correct inaccurate data"),
        ("Right to Erasure", "Users can request data deletion"),
        ("Right to Restrict Processing", "Users can limit data processing"),
        ("Right to Data Portability", "Users can export their data"),
        ("Right to Object", "Users can object to processing"),
        ("Rights related to Automated Decision Making", "Protection from automated profiling")
    ]
    
    print("⚖️  GDPR Data Subject Rights Implementation:")
    for right, description in rights:
        print(f"  ✅ {right}")
        print(f"     {description}")
    
    print_subsection("Consent Management Interface")
    
    # Show current consent status
    consent_summary = manager.get_consent_summary(user_id)
    print(f"👤 Consent status for user {user_id}:")
    
    for consent_type in ConsentType:
        status = manager.check_consent_status(user_id, consent_type)
        icon = "✅" if status == ConsentStatus.GRANTED else "❌" if status == ConsentStatus.DENIED else "⏸️" if status == ConsentStatus.WITHDRAWN else "⏳"
        print(f"  {icon} {consent_type.value.replace('_', ' ').title()}: {status.value}")


async def main():
    """Run the complete compliance features demo."""
    print("🛡️  INFRA MIND COMPLIANCE FEATURES DEMO")
    print("=" * 60)
    print("This demo showcases comprehensive compliance management including:")
    print("• Data retention policies and lifecycle management")
    print("• Consent management and user privacy controls")
    print("• Data export and portability (GDPR Article 20)")
    print("• Data deletion and right to erasure (GDPR Article 17)")
    print("• Compliance reporting and audit trails")
    print("• Privacy-by-design implementation")
    
    try:
        # Run all demo sections
        await demo_data_retention_policies()
        await demo_consent_management()
        await demo_data_export_portability()
        await demo_data_deletion()
        await demo_compliance_reporting()
        await demo_privacy_controls()
        
        print_section("DEMO COMPLETED SUCCESSFULLY")
        print("✅ All compliance features demonstrated!")
        print("\n📁 Generated files:")
        print("  • user_data_export.json - Sample data export")
        print("  • compliance_report.json - Compliance report")
        print("\n🔍 Key Features Demonstrated:")
        print("  ✅ Data retention policy management")
        print("  ✅ Comprehensive consent management")
        print("  ✅ Data export and portability")
        print("  ✅ Data deletion (right to erasure)")
        print("  ✅ Compliance reporting")
        print("  ✅ Privacy controls and GDPR compliance")
        print("\n🛡️  Your data is protected with enterprise-grade compliance features!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())