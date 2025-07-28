import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

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
}

const initialState: AssessmentState = {
    assessments: [],
    currentAssessment: null,
    loading: false,
    error: null,
};

// Async thunks
export const createAssessment = createAsyncThunk(
    'assessment/create',
    async (assessmentData: Partial<Assessment>) => {
        // Simulate API call
        const response = await new Promise<Assessment>((resolve) => {
            setTimeout(() => {
                resolve({
                    id: Date.now().toString(),
                    businessRequirements: assessmentData.businessRequirements || {} as BusinessRequirements,
                    technicalRequirements: assessmentData.technicalRequirements || {} as TechnicalRequirements,
                    status: 'draft',
                    progress: 0,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                });
            }, 1000);
        });
        return response;
    }
);

export const updateAssessment = createAsyncThunk(
    'assessment/update',
    async ({ id, updates }: { id: string; updates: Partial<Assessment> }) => {
        // Simulate API call
        const response = await new Promise<Assessment>((resolve) => {
            setTimeout(() => {
                resolve({
                    id,
                    ...updates,
                    updatedAt: new Date().toISOString(),
                } as Assessment);
            }, 500);
        });
        return response;
    }
);

export const fetchAssessments = createAsyncThunk(
    'assessment/fetchAll',
    async () => {
        // Simulate API call
        const response = await new Promise<Assessment[]>((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: '1',
                        businessRequirements: {
                            companySize: 'mid-size',
                            industry: 'healthcare',
                            budgetRange: '100k-500k',
                            timeline: '6-months',
                            complianceNeeds: ['HIPAA', 'GDPR'],
                            businessGoals: ['cost-optimization', 'scalability'],
                        },
                        technicalRequirements: {
                            currentInfrastructure: { cloud: 'aws', containers: true },
                            workloadCharacteristics: { type: 'ml', scale: 'medium' },
                            performanceRequirements: { latency: 'low', throughput: 'high' },
                            scalabilityNeeds: { horizontal: true, vertical: false },
                            integrationRequirements: ['api', 'database'],
                        },
                        status: 'completed',
                        progress: 100,
                        createdAt: '2024-01-15T10:00:00Z',
                        updatedAt: '2024-01-15T14:30:00Z',
                    },
                ]);
            }, 1000);
        });
        return response;
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
                state.error = action.error.message || 'Failed to fetch assessments';
            });
    },
});

export const { setCurrentAssessment, updateCurrentAssessment, clearError } = assessmentSlice.actions;
export default assessmentSlice.reducer;