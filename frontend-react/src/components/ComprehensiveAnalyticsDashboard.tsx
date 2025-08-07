import React, { useEffect, useState, useMemo } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Chip,
    LinearProgress,
    Alert,
    Stack,
    IconButton,
    Tooltip,
    Badge,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Divider,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Paper,
    Tabs,
    Tab,
} from '@mui/material';
import {
    TrendingUp,
    TrendingDown,
    Warning,
    CheckCircle,
    Error,
    Info,
    Speed,
    Memory,
    Storage,
    NetworkCheck,
    People,
    Assessment,
    CloudQueue,
    Timeline,
    Notifications,
    Close,
    FilterList,
    DateRange,
    Cloud,
} from '@mui/icons-material';
import { useAppSelector } from '@/store/hooks';
import { apiClient } from '@/services/api';
import CostComparisonChart from './charts/CostComparisonChart';
import RecommendationScoreChart from './charts/RecommendationScoreChart';
import AssessmentResultsChart from './charts/AssessmentResultsChart';

interface AnalyticsData {
    overall_performance: {
        score: number;
        trend: 'up' | 'down' | 'stable';
    };
    cost_efficiency: {
        score: number;
        trend: 'up' | 'down' | 'stable';
    };
    security_compliance: {
        score: number;
        trend: 'up' | 'down' | 'stable';
    };
    cost_breakdown: {
        aws: number;
        azure: number;
        gcp: number;
    };
    performance_by_service: {
        service: string;
        provider: string;
        score: number;
    }[];
    alerts_by_severity: {
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
    operational_insights: {
        id: string;
        insight: string;
        recommendation: string;
        severity: 'low' | 'medium' | 'high';
        category: 'cost' | 'performance' | 'security' | 'reliability';
    }[];
    feature_usage: {
        feature: string;
        usage_count: number;
        user_engagement_score: number;
    }[];
}

export default function ComprehensiveAnalyticsDashboard() {
    const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [timeframe, setTimeframe] = useState('30d');
    const [providerFilter, setProviderFilter] = useState('all');
    const [activeTab, setActiveTab] = useState(0);

    useEffect(() => {
        const fetchAnalytics = async () => {
            setLoading(true);
            setError(null);
            try {
                // Simulate API call
                const response = await new Promise<AnalyticsData>((resolve) => {
                    setTimeout(() => {
                        resolve({
                            overall_performance: { score: 85, trend: 'up' },
                            cost_efficiency: { score: 78, trend: 'down' },
                            security_compliance: { score: 92, trend: 'up' },
                            cost_breakdown: { aws: 12500, azure: 9800, gcp: 7600 },
                            performance_by_service: [
                                { service: 'EC2', provider: 'AWS', score: 88 },
                                { service: 'RDS', provider: 'AWS', score: 92 },
                                { service: 'Azure VMs', provider: 'Azure', score: 85 },
                                { service: 'Azure SQL', provider: 'Azure', score: 89 },
                                { service: 'Compute Engine', provider: 'GCP', score: 90 },
                                { service: 'Cloud SQL', provider: 'GCP', score: 91 },
                            ],
                            alerts_by_severity: { critical: 5, high: 12, medium: 34, low: 56 },
                            operational_insights: [
                                {
                                    id: '1',
                                    insight: 'High CPU utilization on RDS instances during peak hours.',
                                    recommendation: 'Consider upgrading to a larger instance class or implementing read replicas.',
                                    severity: 'high',
                                    category: 'performance',
                                },
                                {
                                    id: '2',
                                    insight: 'Unused EBS volumes detected in us-east-1.',
                                    recommendation: 'Review and delete unused volumes to reduce costs.',
                                    severity: 'medium',
                                    category: 'cost',
                                },
                                {
                                    id: '3',
                                    insight: 'S3 buckets without public access block.',
                                    recommendation: 'Enable public access block on all S3 buckets to enhance security.',
                                    severity: 'high',
                                    category: 'security',
                                },
                            ],
                            feature_usage: [
                                { feature: 'Assessments', usage_count: 120, user_engagement_score: 85 },
                                { feature: 'Reports', usage_count: 95, user_engagement_score: 78 },
                                { feature: 'Scenarios', usage_count: 65, user_engagement_score: 92 },
                                { feature: 'Analytics', usage_count: 45, user_engagement_score: 65 },
                            ],
                        });
                    }, 1000);
                });
                setAnalytics(response);
            } catch (err) {
                setError('Failed to fetch analytics data.');
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, [timeframe, providerFilter]);

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    const filteredPerformanceData = useMemo(() => {
        if (!analytics) return [];
        if (providerFilter === 'all') return analytics.performance_by_service;
        return analytics.performance_by_service.filter(
            (service) => service.provider.toLowerCase() === providerFilter
        );
    }, [analytics, providerFilter]);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    if (!analytics) {
        return <Alert severity="info">No analytics data available.</Alert>;
    }

    return (
        <Box>
            {/* Header and Filters */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                    Comprehensive Analytics
                </Typography>
                <Stack direction="row" spacing={2}>
                    <FormControl size="small">
                        <InputLabel>Timeframe</InputLabel>
                        <Select
                            value={timeframe}
                            label="Timeframe"
                            onChange={(e) => setTimeframe(e.target.value)}
                        >
                            <MenuItem value="7d">Last 7 Days</MenuItem>
                            <MenuItem value="30d">Last 30 Days</MenuItem>
                            <MenuItem value="90d">Last 90 Days</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl size="small">
                        <InputLabel>Provider</InputLabel>
                        <Select
                            value={providerFilter}
                            label="Provider"
                            onChange={(e) => setProviderFilter(e.target.value)}
                        >
                            <MenuItem value="all">All Providers</MenuItem>
                            <MenuItem value="aws">AWS</MenuItem>
                            <MenuItem value="azure">Azure</MenuItem>
                            <MenuItem value="gcp">GCP</MenuItem>
                        </Select>
                    </FormControl>
                </Stack>
            </Box>

            {/* Key Metrics */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Overall Performance
                            </Typography>
                            <Stack direction="row" alignItems="center" spacing={1}>
                                <Typography variant="h4" color="primary">
                                    {analytics.overall_performance.score}
                                </Typography>
                                {analytics.overall_performance.trend === 'up' ? (
                                    <TrendingUp color="success" />
                                ) : (
                                    <TrendingDown color="error" />
                                )}
                            </Stack>
                            <LinearProgress
                                variant="determinate"
                                value={analytics.overall_performance.score}
                                sx={{ mt: 1 }}
                            />
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Cost Efficiency
                            </Typography>
                            <Stack direction="row" alignItems="center" spacing={1}>
                                <Typography variant="h4" color="secondary">
                                    {analytics.cost_efficiency.score}
                                </Typography>
                                {analytics.cost_efficiency.trend === 'up' ? (
                                    <TrendingUp color="success" />
                                ) : (
                                    <TrendingDown color="error" />
                                )}
                            </Stack>
                            <LinearProgress
                                variant="determinate"
                                value={analytics.cost_efficiency.score}
                                color="secondary"
                                sx={{ mt: 1 }}
                            />
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Security & Compliance
                            </Typography>
                            <Stack direction="row" alignItems="center" spacing={1}>
                                <Typography variant="h4" color="success">
                                    {analytics.security_compliance.score}
                                </Typography>
                                {analytics.security_compliance.trend === 'up' ? (
                                    <TrendingUp color="success" />
                                ) : (
                                    <TrendingDown color="error" />
                                )}
                            </Stack>
                            <LinearProgress
                                variant="determinate"
                                value={analytics.security_compliance.score}
                                color="success"
                                sx={{ mt: 1 }}
                            />
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={activeTab} onChange={handleTabChange} centered>
                    <Tab label="Operational Insights" />
                    <Tab label="Performance Analysis" />
                    <Tab label="Cost Breakdown" />
                    <Tab label="Feature Usage" />
                </Tabs>
            </Paper>

            {/* Tab Panels */}
            {activeTab === 0 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Operational Insights
                        </Typography>
                        <List>
                            {(analytics.operational_insights || []).slice(0, 3).map((insight, index) => (
                                <React.Fragment key={insight.id}>
                                    <ListItem>
                                        <ListItemIcon>
                                            <Chip
                                                label={insight.severity}
                                                size="small"
                                                color={
                                                    insight.severity === 'high' ? 'error' :
                                                        insight.severity === 'medium' ? 'warning' : 'info'
                                                }
                                            />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={insight.insight}
                                            secondary={insight.recommendation}
                                        />
                                    </ListItem>
                                    {index < 2 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            )}

            {activeTab === 1 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Performance by Service
                        </Typography>
                        <RecommendationScoreChart
                            data={filteredPerformanceData.map(d => ({
                                service: d.service,
                                provider: d.provider,
                                performance: d.score,
                                color: d.provider === 'AWS' ? '#FF9900' : d.provider === 'Azure' ? '#0078D4' : '#4285F4'
                            }))}
                            title=""
                        />
                    </CardContent>
                </Card>
            )}

            {activeTab === 2 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Cost Breakdown by Provider
                        </Typography>
                        <CostComparisonChart
                            data={[
                                { provider: 'AWS', total: analytics.cost_breakdown.aws, color: '#FF9900' },
                                { provider: 'Azure', total: analytics.cost_breakdown.azure, color: '#0078D4' },
                                { provider: 'GCP', total: analytics.cost_breakdown.gcp, color: '#4285F4' },
                            ]}
                            title=""
                            showBreakdown={false}
                        />
                    </CardContent>
                </Card>
            )}

            {activeTab === 3 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Feature Usage & Engagement
                        </Typography>
                        <Grid container spacing={2}>
                            {analytics.feature_usage.map((feature) => (
                                <Grid item xs={12} sm={6} key={feature.feature}>
                                    <Typography variant="body2" fontWeight="medium">
                                        {feature.feature.charAt(0).toUpperCase() + feature.feature.slice(1)}
                                    </Typography>
                                    <Stack direction="row" spacing={2} alignItems="center">
                                        <Box sx={{ width: '100%' }}>
                                            <LinearProgress
                                                variant="determinate"
                                                value={feature.user_engagement_score}
                                            />
                                        </Box>
                                        <Typography variant="body2" color="text.secondary">
                                            {feature.user_engagement_score}%
                                        </Typography>
                                    </Stack>
                                </Grid>
                            ))}
                        </Grid>
                    </CardContent>
                </Card>
            )}

            {/* Alerts Summary */}
            <Card sx={{ mt: 3 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Alerts Summary
                    </Typography>
                    <Grid container spacing={2}>
                        {Object.entries(analytics.alerts_by_severity).map(([severity, count]) => (
                            <Grid item xs={6} sm={3} key={severity}>
                                <Paper
                                    variant="outlined"
                                    sx={{ p: 2, textAlign: 'center' }}
                                >
                                    <Typography variant="h5" color={
                                        severity === 'critical' ? 'error' :
                                            severity === 'high' ? 'error' :
                                                severity === 'medium' ? 'warning' : 'info'
                                    }>
                                        {count}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {severity.charAt(0).toUpperCase() + severity.slice(1)}
                                    </Typography>
                                </Paper>
                            </Grid>
                        ))}
                    </Grid>
                </CardContent>
            </Card>

            {/* Loading state for sections */}
            {loading && <LinearProgress sx={{ mb: 2 }} value={0} />}
        </Box>
    );
}
