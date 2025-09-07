'use client';

export interface Resource {
    id: string;
    name: string;
    type: string;
    provider: 'aws' | 'azure' | 'gcp' | 'kubernetes';
    region?: string;
    environment: 'dev' | 'staging' | 'prod';
    tags: Record<string, string>;
    properties: Record<string, any>;
    dependencies: {
        depends_on: string[];
        dependents: string[];
    };
    cost_info?: {
        monthly_cost: number;
        currency: string;
    };
    compliance_info?: {
        policies: string[];
        classifications: string[];
    };
    created_at: string;
    last_modified: string;
}

export interface ChangeRequest {
    id: string;
    title: string;
    description: string;
    change_type: 'create' | 'update' | 'delete' | 'replace';
    resources: ResourceChange[];
    requester: {
        id: string;
        name: string;
        email: string;
    };
    target_environment: string;
    scheduled_time?: string;
    urgency: 'low' | 'medium' | 'high' | 'critical';
    change_category: 'configuration' | 'deployment' | 'security' | 'scaling' | 'maintenance';
    rollback_plan?: string;
    testing_plan?: string;
    created_at: string;
}

export interface ResourceChange {
    resource_id: string;
    action: 'create' | 'update' | 'delete' | 'replace';
    before_state?: any;
    after_state?: any;
    change_details: {
        modified_attributes: string[];
        configuration_diff: string;
        risk_factors: string[];
    };
}

export interface ImpactAnalysisResult {
    id: string;
    change_request_id: string;
    analysis_timestamp: string;
    overall_risk_score: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    confidence_score: number;
    
    blast_radius: {
        directly_affected: ResourceImpact[];
        indirectly_affected: ResourceImpact[];
        total_affected_count: number;
        affected_environments: string[];
        affected_regions: string[];
    };
    
    dependency_analysis: {
        upstream_dependencies: DependencyImpact[];
        downstream_dependencies: DependencyImpact[];
        circular_dependencies: CircularDependency[];
        cascade_potential: number;
    };
    
    business_impact: {
        service_disruption_risk: number;
        user_impact_assessment: {
            affected_users: number;
            user_groups: string[];
            impact_severity: 'none' | 'minimal' | 'moderate' | 'severe';
        };
        financial_impact: {
            potential_cost_change: number;
            downtime_cost_estimate: number;
            recovery_cost_estimate: number;
        };
        sla_impact: {
            affected_slas: string[];
            availability_risk: number;
            performance_risk: number;
        };
    };
    
    compliance_impact: {
        policy_violations: PolicyViolation[];
        regulatory_concerns: RegulatoryImpact[];
        security_implications: SecurityImplication[];
        audit_requirements: string[];
    };
    
    operational_impact: {
        monitoring_changes_needed: string[];
        alerting_updates_required: string[];
        documentation_updates: string[];
        team_notifications: string[];
        skill_requirements: string[];
    };
    
    risk_mitigation: {
        recommendations: Recommendation[];
        required_approvals: string[];
        testing_requirements: TestingRequirement[];
        rollback_procedures: RollbackProcedure[];
    };
    
    timeline_analysis: {
        estimated_duration: string;
        maintenance_windows: MaintenanceWindow[];
        critical_path_resources: string[];
        parallel_execution_opportunities: string[];
    };
    
    alternatives: {
        alternative_approaches: AlternativeApproach[];
        phased_rollout_options: PhasedRollout[];
        blue_green_feasibility: boolean;
        canary_deployment_options: CanaryOption[];
    };
}

export interface ResourceImpact {
    resource_id: string;
    resource_name: string;
    resource_type: string;
    impact_type: 'configuration' | 'availability' | 'performance' | 'security' | 'cost';
    impact_severity: 'low' | 'medium' | 'high' | 'critical';
    impact_description: string;
    estimated_downtime: string;
    recovery_time: string;
    mitigation_actions: string[];
}

export interface DependencyImpact {
    resource_id: string;
    resource_name: string;
    dependency_type: 'hard' | 'soft' | 'data' | 'network';
    impact_propagation_risk: number;
    failure_scenarios: FailureScenario[];
    contingency_plans: string[];
}

export interface CircularDependency {
    resources_involved: string[];
    dependency_chain: string[];
    risk_assessment: string;
    resolution_strategies: string[];
}

export interface PolicyViolation {
    policy_name: string;
    violation_type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    remediation_steps: string[];
    auto_remediation_available: boolean;
}

export interface RegulatoryImpact {
    regulation: string;
    impact_description: string;
    compliance_actions_required: string[];
    reporting_requirements: string[];
    risk_level: 'low' | 'medium' | 'high';
}

export interface SecurityImplication {
    security_domain: string;
    risk_description: string;
    threat_vectors: string[];
    mitigation_controls: string[];
    security_review_required: boolean;
}

export interface Recommendation {
    type: 'best_practice' | 'risk_reduction' | 'optimization' | 'alternative';
    priority: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    description: string;
    implementation_effort: 'low' | 'medium' | 'high';
    potential_benefits: string[];
    risks_if_ignored: string[];
}

export interface TestingRequirement {
    test_type: 'unit' | 'integration' | 'performance' | 'security' | 'user_acceptance';
    description: string;
    test_environments: string[];
    estimated_duration: string;
    required_resources: string[];
    success_criteria: string[];
}

export interface RollbackProcedure {
    trigger_conditions: string[];
    rollback_steps: string[];
    estimated_rollback_time: string;
    data_recovery_required: boolean;
    validation_steps: string[];
    point_of_no_return?: string;
}

export interface MaintenanceWindow {
    start_time: string;
    end_time: string;
    timezone: string;
    impact_level: 'low' | 'medium' | 'high';
    affected_services: string[];
    user_notification_required: boolean;
}

export interface AlternativeApproach {
    name: string;
    description: string;
    pros: string[];
    cons: string[];
    risk_level: 'low' | 'medium' | 'high';
    implementation_complexity: 'low' | 'medium' | 'high';
    estimated_timeline: string;
}

export interface PhasedRollout {
    phase_name: string;
    phase_description: string;
    resources_included: string[];
    success_criteria: string[];
    rollback_triggers: string[];
    duration: string;
}

export interface CanaryOption {
    traffic_percentage: number;
    duration: string;
    success_metrics: string[];
    rollback_triggers: string[];
    monitoring_requirements: string[];
}

export interface FailureScenario {
    scenario: string;
    probability: 'low' | 'medium' | 'high';
    impact: 'low' | 'medium' | 'high' | 'critical';
    detection_methods: string[];
    response_procedures: string[];
}

class ChangeImpactAnalysisService {
    private baseUrl: string;
    private token: string | null = null;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        this.token = typeof window !== 'undefined' ? typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null : null;
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
            throw new Error(`Change Impact API Error: ${response.statusText}`);
        }

        return response.json();
    }

    // Resource Discovery
    async discoverResources(environment: string, provider?: string): Promise<Resource[]> {
        const params = new URLSearchParams({ environment });
        if (provider) params.append('provider', provider);
        
        return this.makeRequest(`/api/change-impact/resources?${params}`);
    }

    async getResource(resourceId: string): Promise<Resource> {
        return this.makeRequest(`/api/change-impact/resources/${resourceId}`);
    }

    async getResourceDependencies(resourceId: string, depth: number = 2): Promise<{
        upstream: Resource[];
        downstream: Resource[];
        dependency_graph: any;
    }> {
        return this.makeRequest(`/api/change-impact/resources/${resourceId}/dependencies?depth=${depth}`);
    }

    // Change Impact Analysis
    async analyzeChange(changeRequest: ChangeRequest): Promise<ImpactAnalysisResult> {
        return this.makeRequest('/api/change-impact/analyze', {
            method: 'POST',
            body: JSON.stringify(changeRequest),
        });
    }

    async analyzeResourceChange(
        resourceId: string,
        changeDetails: {
            action: 'create' | 'update' | 'delete' | 'replace';
            before_state?: any;
            after_state?: any;
            change_attributes: string[];
        }
    ): Promise<ImpactAnalysisResult> {
        return this.makeRequest(`/api/change-impact/resources/${resourceId}/analyze`, {
            method: 'POST',
            body: JSON.stringify(changeDetails),
        });
    }

    async getBulkImpactAnalysis(resourceIds: string[], changeType: string): Promise<{
        combined_analysis: ImpactAnalysisResult;
        individual_analyses: ImpactAnalysisResult[];
        cross_impact_matrix: any;
    }> {
        return this.makeRequest('/api/change-impact/bulk-analyze', {
            method: 'POST',
            body: JSON.stringify({ resource_ids: resourceIds, change_type: changeType }),
        });
    }

    // Scenario Simulation
    async simulateFailure(resourceId: string, failureType: string): Promise<{
        simulation_id: string;
        affected_resources: ResourceImpact[];
        cascade_effects: any[];
        recovery_scenarios: any[];
        estimated_impact: {
            downtime: string;
            affected_users: number;
            financial_impact: number;
        };
    }> {
        return this.makeRequest(`/api/change-impact/simulate-failure`, {
            method: 'POST',
            body: JSON.stringify({ resource_id: resourceId, failure_type: failureType }),
        });
    }

    async simulateDeployment(
        changeRequest: ChangeRequest,
        deploymentStrategy: 'blue_green' | 'canary' | 'rolling' | 'direct'
    ): Promise<{
        simulation_id: string;
        deployment_timeline: any[];
        risk_assessment: any;
        rollback_scenarios: any[];
        success_probability: number;
    }> {
        return this.makeRequest('/api/change-impact/simulate-deployment', {
            method: 'POST',
            body: JSON.stringify({ change_request: changeRequest, deployment_strategy: deploymentStrategy }),
        });
    }

    // Risk Assessment
    async calculateRiskScore(analysisId: string): Promise<{
        overall_risk_score: number;
        risk_breakdown: {
            technical_risk: number;
            business_risk: number;
            compliance_risk: number;
            operational_risk: number;
        };
        risk_factors: Array<{
            factor: string;
            weight: number;
            score: number;
            explanation: string;
        }>;
        recommendations: Recommendation[];
    }> {
        return this.makeRequest(`/api/change-impact/risk-score/${analysisId}`);
    }

    async getHistoricalRiskData(environment: string, timeRange: string): Promise<{
        risk_trends: any[];
        failure_patterns: any[];
        success_rates: any;
        lessons_learned: string[];
    }> {
        return this.makeRequest(`/api/change-impact/historical-risk?environment=${environment}&time_range=${timeRange}`);
    }

    // Compliance Analysis
    async checkCompliance(changeRequest: ChangeRequest): Promise<{
        compliance_status: 'compliant' | 'non_compliant' | 'requires_review';
        policy_violations: PolicyViolation[];
        regulatory_impacts: RegulatoryImpact[];
        required_approvals: string[];
        remediation_plan: string[];
    }> {
        return this.makeRequest('/api/change-impact/compliance-check', {
            method: 'POST',
            body: JSON.stringify(changeRequest),
        });
    }

    async getPolicyTemplates(): Promise<Array<{
        id: string;
        name: string;
        description: string;
        rules: any[];
        applicable_resources: string[];
    }>> {
        return this.makeRequest('/api/change-impact/policy-templates');
    }

    // Recommendations Engine
    async getOptimizationRecommendations(analysisId: string): Promise<{
        cost_optimizations: Recommendation[];
        performance_improvements: Recommendation[];
        security_enhancements: Recommendation[];
        reliability_improvements: Recommendation[];
    }> {
        return this.makeRequest(`/api/change-impact/recommendations/${analysisId}`);
    }

    async getAlternativeImplementations(changeRequest: ChangeRequest): Promise<{
        alternatives: AlternativeApproach[];
        recommended_approach: AlternativeApproach;
        comparison_matrix: any;
    }> {
        return this.makeRequest('/api/change-impact/alternatives', {
            method: 'POST',
            body: JSON.stringify(changeRequest),
        });
    }

    // Timeline and Planning
    async generateExecutionPlan(analysisId: string): Promise<{
        execution_timeline: Array<{
            phase: string;
            duration: string;
            tasks: string[];
            dependencies: string[];
            risk_level: string;
        }>;
        critical_path: string[];
        resource_requirements: any;
        checkpoint_schedule: any[];
    }> {
        return this.makeRequest(`/api/change-impact/execution-plan/${analysisId}`);
    }

    async optimizeMaintenanceWindow(
        changeRequest: ChangeRequest,
        constraints: {
            preferred_start?: string;
            max_duration?: string;
            blackout_periods?: Array<{ start: string; end: string }>;
        }
    ): Promise<{
        optimal_windows: MaintenanceWindow[];
        impact_comparison: any;
        user_impact_analysis: any;
    }> {
        return this.makeRequest('/api/change-impact/optimize-maintenance-window', {
            method: 'POST',
            body: JSON.stringify({ change_request: changeRequest, constraints }),
        });
    }

    // Monitoring and Validation
    async setupImpactMonitoring(analysisId: string): Promise<{
        monitoring_plan: {
            metrics_to_track: string[];
            alert_thresholds: any;
            dashboard_config: any;
        };
        validation_checklist: string[];
        rollback_triggers: string[];
    }> {
        return this.makeRequest(`/api/change-impact/setup-monitoring/${analysisId}`, {
            method: 'POST',
        });
    }

    async validatePredictions(analysisId: string, actualOutcome: any): Promise<{
        accuracy_score: number;
        prediction_deviations: any[];
        model_improvements: string[];
        lessons_learned: string[];
    }> {
        return this.makeRequest(`/api/change-impact/validate-predictions/${analysisId}`, {
            method: 'POST',
            body: JSON.stringify(actualOutcome),
        });
    }

    // Export and Reporting
    async exportAnalysis(analysisId: string, format: 'pdf' | 'json' | 'xlsx'): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/api/change-impact/export/${analysisId}?format=${format}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
        });

        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }

        return response.blob();
    }

    async generateRiskReport(analysisId: string): Promise<{
        executive_summary: string;
        risk_matrix: any;
        detailed_findings: any[];
        recommendations: Recommendation[];
        appendices: any;
    }> {
        return this.makeRequest(`/api/change-impact/risk-report/${analysisId}`);
    }

    // Machine Learning and Predictions
    async trainPredictionModel(trainingData: any[]): Promise<{
        model_id: string;
        training_accuracy: number;
        validation_metrics: any;
        feature_importance: any[];
    }> {
        return this.makeRequest('/api/change-impact/train-model', {
            method: 'POST',
            body: JSON.stringify({ training_data: trainingData }),
        });
    }

    async getPredictionConfidence(analysisId: string): Promise<{
        confidence_score: number;
        confidence_intervals: any;
        uncertainty_factors: string[];
        model_performance_metrics: any;
    }> {
        return this.makeRequest(`/api/change-impact/prediction-confidence/${analysisId}`);
    }
}

// Singleton instance
let changeImpactService: ChangeImpactAnalysisService | null = null;

export const getChangeImpactService = (): ChangeImpactAnalysisService => {
    if (!changeImpactService) {
        changeImpactService = new ChangeImpactAnalysisService();
    }
    return changeImpactService;
};

export default ChangeImpactAnalysisService;