"""
Additional compliance check implementations for SOC 2 and ISO 27001.
These functions should be added to the ComplianceCheckEngine class.
"""

from typing import Tuple, Dict, List, Any
from .compliance_engine import CheckStatus

# ========== SOC 2 CHECK IMPLEMENTATIONS ==========

async def _check_soc2_access_controls(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check SOC 2 access controls."""
    return await self._check_workforce_authorization(assessment)


async def _check_soc2_user_provisioning(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check user provisioning process."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_provisioning = any([
            'provisioning' in str(security_config).lower(),
            'onboarding' in str(security_config).lower(),
            'user lifecycle' in str(security_config).lower(),
            'access request' in str(security_config).lower()
        ])

        if has_provisioning:
            return (CheckStatus.PASS, {'user_provisioning_documented': True}, [])
        else:
            return (CheckStatus.FAIL, {'user_provisioning_documented': False}, ['User management system'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_monitoring(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check system monitoring."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_monitoring = any([
            'monitoring' in str(security_config).lower(),
            'cloudwatch' in str(security_config).lower(),
            'observability' in str(security_config).lower(),
            'siem' in str(security_config).lower(),
            'alerts' in str(security_config).lower()
        ])

        if has_monitoring:
            return (CheckStatus.PASS, {'system_monitoring_enabled': True}, [])
        else:
            return (CheckStatus.FAIL, {'system_monitoring_enabled': False}, ['All systems'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_change_management(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check change management procedures."""
    try:
        # Check for CI/CD or change management indicators
        infrastructure = assessment.technical_requirements.get('infrastructure_requirements', {}) if assessment.technical_requirements else {}

        has_change_mgmt = any([
            'ci/cd' in str(infrastructure).lower(),
            'change management' in str(infrastructure).lower(),
            'deployment' in str(infrastructure).lower(),
            'pipeline' in str(infrastructure).lower()
        ])

        if has_change_mgmt:
            return (CheckStatus.PASS, {'change_management_implemented': True}, [])
        else:
            return (CheckStatus.FAIL, {'change_management_implemented': False}, ['Development process'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_availability(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check availability commitments."""
    try:
        requirements = assessment.technical_requirements.get('performance_requirements', {}) if assessment.technical_requirements else {}

        has_availability = any([
            'availability' in str(requirements).lower(),
            'uptime' in str(requirements).lower(),
            'sla' in str(requirements).lower(),
            'redundancy' in str(requirements).lower(),
            'failover' in str(requirements).lower()
        ])

        if has_availability:
            return (CheckStatus.PASS, {'availability_controls_implemented': True}, [])
        else:
            return (CheckStatus.FAIL, {'availability_controls_implemented': False}, ['Critical systems'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_risk_assessment(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check risk assessment procedures."""
    try:
        # This assessment itself counts as a risk assessment
        if assessment.created_at:
            return (CheckStatus.PASS, {'risk_assessment_conducted': True, 'last_assessment': assessment.created_at.isoformat()}, [])
        else:
            return (CheckStatus.FAIL, {'risk_assessment_conducted': False}, ['Security program'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_training(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check security awareness training."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_training = any([
            'training' in str(security_config).lower(),
            'awareness' in str(security_config).lower(),
            'education' in str(security_config).lower()
        ])

        if has_training:
            return (CheckStatus.PASS, {'training_program_exists': True}, [])
        else:
            return (CheckStatus.FAIL, {'training_program_exists': False}, ['All personnel'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_control_activities(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check control activities."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_controls = any([
            'control' in str(security_config).lower(),
            'security' in str(security_config).lower()
        ])

        if has_controls:
            return (CheckStatus.PASS, {'controls_documented': True}, [])
        else:
            return (CheckStatus.FAIL, {'controls_documented': False}, ['Security program'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_soc2_vendor_management(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check vendor management."""
    try:
        business_reqs = assessment.business_requirements if assessment.business_requirements else {}

        has_vendor_mgmt = any([
            'vendor' in str(business_reqs).lower(),
            'third party' in str(business_reqs).lower(),
            'supplier' in str(business_reqs).lower()
        ])

        if has_vendor_mgmt:
            return (CheckStatus.PASS, {'vendor_management_process_exists': True}, [])
        else:
            return (CheckStatus.PARTIAL, {'vendor_management_process_exists': False}, ['Vendor relationships'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


# ========== ISO 27001 CHECK IMPLEMENTATIONS ==========

async def _check_iso_security_policy(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check information security policy."""
    try:
        # Check if security requirements are documented
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_policy = any([
            'policy' in str(security_config).lower(),
            'security' in str(security_config).lower()
        ])

        if has_policy:
            return (CheckStatus.PASS, {'security_policy_exists': True}, [])
        else:
            return (CheckStatus.FAIL, {'security_policy_exists': False}, ['Organization-wide'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_segregation_duties(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check segregation of duties."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_segregation = any([
            'segregation' in str(security_config).lower(),
            'separation of duties' in str(security_config).lower(),
            'dual control' in str(security_config).lower()
        ])

        if has_segregation:
            return (CheckStatus.PASS, {'segregation_of_duties_implemented': True}, [])
        else:
            return (CheckStatus.FAIL, {'segregation_of_duties_implemented': False}, ['Critical processes'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_asset_inventory(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check asset inventory."""
    try:
        infrastructure = assessment.technical_requirements.get('infrastructure_requirements', {}) if assessment.technical_requirements else {}

        has_inventory = any([
            'inventory' in str(infrastructure).lower(),
            'asset' in str(infrastructure).lower(),
            'cmdb' in str(infrastructure).lower()
        ])

        if has_inventory:
            return (CheckStatus.PASS, {'asset_inventory_maintained': True}, [])
        else:
            return (CheckStatus.FAIL, {'asset_inventory_maintained': False}, ['All information assets'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_privileged_access(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check privileged access management."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_pam = any([
            'privileged' in str(security_config).lower(),
            'admin' in str(security_config).lower(),
            'pam' in str(security_config).lower(),
            'bastion' in str(security_config).lower()
        ])

        if has_pam:
            return (CheckStatus.PASS, {'privileged_access_managed': True}, [])
        else:
            return (CheckStatus.FAIL, {'privileged_access_managed': False}, ['Administrative accounts'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_crypto_policy(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check cryptographic controls policy."""
    try:
        security_config = assessment.technical_requirements.get('security_requirements', {}) if assessment.technical_requirements else {}

        has_crypto_policy = any([
            'encryption' in str(security_config).lower(),
            'cryptograph' in str(security_config).lower(),
            'kms' in str(security_config).lower()
        ])

        if has_crypto_policy:
            return (CheckStatus.PASS, {'crypto_policy_exists': True}, [])
        else:
            return (CheckStatus.FAIL, {'crypto_policy_exists': False}, ['Encryption practices'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_key_management(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check key management."""
    try:
        infrastructure = assessment.technical_requirements.get('infrastructure_requirements', {}) if assessment.technical_requirements else {}

        has_key_mgmt = any([
            'kms' in str(infrastructure).lower(),
            'key management' in str(infrastructure).lower(),
            'vault' in str(infrastructure).lower()
        ])

        if has_key_mgmt:
            return (CheckStatus.PASS, {'key_management_implemented': True}, [])
        else:
            return (CheckStatus.FAIL, {'key_management_implemented': False}, ['Cryptographic keys'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_operating_procedures(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check documented operating procedures."""
    try:
        # Check if there's any documentation
        has_docs = bool(assessment.technical_requirements) or bool(assessment.business_requirements)

        if has_docs:
            return (CheckStatus.PARTIAL, {'procedures_documented': True}, [])
        else:
            return (CheckStatus.FAIL, {'procedures_documented': False}, ['Operations'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])


async def _check_iso_legal_compliance(self, assessment: Any) -> Tuple[CheckStatus, Dict, List[str]]:
    """Check compliance with legal requirements."""
    try:
        # Check if compliance requirements are identified
        compliance_reqs = assessment.technical_requirements.get('compliance_requirements', []) if assessment.technical_requirements else []

        if compliance_reqs:
            return (CheckStatus.PASS, {'legal_requirements_identified': True, 'requirements': compliance_reqs}, [])
        else:
            return (CheckStatus.FAIL, {'legal_requirements_identified': False}, ['Regulatory compliance'])
    except Exception as e:
        return (CheckStatus.ERROR, {'error': str(e)}, [])
