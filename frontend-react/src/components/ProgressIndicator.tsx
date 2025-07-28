'use client';

import React from 'react';
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

    const getStatusColor = (status: ProgressStep['status']) => {
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
                            color={getStatusColor(step.status) as any}
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
                                            color={getStatusColor(step.status) as any}
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

    const currentAssessment = assessments[0]; // Get the most recent assessment

    const steps: ProgressStep[] = [
        {
            label: 'Business Requirements',
            description: 'Collect business goals and constraints',
            status: currentAssessment?.businessRequirements ? 'completed' : 'pending',
        },
        {
            label: 'Technical Assessment',
            description: 'Analyze current infrastructure and requirements',
            status: currentAssessment?.technicalRequirements ? 'completed' :
                assessmentLoading ? 'active' : 'pending',
        },
        {
            label: 'Agent Analysis',
            description: 'AI agents analyze requirements and generate recommendations',
            status: currentAssessment?.status === 'completed' ? 'completed' :
                currentAssessment?.status === 'in_progress' ? 'active' : 'pending',
            progress: currentAssessment?.progress || 0,
        },
        {
            label: 'Scenario Modeling',
            description: 'Generate and compare infrastructure scenarios',
            status: scenarios.length > 0 ? 'completed' :
                scenarioLoading ? 'active' : 'pending',
        },
        {
            label: 'Report Generation',
            description: 'Create comprehensive strategy reports',
            status: reports.length > 0 ? 'completed' :
                reportLoading ? 'active' : 'pending',
        },
    ];

    return steps;
}