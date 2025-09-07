'use client';

export interface VendorLockInAssessment {
    id: string;
    assessment_name: string;
    current_provider: 'aws' | 'azure' | 'gcp' | 'hybrid' | 'multi_cloud';
    assessment_date: string;
    overall_risk_score: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    services_analyzed: ServiceLockInAnalysis[];
    migration_scenarios: MigrationScenario[];
    mitigation_strategies: MitigationStrategy[];
    business_impact: BusinessImpactAnalysis;
    recommendations: LockInRecommendation[];
}

export interface ServiceLockInAnalysis {
    service_name: string;
    service_category: 'compute' | 'storage' | 'database' | 'networking' | 'ai_ml' | 'analytics' | 'security' | 'devops';
    current_provider: string;
    lock_in_score: number;
    lock_in_factors: LockInFactor[];
    portability_assessment: PortabilityAssessment;
    alternatives: ServiceAlternative[];
    migration_complexity: 'low' | 'medium' | 'high' | 'critical';
    estimated_migration_cost: number;
    estimated_migration_time: string;
    data_portability: DataPortabilityAnalysis;
}

export interface LockInFactor {
    factor_type: 'proprietary_apis' | 'data_format' | 'integration_dependencies' | 'licensing' | 'custom_features' | 'skill_dependencies' | 'contractual';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    impact_on_migration: string;
    mitigation_difficulty: 'easy' | 'moderate' | 'difficult' | 'very_difficult';
    estimated_effort_to_resolve: string;
    dependencies: string[];
}

export interface PortabilityAssessment {
    standards_compliance: {
        open_standards_used: boolean;
        proprietary_extensions: string[];
        interoperability_score: number;
    };
    api_compatibility: {
        standard_apis_percentage: number;
        vendor_specific_apis: string[];
        migration_wrappers_available: boolean;
    };
    data_formats: {
        standard_formats_used: boolean;
        proprietary_formats: string[];
        export_capabilities: ExportCapability[];
    };
    architecture_patterns: {
        cloud_native_architecture: boolean;
        vendor_specific_patterns: string[];
        abstraction_layer_present: boolean;
    };
}

export interface ExportCapability {
    data_type: string;
    export_format: string;
    full_fidelity_export: boolean;
    automated_export: boolean;
    export_limitations: string[];
    estimated_export_time: string;
}

export interface ServiceAlternative {
    provider: string;
    service_name: string;
    feature_parity_score: number;
    cost_comparison: {
        current_monthly_cost: number;
        alternative_monthly_cost: number;
        cost_difference_percentage: number;
    };
    migration_effort: {
        complexity_score: number;
        estimated_hours: number;
        required_skills: string[];
        automation_potential: number;
    };
    pros: string[];
    cons: string[];
    risk_factors: string[];
}

export interface DataPortabilityAnalysis {
    total_data_volume: number;
    data_types: Array<{
        type: string;
        volume: number;
        format: string;
        export_complexity: 'simple' | 'moderate' | 'complex';
        migration_time_estimate: string;
    }>;
    export_costs: {
        data_transfer_costs: number;
        processing_costs: number;
        storage_costs: number;
        total_estimated_cost: number;
    };
    compliance_considerations: string[];
    data_sovereignty_issues: string[];
}

export interface MigrationScenario {
    id: string;
    scenario_name: string;
    scenario_type: 'lift_and_shift' | 'refactor' | 'rearchitect' | 'hybrid' | 'gradual_migration';
    target_providers: string[];
    timeline: {
        planning_phase: string;
        execution_phase: string;
        validation_phase: string;
        total_duration: string;
    };
    cost_analysis: {
        migration_costs: number;
        ongoing_cost_difference: number;
        roi_timeline: string;
        break_even_point: string;
    };
    risk_assessment: {
        technical_risks: RiskItem[];
        business_risks: RiskItem[];
        operational_risks: RiskItem[];
        overall_risk_score: number;
    };
    benefits: ScenarioBenefit[];
    prerequisites: string[];
    success_criteria: string[];
}

export interface RiskItem {
    risk_description: string;
    probability: 'low' | 'medium' | 'high';
    impact: 'low' | 'medium' | 'high' | 'critical';
    risk_score: number;
    mitigation_plan: string;
    owner: string;
}

export interface ScenarioBenefit {
    benefit_type: 'cost_savings' | 'performance' | 'flexibility' | 'compliance' | 'innovation' | 'risk_reduction';
    description: string;
    quantified_value?: number;
    timeline_to_realize: string;
    measurement_criteria: string[];
}

export interface MitigationStrategy {
    id: string;
    strategy_name: string;
    strategy_type: 'abstraction_layer' | 'multi_cloud_architecture' | 'containerization' | 'microservices' | 'api_standardization' | 'data_standardization';
    applicability: string[];
    implementation_complexity: 'low' | 'medium' | 'high';
    effectiveness_score: number;
    implementation_cost: number;
    implementation_timeline: string;
    prerequisites: string[];
    benefits: string[];
    limitations: string[];
    monitoring_requirements: string[];
}

export interface BusinessImpactAnalysis {
    operational_impact: {
        service_disruption_risk: number;
        performance_impact_during_migration: string;
        operational_overhead_increase: string;
        staff_training_requirements: string[];
    };
    financial_impact: {
        migration_investment: number;
        ongoing_cost_changes: number;
        risk_of_vendor_price_increases: number;
        opportunity_cost: number;
        potential_savings: number;
    };
    strategic_impact: {
        innovation_velocity_impact: string;
        market_agility_impact: string;
        competitive_advantage_considerations: string[];
        future_technology_adoption_flexibility: string;
    };
    compliance_impact: {
        regulatory_considerations: string[];
        data_residency_requirements: string[];
        audit_trail_continuity: string;
        compliance_certification_impacts: string[];
    };
}

export interface LockInRecommendation {
    id: string;
    recommendation_type: 'immediate' | 'short_term' | 'long_term' | 'strategic';
    priority: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    description: string;
    rationale: string;
    expected_benefits: string[];
    implementation_steps: string[];
    estimated_cost: number;
    estimated_timeline: string;
    success_metrics: string[];
    stakeholders: string[];
    dependencies: string[];
    risks: string[];
}

export interface MultiCloudStrategy {
    id: string;
    strategy_name: string;
    description: string;
    target_architecture: {
        primary_provider: string;
        secondary_providers: string[];
        workload_distribution: WorkloadDistribution[];
        data_distribution_strategy: string;
        networking_approach: string;
    };
    governance_model: {
        decision_framework: string;
        cost_management_approach: string;
        security_model: string;
        compliance_strategy: string;
        vendor_relationship_management: string;
    };
    implementation_roadmap: RoadmapPhase[];
    cost_implications: {
        setup_costs: number;
        ongoing_operational_costs: number;
        potential_savings: number;
        roi_analysis: any;
    };
    risk_mitigation: {
        vendor_dependency_reduction: number;
        service_resilience_improvement: number;
        negotiation_power_enhancement: string;
        innovation_access_improvement: string;
    };
}

export interface WorkloadDistribution {
    workload_type: string;
    primary_provider: string;
    backup_provider?: string;
    distribution_rationale: string;
    migration_priority: number;
}

export interface RoadmapPhase {
    phase_number: number;
    phase_name: string;
    duration: string;
    objectives: string[];
    deliverables: string[];
    success_criteria: string[];
    dependencies: string[];
    resources_required: string[];
    budget_allocation: number;
}

export interface ContractAnalysis {
    id: string;
    vendor_name: string;
    contract_type: 'commitment' | 'pay_as_you_go' | 'enterprise_agreement' | 'hybrid';
    contract_duration: string;
    early_termination_clauses: {
        termination_fees: number;
        notice_period: string;
        conditions: string[];
    };
    volume_commitments: {
        minimum_spend: number;
        usage_commitments: any[];
        penalties_for_underutilization: string;
    };
    pricing_structure: {
        discount_tiers: any[];
        price_protection: boolean;
        price_escalation_clauses: string[];
    };
    service_level_agreements: {
        uptime_guarantees: string;
        performance_guarantees: string;
        support_commitments: string;
        penalties_for_non_compliance: string;
    };
    lock_in_implications: {
        switching_barriers: string[];
        negotiation_leverage: string;
        renewal_risks: string[];
    };
}

class VendorLockInAnalysisService {
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
            throw new Error(`Vendor Lock-in Analysis API Error: ${response.statusText}`);
        }

        return response.json();
    }

    // Assessment Management
    async createLockInAssessment(config: {
        assessment_name: string;
        current_provider: string;
        scope: string[];
        include_migration_scenarios: boolean;
        include_cost_analysis: boolean;
    }): Promise<VendorLockInAssessment> {
        return this.makeRequest('/api/vendor-lockin/assessments', {
            method: 'POST',
            body: JSON.stringify(config),
        });
    }

    async getLockInAssessments(filters?: {
        provider?: string;
        risk_level?: string;
        created_after?: string;
    }): Promise<VendorLockInAssessment[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, value.toString());
                }
            });
        }
        return this.makeRequest(`/api/vendor-lockin/assessments?${params}`);
    }

    async getAssessmentDetails(assessmentId: string): Promise<VendorLockInAssessment & {
        detailed_service_analysis: any[];
        dependency_graph: any;
        migration_timeline: any[];
    }> {
        return this.makeRequest(`/api/vendor-lockin/assessments/${assessmentId}`);
    }

    async updateAssessment(assessmentId: string, updates: Partial<VendorLockInAssessment>): Promise<VendorLockInAssessment> {
        return this.makeRequest(`/api/vendor-lockin/assessments/${assessmentId}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    // Service Analysis
    async analyzeServiceLockIn(serviceConfig: {
        service_name: string;
        provider: string;
        usage_patterns: any[];
        integration_points: string[];
        data_dependencies: any[];
    }): Promise<ServiceLockInAnalysis> {
        return this.makeRequest('/api/vendor-lockin/services/analyze', {
            method: 'POST',
            body: JSON.stringify(serviceConfig),
        });
    }

    async getServiceAlternatives(serviceName: string, provider: string, requirements?: {
        performance_requirements: any;
        cost_constraints: any;
        feature_requirements: string[];
    }): Promise<ServiceAlternative[]> {
        const body: any = { service_name: serviceName, provider };
        if (requirements) body.requirements = requirements;
        
        return this.makeRequest('/api/vendor-lockin/services/alternatives', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async getBulkServiceAnalysis(services: Array<{
        service_name: string;
        provider: string;
        criticality: 'low' | 'medium' | 'high';
    }>): Promise<{
        services: ServiceLockInAnalysis[];
        portfolio_risk_score: number;
        priority_migration_services: string[];
        interdependency_map: any;
    }> {
        return this.makeRequest('/api/vendor-lockin/services/bulk-analyze', {
            method: 'POST',
            body: JSON.stringify({ services }),
        });
    }

    // Migration Scenario Planning
    async generateMigrationScenarios(assessmentId: string, preferences?: {
        preferred_target_providers: string[];
        max_migration_duration: string;
        budget_constraints: number;
        risk_tolerance: 'low' | 'medium' | 'high';
        business_continuity_requirements: string[];
    }): Promise<MigrationScenario[]> {
        const body: any = { assessment_id: assessmentId };
        if (preferences) body.preferences = preferences;
        
        return this.makeRequest('/api/vendor-lockin/migration-scenarios/generate', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    async compareMigrationScenarios(scenarioIds: string[]): Promise<{
        comparison_matrix: any[];
        recommended_scenario: string;
        decision_factors: any[];
        sensitivity_analysis: any;
    }> {
        return this.makeRequest('/api/vendor-lockin/migration-scenarios/compare', {
            method: 'POST',
            body: JSON.stringify({ scenario_ids: scenarioIds }),
        });
    }

    async simulateMigrationScenario(scenarioId: string, simulationParams?: {
        include_disruption_analysis: boolean;
        include_cost_variations: boolean;
        monte_carlo_iterations: number;
    }): Promise<{
        simulation_results: any;
        risk_distribution: any[];
        cost_distribution: any[];
        timeline_variations: any[];
        success_probability: number;
    }> {
        const body: any = { scenario_id: scenarioId };
        if (simulationParams) body.simulation_params = simulationParams;
        
        return this.makeRequest('/api/vendor-lockin/migration-scenarios/simulate', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    // Multi-Cloud Strategy
    async generateMultiCloudStrategy(requirements: {
        business_objectives: string[];
        technical_requirements: any[];
        compliance_requirements: string[];
        budget_constraints: number;
        timeline_constraints: string;
        risk_tolerance: string;
    }): Promise<MultiCloudStrategy> {
        return this.makeRequest('/api/vendor-lockin/multi-cloud/strategy', {
            method: 'POST',
            body: JSON.stringify(requirements),
        });
    }

    async getMultiCloudStrategies(filters?: {
        strategy_type?: string;
        created_after?: string;
    }): Promise<MultiCloudStrategy[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, value.toString());
                }
            });
        }
        return this.makeRequest(`/api/vendor-lockin/multi-cloud/strategies?${params}`);
    }

    async validateMultiCloudStrategy(strategyId: string): Promise<{
        validation_results: any[];
        feasibility_score: number;
        potential_issues: any[];
        optimization_suggestions: string[];
        implementation_readiness: string;
    }> {
        return this.makeRequest(`/api/vendor-lockin/multi-cloud/strategies/${strategyId}/validate`);
    }

    // Contract Analysis
    async analyzeContract(contractData: {
        vendor_name: string;
        contract_text?: string;
        contract_file?: File;
        contract_metadata: any;
    }): Promise<ContractAnalysis> {
        const formData = new FormData();
        formData.append('vendor_name', contractData.vendor_name);
        formData.append('contract_metadata', JSON.stringify(contractData.contract_metadata));
        
        if (contractData.contract_text) {
            formData.append('contract_text', contractData.contract_text);
        }
        if (contractData.contract_file) {
            formData.append('contract_file', contractData.contract_file);
        }

        const response = await fetch(`${this.baseUrl}/api/vendor-lockin/contracts/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Contract analysis failed: ${response.statusText}`);
        }

        return response.json();
    }

    async getContractAnalyses(): Promise<ContractAnalysis[]> {
        return this.makeRequest('/api/vendor-lockin/contracts');
    }

    async getContractRenewalRecommendations(contractId: string): Promise<{
        renewal_strategy: string;
        negotiation_points: string[];
        alternative_options: any[];
        risk_mitigation_clauses: string[];
        cost_optimization_opportunities: any[];
    }> {
        return this.makeRequest(`/api/vendor-lockin/contracts/${contractId}/renewal-recommendations`);
    }

    // Mitigation Strategies
    async getMitigationStrategies(assessmentId?: string): Promise<MitigationStrategy[]> {
        const params = assessmentId ? `?assessment_id=${assessmentId}` : '';
        return this.makeRequest(`/api/vendor-lockin/mitigation-strategies${params}`);
    }

    async implementMitigationStrategy(strategyId: string, implementationPlan: {
        phases: RoadmapPhase[];
        success_metrics: string[];
        monitoring_plan: string[];
        rollback_plan: string[];
    }): Promise<{
        implementation_id: string;
        timeline: string;
        monitoring_dashboard_url: string;
        success_criteria: string[];
    }> {
        return this.makeRequest(`/api/vendor-lockin/mitigation-strategies/${strategyId}/implement`, {
            method: 'POST',
            body: JSON.stringify(implementationPlan),
        });
    }

    async trackMitigationProgress(implementationId: string): Promise<{
        progress_percentage: number;
        current_phase: string;
        completed_milestones: string[];
        upcoming_milestones: string[];
        issues_encountered: any[];
        effectiveness_metrics: any[];
    }> {
        return this.makeRequest(`/api/vendor-lockin/mitigation-strategies/implementations/${implementationId}/progress`);
    }

    // Risk Monitoring and Alerts
    async configureLockInMonitoring(config: {
        risk_score_threshold: number;
        contract_renewal_alerts: boolean;
        service_dependency_monitoring: boolean;
        cost_escalation_alerts: boolean;
        new_service_adoption_reviews: boolean;
        notification_channels: string[];
    }): Promise<void> {
        await this.makeRequest('/api/vendor-lockin/monitoring/config', {
            method: 'PUT',
            body: JSON.stringify(config),
        });
    }

    async getLockInAlerts(): Promise<Array<{
        id: string;
        alert_type: string;
        severity: 'info' | 'warning' | 'critical';
        message: string;
        affected_services: string[];
        recommended_actions: string[];
        created_at: string;
    }>> {
        return this.makeRequest('/api/vendor-lockin/alerts');
    }

    // Reporting and Analytics
    async generateLockInReport(reportConfig: {
        report_type: 'executive_summary' | 'detailed_analysis' | 'migration_plan' | 'multi_cloud_strategy';
        assessment_ids: string[];
        format: 'pdf' | 'pptx' | 'excel';
        include_charts: boolean;
        include_recommendations: boolean;
    }): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/api/vendor-lockin/reports/generate`, {
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

    async getLockInTrends(timeframe: string = '12m'): Promise<{
        risk_score_trends: any[];
        service_diversity_trends: any[];
        migration_activity: any[];
        cost_impact_trends: any[];
        contract_renewal_timeline: any[];
    }> {
        return this.makeRequest(`/api/vendor-lockin/trends?timeframe=${timeframe}`);
    }

    async getBenchmarkData(): Promise<{
        industry_averages: any;
        best_practices: string[];
        peer_comparisons: any[];
        maturity_assessment: any;
    }> {
        return this.makeRequest('/api/vendor-lockin/benchmarks');
    }
}

// Singleton instance
let vendorLockInAnalysisService: VendorLockInAnalysisService | null = null;

export const getVendorLockInAnalysisService = (): VendorLockInAnalysisService => {
    if (!vendorLockInAnalysisService) {
        vendorLockInAnalysisService = new VendorLockInAnalysisService();
    }
    return vendorLockInAnalysisService;
};

export default VendorLockInAnalysisService;