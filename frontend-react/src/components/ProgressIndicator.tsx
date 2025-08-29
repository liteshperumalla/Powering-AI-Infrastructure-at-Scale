'use client';

import React, { useMemo } from 'react';
import {
    Box,
    LinearProgress,
    CircularProgress,
    Typography,
    Card,
    CardContent,
    Stepper,
    Step,
    StepLabel,
    StepContent,
    Chip,
    Avatar,
} from '@mui/material';
import {
    CheckCircle,
    RadioButtonUnchecked,
    Schedule,
    Error,
} from '@mui/icons-material';
import { useAppSelector } from '@/store/hooks';

interface ProgressStep {
    label: string;
    description?: string;
    status: 'completed' | 'active' | 'pending' | 'error';
    progress?: number;
}

interface ProgressIndicatorProps {
    title: string;
    steps: ProgressStep[];
    variant?: 'linear' | 'circular' | 'stepper';
    showPercentage?: boolean;
    compact?: boolean;
}

export default function ProgressIndicator({
    title,
    steps,
    variant = 'stepper',
    showPercentage = true,
    compact = false,
}: ProgressIndicatorProps) {
    const { loading } = useAppSelector(state => state.ui);

    const completedSteps = steps.filter(step => step.status === 'completed').length;
    const totalSteps = steps.length;
    const overallProgress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

    const getStepIcon = (status: ProgressStep['status']) => {
        switch (status) {
            case 'completed':
                return <CheckCircle color="success" />;
            case 'active':
                return <CircularProgress size={20} />;
            case 'error':
                return <Error color="error" />;
            default:
                return <RadioButtonUnchecked color="disabled" />;
        }
    };

    type ChipColor = 'success' | 'primary' | 'error' | 'default';

    const getStatusColor = (status: ProgressStep['status']): ChipColor => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'active':
                return 'primary';
            case 'error':
                return 'error';
            default:
                return 'default';
        }
    };

    if (compact) {
        return (
            <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2" fontWeight="medium">
                        {title}
                    </Typography>
                    {showPercentage && (
                        <Typography variant="body2" color="text.secondary">
                            {Math.round(overallProgress)}%
                        </Typography>
                    )}
                </Box>
                <LinearProgress
                    variant="determinate"
                    value={overallProgress}
                    sx={{ height: 8, borderRadius: 4 }}
                />
                <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    {steps.map((step, index) => (
                        <Chip
                            key={index}
                            label={step.label}
                            size="small"
                            color={getStatusColor(step.status)}
                            variant={step.status === 'completed' ? 'filled' : 'outlined'}
                            icon={getStepIcon(step.status)}
                        />
                    ))}
                </Box>
            </Box>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">{title}</Typography>
                    {showPercentage && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="h6" color="primary">
                                {Math.round(overallProgress)}%
                            </Typography>
                            {variant === 'circular' && (
                                <CircularProgress
                                    variant="determinate"
                                    value={overallProgress}
                                    size={40}
                                    thickness={4}
                                />
                            )}
                        </Box>
                    )}
                </Box>

                {variant === 'linear' && (
                    <Box sx={{ mb: 3 }}>
                        <LinearProgress
                            variant="determinate"
                            value={overallProgress}
                            sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            {completedSteps} of {totalSteps} steps completed
                        </Typography>
                    </Box>
                )}

                {variant === 'stepper' && (
                    <Stepper orientation="vertical">
                        {steps.map((step, index) => (
                            <Step key={index} active={step.status === 'active'} completed={step.status === 'completed'}>
                                <StepLabel
                                    error={step.status === 'error'}
                                    icon={getStepIcon(step.status)}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Typography variant="body1" fontWeight="medium">
                                            {step.label}
                                        </Typography>
                                        {step.status === 'completed' && (
                                            <Chip
                                                label="✓"
                                                size="small"
                                                color="success"
                                                variant="filled"
                                                sx={{ minWidth: 'auto', px: 1 }}
                                            />
                                        )}
                                        {step.status === 'active' && (
                                            <Chip
                                                label="In Progress"
                                                size="small"
                                                color="primary"
                                                variant="outlined"
                                            />
                                        )}
                                        {step.status === 'error' && (
                                            <Chip
                                                label="Error"
                                                size="small"
                                                color="error"
                                                variant="outlined"
                                            />
                                        )}
                                    </Box>
                                </StepLabel>
                                {step.description && (
                                    <StepContent>
                                        <Typography variant="body2" color="text.secondary">
                                            {step.description}
                                        </Typography>
                                        {step.progress !== undefined && step.status === 'active' && (
                                            <Box sx={{ mt: 1 }}>
                                                <LinearProgress
                                                    variant="determinate"
                                                    value={step.progress}
                                                    sx={{ height: 6, borderRadius: 3 }}
                                                />
                                                <Typography variant="caption" color="text.secondary">
                                                    {step.progress}% complete
                                                </Typography>
                                            </Box>
                                        )}
                                    </StepContent>
                                )}
                            </Step>
                        ))}
                    </Stepper>
                )}

                {loading.global && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Processing...
                        </Typography>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
}

// Hook for creating progress steps from Redux state
export function useProgressSteps() {
    const { assessments, loading: assessmentLoading } = useAppSelector(state => state.assessment);
    const { reports, loading: reportLoading } = useAppSelector(state => state.report);
    const { scenarios, loading: scenarioLoading } = useAppSelector(state => state.scenario);

    const currentAssessment = assessments && assessments.length > 0 ? assessments[0] : null;

    const steps: ProgressStep[] = useMemo(() => {
        const assessmentProgress = currentAssessment?.progress || {};
        const currentStep = assessmentProgress.current_step || 'created';
        const completedSteps = assessmentProgress.completed_steps || [];
        
        // FIXED: Use backend progress data accurately - if status is completed, show 100%
        // but if backend progress_percentage is 0, use that instead of assuming completion
        let progressPercentage = assessmentProgress.progress_percentage || currentAssessment?.progress_percentage || 0;
        
        // Override with 100% only if assessment status is explicitly 'completed' and we have completed steps
        if (currentAssessment?.status === 'completed' && completedSteps.length > 0) {
            progressPercentage = 100;
        }
        
        // Debug progress synchronization
        console.log('🔍 Progress Debug:', {
            assessmentId: currentAssessment?.id,
            status: currentAssessment?.status,
            backendProgressPercentage: assessmentProgress.progress_percentage,
            topLevelProgressPercentage: currentAssessment?.progress_percentage,
            calculatedProgressPercentage: progressPercentage,
            currentStep,
            completedSteps,
            completedStepsCount: completedSteps.length
        });
        
        // Define the correct workflow order matching the backend assessments.py
        const workflowSteps = [
            {
                id: 'created',
                label: 'Assessment Created',
                description: 'Initial assessment setup and requirements collection',
                targetProgress: 5
            },
            {
                id: 'initializing',
                label: 'Initializing Workflow',
                description: 'Setting up AI agents and preparing analysis pipeline',
                targetProgress: 20
            },
            {
                id: 'analysis',
                label: 'Multi-Agent Analysis',
                description: 'CTO, Cloud Engineer, Infrastructure, AI Consultant, MLOps, Compliance, Research, Web Research, Simulation and Chatbot agents analyzing requirements',
                targetProgress: 40
            },
            {
                id: 'recommendations',
                label: 'Generating Recommendations',
                description: 'AI agents generating personalized cloud infrastructure recommendations',
                targetProgress: 60
            },
            {
                id: 'report_generation',
                label: 'Report Generation',
                description: 'Creating executive summary, technical roadmap, and cost analysis reports',
                targetProgress: 80
            },
            {
                id: 'completed',
                label: 'Analysis Complete',
                description: 'Assessment workflow completed with recommendations and reports ready',
                targetProgress: 100
            }
        ];

        return workflowSteps.map((step, index) => {
            let status: ProgressStep['status'] = 'pending';
            let progress = 0;

            // Check if this step is completed
            if (completedSteps.includes(step.id) || progressPercentage >= step.targetProgress) {
                status = 'completed';
                progress = 100;
            }
            // Check if this is the current active step
            else if (currentStep === step.id || 
                     (currentStep.includes(step.id)) ||
                     (step.id === 'analysis' && (currentStep.includes('agent') || currentStep.includes('llm'))) ||
                     (step.id === 'initializing' && (currentStep.includes('initializ') || currentStep.includes('workflow'))) ||
                     (step.id === 'report_generation' && currentStep.includes('report'))) {
                status = 'active';
                
                // Calculate progress within the current step based on overall progress
                const prevTargetProgress = index > 0 ? workflowSteps[index - 1].targetProgress : 0;
                const stepRange = step.targetProgress - prevTargetProgress;
                const stepProgress = progressPercentage - prevTargetProgress;
                
                if (stepProgress > 0 && stepRange > 0) {
                    progress = Math.min(Math.max((stepProgress / stepRange) * 100, 0), 100);
                } else {
                    progress = 10; // Show some progress for active step
                }
            }
            // Check for failed state
            else if (currentStep === 'failed' || currentStep.includes('failed') || assessmentProgress.error) {
                if (index <= workflowSteps.findIndex(s => s.id === currentStep.replace('_failed', ''))) {
                    status = 'error';
                } else {
                    status = 'pending';
                }
                progress = 0;
            }
            // Step is pending (future step)
            else {
                status = 'pending';
                progress = 0;
            }

            return {
                label: step.label,
                description: step.description,
                status,
                progress: Math.round(progress),
            };
        });
    }, [currentAssessment, assessmentLoading, reportLoading, scenarioLoading]);

    return steps;
}
