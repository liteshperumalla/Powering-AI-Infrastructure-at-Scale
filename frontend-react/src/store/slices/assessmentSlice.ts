import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

// Business Goals structure matching backend
export interface BusinessGoal {
    goal: string;
    priority: 'low' | 'medium' | 'high';
    timeline_months?: number;
    success_metrics: string[];
}

// Growth Projection structure matching backend  
export interface GrowthProjection {
    current_users: number;
    projected_users_6m?: number;
    projected_users_12m?: number;
    projected_users_24m?: number;
    current_revenue?: number;
    projected_revenue_12m?: number;
}

// Budget Constraints structure matching backend
export interface BudgetConstraints {
    total_budget_range: string;
    preferred_budget: number;
    budget_flexibility: 'low' | 'medium' | 'high';
    cost_optimization_priority: 'low' | 'medium' | 'high';
}

// Team Structure matching backend
export interface TeamStructure {
    total_developers: number;
    senior_developers: number;
    devops_engineers: number;
    data_engineers: number;
    cloud_expertise_level: number; // 1-5 scale
    kubernetes_expertise?: number;
    database_expertise?: number;
    preferred_technologies?: string[];
}

export interface BusinessRequirements {
    // Core fields
    company_size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
    industry: string;
    
    // Enhanced business fields from Step 1
    company_name?: string;
    geographic_regions?: string[];
    customer_base_size?: 'small' | 'medium' | 'enterprise' | 'enterprise_global';
    revenue_model?: 'subscription' | 'saas' | 'platform_fees' | 'transaction_based' | 'licensing';
    growth_stage?: 'startup' | 'early_stage' | 'growing' | 'series-a' | 'series-b' | 'series-c' | 'late_stage' | 'public';
    key_competitors?: string;
    mission_critical_systems?: string[];
    
    // Existing structured fields
    business_goals: BusinessGoal[];
    growth_projection: GrowthProjection;
    budget_constraints: BudgetConstraints;
    team_structure: TeamStructure;
    compliance_requirements?: string[];
    project_timeline_months: number;
    urgency_level?: 'low' | 'medium' | 'high';
    current_pain_points?: string[];
    success_criteria?: string[];
}

export interface TechnicalRequirements {
    // Core fields
    current_infrastructure?: string;
    workload_types: string[];
    
    // Enhanced technical fields from Steps 2-6
    current_cloud_providers?: string[];
    current_services?: string[];
    technical_team_size?: number;
    infrastructure_age?: 'legacy' | 'established' | 'recent' | 'modern';
    current_architecture?: 'monolithic' | 'microservices' | 'serverless' | 'event_driven_microservices';
    
    // AI/ML fields
    ai_use_cases?: string[];
    current_ai_maturity?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    expected_data_volume?: string;
    data_types?: string[];
    
    // Performance fields
    current_user_load?: string;
    expected_growth_rate?: string;
    budget_flexibility?: 'low' | 'medium' | 'high';
    total_budget_range?: string;
    
    // Programming and frameworks
    preferred_programming_languages?: string[];
    development_frameworks?: string[];
    database_types?: string[];
    
    // Operations
    monitoring_requirements?: string[];
    ci_cd_requirements?: string[];
    backup_requirements?: string[];
    deployment_preferences?: string[];
    
    // Existing structured fields (enhanced)
    performance_requirements?: {
        api_response_time_ms?: number;
        requests_per_second?: number;
        concurrent_users?: number;
        uptime_percentage?: number;
        response_time_requirement?: string;
        requests_per_second_requirement?: string;
        uptime_requirement?: string;
        peak_load_multiplier?: number;
        auto_scaling_required?: boolean;
        global_distribution?: boolean;
    };
    
    scalability_requirements?: {
        current_data_size_gb?: number;
        current_daily_transactions?: number;
        expected_data_growth_rate?: string;
        peak_load_multiplier?: number;
        auto_scaling_required?: boolean;
        global_distribution_required?: boolean;
        cdn_required?: boolean;
        planned_regions?: string[];
    };
    
    security_requirements?: {
        encryption_at_rest_required?: boolean;
        encryption_in_transit_required?: boolean;
        multi_factor_auth_required?: boolean;
        single_sign_on_required?: boolean;
        role_based_access_control?: boolean;
        vpc_isolation_required?: boolean;
        firewall_required?: boolean;
        ddos_protection_required?: boolean;
        security_monitoring_required?: boolean;
        audit_logging_required?: boolean;
        vulnerability_scanning_required?: boolean;
        data_loss_prevention_required?: boolean;
        backup_encryption_required?: boolean;
        encryption_requirements?: string[];
        access_control_methods?: string[];
        network_security?: string[];
        data_classification?: string;
        security_level?: 'basic' | 'standard' | 'high' | 'critical';
    };
    
    integration_requirements?: {
        existing_databases?: string[];
        existing_apis?: string[];
        legacy_systems?: string[];
        payment_processors?: string[];
        analytics_platforms?: string[];
        marketing_tools?: string[];
        rest_api_required?: boolean;
        graphql_api_required?: boolean;
        websocket_support_required?: boolean;
        real_time_sync_required?: boolean;
        batch_sync_acceptable?: boolean;
        data_storage_solution?: string[];
        networking_requirements?: string[];
    };
}

export interface Assessment {
    id: string;
    businessRequirements?: BusinessRequirements;
    technicalRequirements?: TechnicalRequirements;
    business_requirements?: BusinessRequirements; // Backend naming
    technical_requirements?: TechnicalRequirements; // Backend naming
    status: 'draft' | 'in_progress' | 'completed' | 'failed';
    progress_percentage: number;
    title: string;
    description?: string;
    business_goal?: string;
    priority?: 'low' | 'medium' | 'high' | 'critical';
    
    // Core fields for display
    company_size: string;
    industry: string;
    budget_range: string;
    workload_types: string[];
    
    // Enhanced fields for display (extracted from requirements)
    company_name?: string;
    geographic_regions?: string[];
    ai_use_cases?: string[];
    technical_team_size?: number;
    expected_data_volume?: string;
    
    // Status and progress
    recommendations_generated: boolean;
    reports_generated: boolean;
    workflow_id?: string;
    agent_states?: Record<string, unknown>;
    workflow_progress?: Record<string, unknown>;
    progress?: {
        current_step?: string;
        completed_steps?: string[];
        total_steps?: number;
        progress_percentage?: number;
        error?: string;
    };
    
    // Timestamps
    created_at: string;
    updated_at: string;
    started_at?: string;
    completed_at?: string;
    
    // Metadata
    source?: string;
    tags?: string[];
    metadata?: Record<string, unknown>;
}

interface AssessmentState {
    assessments: Assessment[];
    currentAssessment: Assessment | null;
    loading: boolean;
    error: string | null;
    workflowId: string | null;
    recommendations: unknown[];
    recommendationsLoading: boolean;
}

const initialState: AssessmentState = {
    assessments: [],
    currentAssessment: null,
    loading: false,
    error: null,
    workflowId: null,
    recommendations: [],
    recommendationsLoading: false,
};

// Async thunks - Real API integration
export const createAssessment = createAsyncThunk(
    'assessment/create',
    async (assessmentData: {
        title: string;
        description?: string;
        business_requirements: BusinessRequirements;
        technical_requirements: TechnicalRequirements;
    }, { rejectWithValue }) => {
        try {
            const response = await apiClient.createAssessment(assessmentData);
            return response;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to create assessment');
        }
    }
);

export const updateAssessment = createAsyncThunk(
    'assessment/update',
    async ({ id, updates }: { id: string; updates: Partial<Assessment> }, { rejectWithValue }) => {
        try {
            const response = await apiClient.updateAssessment(id, updates);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to update assessment');
        }
    }
);

export const fetchAssessments = createAsyncThunk(
    'assessment/fetchAll',
    async (_, { rejectWithValue }) => {
        try {
            console.log('🔄 Fetching assessments...');
            const response = await apiClient.getAssessments();
            console.log('📊 Assessments API response:', response);
            console.log('📊 Assessments array:', response.assessments);
            
            try {
                console.log('🔍 Starting response inspection...');
                console.log('🔍 Response type:', typeof response);
                console.log('🔍 Response keys:', response && typeof response === 'object' ? Object.keys(response) : 'N/A - not an object');
            } catch (inspectionError) {
                console.error('❌ Error during response inspection:', inspectionError);
            }
            console.log('🔍 Response.assessments type:', typeof response.assessments);
            console.log('🔍 Response.assessments length:', response.assessments?.length);
            console.log('🎯 About to return response to Redux...');
            
            // Validate response structure
            if (!response || typeof response !== 'object') {
                console.error('❌ Invalid response structure:', response);
                throw new Error('Invalid API response structure');
            }
            
            if (!Array.isArray(response.assessments)) {
                console.error('❌ response.assessments is not an array:', response.assessments);
                throw new Error('Assessments data is not an array');
            }
            
            console.log('✅ Response validation passed, returning to Redux...');
            return response;
        } catch (error) {
            console.error('❌ Failed to fetch assessments:', error);
            console.error('❌ Error details:', {
                message: error instanceof Error ? error.message : 'Unknown error',
                stack: error instanceof Error ? error.stack : undefined,
                type: typeof error
            });
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch assessments');
        }
    }
);

export const fetchAssessment = createAsyncThunk(
    'assessment/fetchOne',
    async (id: string, { rejectWithValue }) => {
        try {
            const response = await apiClient.getAssessment(id);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch assessment');
        }
    }
);

export const deleteAssessment = createAsyncThunk(
    'assessment/delete',
    async (id: string, { rejectWithValue }) => {
        try {
            await apiClient.deleteAssessment(id);
            return id;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to delete assessment');
        }
    }
);

export const generateRecommendations = createAsyncThunk(
    'assessment/generateRecommendations',
    async (assessmentId: string, { rejectWithValue }) => {
        try {
            const response = await apiClient.generateRecommendations(assessmentId);
            return response;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to generate recommendations');
        }
    }
);

const assessmentSlice = createSlice({
    name: 'assessment',
    initialState,
    reducers: {
        setCurrentAssessment: (state, action: PayloadAction<Assessment | null>) => {
            state.currentAssessment = action.payload;
        },
        updateCurrentAssessment: (state, action: PayloadAction<Partial<Assessment>>) => {
            if (state.currentAssessment) {
                state.currentAssessment = { ...state.currentAssessment, ...action.payload };
            }
        },
        clearError: (state) => {
            state.error = null;
        },
        setWorkflowId: (state, action: PayloadAction<string | null>) => {
            state.workflowId = action.payload;
        },
        setRecommendations: (state, action: PayloadAction<unknown[]>) => {
            state.recommendations = action.payload;
        },
    },
    extraReducers: (builder) => {
        builder
            // Create assessment
            .addCase(createAssessment.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createAssessment.fulfilled, (state, action) => {
                state.loading = false;
                state.assessments.push(action.payload);
                state.currentAssessment = action.payload;
                // Set workflowId if returned from backend
                if (action.payload.workflow_id) {
                    state.workflowId = action.payload.workflow_id;
                }
            })
            .addCase(createAssessment.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to create assessment';
            })
            // Update assessment
            .addCase(updateAssessment.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateAssessment.fulfilled, (state, action) => {
                state.loading = false;
                const index = state.assessments.findIndex(a => a.id === action.payload.id);
                if (index !== -1) {
                    state.assessments[index] = action.payload;
                }
                if (state.currentAssessment?.id === action.payload.id) {
                    state.currentAssessment = action.payload;
                }
            })
            .addCase(updateAssessment.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to update assessment';
            })
            // Fetch assessments
            .addCase(fetchAssessments.pending, (state) => {
                console.log('🔄 Redux: fetchAssessments.pending triggered');
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchAssessments.fulfilled, (state, action) => {
                state.loading = false;
                // Extract the assessments array from the API response
                const assessments = action.payload.assessments || [];
                state.assessments = assessments;
                console.log('🔄 Redux: fetchAssessments.fulfilled - Updated state with', assessments.length, 'assessments');
                console.log('🔄 Redux: Assessment IDs:', assessments.map(a => a.id));
            })
            .addCase(fetchAssessments.rejected, (state, action) => {
                console.log('❌ Redux: fetchAssessments.rejected triggered', action.payload);
                state.loading = false;
                state.error = action.payload as string || 'Failed to fetch assessments';
            })
            // Fetch single assessment
            .addCase(fetchAssessment.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchAssessment.fulfilled, (state, action) => {
                state.loading = false;
                state.currentAssessment = action.payload;
                // Update in assessments array if exists
                const index = state.assessments.findIndex(a => a.id === action.payload.id);
                if (index !== -1) {
                    state.assessments[index] = action.payload;
                } else {
                    state.assessments.push(action.payload);
                }
            })
            .addCase(fetchAssessment.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string || 'Failed to fetch assessment';
            })
            // Delete assessment
            .addCase(deleteAssessment.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(deleteAssessment.fulfilled, (state, action) => {
                state.loading = false;
                state.assessments = state.assessments.filter(a => a.id !== action.payload);
                if (state.currentAssessment?.id === action.payload) {
                    state.currentAssessment = null;
                }
            })
            .addCase(deleteAssessment.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string || 'Failed to delete assessment';
            })
            // Generate recommendations
            .addCase(generateRecommendations.pending, (state) => {
                state.recommendationsLoading = true;
                state.error = null;
            })
            .addCase(generateRecommendations.fulfilled, (state, action) => {
                state.recommendationsLoading = false;
                state.workflowId = action.payload.workflow_id;
            })
            .addCase(generateRecommendations.rejected, (state, action) => {
                state.recommendationsLoading = false;
                state.error = action.payload as string || 'Failed to generate recommendations';
            });
    },
});

export const {
    setCurrentAssessment,
    updateCurrentAssessment,
    clearError,
    setWorkflowId,
    setRecommendations
} = assessmentSlice.actions;
export default assessmentSlice.reducer;