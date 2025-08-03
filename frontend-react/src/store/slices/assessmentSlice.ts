import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

export interface BusinessRequirements {
    companySize: string;
    industry: string;
    budgetRange: string;
    timeline: string;
    complianceNeeds: string[];
    businessGoals: string[];
}

export interface TechnicalRequirements {
    currentInfrastructure: Record<string, unknown>;
    workloadCharacteristics: Record<string, unknown>;
    performanceRequirements: Record<string, unknown>;
    scalabilityNeeds: Record<string, unknown>;
    integrationRequirements: string[];
}

export interface Assessment {
    id: string;
    businessRequirements: BusinessRequirements;
    technicalRequirements: TechnicalRequirements;
    status: 'draft' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    createdAt: string;
    updatedAt: string;
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
            const response = await apiClient.getAssessments();
            return response;
        } catch (error) {
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
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchAssessments.fulfilled, (state, action) => {
                state.loading = false;
                state.assessments = action.payload;
            })
            .addCase(fetchAssessments.rejected, (state, action) => {
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