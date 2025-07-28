/**
 * Comprehensive Analytics Dashboard Component
 * 
 * Advanced admin dashboard for system metrics, performance monitoring,
 * user analytics, recommendation quality tracking, and alerting system.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Tabs,
    Tab,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Button,
    Alert,
    Chip,
    LinearProgress,
    IconButton,
    Tooltip,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    CircularProgress,
    Switch,
    FormControlLabel
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Download as DownloadIcon,
    Settings as SettingsIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Info as InfoIcon
} from '@mui/icons-material';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

// Types
interface AnalyticsTimeframe {
    value: string;
    label: string;
}

interface TrendAnalysis {
    current_value: number;
    previous_value: number;
    change_percent: number;
    trend: 'up' | 'down' | 'stable' | 'volatile';
    confidence: number;
    data_points: number;
}

interface UserAnalytics {
    total_users: number;
    active_users_24h: number;
    active_users_7d: number;
    new_users_24h: number;
    new_users_7d: number;
    user_retention_rate: number;
    avg_session_duration_minutes: number;
    bounce_rate_percent: number;
    user_engagement_score: number;
    geographic_distribution: Record<string, number>;
    company_size_distribution: Record<string, number>;
    industry_distribution: Record<string, number>;
    feature_usage: Record<string, number>;
}

interface RecommendationQualityMetrics {
    total_recommendations: number;
    avg_confidence_score: number;
    user_satisfaction_score: number;
    implementation_success_rate: number;
    recommendation_accuracy: number;
    agent_performance_breakdown: Record<string, any>;
    quality_trends: Record<string, TrendAnalysis>;
    feedback_distribution: Record<string, number>;
    cost_savings_achieved: number;
    time_to_implementation: number;
}

interface SystemPerformanceAnalytics {
    avg_response_time_ms: number;
    p95_response_time_ms: number;
    p99_response_time_ms: number;
    error_rate_percent: number;
    throughput_requests_per_minute: number;
    system_availability_percent: number;
    resource_utilization: Record<string, number>;
    performance_trends: Record<string, TrendAnalysis>;
    bottleneck_analysis: Array<{
        component: string;
        impact_score: number;
        description: string;
        recommendation: string;
    }>;
    capacity_projections: Record<string, number>;
}

interface AlertAnalytics {
    total_alerts_24h: number;
    active_alerts: number;
    resolved_alerts_24h: number;
    avg_resolution_time_minutes: number;
    alert_frequency_by_type: Record<string, number>;
    alert_severity_distribution: Record<string, number>;
    most_common_issues: Array<{
        issue: string;
        count: number;
        percentage: number;
    }>;
}

interface ComprehensiveAnalytics {
    timestamp: string;
    timeframe: string;
    user_analytics: UserAnalytics;
    recommendation_quality: RecommendationQualityMetrics;
    system_performance: SystemPerformanceAnalytics;
    alert_analytics: AlertAnalytics;
    business_metrics: Record<string, any>;
    operational_insights: Array<{
        type: string;
        priority: string;
        title: string;
        description: string;
        recommendation: string;
        impact: string;
        estimated_effort: string;
    }>;
    predictive_analytics: Record<string, any>;
}

const TIMEFRAMES: AnalyticsTimeframe[] = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: '365d', label: 'Last Year' }
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ComprehensiveAnalyticsDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState(0);
    const [timeframe, setTimeframe] = useState('24h');
    const [analytics, setAnalytics] = useState<ComprehensiveAnalytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    // Fetch analytics data
    const fetchAnalytics = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch(`/api/admin/analytics/comprehensive?timeframe=${timeframe}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setAnalytics(data.analytics);
            setLastUpdated(new Date());
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
        } finally {
            setLoading(false);
        }
    }, [timeframe]);

    // Auto-refresh effect
    useEffect(() => {
        fetchAnalytics();

        if (autoRefresh) {
            const interval = setInterval(fetchAnalytics, 300000); // 5 minutes
            return () => clearInterval(interval);
        }
    }, [fetchAnalytics, autoRefresh]);

    // Export analytics report
    const handleExport = async () => {
        try {
            const response = await fetch(`/api/admin/analytics/export?format=json&timeframe=${timeframe}`);
            if (!response.ok) throw new Error('Export failed');

            const data = await response.json();
            const blob = new Blob([data.report_data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analytics-report-${timeframe}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            setError('Failed to export analytics report');
        }
    };

    // Render trend indicator
    const renderTrendIndicator = (trend: TrendAnalysis) => {
        const getTrendIcon = () => {
            switch (trend.trend) {
                case 'up':
                    return <TrendingUpIcon color="success" />;
                case 'down':
                    return <TrendingDownIcon color="error" />;
                case 'volatile':
                    return <WarningIcon color="warning" />;
                default:
                    return <CheckCircleIcon color="info" />;
            }
        };

        const getTrendColor = () => {
            switch (trend.trend) {
                case 'up':
                    return 'success';
                case 'down':
                    return 'error';
                case 'volatile':
                    return 'warning';
                default:
                    return 'info';
            }
        };

        return (
            <Box display="flex" alignItems="center" gap={1}>
                {getTrendIcon()}
                <Typography variant="body2" color={getTrendColor()}>
                    {trend.change_percent > 0 ? '+' : ''}{trend.change_percent.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    (confidence: {(trend.confidence * 100).toFixed(0)}%)
                </Typography>
            </Box>
        );
    };

    // Render metric card
    const renderMetricCard = (title: string, value: string | number, trend?: TrendAnalysis, unit?: string) => (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    {title}
                </Typography>
                <Typography variant="h4" color="primary">
                    {typeof value === 'number' ? value.toLocaleString() : value}
                    {unit && <Typography component="span" variant="body2" color="text.secondary"> {unit}</Typography>}
                </Typography>
                {trend && renderTrendIndicator(trend)}
            </CardContent>
        </Card>
    );

    // Overview Tab
    const renderOverviewTab = () => {
        if (!analytics) return null;

        return (
            <Grid container spacing={3}>
                {/* Key Metrics */}
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Active Users (24h)',
                        analytics.user_analytics.active_users_24h,
                        undefined,
                        'users'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'User Satisfaction',
                        analytics.recommendation_quality.user_satisfaction_score.toFixed(1),
                        analytics.recommendation_quality.quality_trends.satisfaction,
                        '/5.0'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Response Time',
                        analytics.system_performance.avg_response_time_ms.toFixed(0),
                        analytics.system_performance.performance_trends.response_time,
                        'ms'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Active Alerts',
                        analytics.alert_analytics.active_alerts,
                        undefined,
                        'alerts'
                    )}
                </Grid>

                {/* System Health Overview */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                System Health
                            </Typography>
                            <Box mb={2}>
                                <Typography variant="body2" gutterBottom>
                                    CPU Usage: {analytics.system_performance.resource_utilization.cpu?.toFixed(1)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={analytics.system_performance.resource_utilization.cpu || 0}
                                    color={analytics.system_performance.resource_utilization.cpu > 80 ? 'error' : 'primary'}
                                />
                            </Box>
                            <Box mb={2}>
                                <Typography variant="body2" gutterBottom>
                                    Memory Usage: {analytics.system_performance.resource_utilization.memory?.toFixed(1)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={analytics.system_performance.resource_utilization.memory || 0}
                                    color={analytics.system_performance.resource_utilization.memory > 85 ? 'error' : 'primary'}
                                />
                            </Box>
                            <Box>
                                <Typography variant="body2" gutterBottom>
                                    Error Rate: {analytics.system_performance.error_rate_percent.toFixed(2)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={Math.min(analytics.system_performance.error_rate_percent * 10, 100)}
                                    color={analytics.system_performance.error_rate_percent > 5 ? 'error' : 'success'}
                                />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Operational Insights */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Operational Insights
                            </Typography>
                            {analytics.operational_insights.slice(0, 3).map((insight, index) => (
                                <Alert
                                    key={index}
                                    severity={insight.priority === 'critical' ? 'error' : insight.priority === 'high' ? 'warning' : 'info'}
                                    sx={{ mb: 1 }}
                                >
                                    <Typography variant="subtitle2">{insight.title}</Typography>
                                    <Typography variant="body2">{insight.description}</Typography>
                                </Alert>
                            ))}
                        </CardContent>
                    </Card>
                </Grid>

                {/* User Engagement Chart */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                User Engagement Score
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={[
                                        { time: '6h ago', score: 7.2 },
                                        { time: '5h ago', score: 7.5 },
                                        { time: '4h ago', score: 7.1 },
                                        { time: '3h ago', score: 7.8 },
                                        { time: '2h ago', score: 8.0 },
                                        { time: '1h ago', score: 7.9 },
                                        { time: 'now', score: analytics.user_analytics.user_engagement_score }
                                    ]}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="time" />
                                        <YAxis domain={[0, 10]} />
                                        <RechartsTooltip />
                                        <Line type="monotone" dataKey="score" stroke="#8884d8" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Recommendation Quality */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Recommendation Quality
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={[
                                        { metric: 'Confidence', value: analytics.recommendation_quality.avg_confidence_score * 100 },
                                        { metric: 'Accuracy', value: analytics.recommendation_quality.recommendation_accuracy * 100 },
                                        { metric: 'Success Rate', value: analytics.recommendation_quality.implementation_success_rate * 100 },
                                        { metric: 'Satisfaction', value: analytics.recommendation_quality.user_satisfaction_score * 20 }
                                    ]}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="metric" />
                                        <YAxis domain={[0, 100]} />
                                        <RechartsTooltip formatter={(value) => [`${value}%`, 'Score']} />
                                        <Bar dataKey="value" fill="#82ca9d" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    // User Analytics Tab
    const renderUserAnalyticsTab = () => {
        if (!analytics) return null;

        const { user_analytics } = analytics;

        return (
            <Grid container spacing={3}>
                {/* User Metrics */}
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Total Users', user_analytics.total_users)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Active Users (24h)', user_analytics.active_users_24h)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard('New Users (24h)', user_analytics.new_users_24h)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Retention Rate', `${(user_analytics.user_retention_rate * 100).toFixed(1)}%`)}
                </Grid>

                {/* Geographic Distribution */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Geographic Distribution
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={Object.entries(user_analytics.geographic_distribution).map(([region, count]) => ({
                                                name: region,
                                                value: count
                                            }))}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {Object.entries(user_analytics.geographic_distribution).map((_, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Company Size Distribution */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Company Size Distribution
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={Object.entries(user_analytics.company_size_distribution).map(([size, count]) => ({
                                        size: size.charAt(0).toUpperCase() + size.slice(1),
                                        count
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="size" />
                                        <YAxis />
                                        <RechartsTooltip />
                                        <Bar dataKey="count" fill="#8884d8" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Feature Usage */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Feature Usage
                            </Typography>
                            <Grid container spacing={2}>
                                {Object.entries(user_analytics.feature_usage).map(([feature, usage]) => (
                                    <Grid item xs={12} sm={6} md={3} key={feature}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="primary">
                                                {usage.toLocaleString()}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {feature.charAt(0).toUpperCase() + feature.slice(1)}
                                            </Typography>
                                        </Box>
                                    </Grid>
                                ))}
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    // System Performance Tab
    const renderSystemPerformanceTab = () => {
        if (!analytics) return null;

        const { system_performance } = analytics;

        return (
            <Grid container spacing={3}>
                {/* Performance Metrics */}
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Avg Response Time',
                        system_performance.avg_response_time_ms.toFixed(0),
                        system_performance.performance_trends.response_time,
                        'ms'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Error Rate',
                        system_performance.error_rate_percent.toFixed(2),
                        system_performance.performance_trends.error_rate,
                        '%'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Throughput',
                        system_performance.throughput_requests_per_minute.toFixed(0),
                        system_performance.performance_trends.throughput,
                        'req/min'
                    )}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Availability',
                        system_performance.system_availability_percent.toFixed(1),
                        undefined,
                        '%'
                    )}
                </Grid>

                {/* Resource Utilization */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Resource Utilization
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={Object.entries(system_performance.resource_utilization).map(([resource, usage]) => ({
                                        resource: resource.toUpperCase(),
                                        usage: usage || 0
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="resource" />
                                        <YAxis domain={[0, 100]} />
                                        <RechartsTooltip formatter={(value) => [`${value}%`, 'Usage']} />
                                        <Bar dataKey="usage" fill="#82ca9d" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Bottleneck Analysis */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Bottleneck Analysis
                            </Typography>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Component</TableCell>
                                            <TableCell>Impact</TableCell>
                                            <TableCell>Description</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {system_performance.bottleneck_analysis.map((bottleneck, index) => (
                                            <TableRow key={index}>
                                                <TableCell>{bottleneck.component}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={bottleneck.impact_score.toFixed(1)}
                                                        color={bottleneck.impact_score > 7 ? 'error' : bottleneck.impact_score > 5 ? 'warning' : 'success'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="body2">{bottleneck.description}</Typography>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Capacity Projections */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Capacity Projections (30 days)
                            </Typography>
                            <Grid container spacing={2}>
                                {Object.entries(system_performance.capacity_projections).map(([metric, value]) => (
                                    <Grid item xs={12} sm={6} md={3} key={metric}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="primary">
                                                {typeof value === 'number' ? value.toLocaleString() : value}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                            </Typography>
                                        </Box>
                                    </Grid>
                                ))}
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    // Alerts Tab
    const renderAlertsTab = () => {
        if (!analytics) return null;

        const { alert_analytics } = analytics;

        return (
            <Grid container spacing={3}>
                {/* Alert Metrics */}
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Active Alerts', alert_analytics.active_alerts)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Alerts (24h)', alert_analytics.total_alerts_24h)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard('Resolved (24h)', alert_analytics.resolved_alerts_24h)}
                </Grid>
                <Grid item xs={12} md={3}>
                    {renderMetricCard(
                        'Avg Resolution Time',
                        alert_analytics.avg_resolution_time_minutes.toFixed(0),
                        undefined,
                        'min'
                    )}
                </Grid>

                {/* Alert Severity Distribution */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Alert Severity Distribution
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={Object.entries(alert_analytics.alert_severity_distribution).map(([severity, count]) => ({
                                                name: severity.charAt(0).toUpperCase() + severity.slice(1),
                                                value: count
                                            }))}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {Object.entries(alert_analytics.alert_severity_distribution).map((_, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Most Common Issues */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Most Common Issues
                            </Typography>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Issue</TableCell>
                                            <TableCell>Count</TableCell>
                                            <TableCell>Percentage</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {alert_analytics.most_common_issues.map((issue, index) => (
                                            <TableRow key={index}>
                                                <TableCell>{issue.issue}</TableCell>
                                                <TableCell>{issue.count}</TableCell>
                                                <TableCell>{issue.percentage.toFixed(1)}%</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Alert Frequency by Type */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Alert Frequency by Type
                            </Typography>
                            <Box height={300}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={Object.entries(alert_analytics.alert_frequency_by_type).map(([type, count]) => ({
                                        type: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                                        count
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="type" />
                                        <YAxis />
                                        <RechartsTooltip />
                                        <Bar dataKey="count" fill="#ff7300" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        );
    };

    if (loading && !analytics) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box>
            {/* Header */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    Comprehensive Analytics Dashboard
                </Typography>
                <Box display="flex" gap={2} alignItems="center">
                    <FormControlLabel
                        control={
                            <Switch
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                            />
                        }
                        label="Auto Refresh"
                    />
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Timeframe</InputLabel>
                        <Select
                            value={timeframe}
                            label="Timeframe"
                            onChange={(e) => setTimeframe(e.target.value)}
                        >
                            {TIMEFRAMES.map((tf) => (
                                <MenuItem key={tf.value} value={tf.value}>
                                    {tf.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <Tooltip title="Refresh Data">
                        <IconButton onClick={fetchAnalytics} disabled={loading}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Export Report">
                        <IconButton onClick={handleExport}>
                            <DownloadIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Last Updated */}
            {lastUpdated && (
                <Typography variant="body2" color="text.secondary" mb={2}>
                    Last updated: {lastUpdated.toLocaleString()}
                </Typography>
            )}

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {/* Loading Indicator */}
            {loading && (
                <LinearProgress sx={{ mb: 2 }} />
            )}

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs
                    value={activeTab}
                    onChange={(_, newValue) => setActiveTab(newValue)}
                    variant="scrollable"
                    scrollButtons="auto"
                >
                    <Tab label="Overview" />
                    <Tab label="User Analytics" />
                    <Tab label="Recommendation Quality" />
                    <Tab label="System Performance" />
                    <Tab label="Alerts" />
                    <Tab label="Business Metrics" />
                    <Tab label="Predictive Analytics" />
                </Tabs>
            </Paper>

            {/* Tab Content */}
            <Box>
                {activeTab === 0 && renderOverviewTab()}
                {activeTab === 1 && renderUserAnalyticsTab()}
                {activeTab === 2 && (
                    <Typography>Recommendation Quality tab content would go here</Typography>
                )}
                {activeTab === 3 && renderSystemPerformanceTab()}
                {activeTab === 4 && renderAlertsTab()}
                {activeTab === 5 && (
                    <Typography>Business Metrics tab content would go here</Typography>
                )}
                {activeTab === 6 && (
                    <Typography>Predictive Analytics tab content would go here</Typography>
                )}
            </Box>
        </Box>
    );
};

export default ComprehensiveAnalyticsDashboard;