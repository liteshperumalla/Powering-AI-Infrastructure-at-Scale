import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface ScenarioParameters {
    timeHorizon: '6-months' | '1-year' | '2-years' | '3-years';
    scalingFactor: number;
    budgetConstraint: number;
    complianceLevel: 'basic' | 'standard' | 'strict';
    performanceTarget: 'cost-optimized' | 'balanced' | 'performance-optimized';
}

export interface CloudService {
    name: string;
    provider: 'AWS' | 'Azure' | 'GCP';
    type: string;
    monthlyCost: number;
    performance: number;
    scalability: number;
    compliance: number;
}

export interface ScenarioResult {
    totalCost: number;
    performanceScore: number;
    complianceScore: number;
    scalabilityScore: number;
    services: CloudService[];
    projections: {
        month: number;
        cost: number;
        performance: number;
        utilization: number;
    }[];
}

export interface Scenario {
    id: string;
    name: string;
    description: string;
    parameters: ScenarioParameters;
    result: ScenarioResult | null;
    status: 'draft' | 'running' | 'completed' | 'error';
    createdAt: string;
    updatedAt: string;
}

interface ScenarioState {
    scenarios: Scenario[];
    currentScenario: Scenario | null;
    comparisonScenarios: Scenario[];
    loading: boolean;
    error: string | null;
    simulationProgress: number;
}

const initialState: ScenarioState = {
    scenarios: [],
    currentScenario: null,
    comparisonScenarios: [],
    loading: false,
    error: null,
    simulationProgress: 0,
};

// Async thunks
export const createScenario = createAsyncThunk(
    'scenario/create',
    async (scenarioData: Omit<Scenario, 'id' | 'result' | 'status' | 'createdAt' | 'updatedAt'>) => {
        // Simulate API call
        const response = await new Promise<Scenario>((resolve) => {
            setTimeout(() => {
                resolve({
                    id: Date.now().toString(),
                    ...scenarioData,
                    result: null,
                    status: 'draft',
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                });
            }, 500);
        });
        return response;
    }
);

export const runScenarioSimulation = createAsyncThunk(
    'scenario/simulate',
    async (scenarioId: string, { dispatch }) => {
        // Simulate progress updates
        for (let progress = 0; progress <= 100; progress += 10) {
            dispatch(setSimulationProgress(progress));
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        // Simulate API call for scenario simulation
        const response = await new Promise<ScenarioResult>((resolve) => {
            setTimeout(() => {
                resolve({
                    totalCost: 12500,
                    performanceScore: 85,
                    complianceScore: 92,
                    scalabilityScore: 88,
                    services: [
                        {
                            name: 'EC2 t3.large',
                            provider: 'AWS',
                            type: 'Compute',
                            monthlyCost: 67.32,
                            performance: 85,
                            scalability: 90,
                            compliance: 95,
                        },
                        {
                            name: 'RDS PostgreSQL',
                            provider: 'AWS',
                            type: 'Database',
                            monthlyCost: 145.60,
                            performance: 88,
                            scalability: 85,
                            compliance: 98,
                        },
                        {
                            name: 'S3 Standard',
                            provider: 'AWS',
                            type: 'Storage',
                            monthlyCost: 23.50,
                            performance: 90,
                            scalability: 95,
                            compliance: 99,
                        },
                    ],
                    projections: Array.from({ length: 12 }, (_, i) => ({
                        month: i + 1,
                        cost: 12500 + (i * 500) + (Math.random() * 1000 - 500),
                        performance: 85 + (Math.random() * 10 - 5),
                        utilization: 60 + (i * 2) + (Math.random() * 10 - 5),
                    })),
                });
            }, 1000);
        });
        return { scenarioId, result: response };
    }
);

export const duplicateScenario = createAsyncThunk(
    'scenario/duplicate',
    async (scenarioId: string, { getState }) => {
        const state = getState() as { scenario: ScenarioState };
        const originalScenario = state.scenario.scenarios.find(s => s.id === scenarioId);

        if (!originalScenario) {
            throw new Error('Scenario not found');
        }

        // Simulate API call
        const response = await new Promise<Scenario>((resolve) => {
            setTimeout(() => {
                resolve({
                    ...originalScenario,
                    id: Date.now().toString(),
                    name: `${originalScenario.name} (Copy)`,
                    result: null,
                    status: 'draft',
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                });
            }, 500);
        });
        return response;
    }
);

export const fetchScenarios = createAsyncThunk(
    'scenario/fetchAll',
    async () => {
        // Simulate API call
        const response = await new Promise<Scenario[]>((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: '1',
                        name: 'Current State Analysis',
                        description: 'Analysis of current infrastructure costs and performance',
                        parameters: {
                            timeHorizon: '1-year',
                            scalingFactor: 1.0,
                            budgetConstraint: 50000,
                            complianceLevel: 'standard',
                            performanceTarget: 'balanced',
                        },
                        result: {
                            totalCost: 12500,
                            performanceScore: 85,
                            complianceScore: 92,
                            scalabilityScore: 88,
                            services: [
                                {
                                    name: 'EC2 t3.large',
                                    provider: 'AWS',
                                    type: 'Compute',
                                    monthlyCost: 67.32,
                                    performance: 85,
                                    scalability: 90,
                                    compliance: 95,
                                },
                            ],
                            projections: Array.from({ length: 12 }, (_, i) => ({
                                month: i + 1,
                                cost: 12500 + (i * 500),
                                performance: 85,
                                utilization: 60 + (i * 2),
                            })),
                        },
                        status: 'completed',
                        createdAt: '2024-01-15T10:00:00Z',
                        updatedAt: '2024-01-15T14:30:00Z',
                    },
                    {
                        id: '2',
                        name: 'Optimized Multi-Cloud',
                        description: 'Cost-optimized multi-cloud deployment scenario',
                        parameters: {
                            timeHorizon: '2-years',
                            scalingFactor: 1.5,
                            budgetConstraint: 75000,
                            complianceLevel: 'strict',
                            performanceTarget: 'cost-optimized',
                        },
                        result: {
                            totalCost: 9800,
                            performanceScore: 78,
                            complianceScore: 98,
                            scalabilityScore: 92,
                            services: [
                                {
                                    name: 'Compute Engine n1-standard-4',
                                    provider: 'GCP',
                                    type: 'Compute',
                                    monthlyCost: 58.90,
                                    performance: 82,
                                    scalability: 88,
                                    compliance: 94,
                                },
                            ],
                            projections: Array.from({ length: 24 }, (_, i) => ({
                                month: i + 1,
                                cost: 9800 + (i * 300),
                                performance: 78,
                                utilization: 55 + (i * 1.5),
                            })),
                        },
                        status: 'completed',
                        createdAt: '2024-01-15T11:00:00Z',
                        updatedAt: '2024-01-15T15:30:00Z',
                    },
                ]);
            }, 1000);
        });
        return response;
    }
);

const scenarioSlice = createSlice({
    name: 'scenario',
    initialState,
    reducers: {
        setCurrentScenario: (state, action: PayloadAction<Scenario | null>) => {
            state.currentScenario = action.payload;
        },
        addToComparison: (state, action: PayloadAction<Scenario>) => {
            if (state.comparisonScenarios.length < 3 &&
                !state.comparisonScenarios.find(s => s.id === action.payload.id)) {
                state.comparisonScenarios.push(action.payload);
            }
        },
        removeFromComparison: (state, action: PayloadAction<string>) => {
            state.comparisonScenarios = state.comparisonScenarios.filter(s => s.id !== action.payload);
        },
        clearComparison: (state) => {
            state.comparisonScenarios = [];
        },
        setSimulationProgress: (state, action: PayloadAction<number>) => {
            state.simulationProgress = action.payload;
        },
        updateScenarioParameters: (state, action: PayloadAction<{ scenarioId: string; parameters: ScenarioParameters }>) => {
            const scenario = state.scenarios.find(s => s.id === action.payload.scenarioId);
            if (scenario) {
                scenario.parameters = action.payload.parameters;
                scenario.updatedAt = new Date().toISOString();
            }
            if (state.currentScenario?.id === action.payload.scenarioId) {
                state.currentScenario.parameters = action.payload.parameters;
                state.currentScenario.updatedAt = new Date().toISOString();
            }
        },
        clearError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Create scenario
            .addCase(createScenario.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(createScenario.fulfilled, (state, action) => {
                state.loading = false;
                state.scenarios.push(action.payload);
                state.currentScenario = action.payload;
            })
            .addCase(createScenario.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to create scenario';
            })
            // Run simulation
            .addCase(runScenarioSimulation.pending, (state) => {
                state.loading = true;
                state.error = null;
                state.simulationProgress = 0;
            })
            .addCase(runScenarioSimulation.fulfilled, (state, action) => {
                state.loading = false;
                state.simulationProgress = 100;
                const scenario = state.scenarios.find(s => s.id === action.payload.scenarioId);
                if (scenario) {
                    scenario.result = action.payload.result;
                    scenario.status = 'completed';
                    scenario.updatedAt = new Date().toISOString();
                }
                if (state.currentScenario?.id === action.payload.scenarioId) {
                    state.currentScenario.result = action.payload.result;
                    state.currentScenario.status = 'completed';
                    state.currentScenario.updatedAt = new Date().toISOString();
                }
            })
            .addCase(runScenarioSimulation.rejected, (state, action) => {
                state.loading = false;
                state.simulationProgress = 0;
                state.error = action.error.message || 'Failed to run simulation';
            })
            // Duplicate scenario
            .addCase(duplicateScenario.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(duplicateScenario.fulfilled, (state, action) => {
                state.loading = false;
                state.scenarios.push(action.payload);
            })
            .addCase(duplicateScenario.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to duplicate scenario';
            })
            // Fetch scenarios
            .addCase(fetchScenarios.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchScenarios.fulfilled, (state, action) => {
                state.loading = false;
                state.scenarios = action.payload;
            })
            .addCase(fetchScenarios.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to fetch scenarios';
            });
    },
});

export const {
    setCurrentScenario,
    addToComparison,
    removeFromComparison,
    clearComparison,
    setSimulationProgress,
    updateScenarioParameters,
    clearError,
} = scenarioSlice.actions;

export default scenarioSlice.reducer;