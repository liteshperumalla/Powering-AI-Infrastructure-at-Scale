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
    { key: 'created', label: 'Assessment Created' },
    { key: 'initializing', label: 'Initializing Workflow' },
    { key: 'analysis', label: 'Multi-Agent Analysis' },
    { key: 'recommendations', label: 'Generating Recommendations' },
    { key: 'report_generation', label: 'Report Generation' },
    { key: 'completed', label: 'Analysis Complete' }
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
            // Use the existing assessment endpoint instead of non-existent workflow status endpoint
            const response = await apiClient.getAssessment(assessmentId);
            const progress = response.progress || {};

            setWorkflowState(prev => ({
                ...prev,
                currentStep: progress.current_step || 'created',
                progress: progress.progress_percentage || 0,
                status: response.status || 'draft',
                steps: [], // We'll map this from our known workflow steps
                canAdvance: response.status === 'draft' || response.status === 'failed',
                isRunning: response.status === 'in_progress',
                error: progress.error || null
            }));

            if (onProgressUpdate) {
                onProgressUpdate(progress.progress_percentage || 0, response.status || '');
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
            // Use the existing start workflow endpoint
            await apiClient.startAssessmentAnalysis(assessmentId, {
                assessment_id: assessmentId,
                priority: 'high',
                use_advanced_analysis: true
            });
            await loadWorkflowStatus(); // Refresh status after starting
        } catch (error) {
            console.error('Failed to start workflow:', error);
            setWorkflowState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Failed to start workflow'
            }));
        } finally {
            setWorkflowState(prev => ({ ...prev, loading: false }));
        }
    };

    const handleRefresh = async () => {
        setWorkflowState(prev => ({ ...prev, loading: true, error: null }));
        try {
            await loadWorkflowStatus();
        } finally {
            setWorkflowState(prev => ({ ...prev, loading: false }));
        }
    };

    const getStepStatus = (stepKey: string) => {
        // Map based on current step and progress percentage
        const currentStepIndex = WORKFLOW_STEPS.findIndex(step => step.key === workflowState.currentStep);
        const stepIndex = WORKFLOW_STEPS.findIndex(step => step.key === stepKey);

        if (stepIndex < currentStepIndex) {
            return 'completed';
        } else if (stepIndex === currentStepIndex && workflowState.status === 'in_progress') {
            return 'in_progress';
        } else if (stepIndex === currentStepIndex && workflowState.status === 'failed') {
            return 'failed';
        } else {
            return 'pending';
        }
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
                    <Typography variant="h6" color="text.primary">
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
                        startIcon={workflowState.loading ? <CircularProgress size={20} /> : <RefreshIcon />}
                        onClick={handleRefresh}
                        disabled={workflowState.loading}
                    >
                        Refresh Status
                    </Button>

                    {workflowState.canAdvance && (
                        <Button
                            variant="contained"
                            startIcon={workflowState.loading ? <CircularProgress size={20} /> : <PlayIcon />}
                            onClick={handleAdvanceStep}
                            disabled={workflowState.loading || !workflowState.canAdvance}
                        >
                            Start Analysis
                        </Button>
                    )}
                </Box>

                {/* Manual Trigger Notice */}
                {workflowState.canAdvance && workflowState.status !== 'in_progress' && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                        This assessment is ready to start. Click "Start Analysis" to begin the AI workflow.
                    </Alert>
                )}
            </CardContent>
        </Card>
    );
};

export default WorkflowProgress;