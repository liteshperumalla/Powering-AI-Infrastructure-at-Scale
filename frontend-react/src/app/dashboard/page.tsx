'use client';

import React, { useEffect, useState } from 'react';
import {
    Container,
    Box,
    Card,
    CardContent,
    Button,
    Avatar,
    Typography,
    SpeedDial,
    SpeedDialAction,
    SpeedDialIcon,
    Chip,
} from '@mui/material';
import {
    Assessment,
    GetApp,
    Compare,
    Analytics,
    CloudDownload,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import Navigation from '@/components/Navigation';
import CostComparisonChart from '@/components/charts/CostComparisonChart';
import RecommendationScoreChart from '@/components/charts/RecommendationScoreChart';
import AssessmentResultsChart from '@/components/charts/AssessmentResultsChart';
import RecommendationTable from '@/components/RecommendationTable';
import ReportPreview from '@/components/ReportPreview';
// import D3InteractiveChart from '@/components/charts/D3InteractiveChart';
import AdvancedReportExport from '@/components/AdvancedReportExport';
import ScenarioComparison from '@/components/ScenarioComparison';
import ProgressIndicator, { useProgressSteps } from '@/components/ProgressIndicator';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { fetchAssessments } from '@/store/slices/assessmentSlice';
import { fetchReports } from '@/store/slices/reportSlice';
import { fetchScenarios } from '@/store/slices/scenarioSlice';
import { openModal, closeModal, addNotification } from '@/store/slices/uiSlice';
import RealTimeProgress from '@/components/RealTimeProgress';
import RealTimeDashboard from '@/components/RealTimeDashboard';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useSystemWebSocket } from '@/hooks/useWebSocket';
import { apiClient } from '@/services/api';

interface SystemHealth {
    status: 'healthy' | 'degraded' | 'unhealthy';
}

interface SystemMetrics {
    active_workflows: number;
}

export default function DashboardPage() {
    const router = useRouter();
    const dispatch = useAppDispatch();

    const { assessments, loading: assessmentLoading, workflowId } = useAppSelector(state => state.assessment);
    const { reports, loading: reportLoading } = useAppSelector(state => state.report);
    const { scenarios, comparisonScenarios } = useAppSelector(state => state.scenario);
    const { modals } = useAppSelector(state => state.ui);
    const { user, isAuthenticated } = useAppSelector(state => state.auth);

    const [speedDialOpen, setSpeedDialOpen] = useState(false);
    const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
    const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null); // ✅ fixed

    const {
        isConnected: wsConnected,
        lastMessage,
        sendTypedMessage, // ✅ still unused, but not throwing now
    } = useSystemWebSocket();

    const progressSteps = useProgressSteps();

    useEffect(() => {
        if (isAuthenticated) {
            dispatch(fetchAssessments());
            dispatch(fetchReports());
            dispatch(fetchScenarios());
            loadSystemData();
        }
    }, [dispatch, isAuthenticated]);

    const loadSystemData = async () => {
        try {
            const [health, metrics] = await Promise.all([
                apiClient.checkHealth(),
                apiClient.getSystemMetrics().catch(() => null),
            ]);
            setSystemHealth(health);
            setSystemMetrics(metrics);
        } catch (error) {
            console.error('Failed to load system data:', error);
        }
    };

    useEffect(() => {
        if (lastMessage) {
            try {
                const message = JSON.parse(lastMessage.data);
                switch (message.type) {
                    case 'notification':
                        dispatch(addNotification({
                            type: message.data.type,
                            message: message.data.message,
                        }));
                        break;
                    case 'metrics_update':
                        setSystemMetrics(message.data);
                        break;
                    case 'alert':
                        dispatch(addNotification({
                            type: 'warning',
                            message: `System Alert: ${message.data.message}`,
                        }));
                        break;
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        }
    }, [lastMessage, dispatch]);

    // Sample D3 data for interactive visualization (commented out for now)
    // const d3SampleData = [
    //     { id: '1', x: 10, y: 20, category: 'AWS', value: 1200, label: 'EC2 Instances', metadata: { region: 'us-east-1' } },
    //     { id: '2', x: 15, y: 25, category: 'AWS', value: 800, label: 'RDS Database', metadata: { region: 'us-east-1' } },
    //     { id: '3', x: 20, y: 15, category: 'Azure', value: 1100, label: 'Virtual Machines', metadata: { region: 'eastus' } },
    //     { id: '4', x: 25, y: 30, category: 'Azure', value: 700, label: 'SQL Database', metadata: { region: 'eastus' } },
    //     { id: '5', x: 30, y: 18, category: 'GCP', value: 950, label: 'Compute Engine', metadata: { region: 'us-central1' } },
    //     { id: '6', x: 35, y: 22, category: 'GCP', value: 600, label: 'Cloud SQL', metadata: { region: 'us-central1' } },
    // ];

    const handleSpeedDialAction = (action: string) => {
        setSpeedDialOpen(false);

        switch (action) {
            case 'export':
                if (reports.length > 0) {
                    dispatch(openModal('reportExport'));
                } else {
                    dispatch(addNotification({
                        type: 'warning',
                        message: 'No reports available to export',
                    }));
                }
                break;
            case 'compare':
                if (scenarios.length >= 2) {
                    dispatch(openModal('scenarioComparison'));
                } else {
                    dispatch(addNotification({
                        type: 'warning',
                        message: 'Need at least 2 scenarios to compare',
                    }));
                }
                break;
            case 'analytics':
                router.push('/analytics');
                break;
            case 'download':
                dispatch(addNotification({
                    type: 'info',
                    message: 'Download feature coming soon',
                }));
                break;
        }
    };

    return (
        <ProtectedRoute>
            <Navigation title="Dashboard">
                <Container maxWidth="lg">
                    {/* Welcome Section */}
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h4" gutterBottom>
                            Welcome back{user?.name ? `, ${user.name}` : ''}!
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Here&apos;s an overview of your AI infrastructure assessment progress.
                        </Typography>

                        {/* System Status */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                            <Chip
                                label={wsConnected ? 'Connected' : 'Disconnected'}
                                color={wsConnected ? 'success' : 'error'}
                                size="small"
                            />
                            {systemHealth && (
                                <Chip
                                    label={`System: ${systemHealth.status}`}
                                    color={systemHealth.status === 'healthy' ? 'success' : 'warning'}
                                    size="small"
                                />
                            )}
                            {systemMetrics && (
                                <Typography variant="caption" color="text.secondary">
                                    {systemMetrics.active_workflows} active workflows
                                </Typography>
                            )}
                        </Box>
                    </Box>

                    {/* Quick Actions */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Start Assessment
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Begin your AI infrastructure evaluation
                                </Typography>
                                <Button
                                    variant="contained"
                                    fullWidth
                                    onClick={() => router.push('/assessment')}
                                >
                                    Start Now
                                </Button>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    View Reports
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Access your generated reports
                                </Typography>
                                <Button
                                    variant="outlined"
                                    fullWidth
                                    onClick={() => router.push('/reports')}
                                >
                                    View Reports
                                </Button>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Cloud Services
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    Explore cloud recommendations
                                </Typography>
                                <Button
                                    variant="outlined"
                                    fullWidth
                                    onClick={() => router.push('/cloud-services')}
                                >
                                    Explore
                                </Button>
                            </CardContent>
                        </Card>
                    </Box>

                    {/* Data Visualization Section */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
                        {/* Cost Comparison Chart */}
                        <Box>
                            <CostComparisonChart
                                data={[
                                    {
                                        provider: 'AWS',
                                        compute: 1200,
                                        storage: 300,
                                        networking: 150,
                                        total: 1650,
                                        color: '#FF9900'
                                    },
                                    {
                                        provider: 'Azure',
                                        compute: 1100,
                                        storage: 280,
                                        networking: 120,
                                        total: 1500,
                                        color: '#0078D4'
                                    },
                                    {
                                        provider: 'GCP',
                                        compute: 1050,
                                        storage: 250,
                                        networking: 100,
                                        total: 1400,
                                        color: '#4285F4'
                                    }
                                ]}
                                title="Monthly Cost Comparison"
                                showBreakdown={true}
                            />
                        </Box>

                        {/* Recommendation Score Chart */}
                        <Box>
                            <RecommendationScoreChart
                                data={[
                                    {
                                        service: 'EC2 Instances',
                                        costEfficiency: 85,
                                        performance: 90,
                                        scalability: 95,
                                        security: 88,
                                        compliance: 92,
                                        businessAlignment: 87,
                                        provider: 'AWS',
                                        color: '#FF9900'
                                    },
                                    {
                                        service: 'Azure VMs',
                                        costEfficiency: 82,
                                        performance: 88,
                                        scalability: 90,
                                        security: 90,
                                        compliance: 95,
                                        businessAlignment: 85,
                                        provider: 'Azure',
                                        color: '#0078D4'
                                    },
                                    {
                                        service: 'Compute Engine',
                                        costEfficiency: 88,
                                        performance: 85,
                                        scalability: 92,
                                        security: 87,
                                        compliance: 90,
                                        businessAlignment: 89,
                                        provider: 'GCP',
                                        color: '#4285F4'
                                    }
                                ]}
                                title="Service Performance Scores"
                            />
                        </Box>
                    </Box>

                    {/* Real-Time System Dashboard */}
                    <Box sx={{ mb: 4 }}>
                        <RealTimeDashboard />
                    </Box>

                    {/* Assessment Results Chart */}
                    <Box sx={{ mb: 4 }}>
                        <AssessmentResultsChart
                            data={[
                                {
                                    category: 'Infrastructure Readiness',
                                    currentScore: 75,
                                    targetScore: 90,
                                    improvement: 15,
                                    color: '#8884d8'
                                },
                                {
                                    category: 'Security & Compliance',
                                    currentScore: 82,
                                    targetScore: 95,
                                    improvement: 13,
                                    color: '#82ca9d'
                                },
                                {
                                    category: 'Cost Optimization',
                                    currentScore: 68,
                                    targetScore: 85,
                                    improvement: 17,
                                    color: '#ffc658'
                                },
                                {
                                    category: 'Scalability',
                                    currentScore: 71,
                                    targetScore: 88,
                                    improvement: 17,
                                    color: '#ff7300'
                                },
                                {
                                    category: 'Performance',
                                    currentScore: 79,
                                    targetScore: 92,
                                    improvement: 13,
                                    color: '#00ff88'
                                }
                            ]}
                            title="AI Infrastructure Assessment Results"
                            showComparison={true}
                        />
                    </Box>

                    {/* Recommendation Table */}
                    <Box sx={{ mb: 4 }}>
                        <RecommendationTable
                            recommendations={[
                                {
                                    id: '1',
                                    serviceName: 'Amazon EC2 t3.large',
                                    provider: 'AWS' as const,
                                    serviceType: 'Compute',
                                    costEstimate: 67.32,
                                    confidenceScore: 92,
                                    businessAlignment: 88,
                                    implementationComplexity: 'Low' as const,
                                    pros: ['High availability', 'Auto-scaling capabilities', 'Extensive documentation'],
                                    cons: ['Higher cost than alternatives', 'Complex pricing model'],
                                    status: 'recommended' as const
                                },
                                {
                                    id: '2',
                                    serviceName: 'Azure Standard_D4s_v3',
                                    provider: 'Azure' as const,
                                    serviceType: 'Compute',
                                    costEstimate: 62.05,
                                    confidenceScore: 89,
                                    businessAlignment: 85,
                                    implementationComplexity: 'Medium' as const,
                                    pros: ['Good integration with Microsoft ecosystem', 'Competitive pricing'],
                                    cons: ['Limited availability zones', 'Steeper learning curve'],
                                    status: 'alternative' as const
                                },
                                {
                                    id: '3',
                                    serviceName: 'Google Cloud n1-standard-4',
                                    provider: 'GCP' as const,
                                    serviceType: 'Compute',
                                    costEstimate: 58.90,
                                    confidenceScore: 85,
                                    businessAlignment: 82,
                                    implementationComplexity: 'Medium' as const,
                                    pros: ['Best price-performance ratio', 'Excellent machine learning integration'],
                                    cons: ['Smaller market share', 'Limited enterprise support'],
                                    status: 'alternative' as const
                                }
                            ]}
                            title="Top Service Recommendations"
                        />
                    </Box>

                    {/* Report Preview and Progress */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 4 }}>
                        {/* Report Preview */}
                        <Box>
                            {reports.length > 0 ? (
                                <ReportPreview
                                    report={reports[0]}
                                    onDownload={(reportId) => {
                                        apiClient.downloadReport(reportId)
                                            .then(blob => {
                                                const url = window.URL.createObjectURL(blob);
                                                const a = document.createElement('a');
                                                a.href = url;
                                                a.download = `report-${reportId}.pdf`;
                                                a.click();
                                                window.URL.revokeObjectURL(url);
                                            })
                                            .catch(error => {
                                                dispatch(addNotification({
                                                    type: 'error',
                                                    message: 'Failed to download report',
                                                }));
                                            });
                                    }}
                                    onView={(reportId) => router.push(`/reports/${reportId}`)}
                                />
                            ) : (
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            No Reports Yet
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            Complete an assessment to generate your first report.
                                        </Typography>
                                        <Button
                                            variant="contained"
                                            onClick={() => router.push('/assessment')}
                                        >
                                            Start Assessment
                                        </Button>
                                    </CardContent>
                                </Card>
                            )}
                        </Box>

                        {/* Progress Overview */}
                        <Box>
                            {workflowId && assessments.length > 0 ? (
                                <RealTimeProgress
                                    assessmentId={assessments[0].id}
                                    workflowId={workflowId}
                                    onComplete={(results) => {
                                        dispatch(addNotification({
                                            type: 'success',
                                            message: 'Assessment completed successfully!',
                                        }));
                                        // Refresh data
                                        dispatch(fetchAssessments());
                                        dispatch(fetchReports());
                                    }}
                                    onError={(error) => {
                                        dispatch(addNotification({
                                            type: 'error',
                                            message: `Assessment failed: ${error}`,
                                        }));
                                    }}
                                />
                            ) : (
                                <ProgressIndicator
                                    title="Assessment Progress"
                                    steps={progressSteps}
                                    variant="stepper"
                                    showPercentage={true}
                                />
                            )}

                            <Card sx={{ mt: 2 }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Recent Activity
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                        {assessments.slice(0, 3).map((assessment, index) => (
                                            <Box key={assessment.id} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                                    <Assessment />
                                                </Avatar>
                                                <Box>
                                                    <Typography variant="body2">
                                                        Assessment {assessment.status}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {new Date(assessment.updatedAt).toLocaleDateString()}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        ))}
                                        {reports.slice(0, 2).map((report, index) => (
                                            <Box key={report.id} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Avatar sx={{ width: 32, height: 32, bgcolor: 'success.main' }}>
                                                    <GetApp />
                                                </Avatar>
                                                <Box>
                                                    <Typography variant="body2">Report generated</Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {new Date(report.generated_at).toLocaleDateString()}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        ))}
                                    </Box>
                                </CardContent>
                            </Card>
                        </Box>
                    </Box>

                    {/* Speed Dial for Quick Actions */}
                    <SpeedDial
                        ariaLabel="Quick Actions"
                        sx={{ position: 'fixed', bottom: 16, right: 16 }}
                        icon={<SpeedDialIcon />}
                        open={speedDialOpen}
                        onClose={() => setSpeedDialOpen(false)}
                        onOpen={() => setSpeedDialOpen(true)}
                    >
                        <SpeedDialAction
                            icon={<GetApp />}
                            tooltipTitle="Export Report"
                            onClick={() => handleSpeedDialAction('export')}
                        />
                        <SpeedDialAction
                            icon={<Compare />}
                            tooltipTitle="Compare Scenarios"
                            onClick={() => handleSpeedDialAction('compare')}
                        />
                        <SpeedDialAction
                            icon={<Analytics />}
                            tooltipTitle="Advanced Analytics"
                            onClick={() => handleSpeedDialAction('analytics')}
                        />
                        <SpeedDialAction
                            icon={<CloudDownload />}
                            tooltipTitle="Download Data"
                            onClick={() => handleSpeedDialAction('download')}
                        />
                    </SpeedDial>

                    {/* Advanced Modals */}
                    <AdvancedReportExport
                        open={modals.reportExport}
                        onClose={() => dispatch(closeModal('reportExport'))}
                        reportId={reports[0]?.id || ''}
                    />

                    <ScenarioComparison
                        open={modals.scenarioComparison}
                        onClose={() => dispatch(closeModal('scenarioComparison'))}
                    />
                </Container>
            </Navigation>
        </ProtectedRoute>
    );
}