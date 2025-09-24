'use client';

import React, { useState, useEffect } from 'react';
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
    Divider,
} from '@mui/material';
import {
    Analytics as AnalyticsIcon,
    TrendingUp,
    Assessment,
    Timeline,
    Security,
    CloudQueue,
    ExpandMore,
    Refresh,
    TrendingDown,
    Warning,
    CheckCircle,
    MonetizationOn,
    Speed,
    Shield,
} from '@mui/icons-material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiClient } from '@/services/api';
import { cacheBuster, forceRefresh } from '@/utils/cache-buster';

interface AnalyticsData {
    timestamp: string;
    timeframe: string;
    analytics: {
        cost_modeling: any;
        scaling_simulations: any;
        performance_benchmarks: any;
        multi_cloud_analysis: any;
        security_analytics: any;
        recommendation_trends: any;
    };
    predictive_insights: any;
    optimization_opportunities: any[];
}

export default function AnalyticsPage() {
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [timeframe, setTimeframe] = useState('7d');

    const fetchAnalyticsData = async () => {
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
            
            setAnalyticsData(data);
        } catch (err) {
            console.error('Failed to fetch analytics data:', err);
            setError(err instanceof Error ? err.message : 'Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    // Effect to fetch data when timeframe changes
    useEffect(() => {
        console.log(`🔄 Analytics timeframe changed to: ${timeframe}`);
        fetchAnalyticsData();
    }, [timeframe]);
    
    // Listen for assessment completion events to refresh analytics
    useEffect(() => {
        const handleAssessmentCompleted = (event: any) => {
            console.log('Assessment completed, refreshing analytics:', event.detail);
            // Refresh analytics data when an assessment is completed
            fetchAnalyticsData();
        };
        
        if (typeof window !== 'undefined') {
            window.addEventListener('assessment-completed', handleAssessmentCompleted);
            
            return () => {
                window.removeEventListener('assessment-completed', handleAssessmentCompleted);
            };
        }
    }, []);

    const handleTimeframeChange = (event: any) => {
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
                                <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <AnalyticsIcon sx={{ fontSize: 40 }} />
                                    Advanced Analytics
                                </Typography>
                                <Typography variant="body1" color="text.secondary">
                                    Comprehensive analytics and insights for your AI infrastructure assessments.
                                </Typography>
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
                                    onClick={fetchAnalyticsData}
                                    size="small"
                                >
                                    Refresh
                                </Button>
                            </Box>
                        </Box>
                        {analyticsData && (
                            <Typography variant="caption" color="text.secondary">
                                Last updated: {new Date(analyticsData.timestamp).toLocaleString()}
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
                                            <Typography variant="h6">Cost Analysis</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.cost_modeling?.current_analysis ? (
                                            <>
                                                <Box sx={{ mb: 2 }}>
                                                    <Typography variant="h4" color="primary">
                                                        {formatCurrency(analyticsData.analytics.cost_modeling.current_analysis.total_monthly_cost)}
                                                    </Typography>
                                                    <Typography variant="body2" color="text.secondary">
                                                        Total Monthly Cost
                                                    </Typography>
                                                </Box>
                                                
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
                                                                {analyticsData.analytics.cost_modeling.cost_optimization_opportunities.map((opportunity: any, index: number) => (
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
                                            <Typography variant="h6">Performance Benchmarks</Typography>
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
                                            <Typography variant="h6">Security Status</Typography>
                                        </Box>
                                        
                                        {analyticsData.analytics.security_analytics?.global_security?.threat_landscape ? (
                                            <>
                                                <Box sx={{ mb: 3 }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                                        <Typography variant="h4">
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

                                                {analyticsData.analytics.security_analytics.global_security.compliance_status && (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Compliance Status</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <Grid container spacing={1}>
                                                                {Object.entries(analyticsData.analytics.security_analytics.global_security.compliance_status).map(([standard, data]: [string, any]) => (
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
                                                                ))}
                                                            </Grid>
                                                        </AccordionDetails>
                                                    </Accordion>
                                                )}
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
                                            <Typography variant="h6">Multi-Cloud Strategy</Typography>
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

                                                {analyticsData.analytics.multi_cloud_analysis.global_strategy.workload_distribution && (
                                                    <Accordion>
                                                        <AccordionSummary expandIcon={<ExpandMore />}>
                                                            <Typography variant="subtitle2">Workload Distribution</Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails>
                                                            <Grid container spacing={2}>
                                                                {Object.entries(analyticsData.analytics.multi_cloud_analysis.global_strategy.workload_distribution).map(([workloadType, distribution]: [string, any]) => (
                                                                    <Grid item xs={12} key={workloadType}>
                                                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                                                            {workloadType.replace(/_/g, ' ').toUpperCase()}
                                                                        </Typography>
                                                                        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                                                            <Chip label={`AWS: ${distribution.aws_percentage}%`} size="small" />
                                                                            <Chip label={`GCP: ${distribution.gcp_percentage}%`} size="small" />
                                                                            <Chip label={`Azure: ${distribution.azure_percentage}%`} size="small" />
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
                                            <Typography variant="h6">Optimization Opportunities</Typography>
                                        </Box>
                                        
                                        {analyticsData.optimization_opportunities?.length > 0 && (
                                            <Grid container spacing={2}>
                                                {analyticsData.optimization_opportunities.map((opportunity, index) => (
                                                    <Grid item xs={12} md={6} lg={4} key={`opt-opp-${index}-${opportunity.title?.replace(/\s+/g, '-') || 'untitled'}`}>
                                                        <Paper sx={{ p: 2, height: '100%' }}>
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                                                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
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
                                                                    {formatCurrency(opportunity.potential_savings)}
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
                                                <Typography variant="h6">Predictive Insights</Typography>
                                            </Box>
                                            
                                            <Grid container spacing={2}>
                                                {analyticsData.predictive_insights.cost_predictions && (
                                                    <Grid item xs={12} md={4}>
                                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                                                            <Typography variant="h5">
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