'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    LinearProgress,
    Button,
    Stepper,
    Step,
    StepLabel,
    Alert,
    CircularProgress,
    Chip,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    Pause as PauseIcon,
    SkipNext as NextIcon,
    Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiClient } from '../services/api';

interface WorkflowStep {
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    description?: string;
    progress?: number;
}

interface WorkflowProgressProps {
    assessmentId: string;
    onProgressUpdate?: (progress: number, status: string) => void;
    autoRefresh?: boolean;
    refreshInterval?: number;
}

const WORKFLOW_STEPS = [
    { key: 'initialization', label: 'Initialization' },
    { key: 'analysis', label: 'Analysis' },
    { key: 'optimization', label: 'Optimization' },
    { key: 'report_generation', label: 'Report Generation' },
    { key: 'completion', label: 'Completion' }
];

const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
    assessmentId,
    onProgressUpdate,
    autoRefresh = true,
    refreshInterval = 5000
}) => {
    const [workflowState, setWorkflowState] = useState({
        currentStep: '',
        progress: 0,
        status: '',
        steps: [] as WorkflowStep[],
        loading: false,
        error: null as string | null,
        canAdvance: false,
        isRunning: false
    });

    useEffect(() => {
        loadWorkflowStatus();
        
        if (autoRefresh) {
            const interval = setInterval(loadWorkflowStatus, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [assessmentId, autoRefresh, refreshInterval]);

    const loadWorkflowStatus = async () => {
        try {
            const response = await apiClient.getAssessmentWorkflowStatus(assessmentId);
            setWorkflowState(prev => ({
                ...prev,
                currentStep: response.current_step || '',
                progress: response.progress || 0,
                status: response.status || '',
                steps: response.steps || [],
                canAdvance: response.can_advance || false,
                isRunning: response.is_running || false,
                error: null
            }));

            if (onProgressUpdate) {
                onProgressUpdate(response.progress || 0, response.status || '');
            }
        } catch (error) {
            console.error('Failed to load workflow status:', error);
            setWorkflowState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Failed to load workflow status'
            }));
        }
    };

    const handleAdvanceStep = async () => {
        setWorkflowState(prev => ({ ...prev, loading: true, error: null }));
        
        try {
            await apiClient.advanceAssessmentWorkflow(assessmentId);
            await loadWorkflowStatus(); // Refresh status after advancing
        } catch (error) {
            console.error('Failed to advance workflow:', error);
            setWorkflowState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Failed to advance workflow'
            }));
        } finally {
            setWorkflowState(prev => ({ ...prev, loading: false }));
        }
    };

    const handlePauseResume = async () => {
        setWorkflowState(prev => ({ ...prev, loading: true, error: null }));
        
        try {
            if (workflowState.isRunning) {
                await apiClient.pauseAssessmentWorkflow(assessmentId);
            } else {
                await apiClient.resumeAssessmentWorkflow(assessmentId);
            }
            await loadWorkflowStatus();
        } catch (error) {
            console.error('Failed to pause/resume workflow:', error);
            setWorkflowState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Failed to pause/resume workflow'
            }));
        } finally {
            setWorkflowState(prev => ({ ...prev, loading: false }));
        }
    };

    const getStepStatus = (stepKey: string) => {
        const step = workflowState.steps.find(s => s.name === stepKey);
        if (!step) return 'pending';
        return step.status;
    };

    const getCurrentStepIndex = () => {
        return WORKFLOW_STEPS.findIndex(step => step.key === workflowState.currentStep);
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed': return 'success';
            case 'in_progress': return 'primary';
            case 'failed': return 'error';
            case 'paused': return 'warning';
            default: return 'default';
        }
    };

    return (
        <Card sx={{ mb: 3 }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                        Workflow Progress
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Chip 
                            label={workflowState.status.replace('_', ' ').toUpperCase()}
                            color={getStatusColor(workflowState.status) as any}
                            size="small"
                        />
                        <Tooltip title="Refresh Status">
                            <IconButton 
                                size="small" 
                                onClick={loadWorkflowStatus}
                                disabled={workflowState.loading}
                            >
                                <RefreshIcon />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>

                {workflowState.error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => 
                        setWorkflowState(prev => ({ ...prev, error: null }))
                    }>
                        {workflowState.error}
                    </Alert>
                )}

                {/* Overall Progress */}
                <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                            Overall Progress
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                            {workflowState.progress}%
                        </Typography>
                    </Box>
                    <LinearProgress 
                        variant="determinate" 
                        value={workflowState.progress} 
                        sx={{ height: 8, borderRadius: 4 }}
                    />
                </Box>

                {/* Workflow Steps */}
                <Stepper activeStep={getCurrentStepIndex()} sx={{ mb: 3 }}>
                    {WORKFLOW_STEPS.map((step, index) => {
                        const stepStatus = getStepStatus(step.key);
                        return (
                            <Step key={step.key}>
                                <StepLabel 
                                    error={stepStatus === 'failed'}
                                    completed={stepStatus === 'completed'}
                                >
                                    <Box>
                                        <Typography variant="body2">
                                            {step.label}
                                        </Typography>
                                        {step.key === workflowState.currentStep && (
                                            <Typography variant="caption" color="primary">
                                                Current Step
                                            </Typography>
                                        )}
                                    </Box>
                                </StepLabel>
                            </Step>
                        );
                    })}
                </Stepper>

                {/* Current Step Details */}
                {workflowState.currentStep && (
                    <Card variant="outlined" sx={{ mb: 3, bgcolor: 'action.hover' }}>
                        <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                                Current Step: {WORKFLOW_STEPS.find(s => s.key === workflowState.currentStep)?.label}
                            </Typography>
                            {workflowState.steps.find(s => s.name === workflowState.currentStep)?.description && (
                                <Typography variant="body2" color="text.secondary">
                                    {workflowState.steps.find(s => s.name === workflowState.currentStep)?.description}
                                </Typography>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Control Buttons */}
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                    <Button
                        variant="outlined"
                        startIcon={workflowState.isRunning ? <PauseIcon /> : <PlayIcon />}
                        onClick={handlePauseResume}
                        disabled={workflowState.loading || workflowState.status === 'completed'}
                    >
                        {workflowState.isRunning ? 'Pause' : 'Resume'}
                    </Button>
                    
                    {workflowState.canAdvance && (
                        <Button
                            variant="contained"
                            startIcon={workflowState.loading ? <CircularProgress size={20} /> : <NextIcon />}
                            onClick={handleAdvanceStep}
                            disabled={workflowState.loading || !workflowState.canAdvance}
                        >
                            Advance Step
                        </Button>
                    )}
                </Box>

                {/* Manual Trigger Notice */}
                {workflowState.status === 'paused' && workflowState.canAdvance && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                        This assessment is paused and waiting for manual input. 
                        Click "Advance Step" to continue the workflow.
                    </Alert>
                )}
            </CardContent>
        </Card>
    );
};

export default WorkflowProgress;