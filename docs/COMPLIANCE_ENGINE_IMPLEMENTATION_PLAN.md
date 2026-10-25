# Compliance Engine Implementation Plan

## Overview
Transform the compliance system from placeholder data to a fully functional compliance monitoring and assessment platform with real checks, scoring, and remediation tracking.

## Current State Analysis

### ✅ What Exists
- Basic compliance framework definitions (HIPAA, SOC 2, ISO 27001)
- Compliance dashboard API endpoint (`/api/v1/features/assessment/{id}/compliance`)
- Frontend compliance dashboard UI
- Framework metadata (versions, types)

### ❌ What's Missing (Hardcoded/Placeholder Data)
1. **No actual compliance checks executed**
   - `status: "pending_assessment"` hardcoded
   - `overall_compliance_score: 0` static
   - No requirements validation

2. **No findings/issues tracking**
   - `active_findings` always 0
   - No severity classification
   - No remediation tracking

3. **No automated monitoring**
   - `passing_checks: 0`, `failing_checks: 0` hardcoded
   - `last_run: "Never"` static
   - No check execution history

4. **No real calculations**
   - Compliance percentages not calculated from actual data
   - No trend analysis
   - No deadline tracking

## Implementation Phases

### Phase 1: Compliance Check Engine (CURRENT)
**Goal**: Execute real compliance checks against infrastructure

**Components to Build**:

#### 1.1 Compliance Check Definitions
```python
# src/infra_mind/services/compliance_checks.py

class ComplianceCheck:
    - check_id: str
    - framework: str (HIPAA, SOC2, ISO27001)
    - requirement_id: str
    - title: str
    - description: str
    - check_function: callable
    - severity: critical|high|medium|low
    - remediation_guidance: str

# Example checks:
- HIPAA_164_312_a_1: Encryption at rest
- SOC2_CC6_1: Logical access controls
- ISO27001_A_9_2_1: User registration
```

#### 1.2 Check Execution Engine
```python
# Executes checks against assessment data
async def run_compliance_checks(assessment, framework):
    results = []
    for check in get_framework_checks(framework):
        result = await execute_check(check, assessment)
        results.append(result)
    return results
```

#### 1.3 Check Result Schema
```python
{
    "check_id": "HIPAA_164_312_a_1",
    "status": "pass|fail|partial|not_applicable",
    "finding_severity": "critical",
    "affected_resources": ["db-prod-1", "s3-bucket-x"],
    "evidence": {...},
    "remediation_steps": [...]
}
```

### Phase 2: Scoring & Calculations
**Goal**: Calculate real compliance scores from check results

**Calculations**:

```python
# Overall Compliance Score
total_checks = len(checks)
passed_checks = len([c for c in results if c.status == 'pass'])
compliance_score = (passed_checks / total_checks) * 100

# Weighted Score (by severity)
weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
max_score = sum(weights[c.severity] for c in checks)
actual_score = sum(weights[c.severity] for c in passed_checks)
weighted_score = (actual_score / max_score) * 100

# Framework Status
if compliance_score >= 95: status = "compliant"
elif compliance_score >= 70: status = "partially_compliant"
else: status = "non_compliant"
```

### Phase 3: Findings & Remediation
**Goal**: Track issues and remediation progress

**Data Models**:

```python
class ComplianceFinding:
    - id: str
    - framework: str
    - check_id: str
    - severity: critical|high|medium|low
    - status: open|in_progress|resolved|accepted_risk
    - affected_resources: List[str]
    - discovered_date: datetime
    - due_date: datetime
    - assigned_to: str
    - remediation_steps: List[str]
    - evidence: Dict

class RemediationAction:
    - id: str
    - finding_id: str
    - title: str
    - status: pending|in_progress|completed|overdue
    - priority: int
    - estimated_effort: str
    - assigned_to: str
    - due_date: datetime
    - completion_date: Optional[datetime]
```

### Phase 4: Automated Monitoring
**Goal**: Continuous compliance monitoring

**Features**:
- Scheduled check execution (daily/weekly/monthly)
- Real-time monitoring for critical controls
- Alert notifications for new findings
- Compliance drift detection
- Historical trending

### Phase 5: Dashboard Integration
**Goal**: Display all real data in frontend

**API Updates**:
```python
{
    "overall_compliance_score": 78.5,  # Calculated from checks
    "frameworks": [
        {
            "name": "HIPAA",
            "status": "partially_compliant",  # From checks
            "overall_compliance_score": 82,   # Calculated
            "total_checks": 50,
            "passed_checks": 41,
            "failed_checks": 6,
            "partial_checks": 3
        }
    ],
    "active_findings": {
        "critical": 2,  # From failed checks
        "high": 5,
        "medium": 8,
        "low": 12
    },
    "remediation_progress": {
        "total_actions": 27,
        "completed_actions": 15,
        "in_progress_actions": 8,
        "overdue_actions": 4,
        "progress_percentage": 55.6  # 15/27
    },
    "automated_monitoring": {
        "total_checks": 150,
        "passing_checks": 118,
        "failing_checks": 27,
        "last_run": "2025-11-30T07:14:23Z"
    }
}
```

## Implementation Priority

### Week 1: Compliance Check Framework
1. Define check schema
2. Implement 10-15 critical checks per framework (HIPAA, SOC2, ISO27001)
3. Create check execution engine
4. Store results in database

### Week 2: Scoring & Calculations
1. Implement compliance scoring algorithms
2. Calculate framework status from checks
3. Generate findings from failed checks
4. Calculate weighted scores

### Week 3: Remediation Tracking
1. Create remediation action models
2. Track remediation progress
3. Calculate progress percentages
4. Implement deadline tracking

### Week 4: Dashboard Integration
1. Update API to return real data
2. Test frontend with real calculations
3. Add historical trending
4. Implement auto-refresh

## Quick Start: Immediate Implementation

### What to Build RIGHT NOW

**File**: `src/infra_mind/services/compliance_engine.py`

```python
class ComplianceEngine:
    async def assess_framework_compliance(assessment, framework):
        """Run all checks for a framework and calculate compliance."""

        # 1. Get framework checks
        checks = get_framework_checks(framework)

        # 2. Execute checks
        results = []
        for check in checks:
            result = await execute_check(check, assessment)
            results.append(result)

        # 3. Calculate score
        total = len(results)
        passed = len([r for r in results if r['status'] == 'pass'])
        score = (passed / total * 100) if total > 0 else 0

        # 4. Determine status
        if score >= 95: status = "compliant"
        elif score >= 70: status = "partially_compliant"
        else: status = "non_compliant"

        # 5. Extract findings
        findings = []
        for result in results:
            if result['status'] != 'pass':
                findings.append({
                    'severity': result['severity'],
                    'check_id': result['check_id'],
                    'title': result['title'],
                    'description': result['description']
                })

        return {
            'framework': framework,
            'status': status,
            'score': score,
            'total_checks': total,
            'passed_checks': passed,
            'findings': findings
        }
```

## Example Checks to Implement

### HIPAA Checks
```python
HIPAA_CHECKS = [
    {
        "id": "HIPAA_164_312_a_1",
        "title": "Encryption at Rest",
        "requirement": "Implement encryption for ePHI at rest",
        "check": lambda assessment: check_encryption_enabled(assessment.infrastructure),
        "severity": "critical"
    },
    {
        "id": "HIPAA_164_312_e_1",
        "title": "Transmission Security",
        "requirement": "Implement encryption for ePHI in transit",
        "check": lambda assessment: check_tls_enabled(assessment.infrastructure),
        "severity": "critical"
    }
]
```

### SOC 2 Checks
```python
SOC2_CHECKS = [
    {
        "id": "SOC2_CC6_1",
        "title": "Logical Access Controls",
        "requirement": "Implement access controls",
        "check": lambda assessment: check_access_controls(assessment.infrastructure),
        "severity": "high"
    }
]
```

## Success Metrics

### Before (Current State)
- Compliance Score: 0% (hardcoded)
- Findings: 0 (hardcoded)
- Automated Checks: Never run
- Remediation: 0/0

### After (Target State)
- Compliance Score: Real calculation (e.g., 78.5%)
- Findings: Actual issues detected (e.g., 27 findings)
- Automated Checks: Last run timestamp
- Remediation: Real progress (e.g., 15/27 = 55.6%)

## Next Steps

1. **Create `compliance_engine.py`** with check execution framework
2. **Define 15-20 essential checks** across HIPAA, SOC2, ISO27001
3. **Update `generate_compliance_dashboard()`** to call compliance engine
4. **Test with real assessment data**
5. **Verify frontend displays real metrics**

---

**Status**: Ready for implementation
**Estimated Time**: 2-3 days for basic functional system
**Impact**: Transforms compliance from placeholder to production-ready feature
