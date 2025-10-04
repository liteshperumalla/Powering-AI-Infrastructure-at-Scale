'use client';

export interface ComplianceFramework {
    id: string;
    name: string;
    version: string;
    type: 'soc2' | 'gdpr' | 'hipaa' | 'iso27001' | 'pci_dss' | 'nist' | 'custom';
    description: string;
    requirements: ComplianceRequirement[];
    audit_frequency: 'continuous' | 'quarterly' | 'semi_annual' | 'annual';
    last_assessment_date: string;
    next_assessment_date: string;
    overall_compliance_score: number;
    status: 'compliant' | 'partially_compliant' | 'non_compliant' | 'assessment_needed';
}

export interface ComplianceRequirement {
    id: string;
    framework_id: string;
    requirement_id: string;
    title: string;
    description: string;
    category: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    compliance_status: 'compliant' | 'partially_compliant' | 'non_compliant' | 'not_applicable';
    evidence_required: EvidenceRequirement[];
    controls: ComplianceControl[];
    automated_checks: AutomatedCheck[];
    manual_assessments: ManualAssessment[];
    remediation_actions: RemediationAction[];
    last_verified: string;
    next_review_date: string;
    responsible_party: string;
    risk_if_non_compliant: string;
}

export interface EvidenceRequirement {
    id: string;
    evidence_type: 'document' | 'screenshot' | 'log' | 'certificate' | 'policy' | 'procedure' | 'configuration';
    description: string;
    collection_method: 'manual' | 'automated' | 'semi_automated';
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'on_demand';
    retention_period: string;
    storage_location: string;
    access_controls: string[];
    current_status: 'collected' | 'missing' | 'expired' | 'insufficient';
    last_collected: string;
}

export interface ComplianceControl {
    id: string;
    control_id: string;
    control_name: string;
    control_type: 'preventive' | 'detective' | 'corrective' | 'compensating';
    description: string;
    implementation_status: 'implemented' | 'partially_implemented' | 'not_implemented' | 'planned';
    effectiveness: 'effective' | 'partially_effective' | 'ineffective' | 'not_tested';
    automation_level: 'fully_automated' | 'partially_automated' | 'manual';
    monitoring_frequency: string;
    responsible_team: string;
    implementation_date: string;
    last_tested: string;
    next_test_date: string;
    test_results: ControlTestResult[];
}

export interface ControlTestResult {
    test_date: string;
    test_type: 'automated' | 'manual' | 'walkthrough' | 'inquiry';
    result: 'pass' | 'fail' | 'exception' | 'not_applicable';
    findings: string[];
    recommendations: string[];
    tester: string;
    remediation_timeline: string;
}

export interface AutomatedCheck {
    id: string;
    check_name: string;
    check_type: 'configuration' | 'policy' | 'log_analysis' | 'vulnerability_scan' | 'access_review' | 'data_classification';
    description: string;
    check_frequency: 'real_time' | 'hourly' | 'daily' | 'weekly';
    data_sources: string[];
    check_logic: any;
    thresholds: any;
    enabled: boolean;
    last_execution: string;
    last_result: CheckResult;
    historical_results: CheckResult[];
}

export interface CheckResult {
    execution_time: string;
    status: 'pass' | 'fail' | 'warning' | 'error';
    score: number;
    findings: Finding[];
    recommendations: string[];
    raw_data: any;
    execution_duration: string;
}

export interface Finding {
    severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
    category: string;
    description: string;
    affected_resources: string[];
    evidence: any;
    remediation_guidance: string;
    risk_assessment: string;
    compliance_impact: string;
}

export interface ManualAssessment {
    id: string;
    assessment_name: string;
    description: string;
    frequency: 'monthly' | 'quarterly' | 'semi_annual' | 'annual' | 'ad_hoc';
    assessor_requirements: string[];
    assessment_procedure: string[];
    checklist: AssessmentChecklistItem[];
    last_completed: string;
    next_due: string;
    completion_status: 'not_started' | 'in_progress' | 'completed' | 'overdue';
    results: AssessmentResult[];
}

export interface AssessmentChecklistItem {
    id: string;
    item_description: string;
    expected_outcome: string;
    assessment_method: string;
    evidence_requirements: string[];
    criticality: 'low' | 'medium' | 'high';
}

export interface AssessmentResult {
    assessment_date: string;
    assessor: string;
    overall_rating: 'satisfactory' | 'needs_improvement' | 'unsatisfactory';
    checklist_results: Array<{
        item_id: string;
        result: 'pass' | 'fail' | 'partial' | 'n/a';
        notes: string;
        evidence: string[];
    }>;
    findings: string[];
    recommendations: string[];
    action_items: ActionItem[];
}

export interface ActionItem {
    id: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    assigned_to: string;
    due_date: string;
    status: 'open' | 'in_progress' | 'completed' | 'overdue';
    progress_notes: string[];
}

export interface RemediationAction {
    id: string;
    action_type: 'immediate' | 'short_term' | 'long_term';
    description: string;
    impact: string;
    effort_required: 'low' | 'medium' | 'high';
    cost_estimate: number;
    timeline: string;
    dependencies: string[];
    responsible_party: string;
    approval_required: boolean;
    implementation_steps: string[];
    success_criteria: string[];
    status: 'planned' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
    progress_updates: ProgressUpdate[];
}

export interface ProgressUpdate {
    update_date: string;
    progress_percentage: number;
    status_notes: string;
    blockers: string[];
    next_steps: string[];
    updated_by: string;
}

export interface ComplianceReport {
    id: string;
    report_name: string;
    report_type: 'executive_summary' | 'detailed_assessment' | 'audit_report' | 'gap_analysis' | 'remediation_plan';
    frameworks_included: string[];
    reporting_period: {
        start_date: string;
        end_date: string;
    };
    generated_date: string;
    generated_by: string;
    overall_summary: {
        total_requirements: number;
        compliant_requirements: number;
        non_compliant_requirements: number;
        compliance_percentage: number;
        high_risk_findings: number;
        open_remediation_actions: number;
    };
    framework_summaries: FrameworkSummary[];
    key_findings: Finding[];
    recommendations: string[];
    risk_assessment: RiskAssessment;
    remediation_roadmap: RemediationRoadmap;
    appendices: any[];
}

export interface FrameworkSummary {
    framework_id: string;
    framework_name: string;
    compliance_score: number;
    status: string;
    compliant_controls: number;
    non_compliant_controls: number;
    key_gaps: string[];
    improvement_areas: string[];
    next_assessment_date: string;
}

export interface RiskAssessment {
    overall_risk_level: 'low' | 'medium' | 'high' | 'critical';
    risk_categories: Array<{
        category: string;
        risk_level: string;
        description: string;
        potential_impact: string;
        likelihood: string;
        mitigation_priority: number;
    }>;
    compliance_risks: Array<{
        framework: string;
        risk_description: string;
        business_impact: string;
        regulatory_consequences: string[];
        recommended_actions: string[];
    }>;
}

export interface RemediationRoadmap {
    roadmap_phases: Array<{
        phase_name: string;
        duration: string;
        objectives: string[];
        actions: RemediationAction[];
        success_metrics: string[];
        budget_required: number;
    }>;
    critical_path: string[];
    dependencies: Array<{
        action_id: string;
        depends_on: string[];
        blocking_items: string[];
    }>;
    resource_requirements: Array<{
        skill_set: string;
        effort_required: string;
        availability_needed: string;
    }>;
}

export interface ComplianceAudit {
    id: string;
    audit_name: string;
    audit_type: 'internal' | 'external' | 'regulatory' | 'certification';
    frameworks_in_scope: string[];
    auditor_information: {
        name: string;
        organization: string;
        certification: string[];
        contact_information: any;
    };
    audit_timeline: {
        planning_start: string;
        fieldwork_start: string;
        fieldwork_end: string;
        report_delivery: string;
    };
    scope_and_objectives: string[];
    testing_approach: string;
    evidence_requests: EvidenceRequest[];
    findings: AuditFinding[];
    management_responses: ManagementResponse[];
    corrective_action_plans: CorrectiveActionPlan[];
    audit_conclusion: string;
    certification_status?: 'certified' | 'conditional' | 'not_certified';
}

export interface EvidenceRequest {
    id: string;
    requirement_reference: string;
    evidence_description: string;
    format_requirements: string[];
    due_date: string;
    submission_method: string;
    status: 'requested' | 'in_preparation' | 'submitted' | 'accepted' | 'requires_clarification';
    submitted_evidence: any[];
    auditor_notes: string;
}

export interface AuditFinding {
    id: string;
    finding_type: 'observation' | 'deficiency' | 'significant_deficiency' | 'material_weakness';
    severity: 'low' | 'medium' | 'high' | 'critical';
    control_reference: string;
    description: string;
    root_cause_analysis: string;
    business_impact: string;
    compliance_implications: string[];
    evidence: any[];
    auditor_recommendations: string[];
    management_agreed: boolean;
}

export interface ManagementResponse {
    finding_id: string;
    response_date: string;
    management_position: 'agree' | 'partially_agree' | 'disagree';
    response_explanation: string;
    proposed_corrective_actions: string[];
    implementation_timeline: string;
    responsible_parties: string[];
    resource_requirements: any;
}

export interface CorrectiveActionPlan {
    id: string;
    finding_id: string;
    action_description: string;
    implementation_steps: string[];
    responsible_owner: string;
    target_completion_date: string;
    success_criteria: string[];
    monitoring_approach: string;
    status: 'planned' | 'in_progress' | 'completed' | 'overdue';
    progress_updates: ProgressUpdate[];
    effectiveness_validation: {
        validation_method: string;
        validation_date: string;
        validation_result: 'effective' | 'partially_effective' | 'ineffective';
        validation_notes: string;
    };
}

export interface ComplianceDashboard {
    overall_compliance_score: number;
    framework_scores: Array<{
        framework: string;
        score: number;
        trend: 'improving' | 'declining' | 'stable';
    }>;
    active_findings: {
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
    remediation_progress: {
        total_actions: number;
        completed_actions: number;
        overdue_actions: number;
        progress_percentage: number;
    };
    upcoming_deadlines: Array<{
        item: string;
        due_date: string;
        type: 'assessment' | 'remediation' | 'audit' | 'certification';
        priority: string;
    }>;
    automated_monitoring: {
        active_checks: number;
        passing_checks: number;
        failing_checks: number;
        last_execution: string;
    };
    key_metrics: Array<{
        metric_name: string;
        current_value: number;
        target_value: number;
        trend: any[];
    }>;
}

class ComplianceAutomationService {
    private baseUrl: string;
    private token: string | null = null;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        this.token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`Compliance Automation API Error: ${response.statusText}`);
        }

        return response.json();
    }

    // Dashboard and Overview
    async getComplianceDashboard(): Promise<ComplianceDashboard> {
        const response = await this.makeRequest('/api/v2/compliance/dashboard');
        return response.data || {};
    }

    async getComplianceOverview(timeframe: string = '30d'): Promise<{
        compliance_trends: any[];
        risk_trends: any[];
        activity_summary: any;
        upcoming_milestones: any[];
    }> {
        return this.makeRequest(`/api/compliance/overview?timeframe=${timeframe}`);
    }

    // Framework Management
    async getComplianceFrameworks(): Promise<ComplianceFramework[]> {
        const response = await this.makeRequest('/api/v2/compliance/frameworks');
        return response.frameworks || [];
    }

    async getFramework(frameworkId: string): Promise<ComplianceFramework & {
        detailed_requirements: any[];
        control_hierarchy: any;
        assessment_history: any[];
    }> {
        return this.makeRequest(`/api/compliance/frameworks/${frameworkId}`);
    }

    async addFramework(framework: {
        name: string;
        type: string;
        version: string;
        requirements_config: any;
        assessment_schedule: any;
    }): Promise<ComplianceFramework> {
        return this.makeRequest('/api/v2/compliance/frameworks', {
            method: 'POST',
            body: JSON.stringify(framework),
        });
    }

    async updateFramework(frameworkId: string, updates: Partial<ComplianceFramework>): Promise<ComplianceFramework> {
        return this.makeRequest(`/api/compliance/frameworks/${frameworkId}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    async assessFrameworkCompliance(frameworkId: string, assessmentConfig?: {
        include_automated_checks: boolean;
        include_manual_assessments: boolean;
        generate_report: boolean;
    }): Promise<{
        assessment_id: string;
        compliance_score: number;
        assessment_results: any[];
        report_url?: string;
    }> {
        const body: any = { framework_id: frameworkId };
        if (assessmentConfig) body.assessment_config = assessmentConfig;
        
        return this.makeRequest('/api/v2/compliance/frameworks/assess', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    // Automated Monitoring
    async getAutomatedChecks(frameworkId?: string): Promise<AutomatedCheck[]> {
        const params = frameworkId ? `?framework_id=${frameworkId}` : '';
        const response = await this.makeRequest(`/api/compliance/automated-checks${params}`);
        return response.checks || [];
    }

    async createAutomatedCheck(check: {
        framework_id: string;
        requirement_id: string;
        check_name: string;
        check_type: string;
        check_logic: any;
        frequency: string;
        data_sources: string[];
    }): Promise<AutomatedCheck> {
        return this.makeRequest('/api/v2/compliance/automated-checks', {
            method: 'POST',
            body: JSON.stringify(check),
        });
    }

    async executeAutomatedCheck(checkId: string): Promise<CheckResult> {
        return this.makeRequest(`/api/compliance/automated-checks/${checkId}/execute`, {
            method: 'POST',
        });
    }

    async getCheckResults(checkId: string, limit: number = 50): Promise<CheckResult[]> {
        return this.makeRequest(`/api/compliance/automated-checks/${checkId}/results?limit=${limit}`);
    }

    async configureCheckSchedule(checkId: string, schedule: {
        frequency: string;
        enabled: boolean;
        notification_settings: any;
    }): Promise<void> {
        await this.makeRequest(`/api/compliance/automated-checks/${checkId}/schedule`, {
            method: 'PUT',
            body: JSON.stringify(schedule),
        });
    }

    // Evidence Management
    async getEvidenceRequirements(frameworkId?: string): Promise<EvidenceRequirement[]> {
        const params = frameworkId ? `?framework_id=${frameworkId}` : '';
        return this.makeRequest(`/api/compliance/evidence/requirements${params}`);
    }

    async collectEvidence(requirementId: string, evidenceData: {
        evidence_type: string;
        files?: File[];
        text_evidence?: string;
        metadata: any;
        collection_notes: string;
    }): Promise<{
        evidence_id: string;
        collection_status: string;
        validation_results?: any;
    }> {
        const formData = new FormData();
        formData.append('requirement_id', requirementId);
        formData.append('evidence_type', evidenceData.evidence_type);
        formData.append('metadata', JSON.stringify(evidenceData.metadata));
        formData.append('collection_notes', evidenceData.collection_notes);
        
        if (evidenceData.text_evidence) {
            formData.append('text_evidence', evidenceData.text_evidence);
        }
        
        if (evidenceData.files) {
            evidenceData.files.forEach((file, index) => {
                formData.append(`files[${index}]`, file);
            });
        }

        const response = await fetch(`${this.baseUrl}/api/compliance/evidence/collect`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Evidence collection failed: ${response.statusText}`);
        }

        return response.json();
    }

    async validateEvidence(evidenceId: string): Promise<{
        validation_status: 'valid' | 'invalid' | 'incomplete';
        validation_notes: string[];
        required_actions: string[];
    }> {
        return this.makeRequest(`/api/compliance/evidence/${evidenceId}/validate`, {
            method: 'POST',
        });
    }

    async getEvidenceInventory(filters?: {
        framework_id?: string;
        status?: string;
        collected_after?: string;
    }): Promise<Array<{
        evidence_id: string;
        requirement_id: string;
        evidence_type: string;
        collection_date: string;
        status: string;
        validation_status: string;
    }>> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, value.toString());
                }
            });
        }
        return this.makeRequest(`/api/compliance/evidence/inventory?${params}`);
    }

    // Control Testing
    async getControls(frameworkId?: string): Promise<ComplianceControl[]> {
        const params = frameworkId ? `?framework_id=${frameworkId}` : '';
        return this.makeRequest(`/api/compliance/controls${params}`);
    }

    async testControl(controlId: string, testConfig: {
        test_type: string;
        tester: string;
        test_procedures: string[];
        sampling_method?: string;
        sample_size?: number;
    }): Promise<ControlTestResult> {
        return this.makeRequest(`/api/compliance/controls/${controlId}/test`, {
            method: 'POST',
            body: JSON.stringify(testConfig),
        });
    }

    async getControlTestHistory(controlId: string): Promise<ControlTestResult[]> {
        return this.makeRequest(`/api/compliance/controls/${controlId}/test-history`);
    }

    async updateControlImplementation(controlId: string, updates: {
        implementation_status?: string;
        effectiveness?: string;
        implementation_notes?: string;
        responsible_team?: string;
    }): Promise<void> {
        await this.makeRequest(`/api/compliance/controls/${controlId}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    // Remediation Management
    async getRemediationActions(filters?: {
        framework_id?: string;
        priority?: string;
        status?: string;
        assigned_to?: string;
    }): Promise<RemediationAction[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, value.toString());
                }
            });
        }
        return this.makeRequest(`/api/compliance/remediation/actions?${params}`);
    }

    async createRemediationAction(action: {
        requirement_id: string;
        description: string;
        action_type: string;
        priority: string;
        assigned_to: string;
        due_date: string;
        implementation_steps: string[];
        success_criteria: string[];
    }): Promise<RemediationAction> {
        return this.makeRequest('/api/v2/compliance/remediation/actions', {
            method: 'POST',
            body: JSON.stringify(action),
        });
    }

    async updateRemediationProgress(actionId: string, progress: {
        progress_percentage: number;
        status?: string;
        status_notes: string;
        blockers?: string[];
        next_steps?: string[];
    }): Promise<void> {
        await this.makeRequest(`/api/compliance/remediation/actions/${actionId}/progress`, {
            method: 'PUT',
            body: JSON.stringify(progress),
        });
    }

    async getRemediationRoadmap(frameworkId?: string): Promise<RemediationRoadmap> {
        const params = frameworkId ? `?framework_id=${frameworkId}` : '';
        return this.makeRequest(`/api/compliance/remediation/roadmap${params}`);
    }

    // Reporting
    async generateComplianceReport(reportConfig: {
        report_type: string;
        frameworks: string[];
        reporting_period: { start_date: string; end_date: string };
        format: 'pdf' | 'excel' | 'csv';
        include_evidence: boolean;
        include_remediation_plan: boolean;
    }): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/api/compliance/reports/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
            },
            body: JSON.stringify(reportConfig),
        });

        if (!response.ok) {
            throw new Error(`Report generation failed: ${response.statusText}`);
        }

        return response.blob();
    }

    async getReportHistory(): Promise<Array<{
        report_id: string;
        report_name: string;
        generated_date: string;
        report_type: string;
        frameworks: string[];
        status: string;
        download_url?: string;
    }>> {
        return this.makeRequest('/api/v2/compliance/reports/history');
    }

    async scheduleAutomaticReport(schedule: {
        report_name: string;
        report_config: any;
        frequency: 'weekly' | 'monthly' | 'quarterly';
        recipients: string[];
        auto_send: boolean;
    }): Promise<{ schedule_id: string }> {
        return this.makeRequest('/api/v2/compliance/reports/schedule', {
            method: 'POST',
            body: JSON.stringify(schedule),
        });
    }

    // Audit Management
    async getAudits(): Promise<ComplianceAudit[]> {
        const response = await this.makeRequest('/api/v2/compliance/audits');
        return response.audits || [];
    }

    async createAudit(audit: {
        audit_name: string;
        audit_type: string;
        frameworks_in_scope: string[];
        auditor_information: any;
        timeline: any;
        scope: string[];
    }): Promise<ComplianceAudit> {
        return this.makeRequest('/api/v2/compliance/audits', {
            method: 'POST',
            body: JSON.stringify(audit),
        });
    }

    async getAuditDetails(auditId: string): Promise<ComplianceAudit> {
        return this.makeRequest(`/api/compliance/audits/${auditId}`);
    }

    async respondToEvidenceRequest(requestId: string, response: {
        evidence_files?: File[];
        response_notes: string;
        submission_method: string;
    }): Promise<void> {
        const formData = new FormData();
        formData.append('response_notes', response.response_notes);
        formData.append('submission_method', response.submission_method);
        
        if (response.evidence_files) {
            response.evidence_files.forEach((file, index) => {
                formData.append(`evidence_files[${index}]`, file);
            });
        }

        const result = await fetch(`${this.baseUrl}/api/compliance/audits/evidence-requests/${requestId}/respond`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!result.ok) {
            throw new Error(`Evidence submission failed: ${result.statusText}`);
        }
    }

    async submitManagementResponse(findingId: string, response: ManagementResponse): Promise<void> {
        await this.makeRequest(`/api/compliance/audits/findings/${findingId}/respond`, {
            method: 'POST',
            body: JSON.stringify(response),
        });
    }

    // Notifications and Alerts
    async configureComplianceAlerts(config: {
        upcoming_deadlines_days: number;
        failed_checks_threshold: number;
        overdue_actions_alert: boolean;
        compliance_score_threshold: number;
        notification_channels: string[];
        escalation_rules: any[];
    }): Promise<void> {
        await this.makeRequest('/api/v2/compliance/alerts/config', {
            method: 'PUT',
            body: JSON.stringify(config),
        });
    }

    async getActiveAlerts(): Promise<Array<{
        id: string;
        alert_type: string;
        severity: 'info' | 'warning' | 'critical';
        message: string;
        affected_items: string[];
        created_at: string;
        action_required: boolean;
    }>> {
        const response = await this.makeRequest('/api/v2/compliance/alerts');
        return response.alerts || [];
    }

    async acknowledgeAlert(alertId: string, notes?: string): Promise<void> {
        await this.makeRequest(`/api/compliance/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            body: JSON.stringify({ notes }),
        });
    }
}

// Singleton instance
let complianceAutomationService: ComplianceAutomationService | null = null;

export const getComplianceAutomationService = (): ComplianceAutomationService => {
    if (!complianceAutomationService) {
        complianceAutomationService = new ComplianceAutomationService();
    }
    return complianceAutomationService;
};

export default ComplianceAutomationService;