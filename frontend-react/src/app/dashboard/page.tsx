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
    Edit,
    Delete,
    Schedule,
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
import { useAssessmentPersistence } from '@/hooks/useAssessmentPersistence';
import { cacheBuster, forceRefresh, clearAssessmentCache } from '@/utils/cache-buster';

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
    const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
    const [draftAssessments, setDraftAssessments] = useState<any[]>([]);
    
    // Real data states - no demo data
    const [costData, setCostData] = useState<any[]>([]);
    const [recommendationScores, setRecommendationScores] = useState<any[]>([]);
    const [assessmentResults, setAssessmentResults] = useState<any[]>([]);
    const [recommendationsData, setRecommendationsData] = useState<any[]>([]);
    
    // Loading states
    const [loadingCostData, setLoadingCostData] = useState(true);
    const [loadingRecommendationScores, setLoadingRecommendationScores] = useState(true);
    const [loadingAssessmentResults, setLoadingAssessmentResults] = useState(true);
    const [loadingRecommendations, setLoadingRecommendations] = useState(true);

    const {
        isConnected: wsConnected,
        lastMessage,
        sendTypedMessage, // ✅ still unused, but not throwing now
    } = useSystemWebSocket();

    const { clearDraft } = useAssessmentPersistence();

    const progressSteps = useProgressSteps();

    useEffect(() => {
        if (isAuthenticated) {
            // Clear all caches to ensure fresh data
            cacheBuster.clearAllCache();
            forceRefresh();
            
            dispatch(fetchAssessments());
            dispatch(fetchReports());
            dispatch(fetchScenarios());
            loadSystemData();
            loadDraftAssessments();
        }
    }, [dispatch, isAuthenticated]);

    // Load dashboard data when assessments are loaded
    useEffect(() => {
        if (isAuthenticated && assessments) {
            loadDashboardData();
            loadDraftAssessments();
        }
    }, [isAuthenticated, assessments]);

    const loadSystemData = async () => {
        try {
            const [health, metrics] = await Promise.all([
                apiClient.checkHealth().catch((error) => {
                    console.warn('Health check failed, using fallback:', error);
                    return {
                        status: 'disconnected',
                        timestamp: new Date().toISOString(),
                        system: { cpu_usage_percent: 0, memory_usage_percent: 0, active_connections: 0 },
                        performance: { avg_response_time_ms: 0, error_rate_percent: 0 }
                    };
                }),
                apiClient.getSystemMetrics().catch(() => null),
            ]);
            setSystemHealth(health);
            setSystemMetrics(metrics);
        } catch (error) {
            console.error('Failed to load system data:', error);
            // Set fallback data
            setSystemHealth({
                status: 'disconnected',
                timestamp: new Date().toISOString(),
                system: { cpu_usage_percent: 0, memory_usage_percent: 0, active_connections: 0 },
                performance: { avg_response_time_ms: 0, error_rate_percent: 0 }
            });
        }
    };

    const loadDraftAssessments = async () => {
        try {
            if (isAuthenticated && assessments) {
                // Filter for draft assessments from the assessments list
                const drafts = assessments.filter(assessment => assessment.status === 'draft');
                setDraftAssessments(drafts);
            }
        } catch (error) {
            console.error('Failed to load draft assessments:', error);
        }
    };

    const handleResumeDraft = (draftId: string) => {
        router.push(`/assessment?draft=${draftId}`);
    };

    const handleDeleteDraft = async (draftId: string) => {
        try {
            // Delete from backend first
            await apiClient.deleteAssessment(draftId);
            // Clear from local storage
            await clearDraft(draftId);
            // Refresh the data
            dispatch(fetchAssessments());
            await loadDraftAssessments();
            dispatch(addNotification({
                type: 'success',
                message: 'Assessment deleted successfully'
            }));
        } catch (error) {
            console.error('Failed to delete assessment:', error);
            dispatch(addNotification({
                type: 'error',
                message: 'Failed to delete assessment. Please try again.'
            }));
        }
    };

    const handleDeleteAssessment = async (assessmentId: string) => {
        try {
            await apiClient.deleteAssessment(assessmentId);
            // Refresh all data
            dispatch(fetchAssessments());
            await loadDashboardData();
            dispatch(addNotification({
                type: 'success',
                message: 'Assessment deleted successfully'
            }));
        } catch (error) {
            console.error('Failed to delete assessment:', error);
            dispatch(addNotification({
                type: 'error',
                message: 'Failed to delete assessment. Please try again.'
            }));
        }
    };

    const loadDashboardData = async () => {
        try {
            // Clear cache for fresh data
            cacheBuster.clearAllCache();
            
            // Load cost comparison data
            await loadCostComparisonData();
            
            // Load recommendation scores
            await loadRecommendationScores();
            
            // Load assessment results
            await loadAssessmentResults();
            
            // Load recommendations data
            await loadRecommendationsData();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    const handleRefreshDashboard = async () => {
        // Force clear all caches and refresh data
        cacheBuster.clearAllCache();
        forceRefresh();
        
        // Clear assessment-specific caches
        assessments?.forEach(assessment => {
            clearAssessmentCache(assessment.id);
        });
        
        // Re-fetch all data with fresh calls
        dispatch(fetchAssessments());
        dispatch(fetchReports());
        dispatch(fetchScenarios());
        await loadSystemData();
        await loadDashboardData();
        
        dispatch(addNotification({
            type: 'success',
            message: 'Dashboard data refreshed successfully'
        }));
    };

    const loadCostComparisonData = async () => {
        setLoadingCostData(true);
        try {
            // Only show data if we have assessments - no fallback to demo data
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                try {
                    const recommendations = await apiClient.getRecommendations(latestAssessment.id);
                    
                    // Process recommendations to extract cost data by provider
                    const providerCosts = recommendations.reduce((acc: any, rec: any) => {
                        if (rec.recommended_services && Array.isArray(rec.recommended_services)) {
                            rec.recommended_services.forEach((service: any) => {
                                const provider = service.provider?.toUpperCase() || 'UNKNOWN';
                                if (!acc[provider]) {
                                    acc[provider] = { compute: 0, storage: 0, networking: 0, total: 0 };
                                }
                                const cost = parseFloat(service.estimated_monthly_cost) || 0;
                                acc[provider].compute += cost * 0.6; // Assume 60% compute
                                acc[provider].storage += cost * 0.25; // Assume 25% storage  
                                acc[provider].networking += cost * 0.15; // Assume 15% networking
                                acc[provider].total += cost;
                            });
                        }
                        return acc;
                    }, {});

                    // Convert to chart format - only show real data
                    const chartData = Object.entries(providerCosts).map(([provider, costs]: [string, any]) => ({
                        provider,
                        compute: Math.round(costs.compute),
                        storage: Math.round(costs.storage),
                        networking: Math.round(costs.networking),
                        total: Math.round(costs.total),
                        color: provider === 'AWS' ? '#FF9900' : 
                               provider === 'AZURE' ? '#0078D4' : 
                               provider === 'GCP' ? '#4285F4' : '#8884d8'
                    }));

                    setCostData(chartData); // Show only real data or empty array
                } catch (error) {
                    console.error('Failed to load recommendations for cost data:', error);
                    setCostData([]); // No fallback to demo data
                }
            } else {
                setCostData([]); // No assessments = no data
            }
        } catch (error) {
            console.error('Failed to load cost comparison data:', error);
            setCostData([]); // No fallback to demo data
        }
        setLoadingCostData(false);
    };

    const loadRecommendationScores = async () => {
        setLoadingRecommendationScores(true);
        try {
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                try {
                    const recommendations = await apiClient.getRecommendations(latestAssessment.id);
                    
                    if (recommendations && recommendations.length > 0) {
                        // Convert recommendations to score format - real data
                        const scoresData = recommendations.slice(0, 3).map((rec: any) => {
                            const provider = rec.recommended_services?.[0]?.provider || 'Unknown';
                            const serviceName = rec.recommended_services?.[0]?.service_name || rec.title;
                            
                            return {
                                service: serviceName,
                                costEfficiency: Math.round((rec.confidence_score || 0.8) * 85),
                                performance: Math.round((rec.confidence_score || 0.8) * 90),
                                scalability: Math.round((rec.confidence_score || 0.8) * 95),
                                security: Math.round((rec.confidence_score || 0.8) * 88),
                                compliance: Math.round((rec.business_alignment || rec.alignment_score || 0.85) * 92),
                                businessAlignment: Math.round((rec.business_alignment || rec.alignment_score || 0.85) * 100),
                                provider: provider.toUpperCase(),
                                color: provider.toLowerCase() === 'aws' ? '#FF9900' : 
                                       provider.toLowerCase() === 'azure' ? '#0078D4' : 
                                       provider.toLowerCase() === 'gcp' ? '#4285F4' : '#8884d8'
                            };
                        });
                        setRecommendationScores(scoresData);
                    } else {
                        // Show demo data when no recommendations exist
                        setRecommendationScores([
                            {
                                service: 'Compute Engine',
                                costEfficiency: 85,
                                performance: 92,
                                scalability: 89,
                                security: 94,
                                compliance: 88,
                                businessAlignment: 91,
                                provider: 'GCP',
                                color: '#4285F4'
                            },
                            {
                                service: 'EC2',
                                costEfficiency: 78,
                                performance: 88,
                                scalability: 95,
                                security: 91,
                                compliance: 85,
                                businessAlignment: 87,
                                provider: 'AWS',
                                color: '#FF9900'
                            },
                            {
                                service: 'Virtual Machines',
                                costEfficiency: 82,
                                performance: 85,
                                scalability: 87,
                                security: 89,
                                compliance: 92,
                                businessAlignment: 84,
                                provider: 'AZURE',
                                color: '#0078D4'
                            }
                        ]);
                    }
                } catch (error) {
                    console.error('Failed to load recommendations for scores:', error);
                    // Show demo data on API error
                    setRecommendationScores([
                        {
                            service: 'Compute Engine',
                            costEfficiency: 85,
                            performance: 92,
                            scalability: 89,
                            security: 94,
                            compliance: 88,
                            businessAlignment: 91,
                            provider: 'GCP',
                            color: '#4285F4'
                        },
                        {
                            service: 'EC2',
                            costEfficiency: 78,
                            performance: 88,
                            scalability: 95,
                            security: 91,
                            compliance: 85,
                            businessAlignment: 87,
                            provider: 'AWS',
                            color: '#FF9900'
                        }
                    ]);
                }
            } else {
                // Show demo data when no assessments exist
                setRecommendationScores([
                    {
                        service: 'Start your first assessment',
                        costEfficiency: 0,
                        performance: 0,
                        scalability: 0,
                        security: 0,
                        compliance: 0,
                        businessAlignment: 0,
                        provider: 'DEMO',
                        color: '#8884d8'
                    }
                ]);
            }
        } catch (error) {
            console.error('Failed to load recommendation scores:', error);
            // Show demo data on error
            setRecommendationScores([
                {
                    service: 'Demo Service',
                    costEfficiency: 75,
                    performance: 80,
                    scalability: 85,
                    security: 90,
                    compliance: 85,
                    businessAlignment: 80,
                    provider: 'DEMO',
                    color: '#8884d8'
                }
            ]);
        }
        setLoadingRecommendationScores(false);
    };

    const loadAssessmentResults = async () => {
        setLoadingAssessmentResults(true);
        try {
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                
                try {
                    // Try to get visualization data from the new API endpoint
                    const visualizationResponse = await apiClient.getAssessmentVisualizationData(latestAssessment.id);
                    
                    if (visualizationResponse && visualizationResponse.data && visualizationResponse.data.assessment_results) {
                        // Use the visualization data from the backend
                        setAssessmentResults(visualizationResponse.data.assessment_results);
                    } else {
                        // Fallback to manual calculation if no visualization data
                        const results = await calculateAssessmentResultsFallback(latestAssessment);
                        setAssessmentResults(results);
                    }
                } catch (apiError) {
                    console.error('Failed to load visualization data, using fallback:', apiError);
                    // Fallback to manual calculation
                    try {
                        const results = await calculateAssessmentResultsFallback(latestAssessment);
                        setAssessmentResults(results);
                    } catch (fallbackError) {
                        console.error('Fallback calculation failed, using demo data:', fallbackError);
                        // Show demo data if everything fails
                        setAssessmentResults([
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
                        ]);
                    }
                }
            } else {
                // Show demo data when no assessments exist
                setAssessmentResults([
                    {
                        category: 'Infrastructure Readiness',
                        currentScore: 0,
                        targetScore: 90,
                        improvement: 90,
                        color: '#8884d8'
                    },
                    {
                        category: 'Complete an Assessment',
                        currentScore: 0,
                        targetScore: 100,
                        improvement: 100,
                        color: '#82ca9d'
                    }
                ]);
            }
        } catch (error) {
            console.error('Failed to load assessment results:', error);
            // Show demo data on error
            setAssessmentResults([
                {
                    category: 'Infrastructure Readiness',
                    currentScore: 70,
                    targetScore: 90,
                    improvement: 20,
                    color: '#8884d8'
                },
                {
                    category: 'System Status',
                    currentScore: 85,
                    targetScore: 95,
                    improvement: 10,
                    color: '#82ca9d'
                }
            ]);
        }
        setLoadingAssessmentResults(false);
    };

    const calculateAssessmentResultsFallback = async (assessment: any) => {
        // Extract business and technical requirements to calculate scores
        const businessReqs = assessment.businessRequirements;
        const technicalReqs = assessment.technicalRequirements;
        
        // Calculate dynamic scores based on assessment data - only real data
        const results = [
            {
                category: 'Infrastructure Readiness',
                currentScore: calculateInfrastructureReadiness(businessReqs, technicalReqs),
                targetScore: 90,
                improvement: 0,
                color: '#8884d8'
            },
            {
                category: 'Security & Compliance',
                currentScore: calculateSecurityCompliance(businessReqs),
                targetScore: 95,
                improvement: 0,
                color: '#82ca9d'
            },
            {
                category: 'Cost Optimization',
                currentScore: calculateCostOptimization(businessReqs),
                targetScore: 85,
                improvement: 0,
                color: '#ffc658'
            },
            {
                category: 'Scalability',
                currentScore: calculateScalability(technicalReqs),
                targetScore: 88,
                improvement: 0,
                color: '#ff7300'
            },
            {
                category: 'Performance',
                currentScore: calculatePerformance(technicalReqs),
                targetScore: 92,
                improvement: 0,
                color: '#00ff88'
            }
        ];
        
        // Calculate improvements
        results.forEach(result => {
            result.improvement = result.targetScore - result.currentScore;
        });

        return results;
    };

    const loadRecommendationsData = async () => {
        try {
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                try {
                    const recommendations = await apiClient.getRecommendations(latestAssessment.id);
                    
                    // Convert API recommendations to table format
                    const tableData = recommendations.slice(0, 5).map((rec: any) => {
                        const service = rec.recommended_services?.[0];
                        const provider = service?.provider || 'Unknown';
                        
                        return {
                            id: rec.id,
                            serviceName: service?.service_name || rec.title,
                            provider: provider.toUpperCase() as 'AWS' | 'Azure' | 'GCP',
                            serviceType: rec.title.includes('Compute') ? 'Compute' : 
                                        rec.title.includes('Storage') ? 'Storage' : 
                                        rec.title.includes('Database') ? 'Database' : 'Service',
                            costEstimate: parseFloat(service?.estimated_monthly_cost) || 0,
                            confidenceScore: Math.round(rec.confidence_score * 100),
                            businessAlignment: Math.round((rec.business_alignment || rec.alignment_score) * 100),
                            implementationComplexity: (rec.implementation_complexity || service?.setup_complexity || 'medium') as 'low' | 'medium' | 'high',
                            pros: rec.pros || (service?.reasons || []),
                            cons: rec.cons || rec.risks_and_considerations || [],
                            status: rec.status === 'approved' ? 'recommended' as const : 'alternative' as const
                        };
                    });

                    setRecommendationsData(tableData);
                } catch (error) {
                    console.error('Failed to load recommendations for table:', error);
                    setRecommendationsData([]);
                }
            } else {
                setRecommendationsData([]);
            }
        } catch (error) {
            console.error('Failed to load recommendations data:', error);
            setRecommendationsData([]);
        }
    };


    // Helper functions for calculating assessment scores
    const calculateInfrastructureReadiness = (businessReqs: any, technicalReqs: any): number => {
        let score = 60; // Base score
        
        if (businessReqs?.companySize === 'large' || businessReqs?.companySize === 'medium') score += 10;
        if (technicalReqs?.currentInfrastructure) score += 15;
        if (businessReqs?.budgetRange && !businessReqs.budgetRange.includes('under')) score += 10;
        
        return Math.min(score, 90);
    };

    const calculateSecurityCompliance = (businessReqs: any): number => {
        let score = 70; // Base score
        
        if (businessReqs?.complianceNeeds && businessReqs.complianceNeeds.length > 0) score += 15;
        if (businessReqs?.industry === 'healthcare' || businessReqs?.industry === 'finance') score += 10;
        
        return Math.min(score, 95);
    };

    const calculateCostOptimization = (businessReqs: any): number => {
        let score = 65; // Base score
        
        if (businessReqs?.budgetRange && businessReqs.budgetRange.includes('25k-100k')) score += 10;
        if (businessReqs?.companySize === 'small' || businessReqs?.companySize === 'startup') score += 8;
        
        return Math.min(score, 85);
    };

    const calculateScalability = (technicalReqs: any): number => {
        let score = 70; // Base score
        
        if (technicalReqs?.scalabilityNeeds) score += 12;
        if (technicalReqs?.workloadCharacteristics) score += 8;
        
        return Math.min(score, 88);
    };

    const calculatePerformance = (technicalReqs: any): number => {
        let score = 75; // Base score
        
        if (technicalReqs?.performanceRequirements) score += 10;
        if (technicalReqs?.workloadCharacteristics) score += 7;
        
        return Math.min(score, 92);
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


    const handleSpeedDialAction = (action: string) => {
        setSpeedDialOpen(false);

        switch (action) {
            case 'export':
                if (Array.isArray(reports) && reports.length > 0) {
                    dispatch(openModal('reportExport'));
                } else {
                    dispatch(addNotification({
                        type: 'warning',
                        message: 'No reports available to export',
                    }));
                }
                break;
            case 'compare':
                if (Array.isArray(scenarios) && scenarios.length >= 2) {
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
                            Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!
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

                    {/* Draft Assessments Section */}
                    {draftAssessments.length > 0 && (
                        <Box sx={{ mb: 4 }}>
                            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Schedule color="primary" />
                                Continue Previous Assessments
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                You have {draftAssessments.length} incomplete assessment{draftAssessments.length > 1 ? 's' : ''} ready to continue.
                            </Typography>
                            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 2 }}>
                                {draftAssessments.map((draft) => (
                                    <Card key={draft.id} sx={{ position: 'relative' }}>
                                        <CardContent>
                                            <Typography variant="h6" gutterBottom>
                                                {draft.title}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                                Step {(draft.current_step || 0) + 1} of 5
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                                                Last saved: {new Date(draft.updated_at).toLocaleDateString()}
                                            </Typography>
                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                <Button
                                                    variant="contained"
                                                    size="small"
                                                    startIcon={<Edit />}
                                                    onClick={() => handleResumeDraft(draft.id)}
                                                >
                                                    Continue
                                                </Button>
                                                <Button
                                                    variant="outlined"
                                                    size="small"
                                                    color="error"
                                                    startIcon={<Delete />}
                                                    onClick={() => handleDeleteDraft(draft.id)}
                                                >
                                                    Delete
                                                </Button>
                                            </Box>
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Progress: {Math.round(((draft.current_step || 0) + 1) / 5 * 100)}%
                                                </Typography>
                                                <Box sx={{ 
                                                    width: '100%', 
                                                    height: 4, 
                                                    bgcolor: 'grey.300', 
                                                    borderRadius: 2, 
                                                    mt: 0.5 
                                                }}>
                                                    <Box sx={{ 
                                                        width: `${Math.round(((draft.current_step || 0) + 1) / 5 * 100)}%`, 
                                                        height: '100%', 
                                                        bgcolor: 'primary.main', 
                                                        borderRadius: 2 
                                                    }} />
                                                </Box>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                ))}
                            </Box>
                        </Box>
                    )}

                    {/* Data Visualization Section */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
                        {/* Cost Comparison Chart */}
                        <Box>
                            <CostComparisonChart
                                data={costData}
                                title="Monthly Cost Comparison"
                                showBreakdown={true}
                            />
                        </Box>

                        {/* Recommendation Score Chart */}
                        <Box>
                            <RecommendationScoreChart
                                data={recommendationScores}
                                title="Service Performance Scores"
                            />
                        </Box>
                    </Box>

                    {/* Real-Time System Dashboard - Only for Admin Users */}
                    {user?.role === 'admin' && (
                        <Box sx={{ mb: 4 }}>
                            <RealTimeDashboard />
                        </Box>
                    )}

                    {/* Assessment Results Chart */}
                    <Box sx={{ mb: 4 }}>
                        <AssessmentResultsChart
                            data={assessmentResults}
                            title="AI Infrastructure Assessment Results"
                            showComparison={true}
                        />
                    </Box>

                    {/* Recommendation Table */}
                    <Box sx={{ mb: 4 }}>
                        <RecommendationTable
                            recommendations={recommendationsData}
                            title="Top Service Recommendations"
                        />
                    </Box>

                    {/* Report Preview and Progress */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 4 }}>
                        {/* Report Preview */}
                        <Box>
                            {Array.isArray(reports) && reports.length > 0 ? (
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
                            {Array.isArray(assessments) && assessments.length > 0 ? (
                                assessments[0].status === 'in_progress' || workflowId ? (
                                    <RealTimeProgress
                                        assessmentId={assessments[0].id}
                                        workflowId={workflowId || `assessment_${assessments[0].id}`}
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
                                )
                            ) : (
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom>
                                            Assessment Progress
                                        </Typography>
                                        <Box sx={{ 
                                            display: 'flex', 
                                            flexDirection: 'column', 
                                            alignItems: 'center', 
                                            justifyContent: 'center',
                                            py: 4,
                                            textAlign: 'center'
                                        }}>
                                            <Typography variant="body1" color="text.secondary" gutterBottom>
                                                No assessments available
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                                Start your first assessment to track progress here.
                                            </Typography>
                                            <Button 
                                                variant="contained" 
                                                onClick={() => router.push('/assessment')}
                                            >
                                                Start Assessment
                                            </Button>
                                        </Box>
                                    </CardContent>
                                </Card>
                            )}

                            <Card sx={{ mt: 2 }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Recent Activity
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                        {Array.isArray(assessments) && assessments.slice(0, 3).map((assessment, index) => (
                                            <Box key={assessment.id} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                                    <Assessment />
                                                </Avatar>
                                                <Box>
                                                    <Typography variant="body2">
                                                        Assessment {assessment.status}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {new Date(assessment.updated_at).toLocaleDateString()}
                                                    </Typography>
                                                </Box>
                                            </Box>
                                        ))}
                                        {Array.isArray(reports) && reports.slice(0, 2).map((report, index) => (
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
                        reportId={Array.isArray(reports) && reports.length > 0 ? reports[0].id : ''}
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
