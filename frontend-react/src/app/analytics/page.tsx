'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    Grid,
    Chip,
    Paper,
    Alert,
    AlertTitle,
    CircularProgress,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    List,
    ListItem,
    ListItemText,
    LinearProgress,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import {
    Analytics as AnalyticsIcon,
    TrendingUp,
    Timeline,
    CloudQueue,
    ExpandMore,
    Refresh,
    MonetizationOn,
    Speed,
    Shield,
} from '@mui/icons-material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiClient } from '@/services/api';
import { useFreshData } from '@/hooks/useFreshData';

interface CostCurrentAnalysis {
    total_monthly_cost: number;
    assessments_analyzed: number;
}

interface OptimizationOpportunity {
    title?: string;
    opportunity?: string;
    priority?: string;
    description?: string;
    potential_savings?: number | string;
    savings_percentage?: number | string;
    implementation_effort?: string;
    timeline?: string;
    risk_level?: string;
    categories?: string[];
}

interface CostModelingAnalytics {
    current_analysis: CostCurrentAnalysis;
    predictions: Record<string, unknown>[];
    cost_optimization_opportunities: OptimizationOpportunity[];
}

interface ScalingSimulationsAnalytics {
    simulations: Record<string, unknown>[];
    global_recommendations: Record<string, unknown>[];
}

interface PerformanceAnalysis {
    best_compute_performance?: string;
    best_compute_value?: string;
    cost_leader?: string;
}

interface PerformanceBenchmarksAnalytics {
    performance_analysis: PerformanceAnalysis | null;
    benchmarks: Record<string, unknown>;
    recommendations: string[];
}

interface ComplianceStatus {
    status: string;
    score: number;
}

interface ThreatLandscape {
    security_score?: number;
    high_priority_issues?: number;
    total_vulnerabilities?: number;
}

interface SecurityAnalytics {
    global_security: {
        threat_landscape?: ThreatLandscape;
        compliance_status?: Record<string, ComplianceStatus>;
    };
    assessment_security: Record<string, unknown>[];
}

interface WorkloadDistributionEntry {
    aws_percentage?: number;
    gcp_percentage?: number;
    azure_percentage?: number;
    strategy?: string;
}

interface MultiCloudStrategy {
    recommended_distribution?: {
        primary_cloud?: string;
        backup_cloud?: string;
        rationale?: string;
    };
    workload_distribution?: Record<string, WorkloadDistributionEntry>;
}

interface MultiCloudAnalytics {
    global_strategy: MultiCloudStrategy;
    assessment_strategies: Record<string, unknown>[];
}

interface RecommendationTrends {
    [key: string]: unknown;
}

interface PredictiveInsights {
    cost_predictions?: {
        annual_cost_forecast?: number;
        confidence_level?: number;
    };
    capacity_planning?: Record<string, unknown>;
    optimization_predictions?: {
        automation_roi?: string;
        multi_cloud_savings?: string;
    };
}

interface AnalyticsData {
    timestamp: string;
    timeframe: string;
    message?: string;
    analytics: {
        cost_modeling: CostModelingAnalytics;
        scaling_simulations: ScalingSimulationsAnalytics;
        performance_benchmarks: PerformanceBenchmarksAnalytics;
        multi_cloud_analysis: MultiCloudAnalytics;
        security_analytics: SecurityAnalytics;
        recommendation_trends: RecommendationTrends;
    };
    predictive_insights: PredictiveInsights;
    optimization_opportunities: OptimizationOpportunity[];
}

type AnalyticsApiResponse = Partial<AnalyticsData>;

const EMPTY_ANALYTICS: AnalyticsData['analytics'] = {
    cost_modeling: {
        current_analysis: {
            total_monthly_cost: 0,
            assessments_analyzed: 0
        },
        predictions: [],
        cost_optimization_opportunities: []
    },
    scaling_simulations: {
        simulations: [],
        global_recommendations: []
    },
    performance_benchmarks: {
        performance_analysis: null,
        benchmarks: {},
        recommendations: []
    },
    multi_cloud_analysis: {
        global_strategy: {},
        assessment_strategies: []
    },
    security_analytics: {
        global_security: {},
        assessment_security: []
    },
    recommendation_trends: {}
};

const EMPTY_PREDICTIVE_INSIGHTS: PredictiveInsights = {
    cost_predictions: {},
    capacity_planning: {},
    optimization_predictions: {}
};

const normalizeAnalyticsData = (data: AnalyticsApiResponse, fallbackTimeframe: string): AnalyticsData => {
    const analytics = data.analytics ?? {};

    return {
        timestamp: data.timestamp ?? new Date().toISOString(),
        timeframe: data.timeframe ?? fallbackTimeframe,
        message: data.message,
        analytics: {
            cost_modeling: {
                ...EMPTY_ANALYTICS.cost_modeling,
                ...analytics.cost_modeling,
                current_analysis: {
                    ...EMPTY_ANALYTICS.cost_modeling.current_analysis,
                    ...analytics.cost_modeling?.current_analysis
                },
                cost_optimization_opportunities: analytics.cost_modeling?.cost_optimization_opportunities ?? []
            },
            scaling_simulations: {
                ...EMPTY_ANALYTICS.scaling_simulations,
                ...analytics.scaling_simulations
            },
            performance_benchmarks: {
                ...EMPTY_ANALYTICS.performance_benchmarks,
                ...analytics.performance_benchmarks
            },
            multi_cloud_analysis: {
                ...EMPTY_ANALYTICS.multi_cloud_analysis,
                ...analytics.multi_cloud_analysis,
                global_strategy: {
                    ...EMPTY_ANALYTICS.multi_cloud_analysis.global_strategy,
                    ...analytics.multi_cloud_analysis?.global_strategy
                }
            },
            security_analytics: {
                ...EMPTY_ANALYTICS.security_analytics,
                ...analytics.security_analytics,
                global_security: {
                    ...EMPTY_ANALYTICS.security_analytics.global_security,
                    ...analytics.security_analytics?.global_security
                }
            },
            recommendation_trends: analytics.recommendation_trends ?? EMPTY_ANALYTICS.recommendation_trends
        },
        predictive_insights: data.predictive_insights ?? { ...EMPTY_PREDICTIVE_INSIGHTS },
        optimization_opportunities: Array.isArray(data.optimization_opportunities)
            ? data.optimization_opportunities
            : []
    };
};

export default function AnalyticsPage() {
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [timeframe, setTimeframe] = useState('7d');

    const fetchAnalyticsData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            console.log(`🔄 Fetching analytics data for timeframe: ${timeframe}`);
            
            // Clear analytics-specific storage for fresh data
            if (typeof window !== 'undefined') {
                try {
                    localStorage.removeItem(`analytics_${timeframe}_cache`);
                    sessionStorage.removeItem('analytics_data');
                } catch (e) {
                    console.warn('Analytics cache clear failed:', e);
                }
            }
            
            const data = await apiClient.getAdvancedAnalyticsDashboard(timeframe);
            
            console.log('📊 Analytics data received:', {
                timestamp: data.timestamp,
                timeframe: data.timeframe,
                hasAnalytics: !!data.analytics,
                hasOptimizations: data.optimization_opportunities?.length || 0,
                hasMessage: !!data.message,
                costModelingTotal: data.analytics?.cost_modeling?.current_analysis?.total_monthly_cost || 0
            });

            // DEBUG: Log cost optimization opportunities
            console.log('💰 Cost Optimization Opportunities:',
                data.analytics?.cost_modeling?.cost_optimization_opportunities || 'NONE');

            const normalized = normalizeAnalyticsData(data, timeframe);

            // DEBUG: Log normalized data
            console.log('📦 Normalized cost opps:',
                normalized.analytics?.cost_modeling?.cost_optimization_opportunities || 'NONE');

            setAnalyticsData(normalized);
        } catch (err) {
            console.error('Failed to fetch analytics data:', err);
            setError(err instanceof Error ? err.message : 'Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    }, [timeframe]);

    // Auto-refresh analytics data every 30 seconds
    const { forceRefresh: refreshAnalytics, isStale, lastRefresh } = useFreshData('analytics', {
        autoRefresh: true,
        refreshInterval: 30000, // 30 seconds
        dependencies: [timeframe],
        onRefresh: () => {
            console.log('🔄 Auto-refreshing analytics data...');
            fetchAnalyticsData();
        }
    });

    // Effect to fetch data when timeframe changes
    useEffect(() => {
        console.log(`🔄 Analytics timeframe changed to: ${timeframe}`);
        fetchAnalyticsData();
    }, [fetchAnalyticsData, timeframe]);
    
    // Listen for assessment completion events to refresh analytics
    useEffect(() => {
        const handleAssessmentCompleted = (event: CustomEvent<Record<string, unknown>>) => {
            console.log('Assessment completed, refreshing analytics:', event.detail);
            fetchAnalyticsData();
        };
        
        if (typeof window !== 'undefined') {
            const listener: EventListener = (event) => handleAssessmentCompleted(event as CustomEvent<Record<string, unknown>>);
            window.addEventListener('assessment-completed', listener);
            
            return () => {
                window.removeEventListener('assessment-completed', listener);
            };
        }
    }, [fetchAnalyticsData]);

    const handleTimeframeChange = (event: SelectChangeEvent<string>) => {
        setTimeframe(event.target.value);
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'healthy':
            case 'compliant':
                return 'success';
            case 'warning':
            case 'partially compliant':
                return 'warning';
            case 'critical':
            case 'non-compliant':
                return 'error';
            default:
                return 'info';
        }
    };

    const complianceStatus = analyticsData?.analytics.security_analytics.global_security.compliance_status;
    const workloadDistribution = analyticsData?.analytics.multi_cloud_analysis.global_strategy.workload_distribution;
    const parsePotentialSavings = (value?: number | string) => {
        if (typeof value === 'number' && Number.isFinite(value)) {
            return value;
        }
        if (typeof value === 'string') {
            const numeric = Number(value.replace(/[^0-9.-]/g, ''));
            return Number.isFinite(numeric) ? numeric : 0;
        }
        return 0;
    };

    if (loading) {
        return (
            <ProtectedRoute>
                <ResponsiveLayout title="Advanced Analytics">
                    <Container maxWidth="lg">
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
                            <CircularProgress size={60} />
                        </Box>
                    </Container>
                </ResponsiveLayout>
            </ProtectedRoute>
        );
    }

    if (error) {
        return (
            <ProtectedRoute>
                <ResponsiveLayout title="Advanced Analytics">
                    <Container maxWidth="lg">
                        <Alert severity="error" sx={{ mb: 3 }}>
                            <AlertTitle>Analytics Unavailable</AlertTitle>
                            {error}
                        </Alert>
                        <Button 
                            variant="contained" 
                            startIcon={<Refresh />} 
                            onClick={fetchAnalyticsData}
                        >
                            Retry
                        </Button>
                    </Container>
                </ResponsiveLayout>
            </ProtectedRoute>
        );
    }

    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Advanced Analytics">
                <Container maxWidth="lg" sx={{ mt: 3 }}>
                    <Box sx={{ mb: 4 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box>
                                <Typography variant="h4" color="text.primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <AnalyticsIcon sx={{ fontSize: 40 }} />
                                    Advanced Analytics
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Typography variant="body1" color="text.secondary">
                                        Comprehensive analytics and insights for your AI infrastructure assessments
                                    </Typography>
                                    <Chip
                                        label={isStale ? "Data may be outdated" : "Live data"}
                                        size="small"
                                        color={isStale ? "warning" : "success"}
                                        variant="outlined"
                                    />
                                </Box>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                <FormControl size="small" sx={{ minWidth: 120 }}>
                                    <InputLabel>Timeframe</InputLabel>
                                    <Select
                                        value={timeframe}
                                        label="Timeframe"
                                        onChange={handleTimeframeChange}
                                    >
                                        <MenuItem value="1h">1 Hour</MenuItem>
                                        <MenuItem value="24h">24 Hours</MenuItem>
                                        <MenuItem value="7d">7 Days</MenuItem>
                                        <MenuItem value="30d">30 Days</MenuItem>
                                        <MenuItem value="90d">90 Days</MenuItem>
                                    </Select>
                                </FormControl>
                                <Button
                                    startIcon={<Refresh />}
                                    onClick={refreshAnalytics}
                                    size="small"
                                    title={`Last updated: ${new Date(lastRefresh).toLocaleTimeString()}`}
                                >
                                    Refresh
                                </Button>
                            </Box>
                        </Box>
                        {analyticsData && (
                            <Typography variant="caption" color="text.secondary">
                                Data timestamp: {new Date(analyticsData.timestamp).toLocaleString()} •
                                Page refreshed: {new Date(lastRefresh).toLocaleString()}
                            </Typography>
                        )}
                    </Box>

                    {analyticsData ? (
                        <>  
                            {analyticsData.message && (
                                <Alert severity="info" sx={{ mb: 3 }}>
                                    <Typography variant="body2">
                                        {analyticsData.message}
                                    </Typography>
                                </Alert>
                            )}
                            <Grid container spacing={3}>
                            {/* Cost Modeling */}
                            <Grid item xs={12} lg={6} key="cost-modeling">
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                            <MonetizationOn color="primary" />
                                            <Typography variant="h6" color="text.primary">Cost Analysis</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.cost_modeling?.current_analysis ? (
                                            <>
                                                {analyticsData.analytics.cost_modeling.current_analysis.total_monthly_cost > 0 ? (
                                                    <Box sx={{ mb: 2 }}>
                                                        <Typography variant="h4" color="primary">
                                                            {formatCurrency(analyticsData.analytics.cost_modeling.current_analysis.total_monthly_cost)}
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Total Monthly Cost
                                                        </Typography>
                                                    </Box>
                                                ) : (
                                                    <Box sx={{ mb: 2, textAlign: 'center', py: 3 }}>
                                                        <Typography variant="h6" color="text.secondary" gutterBottom>
                                                            No Cost Data Available
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Complete assessments to see cost analysis
                                                        </Typography>
                                                    </Box>
                                                )}

                                                <Typography variant="body2" sx={{ mb: 2 }}>
                                                    Assessments analyzed: {analyticsData.analytics.cost_modeling.current_analysis.assessments_analyzed}
                                                </Typography>

                                                {analyticsData.analytics.cost_modeling.current_analysis.assessments_analyzed === 0 && (
                                                    <Alert severity="info" sx={{ mt: 2 }}>
                                                        <Typography variant="body2">
                                                            Complete your first assessment to see detailed cost analysis and optimization opportunities.
                                                        </Typography>
                                                    </Alert>
                                                )}
                                                
                                                {analyticsData.analytics.cost_modeling.cost_optimization_opportunities?.length > 0 && (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Cost Optimization Opportunities</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <List dense>
                                                                {analyticsData.analytics.cost_modeling.cost_optimization_opportunities.map((opportunity, index) => (
                                                                    <ListItem key={`cost-opp-${opportunity.opportunity?.replace(/\s+/g, '-') || index}`}>
                                                                        <ListItemText
                                                                            primary={opportunity.opportunity}
                                                                            secondary={`${opportunity.potential_savings} (${opportunity.savings_percentage}% savings)`}
                                                                        />
                                                                        <Chip 
                                                                            label={opportunity.implementation_effort} 
                                                                            size="small" 
                                                                            color={opportunity.implementation_effort === 'low' ? 'success' : opportunity.implementation_effort === 'medium' ? 'warning' : 'error'}
                                                                        />
                                                                    </ListItem>
                                                                ))}
                                                            </List>
                                                        </AccordionDetails>
                                                    </Accordion>
                                                )}
                                            </>
                                        ) : (
                                            <Alert severity="info">
                                                <Typography variant="body2">
                                                    Complete assessments to see detailed cost modeling and optimization opportunities.
                                                </Typography>
                                            </Alert>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Performance Benchmarks */}
                            <Grid item xs={12} lg={6} key="performance-benchmarks">
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                            <Speed color="primary" />
                                            <Typography variant="h6" color="text.primary">Performance Benchmarks</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.performance_benchmarks?.performance_analysis ? (
                                            <>
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="body2" color="text.secondary">Best Performance:</Typography>
                                                    <Typography variant="body1">
                                                        {analyticsData.analytics.performance_benchmarks.performance_analysis.best_compute_performance}
                                                    </Typography>
                                                </Box>
                                                
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="body2" color="text.secondary">Best Value:</Typography>
                                                    <Typography variant="body1">
                                                        {analyticsData.analytics.performance_benchmarks.performance_analysis.best_compute_value}
                                                    </Typography>
                                                </Box>
                                                
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="body2" color="text.secondary">Cost Leader:</Typography>
                                                    <Typography variant="body1">
                                                        {analyticsData.analytics.performance_benchmarks.performance_analysis.cost_leader}
                                                    </Typography>
                                                </Box>
                                            </>
                                        ) : (
                                            <Alert severity="info">
                                                <Typography variant="body2">
                                                    Complete assessments to see performance benchmarks and analysis.
                                                </Typography>
                                            </Alert>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Security Analytics */}
                            <Grid item xs={12} lg={6} key="security-analytics">
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                            <Shield color="primary" />
                                            <Typography variant="h6" color="text.primary">Security Status</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.security_analytics?.global_security?.threat_landscape ? (
                                            <>
                                                <Box sx={{ mb: 3 }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                                        <Typography variant="h4" color="text.primary">
                                                            {analyticsData.analytics.security_analytics.global_security.threat_landscape.security_score}
                                                        </Typography>
                                                        <Typography variant="body2" color="text.secondary">/100</Typography>
                                                    </Box>
                                                    <LinearProgress 
                                                        variant="determinate" 
                                                        value={analyticsData.analytics.security_analytics.global_security.threat_landscape.security_score}
                                                        color={analyticsData.analytics.security_analytics.global_security.threat_landscape.security_score > 80 ? 'success' : 'warning'}
                                                    />
                                                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                                        Security Score
                                                    </Typography>
                                                </Box>
                                                
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="body2">
                                                        High Priority Issues: {analyticsData.analytics.security_analytics.global_security.threat_landscape.high_priority_issues}
                                                    </Typography>
                                                    <Typography variant="body2">
                                                        Total Vulnerabilities: {analyticsData.analytics.security_analytics.global_security.threat_landscape.total_vulnerabilities}
                                                    </Typography>
                                                </Box>

                                                {complianceStatus && complianceStatus.note ? (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Compliance Status</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <Alert severity="info">
                                                                {complianceStatus.note}
                                                            </Alert>
                                                            {complianceStatus.available_frameworks && (
                                                                <Box sx={{ mt: 2 }}>
                                                                    <Typography variant="caption" display="block" gutterBottom>
                                                                        Available Frameworks:
                                                                    </Typography>
                                                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                                        {complianceStatus.available_frameworks.map((framework: string) => (
                                                                            <Chip
                                                                                key={framework}
                                                                                label={framework}
                                                                                size="small"
                                                                                variant="outlined"
                                                                            />
                                                                        ))}
                                                                    </Box>
                                                                </Box>
                                                            )}
                                                        </AccordionDetails>
                                                    </Accordion>
                                                ) : complianceStatus && typeof complianceStatus === 'object' && !complianceStatus.note ? (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Compliance Status</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <Grid container spacing={1}>
                                                                {Object.entries(complianceStatus).map(([standard, data]: [string, any]) => {
                                                                    // Only render if data has status property (legacy format)
                                                                    if (data && typeof data === 'object' && data.status) {
                                                                        return (
                                                                            <Grid item xs={6} key={standard}>
                                                                                <Box sx={{ textAlign: 'center', p: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                                                                                    <Typography variant="caption">{standard}</Typography>
                                                                                    <br />
                                                                                    <Chip
                                                                                        label={data.status}
                                                                                        size="small"
                                                                                        color={getStatusColor(data.status)}
                                                                                        variant="outlined"
                                                                                    />
                                                                                    <br />
                                                                                    <Typography variant="caption">{data.score}%</Typography>
                                                                                </Box>
                                                                            </Grid>
                                                                        );
                                                                    }
                                                                    return null;
                                                                })}
                                                            </Grid>
                                                        </AccordionDetails>
                                                    </Accordion>
                                                ) : null}
                                            </>
                                        ) : (
                                            <Alert severity="info">
                                                <Typography variant="body2">
                                                    Complete assessments to see security analytics and compliance status.
                                                </Typography>
                                            </Alert>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Multi-Cloud Analysis */}
                            <Grid item xs={12} lg={6} key="multi-cloud-analysis">
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                            <CloudQueue color="primary" />
                                            <Typography variant="h6" color="text.primary">Multi-Cloud Strategy</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.multi_cloud_analysis?.global_strategy?.recommended_distribution ? (
                                            <>
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="body2" color="text.secondary">Recommended Distribution:</Typography>
                                                    <Typography variant="body1">
                                                        Primary: {analyticsData.analytics.multi_cloud_analysis.global_strategy.recommended_distribution.primary_cloud}
                                                    </Typography>
                                                    <Typography variant="body2" sx={{ mt: 1 }}>
                                                        {analyticsData.analytics.multi_cloud_analysis.global_strategy.recommended_distribution.rationale}
                                                    </Typography>
                                                </Box>

                                                {workloadDistribution && (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Workload Distribution</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <Grid container spacing={2}>
                                                                {Object.entries(workloadDistribution).map(([workloadType, distribution]) => (
                                                                    <Grid item xs={12} key={workloadType}>
                                                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                                                            {workloadType.replace(/_/g, ' ').toUpperCase()}
                                                                        </Typography>
                                                                        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                                                            <Chip label={`AWS: ${distribution.aws_percentage ?? 0}%`} size="small" />
                                                                            <Chip label={`GCP: ${distribution.gcp_percentage ?? 0}%`} size="small" />
                                                                            <Chip label={`Azure: ${distribution.azure_percentage ?? 0}%`} size="small" />
                                                                        </Box>
                                                                        <Typography variant="body2" color="text.secondary">
                                                                            {distribution.strategy}
                                                                        </Typography>
                                                                    </Grid>
                                                                ))}
                                                            </Grid>
                                                        </AccordionDetails>
                                                    </Accordion>
                                                )}
                                            </>
                                        ) : (
                                            <Alert severity="info">
                                                <Typography variant="body2">
                                                    Complete assessments to see multi-cloud strategy recommendations.
                                                </Typography>
                                            </Alert>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Optimization Opportunities */}
                            <Grid item xs={12}>
                                <Card>
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                            <TrendingUp color="primary" />
                                            <Typography variant="h6" color="text.primary">Optimization Opportunities</Typography>
                                        </Box>
                                        
                                        {analyticsData.optimization_opportunities?.length > 0 && (
                                            <Grid container spacing={2}>
                                                {analyticsData.optimization_opportunities.map((opportunity, index) => (
                                                    <Grid item xs={12} md={6} lg={4} key={`opt-opp-${index}-${opportunity.title?.replace(/\s+/g, '-') || 'untitled'}`}>
                                                        <Paper sx={{ p: 2, height: '100%' }}>
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                                                <Typography variant="h6" color="text.primary" sx={{ fontSize: '1rem' }}>
                                                                    {opportunity.title}
                                                                </Typography>
                                                                <Chip 
                                                                    label={opportunity.priority} 
                                                                    size="small" 
                                                                    color={opportunity.priority === 'High' ? 'error' : opportunity.priority === 'Medium' ? 'warning' : 'info'}
                                                                />
                                                            </Box>
                                                            
                                                            <Typography variant="body2" sx={{ mb: 2 }}>
                                                                {opportunity.description}
                                                            </Typography>
                                                            
                                                            <Box sx={{ mb: 2 }}>
                                                                <Typography variant="h5" color="success.main">
                                                                    {formatCurrency(parsePotentialSavings(opportunity.potential_savings))}
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    {opportunity.savings_percentage}% potential savings
                                                                </Typography>
                                                            </Box>
                                                            
                                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                                <Chip 
                                                                    label={opportunity.implementation_effort} 
                                                                    size="small" 
                                                                    variant="outlined"
                                                                />
                                                                <Chip 
                                                                    label={opportunity.timeline} 
                                                                    size="small" 
                                                                    variant="outlined"
                                                                />
                                                                <Chip 
                                                                    label={opportunity.risk_level} 
                                                                    size="small" 
                                                                    variant="outlined"
                                                                    color={opportunity.risk_level === 'Low' ? 'success' : 'warning'}
                                                                />
                                                            </Box>
                                                        </Paper>
                                                    </Grid>
                                                ))}
                                            </Grid>
                                        )}
                                    </CardContent>
                                </Card>
                            </Grid>

                            {/* Predictive Insights */}
                            {analyticsData.predictive_insights && (
                                <Grid item xs={12}>
                                    <Card>
                                        <CardContent>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                                <Timeline color="primary" />
                                                <Typography variant="h6" color="text.primary">Predictive Insights</Typography>
                                            </Box>
                                            
                                            <Grid container spacing={2}>
                                                {analyticsData.predictive_insights.cost_predictions && (
                                                    <Grid item xs={12} md={4}>
                                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                                                            <Typography variant="h5" color="text.primary">
                                                                {formatCurrency(analyticsData.predictive_insights.cost_predictions.annual_cost_forecast)}
                                                            </Typography>
                                                            <Typography variant="body2" color="text.secondary">
                                                                Annual Cost Forecast
                                                            </Typography>
                                                            <Typography variant="caption">
                                                                {(analyticsData.predictive_insights.cost_predictions.confidence_level * 100).toFixed(0)}% confidence
                                                            </Typography>
                                                        </Box>
                                                    </Grid>
                                                )}
                                                
                                                {analyticsData.predictive_insights.optimization_predictions && (
                                                    <>
                                                        <Grid item xs={12} md={4}>
                                                            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', color: 'success.contrastText', borderRadius: 1 }}>
                                                                <Typography variant="body1" fontWeight="bold">
                                                                    {analyticsData.predictive_insights.optimization_predictions.automation_roi}
                                                                </Typography>
                                                                <Typography variant="body2">
                                                                    Automation ROI
                                                                </Typography>
                                                            </Box>
                                                        </Grid>
                                                        <Grid item xs={12} md={4}>
                                                            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.light', color: 'info.contrastText', borderRadius: 1 }}>
                                                                <Typography variant="body1" fontWeight="bold">
                                                                    {analyticsData.predictive_insights.optimization_predictions.multi_cloud_savings}
                                                                </Typography>
                                                                <Typography variant="body2">
                                                                    Multi-Cloud Savings
                                                                </Typography>
                                                            </Box>
                                                        </Grid>
                                                    </>
                                                )}
                                            </Grid>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            )}
                        </Grid>
                        </>
                    ) : (
                        <Alert severity="info">
                            <AlertTitle>No Analytics Data</AlertTitle>
                            Create some assessments to see advanced analytics and insights.
                        </Alert>
                    )}
                </Container>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}
