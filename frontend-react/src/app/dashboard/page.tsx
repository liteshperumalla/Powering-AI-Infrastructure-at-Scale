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

    const { assessments, loading: assessmentLoading, workflowId } = useAppSelector(state => {
        console.log('🔍 Redux Selector - assessments:', state.assessment.assessments?.length || 0, 'items');
        return state.assessment;
    });
    const { reports, loading: reportLoading } = useAppSelector(state => state.report);
    const { scenarios, comparisonScenarios } = useAppSelector(state => state.scenario);
    const { modals } = useAppSelector(state => state.ui);
    const { user, isAuthenticated } = useAppSelector(state => state.auth);

    // Debug Redux state updates
    useEffect(() => {
        console.log('🔄 Redux State Update:', {
            assessments: assessments ? `${assessments.length} assessments` : 'null',
            assessmentLoading,
            reports: reports ? `${reports.length} reports` : 'null',
            reportLoading,
            scenarios: scenarios ? `${scenarios.length} scenarios` : 'null'
        });
        console.log('🔍 Raw assessments value:', assessments);
        console.log('🔍 Assessments type:', typeof assessments);
        console.log('🔍 Is assessments array?', Array.isArray(assessments));
        
        if (assessments && assessments.length > 0) {
            console.log('📊 Assessment details:', assessments.map(a => ({
                id: a.id,
                title: a.title,
                status: a.status,
                progress: a.progress_percentage
            })));
        }
    }, [assessments, reports, scenarios, assessmentLoading, reportLoading]);

    const [speedDialOpen, setSpeedDialOpen] = useState(false);
    const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
    const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
    const [draftAssessments, setDraftAssessments] = useState<any[]>([]);
    const [mounted, setMounted] = useState(false);
    
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

    // Set mounted state
    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        // Check if we have a token in localStorage even if Redux state isn't updated yet
        const hasStoredToken = typeof window !== 'undefined' ? !!localStorage.getItem('auth_token') : false;
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        
        console.log('🔍 Dashboard useEffect Debug:', {
            isAuthenticated,
            hasStoredToken,
            tokenExists: !!token,
            tokenPreview: token ? `${token.substring(0, 20)}...` : 'none',
            mounted,
            user: !!user
        });
        
        if (isAuthenticated || hasStoredToken) {
            console.log('✅ Loading dashboard data...');
            // Clear all caches to ensure fresh data
            cacheBuster.clearAllCache();
            forceRefresh();
            
            // Load all dashboard data
            console.log('📊 Dispatching fetchAssessments...');
            const fetchResult = dispatch(fetchAssessments());
            console.log('🔍 Dispatch result:', fetchResult);
            console.log('🔍 Dispatch result type:', typeof fetchResult);
            
            // Track the promise resolution
            fetchResult.then((result) => {
                console.log('✅ fetchAssessments promise resolved:', result);
            }).catch((error) => {
                console.error('❌ fetchAssessments promise rejected:', error);
            });
            console.log('📋 Dispatching fetchReports...');
            dispatch(fetchReports());
            console.log('🔄 Dispatching fetchScenarios...');
            dispatch(fetchScenarios());
            loadSystemData();
            loadDraftAssessments();
        } else {
            console.log('❌ No authentication - skipping data load');
        }
    }, [dispatch, isAuthenticated, mounted]);

    // Listen for dashboard updates from WebSocket
    useEffect(() => {
        if (lastMessage && isAuthenticated) {
            const handleMessage = async () => {
                try {
                    const message = JSON.parse(lastMessage.data);
                    
                    // Handle different types of dashboard updates
                    switch (message.type) {
                        case 'new_assessment':
                            // Clear old data and refresh when new assessment is created
                            cacheBuster.clearAllCache();
                            clearAssessmentCache(message.assessment_id);
                            dispatch(fetchAssessments());
                            await loadDashboardData(true);
                            dispatch(addNotification({
                                type: 'info',
                                message: message.message || 'New assessment created'
                            }));
                            break;
                            
                        case 'assessment_completed':
                            // Refresh all data when assessment completes
                            cacheBuster.clearAllCache();
                            clearAssessmentCache(message.assessment_id);
                            dispatch(fetchAssessments());
                            dispatch(fetchReports());
                            // Force refresh dashboard data with new visualizations
                            await loadDashboardData(true);
                            // Refresh reports after assessment completion
                            dispatch(fetchReports());
                            // Trigger advanced analytics refresh if user navigates there
                            if (typeof window !== 'undefined') {
                                window.dispatchEvent(new CustomEvent('assessment-completed', {
                                    detail: { assessmentId: message.assessment_id }
                                }));
                            }
                            dispatch(addNotification({
                                type: 'success',
                                message: message.message || 'Assessment completed successfully!'
                            }));
                            break;
                        
                    case 'assessment_progress':
                        // Update progress in real-time
                        dispatch(fetchAssessments());
                        break;
                        
                    case 'dashboard_refresh':
                        // Full dashboard refresh requested
                        handleRefreshDashboard();
                        break;
                        
                    default:
                        // Handle other notification types
                        if (message.type === 'notification') {
                            dispatch(addNotification({
                                type: message.data.type,
                                message: message.data.message,
                            }));
                        }
                }
            } catch (error) {
                console.error('Error parsing dashboard WebSocket message:', error);
            }
            };
            
            handleMessage();
        }
    }, [lastMessage, isAuthenticated, dispatch]);

    // Load dashboard data when assessments are loaded
    useEffect(() => {
        console.log('🎯 Dashboard data loading effect:', {
            isAuthenticated,
            hasAssessments: !!assessments,
            assessmentCount: assessments?.length || 0,
            assessmentsIsArray: Array.isArray(assessments),
            assessmentLoading
        });
        
        // Check if we have valid assessments data to work with
        if (isAuthenticated && Array.isArray(assessments) && assessments.length > 0) {
            console.log('📈 Loading dashboard visualizations with assessments:', assessments.map(a => ({id: a.id, status: a.status})));
            loadDashboardData();
            loadDraftAssessments();
        } else if (isAuthenticated && Array.isArray(assessments) && assessments.length === 0 && !assessmentLoading) {
            console.log('📭 No assessments available - clearing visualization data');
            // Clear visualization data when no assessments
            setCostData([]);
            setRecommendationScores([]);
            setAssessmentResults([]);
            setRecommendationsData([]);
        } else {
            console.log('⏳ Waiting for authentication and assessments...', {
                isAuthenticated,
                assessments: !!assessments,
                assessmentLoading
            });
        }
    }, [isAuthenticated, assessments, assessmentLoading]);

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
            if (isAuthenticated && Array.isArray(assessments)) {
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

    const loadDashboardData = async (forceRefresh = false) => {
        try {
            console.log('📊 loadDashboardData called:', { 
                forceRefresh, 
                assessmentCount: assessments?.length,
                hasValidAssessments: Array.isArray(assessments) && assessments.length > 0,
                firstAssessmentId: assessments?.[0]?.id
            });
            
            if (forceRefresh) {
                // Clear cache for fresh data on forced refresh
                cacheBuster.clearAllCache();
                
                // Clear all visualization state
                setCostData([]);
                setRecommendationScores([]);
                setAssessmentResults([]);
                setRecommendationsData([]);
            }
            
            // Verify we have assessments before proceeding
            if (!Array.isArray(assessments) || assessments.length === 0) {
                console.log('🚫 No assessments available for dashboard data loading');
                return;
            }
            
            // Load cost comparison data
            console.log('💰 Loading cost comparison data...');
            await loadCostComparisonData();
            
            // Load recommendation scores
            console.log('⭐ Loading recommendation scores...');
            await loadRecommendationScores();
            
            // Load assessment results
            console.log('📈 Loading assessment results...');
            await loadAssessmentResults();
            
            // Load recommendations data
            console.log('💡 Loading recommendations data...');
            await loadRecommendationsData();
            
            console.log('✅ Dashboard data loading complete');
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    const handleRefreshDashboard = async () => {
        console.log('🔄 Manual refresh triggered');
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        console.log('🔑 Token status:', { 
            hasToken: !!token, 
            isAuthenticated,
            tokenPreview: token ? `${token.substring(0, 20)}...` : 'none'
        });
        
        // Force clear all caches and refresh data
        cacheBuster.clearAllCache();
        forceRefresh();
        
        // Clear assessment-specific caches
        if (Array.isArray(assessments)) {
            assessments.forEach(assessment => {
                clearAssessmentCache(assessment.id);
            });
        }
        
        // Re-fetch all data with fresh calls
        console.log('📊 Manual refresh: Dispatching fetchAssessments...');
        dispatch(fetchAssessments());
        console.log('📋 Manual refresh: Dispatching fetchReports...');
        dispatch(fetchReports());
        console.log('🔄 Manual refresh: Dispatching fetchScenarios...');
        dispatch(fetchScenarios());
        await loadSystemData();
        await loadDashboardData(true);
        
        dispatch(addNotification({
            type: 'success',
            message: 'Dashboard data refreshed successfully'
        }));
    };

    const handleRegenerateRecommendations = async () => {
        if (!Array.isArray(assessments) || assessments.length === 0) {
            dispatch(addNotification({
                type: 'warning',
                message: 'No assessments available to regenerate recommendations for'
            }));
            return;
        }

        try {
            dispatch(addNotification({
                type: 'info',
                message: 'Starting recommendation regeneration for all assessments...'
            }));

            // Regenerate recommendations for all assessments
            const regenerationPromises = assessments.map(async (assessment) => {
                try {
                    console.log(`🔄 Regenerating recommendations for assessment: ${assessment.id}`);
                    const response = await apiClient.generateRecommendations(assessment.id);
                    console.log(`✅ Recommendation generation started for ${assessment.id}:`, response);
                    return { success: true, assessmentId: assessment.id, response };
                } catch (error) {
                    console.error(`❌ Failed to regenerate recommendations for ${assessment.id}:`, error);
                    return { success: false, assessmentId: assessment.id, error };
                }
            });

            const results = await Promise.all(regenerationPromises);
            const successful = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;

            if (successful > 0) {
                dispatch(addNotification({
                    type: 'success',
                    message: `Recommendation regeneration started for ${successful} assessment${successful > 1 ? 's' : ''}. This may take 3-5 minutes.`
                }));

                // Wait a bit then refresh the dashboard
                setTimeout(() => {
                    handleRefreshDashboard();
                }, 2000);
            }

            if (failed > 0) {
                dispatch(addNotification({
                    type: 'warning',
                    message: `Failed to start regeneration for ${failed} assessment${failed > 1 ? 's' : ''}`
                }));
            }

        } catch (error) {
            console.error('❌ Failed to regenerate recommendations:', error);
            dispatch(addNotification({
                type: 'error',
                message: 'Failed to start recommendation regeneration. Please try again.'
            }));
        }
    };

    // Clear old assessment data when creating new assessment
    const handleNewAssessment = () => {
        // Clear all cached data
        cacheBuster.clearAllCache();
        
        // Clear visualization data
        setCostData([]);
        setRecommendationScores([]);
        setAssessmentResults([]);
        setRecommendationsData([]);
        
        // Navigate to assessment page
        router.push('/assessment');
    };

    const loadCostComparisonData = async () => {
        setLoadingCostData(true);
        try {
            // Only show data if we have assessments - no fallback to demo data
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                try {
                    console.log('💰 Requesting recommendations for assessment:', latestAssessment.id);
                    const recommendations = await apiClient.getRecommendations(latestAssessment.id);
                    console.log('💰 Recommendations response:', recommendations);
                    
                    // Check if recommendations are empty despite being marked as generated
                    if (!recommendations || recommendations.length === 0) {
                        console.log('⚠️ No recommendations found despite recommendations_generated = true');
                        setCostData([]);
                        return;
                    }
                    
                    // Process recommendations to extract cost data by provider
                    const providerCosts = recommendations.reduce((acc: any, rec: any) => {
                        // Use the new data structure with cost_estimates and recommendation_data
                        if (rec.cost_estimates && rec.recommendation_data) {
                            const provider = rec.recommendation_data.provider?.toUpperCase() || 'MULTI_CLOUD';
                            if (!acc[provider]) {
                                acc[provider] = { compute: 0, storage: 0, networking: 0, total: 0 };
                            }
                            
                            // Use cost breakdown if available, otherwise distribute total cost
                            if (rec.cost_estimates.cost_breakdown) {
                                acc[provider].compute += rec.cost_estimates.cost_breakdown.compute || 0;
                                acc[provider].storage += rec.cost_estimates.cost_breakdown.storage || 0;
                                acc[provider].networking += rec.cost_estimates.cost_breakdown.networking || 0;
                            } else {
                                // Fallback: distribute monthly cost proportionally
                                const monthlyCost = rec.cost_estimates.monthly_cost || parseFloat(rec.total_estimated_monthly_cost) || 0;
                                acc[provider].compute += monthlyCost * 0.6;
                                acc[provider].storage += monthlyCost * 0.25;
                                acc[provider].networking += monthlyCost * 0.15;
                            }
                            
                            acc[provider].total += rec.cost_estimates.monthly_cost || parseFloat(rec.total_estimated_monthly_cost) || 0;
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
                    console.log('💰 Set cost data:', chartData);
                } catch (error) {
                    console.error('💰 Failed to load recommendations for cost data:', error);
                    console.error('💰 Error details:', error);
                    setCostData([]); // No fallback to demo data
                    
                    // Show notification about missing recommendations
                    dispatch(addNotification({
                        type: 'warning',
                        message: 'Recommendations data not available for cost visualization. Try regenerating recommendations.'
                    }));
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
                        // Convert recommendations to score format - use new data structure
                        const scoresData = recommendations.slice(0, 3).map((rec: any) => {
                            const provider = rec.recommendation_data?.provider || 'multi_cloud';
                            const serviceName = rec.title;
                            
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
                                       provider.toLowerCase() === 'gcp' ? '#4285F4' : 
                                       provider.toLowerCase() === 'multi_cloud' ? '#9C27B0' : '#8884d8'
                            };
                        });
                        setRecommendationScores(scoresData);
                        console.log('⭐ Set recommendation scores:', scoresData);
                    } else {
                        // No recommendations - show empty data
                        setRecommendationScores([]);
                    }
                } catch (error) {
                    console.error('Failed to load recommendations for scores:', error);
                    // No demo data - show empty array on API error
                    setRecommendationScores([]);
                }
            } else {
                // No assessments - show empty data
                setRecommendationScores([]);
            }
        } catch (error) {
            console.error('Failed to load recommendation scores:', error);
            // No demo data - show empty array on error
            setRecommendationScores([]);
        }
        setLoadingRecommendationScores(false);
    };

    const loadAssessmentResults = async () => {
        setLoadingAssessmentResults(true);
        try {
            if (Array.isArray(assessments) && assessments.length > 0) {
                const latestAssessment = assessments[0];
                
                try {
                    // Force clear assessment-specific cache to ensure fresh data
                    clearAssessmentCache(latestAssessment.id);
                    
                    console.log('📊 Loading assessment results with fresh data for:', {
                        assessmentId: latestAssessment.id,
                        title: latestAssessment.title,
                        status: latestAssessment.status,
                        progress: latestAssessment.progress?.progress_percentage || 0
                    });
                    
                    // Always use fallback calculation for now since the visualization API endpoint needs more work
                    const results = await calculateAssessmentResultsFallback(latestAssessment);
                    setAssessmentResults(results);
                    console.log('📈 Set fresh assessment results:', results);
                    
                    // Optionally try to enhance with backend visualization data
                    try {
                        const visualizationResponse = await apiClient.getAssessmentVisualizationData(latestAssessment.id);
                        
                        if (visualizationResponse && 
                            visualizationResponse.data && 
                            visualizationResponse.data.assessment_results && 
                            visualizationResponse.data.assessment_results.length > 0) {
                            // Use the backend visualization data if available and valid
                            setAssessmentResults(visualizationResponse.data.assessment_results);
                        }
                        // Otherwise keep using the fallback calculation results
                    } catch (vizError) {
                        console.warn('Visualization API not available, using calculated results:', vizError);
                        // Keep using fallback results
                    }
                } catch (fallbackError) {
                    console.error('Failed to calculate assessment results:', fallbackError);
                    // Show empty results only if both methods fail
                    setAssessmentResults([]);
                }
            } else {
                // No assessments - show empty results
                setAssessmentResults([]);
            }
        } catch (error) {
            console.error('Failed to load assessment results:', error);
            // Only show real data - no demo data fallback
            setAssessmentResults([]);
        }
        setLoadingAssessmentResults(false);
    };

    const calculateAssessmentResultsFallback = async (assessment: any) => {
        // Extract business and technical requirements to calculate scores
        const businessReqs = assessment.business_requirements || assessment.businessRequirements;
        const technicalReqs = assessment.technical_requirements || assessment.technicalRequirements;
        
        // Get assessment progress to enhance scores
        const assessmentProgress = assessment.progress?.progress_percentage || 0;
        const isCompleted = assessment.status === 'completed';
        const hasRecommendations = assessment.recommendations_generated;
        const hasReports = assessment.reports_generated;
        
        // Calculate dynamic scores based on assessment data and progress
        let baseScoreMultiplier = 0.7; // Start at 70%
        if (assessmentProgress > 50) baseScoreMultiplier += 0.1;
        if (isCompleted) baseScoreMultiplier += 0.15;
        if (hasRecommendations) baseScoreMultiplier += 0.1;
        if (hasReports) baseScoreMultiplier += 0.05;
        
        const results = [
            {
                category: 'Strategic Planning',
                currentScore: Math.min(calculateInfrastructureReadiness(businessReqs, technicalReqs) * baseScoreMultiplier, 95),
                targetScore: 90,
                improvement: 0,
                color: '#1f77b4'
            },
            {
                category: 'Technical Architecture',
                currentScore: Math.min(calculateScalability(technicalReqs) * baseScoreMultiplier, 92),
                targetScore: 88,
                improvement: 0,
                color: '#ff7f0e'
            },
            {
                category: 'Security & Compliance',
                currentScore: Math.min(calculateSecurityCompliance(businessReqs) * baseScoreMultiplier, 94),
                targetScore: 95,
                improvement: 0,
                color: '#2ca02c'
            },
            {
                category: 'Cost Optimization',
                currentScore: Math.min(calculateCostOptimization(businessReqs) * baseScoreMultiplier, 88),
                targetScore: 85,
                improvement: 0,
                color: '#d62728'
            },
            {
                category: 'Performance & Reliability',
                currentScore: Math.min(calculatePerformance(technicalReqs) * baseScoreMultiplier, 91),
                targetScore: 92,
                improvement: 0,
                color: '#9467bd'
            }
        ];
        
        // Calculate improvements and round scores
        results.forEach(result => {
            result.currentScore = Math.round(result.currentScore);
            result.improvement = Math.max(result.targetScore - result.currentScore, 0);
        });

        return results;
    };

    const loadRecommendationsData = async () => {
        setLoadingRecommendations(true);
        try {
            if (Array.isArray(assessments) && assessments.length > 0) {
                // Find the best assessment to show recommendations from
                const completedAssessment = assessments.find(a => a.status === 'completed' && a.recommendations_generated) || assessments[0];
                
                try {
                    const recommendations = await apiClient.getRecommendations(completedAssessment.id);
                    
                    if (recommendations && recommendations.length > 0) {
                        // Convert API recommendations to table format - use new data structure
                        const tableData = recommendations.slice(0, 5).map((rec: any) => {
                            const provider = rec.recommendation_data?.provider || 'multi_cloud';
                            
                            return {
                                id: rec.id,
                                serviceName: rec.title,
                                provider: provider.toUpperCase() as 'AWS' | 'Azure' | 'GCP' | 'MULTI_CLOUD',
                                serviceType: rec.category || 'Service',
                                costEstimate: rec.cost_estimates?.monthly_cost || parseFloat(rec.total_estimated_monthly_cost) || 0,
                                confidenceScore: Math.round((rec.confidence_score || 0.8) * 100),
                                businessAlignment: Math.round((rec.business_alignment || rec.alignment_score || 0.85) * 100),
                                implementationComplexity: (rec.recommendation_data?.complexity || 'medium') as 'low' | 'medium' | 'high',
                                pros: rec.pros || [`${rec.recommendation_data?.estimated_savings || 0} estimated savings`, `${rec.recommendation_data?.implementation_timeline || 'N/A'} timeline`],
                                cons: rec.cons || rec.risks_and_considerations || [`${rec.recommendation_data?.complexity || 'medium'} complexity`],
                                status: rec.status === 'approved' || rec.confidence_score >= 0.8 ? 'recommended' as const : 'alternative' as const
                            };
                        });

                        setRecommendationsData(tableData);
                        console.log('💡 Set recommendations data:', tableData);
                        console.log('🔍 DEBUG: First recommendation costEstimate type:', typeof tableData[0]?.costEstimate, 'value:', tableData[0]?.costEstimate);
                    } else {
                        setRecommendationsData([]); // No recommendations yet
                    }
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
        setLoadingRecommendations(false);
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
                            <Button
                                variant="outlined"
                                size="small"
                                onClick={handleRefreshDashboard}
                                sx={{ ml: 'auto' }}
                            >
                                Refresh Data
                            </Button>
                            <Button
                                variant="contained"
                                size="small"
                                onClick={handleRegenerateRecommendations}
                                sx={{ ml: 1 }}
                                color="primary"
                            >
                                Regenerate Recommendations
                            </Button>
                            <Button
                                variant="contained"
                                size="small"
                                onClick={() => {
                                    console.log('🧪 DEBUG TEST - Current Redux State:');
                                    console.log('🧪 assessments:', assessments);
                                    console.log('🧪 assessmentLoading:', assessmentLoading);
                                    console.log('🧪 Redux store keys:', Object.keys(assessments || {}));
                                    console.log('🧪 Force loading dashboard data...');
                                    console.log('🧪 Current visualization state:', {
                                        costData: costData?.length || 0,
                                        recommendationScores: recommendationScores?.length || 0,
                                        assessmentResults: assessmentResults?.length || 0,
                                        recommendationsData: recommendationsData?.length || 0
                                    });
                                    if (Array.isArray(assessments) && assessments.length > 0) {
                                        loadDashboardData(true);
                                        // Check state after loading
                                        setTimeout(() => {
                                            console.log('🧪 After loading - visualization state:', {
                                                costData: costData?.length || 0,
                                                recommendationScores: recommendationScores?.length || 0,
                                                assessmentResults: assessmentResults?.length || 0,
                                                recommendationsData: recommendationsData?.length || 0
                                            });
                                        }, 2000);
                                    } else {
                                        console.log('🚫 Cannot load dashboard data - no valid assessments');
                                    }
                                }}
                                color="secondary"
                                sx={{ ml: 1 }}
                            >
                                Debug & Load
                            </Button>
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
                                    onClick={handleNewAssessment}
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
                                            onClick={handleNewAssessment}
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
                                                onClick={handleNewAssessment}
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
