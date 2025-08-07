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
                                        <Chip
                                            label={step.status}
                                            size="small"
                                            color={getStatusColor(step.status)}
                                            variant="outlined"
                                        />
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
        const progressPercentage = assessmentProgress.progress_percentage || 0;
        
        // Define the correct workflow order matching the backend
        const workflowSteps = [
            {
                id: 'created',
                label: 'Assessment Created',
                description: 'Initial assessment setup and requirements collection',
            },
            {
                id: 'analysis',
                label: 'AI Agent Analysis',
                description: 'Multi-agent analysis including CTO, Cloud Engineer, Infrastructure, Security, and Research agents',
            },
            {
                id: 'recommendations',
                label: 'Recommendations Generation',
                description: 'Generating personalized cloud infrastructure recommendations',
            },
            {
                id: 'reports',
                label: 'Report Generation',
                description: 'Creating executive summary, technical roadmap, and cost analysis reports',
            },
            {
                id: 'visualization',
                label: 'Data Visualization',
                description: 'Generating charts and visual representations of recommendations',
            }
        ];

        return workflowSteps.map((step, index) => {
            let status: ProgressStep['status'] = 'pending';
            let progress = 0;

            if (completedSteps.includes(step.id)) {
                status = 'completed';
                progress = 100;
            } else if (currentStep === step.id) {
                status = 'active';
                // Calculate progress within current step
                if (step.id === 'analysis') {
                    // Agent analysis is 80% of total progress (10 agents)
                    progress = Math.min(progressPercentage * 1.25, 100); // Scale 0-80% to 0-100%
                } else if (step.id === 'recommendations') {
                    progress = progressPercentage > 80 ? Math.min((progressPercentage - 80) * 5, 100) : 0;
                } else if (step.id === 'reports') {
                    progress = progressPercentage > 85 ? Math.min((progressPercentage - 85) * 6.67, 100) : 0;
                } else if (step.id === 'visualization') {
                    progress = progressPercentage > 95 ? Math.min((progressPercentage - 95) * 20, 100) : 0;
                } else {
                    progress = 50; // Default progress for current step
                }
            } else if (currentStep === 'failed' && index === workflowSteps.length - 1) {
                status = 'error';
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
