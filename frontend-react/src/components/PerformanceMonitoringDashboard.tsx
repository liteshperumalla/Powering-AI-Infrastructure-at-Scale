/**
 * Performance Monitoring Dashboard Component
 * 
 * Real-time performance monitoring dashboard with alerts, metrics visualization,
 * and system health status.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Alert,
    AlertTitle,
    Chip,
    Button,
    Switch,
    FormControlLabel,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    LinearProgress,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Snackbar
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Warning as WarningIcon,
    Error as ErrorIcon,
    CheckCircle as CheckCircleIcon,
    Settings as SettingsIcon,
    Notifications as NotificationsIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    Timeline as TimelineIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';
import { safeToFixed } from '../utils/numberUtils';

// Types
interface PerformanceMetric {
    name: string;
    value: number;
    unit: string;
    status: 'healthy' | 'warning' | 'critical';
    trend: 'up' | 'down' | 'stable';
    history: Array<{ timestamp: string; value: number }>;
}

interface Alert {
    id: string;
    severity: 'info' | 'warning' | 'critical' | 'emergency';
    metric: string;
    currentValue: number;
    thresholdValue: number;
    message: string;
    timestamp: string;
    acknowledged: boolean;
    acknowledgedBy?: string;
}

interface AlertRule {
    name: string;
    description: string;
    metricName: string;
    warningThreshold: number;
    criticalThreshold: number;
    emergencyThreshold?: number;
    comparisonOperator: string;
    evaluationWindowSeconds: number;
    channels: string[];
    cooldownSeconds: number;
    enabled: boolean;
}

interface DashboardData {
    currentMetrics: Record<string, number>;
    activeAlerts: Alert[];
    monitoringSummary: {
        monitoringActive: boolean;
        activeAlertsCount: number;
        alertRulesCount: number;
        scalingPoliciesCount: number;
        websocketClientsCount: number;
        performanceTrends: Record<string, unknown>;
        lastUpdated: string;
    };
    performanceReport: Record<string, unknown>;
    timestamp: string;
}

interface PerformanceMonitoringDashboardProps {
    assessmentId?: string;
}

const PerformanceMonitoringDashboard: React.FC<PerformanceMonitoringDashboardProps> = ({ assessmentId }) => {
    // State
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
    const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
    const [alertRuleDialogOpen, setAlertRuleDialogOpen] = useState(false);
    const [newAlertRule, setNewAlertRule] = useState<Partial<AlertRule>>({});
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');

    // WebSocket connection for real-time updates
    const {
        isConnected,
        lastMessage,
        sendMessage
    } = useWebSocket({
        url: 'ws://localhost:8000/api/performance/ws'
    });

    // Fetch dashboard data
    const fetchDashboardData = useCallback(async () => {
        if (!assessmentId) {
            setLoading(false);
            return;
        }

        try {
            // Use apiClient for authenticated requests
            const { apiClient } = await import('@/services/api');
            const apiResponse = await apiClient.get<any>(`/features/assessment/${assessmentId}/performance`);

            // Transform API response to match component's expected structure
            const transformedData: DashboardData = {
                currentMetrics: {
                    'response_time': apiResponse.metrics?.response_time?.current || 0,
                    'throughput': apiResponse.metrics?.throughput?.requests_per_second || 0,
                    'error_rate': apiResponse.metrics?.error_rate?.percentage || 0,
                    'uptime': apiResponse.summary?.uptime_percentage || 0,
                    'cpu_usage': 45, // Mock data
                    'memory_usage': 60, // Mock data
                },
                activeAlerts: (apiResponse.alerts || []).map((alert: any) => ({
                    id: alert.id,
                    severity: alert.severity as 'info' | 'warning' | 'critical' | 'emergency',
                    metric: alert.title,
                    currentValue: 0,
                    thresholdValue: 0,
                    message: alert.description,
                    timestamp: alert.timestamp,
                    acknowledged: false,
                })),
                monitoringSummary: {
                    monitoringActive: true,
                    activeAlertsCount: apiResponse.summary?.active_alerts || 0,
                    alertRulesCount: 0,
                    scalingPoliciesCount: 0,
                    websocketClientsCount: 0,
                    performanceTrends: {},
                    lastUpdated: apiResponse.generated_at || new Date().toISOString(),
                },
                performanceReport: apiResponse.summary || {},
                timestamp: apiResponse.generated_at || new Date().toISOString(),
            };

            setDashboardData(transformedData);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
        } finally {
            setLoading(false);
        }
    }, [assessmentId]);

    // Handle WebSocket messages
    useEffect(() => {
        if (lastMessage) {
            try {
                // Ensure lastMessage is a string before parsing
                const messageString = typeof lastMessage === 'string' ? lastMessage : JSON.stringify(lastMessage);
                const message = JSON.parse(messageString);

                switch (message.type) {
                    case 'metrics':
                        if (dashboardData) {
                            setDashboardData(prev => prev ? {
                                ...prev,
                                currentMetrics: message.data,
                                timestamp: message.timestamp
                            } : null);
                        }
                        break;

                    case 'alert':
                        if (dashboardData) {
                            setDashboardData(prev => prev ? {
                                ...prev,
                                activeAlerts: [...prev.activeAlerts, message.data]
                            } : null);
                        }
                        setSnackbarMessage(`New alert: ${message.data.message}`);
                        setSnackbarOpen(true);
                        break;

                    case 'recommendations':
                        setSnackbarMessage('New performance recommendations available');
                        setSnackbarOpen(true);
                        break;
                }
            } catch (err) {
                console.error('Error parsing WebSocket message:', err);
            }
        }
    }, [lastMessage, dashboardData]);

    // Auto-refresh effect
    useEffect(() => {
        if (autoRefresh) {
            const interval = setInterval(fetchDashboardData, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, refreshInterval, fetchDashboardData]);

    // Initial data fetch
    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    // Request real-time metrics via WebSocket
    useEffect(() => {
        if (isConnected) {
            const interval = setInterval(() => {
                sendMessage(JSON.stringify({ type: 'get_metrics' }));
            }, 10000); // Every 10 seconds

            return () => clearInterval(interval);
        }
    }, [isConnected, sendMessage]);

    // Process metrics for display
    const processedMetrics = useMemo(() => {
        if (!dashboardData || !dashboardData.currentMetrics) return [];

        const metrics: PerformanceMetric[] = [];

        Object.entries(dashboardData.currentMetrics || {}).forEach(([name, value]) => {
            let status: 'healthy' | 'warning' | 'critical' = 'healthy';
            let unit = '';

            // Determine status and unit based on metric name
            if (name.includes('cpu') || name.includes('memory') || name.includes('disk')) {
                unit = '%';
                if (value > 90) status = 'critical';
                else if (value > 75) status = 'warning';
            } else if (name.includes('response_time')) {
                unit = 'ms';
                if (value > 5000) status = 'critical';
                else if (value > 2000) status = 'warning';
            } else if (name.includes('error_rate')) {
                unit = '%';
                if (value > 10) status = 'critical';
                else if (value > 5) status = 'warning';
            }

            // Determine trend (simplified)
            const trend = dashboardData.monitoringSummary?.performanceTrends?.[name];
            let trendDirection: 'up' | 'down' | 'stable' = 'stable';
            if (trend && typeof trend === 'object' && 'direction' in trend) {
                const direction = (trend as any).direction;
                trendDirection = direction === 'increasing' ? 'up' :
                    direction === 'decreasing' ? 'down' : 'stable';
            }

            metrics.push({
                name: name.replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                value,
                unit,
                status,
                trend: trendDirection,
                history: [] // Would be populated with historical data
            });
        });

        return metrics;
    }, [dashboardData]);

    // Acknowledge alert
    const acknowledgeAlert = async (alertId: string) => {
        try {
            const response = await fetch(`/api/v1/performance/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                setSnackbarMessage('Alert acknowledged successfully');
                setSnackbarOpen(true);
                fetchDashboardData(); // Refresh data
            }
        } catch (err) {
            setSnackbarMessage('Failed to acknowledge alert');
            setSnackbarOpen(true);
        }
    };

    // Create alert rule
    const createAlertRule = async () => {
        try {
            const response = await fetch('/api/v1/performance/alert-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newAlertRule)
            });

            if (response.ok) {
                setSnackbarMessage('Alert rule created successfully');
                setSnackbarOpen(true);
                setAlertRuleDialogOpen(false);
                setNewAlertRule({});
                fetchDashboardData();
            }
        } catch (err) {
            setSnackbarMessage('Failed to create alert rule');
            setSnackbarOpen(true);
        }
    };

    type ChipColor = 'success' | 'warning' | 'error' | 'default';

    // Get status color
    const getStatusColor = (status: string): ChipColor => {
        switch (status) {
            case 'healthy': return 'success';
            case 'warning': return 'warning';
            case 'critical': return 'error';
            default: return 'default';
        }
    };

    // Get alert severity color
    const getAlertSeverityColor = (severity: string): ChipColor | 'info' => {
        switch (severity) {
            case 'info': return 'info';
            case 'warning': return 'warning';
            case 'critical': return 'error';
            case 'emergency': return 'error';
            default: return 'default';
        }
    };

    if (loading) {
        return (
            <Box sx={{ p: 3 }}>
                <Typography variant="h4" gutterBottom>Performance Monitoring</Typography>
                <LinearProgress />
                <Typography sx={{ mt: 2 }}>Loading performance data...</Typography>
            </Box>
        );
    }

    if (!assessmentId) {
        // Import AssessmentSelector dynamically to avoid circular dependencies
        const AssessmentSelector = require('./AssessmentSelector').default;
        return (
            <AssessmentSelector
                redirectPath="/performance"
                title="Select Assessment for Performance Monitoring"
                description="Choose an assessment to view performance monitoring data"
            />
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error">
                    <AlertTitle>Error Loading Performance Data</AlertTitle>
                    {error}
                </Alert>
                <Button onClick={fetchDashboardData} sx={{ mt: 2 }}>
                    Retry
                </Button>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4">Performance Monitoring</Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <Chip
                        icon={isConnected ? <CheckCircleIcon /> : <ErrorIcon />}
                        label={isConnected ? 'Connected' : 'Disconnected'}
                        color={isConnected ? 'success' : 'error'}
                        size="small"
                    />
                    <FormControlLabel
                        control={
                            <Switch
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                            />
                        }
                        label="Auto Refresh"
                    />
                    <IconButton onClick={fetchDashboardData} disabled={loading}>
                        <RefreshIcon />
                    </IconButton>
                    <Button
                        startIcon={<SettingsIcon />}
                        onClick={() => setAlertRuleDialogOpen(true)}
                    >
                        Alert Rules
                    </Button>
                </Box>
            </Box>

            {/* System Health Overview */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>System Health</Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {(dashboardData?.monitoringSummary?.activeAlertsCount ?? 0) === 0 ? (
                                    <>
                                        <CheckCircleIcon color="success" />
                                        <Typography color="success.main">Healthy</Typography>
                                    </>
                                ) : (
                                    <>
                                        <WarningIcon color="warning" />
                                        <Typography color="warning.main">
                                            {dashboardData?.monitoringSummary?.activeAlertsCount ?? 0} Alert(s)
                                        </Typography>
                                    </>
                                )}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Monitoring Status</Typography>
                            <Chip
                                label={dashboardData?.monitoringSummary?.monitoringActive ? 'Active' : 'Inactive'}
                                color={dashboardData?.monitoringSummary?.monitoringActive ? 'success' : 'error'}
                            />
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Alert Rules</Typography>
                            <Typography variant="h4">
                                {dashboardData?.monitoringSummary?.alertRulesCount || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Connected Clients</Typography>
                            <Typography variant="h4">
                                {dashboardData?.monitoringSummary?.websocketClientsCount || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Performance Metrics */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                {processedMetrics.map((metric) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={metric.name}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                        {metric.name}
                                    </Typography>
                                    {metric.trend === 'up' && <TrendingUpIcon color="error" fontSize="small" />}
                                    {metric.trend === 'down' && <TrendingDownIcon color="success" fontSize="small" />}
                                    {metric.trend === 'stable' && <TimelineIcon color="action" fontSize="small" />}
                                </Box>

                                <Typography variant="h4" sx={{ mb: 1 }}>
                                    {safeToFixed(metric.value, 1)}{metric.unit}
                                </Typography>

                                <Chip
                                    size="small"
                                    label={metric.status}
                                    color={getStatusColor(metric.status)}
                                />

                                {/* Mini chart would go here */}
                                <Box sx={{ height: 40, mt: 2 }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={metric.history}>
                                            <Area
                                                type="monotone"
                                                dataKey="value"
                                                stroke={metric.status === 'critical' ? '#f44336' : metric.status === 'warning' ? '#ff9800' : '#4caf50'}
                                                fill={metric.status === 'critical' ? '#f44336' : metric.status === 'warning' ? '#ff9800' : '#4caf50'}
                                                fillOpacity={0.3}
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Active Alerts */}
            {dashboardData?.activeAlerts && dashboardData.activeAlerts.length > 0 && (
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <NotificationsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Active Alerts
                        </Typography>

                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Severity</TableCell>
                                        <TableCell>Metric</TableCell>
                                        <TableCell>Current Value</TableCell>
                                        <TableCell>Threshold</TableCell>
                                        <TableCell>Message</TableCell>
                                        <TableCell>Time</TableCell>
                                        <TableCell>Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {dashboardData.activeAlerts.map((alert) => (
                                        <TableRow key={alert.id}>
                                            <TableCell>
                                                <Chip
                                                    size="small"
                                                    label={alert.severity.toUpperCase()}
                                                    color={getAlertSeverityColor(alert.severity)}
                                                />
                                            </TableCell>
                                            <TableCell>{alert.metric}</TableCell>
                                            <TableCell>{safeToFixed(alert.currentValue, 2)}</TableCell>
                                            <TableCell>{safeToFixed(alert.thresholdValue, 2)}</TableCell>
                                            <TableCell>{alert.message}</TableCell>
                                            <TableCell>
                                                {new Date(alert.timestamp).toLocaleString()}
                                            </TableCell>
                                            <TableCell>
                                                {!alert.acknowledged && (
                                                    <Button
                                                        size="small"
                                                        onClick={() => acknowledgeAlert(alert.id)}
                                                    >
                                                        Acknowledge
                                                    </Button>
                                                )}
                                                {alert.acknowledged && (
                                                    <Typography variant="caption" color="text.secondary">
                                                        Acknowledged by {alert.acknowledgedBy}
                                                    </Typography>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}

            {/* Performance Chart */}
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">Performance Trends</Typography>
                        <FormControl size="small">
                            <InputLabel>Time Range</InputLabel>
                            <Select
                                value={selectedTimeRange}
                                onChange={(e) => setSelectedTimeRange(e.target.value)}
                                label="Time Range"
                            >
                                <MenuItem value="1h">Last Hour</MenuItem>
                                <MenuItem value="6h">Last 6 Hours</MenuItem>
                                <MenuItem value="24h">Last 24 Hours</MenuItem>
                                <MenuItem value="7d">Last 7 Days</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>

                    <Box sx={{ height: 300 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={[]}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="timestamp" />
                                <YAxis />
                                <RechartsTooltip />
                                <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                                <Line type="monotone" dataKey="memory" stroke="#82ca9d" name="Memory %" />
                                <Line type="monotone" dataKey="responseTime" stroke="#ffc658" name="Response Time (ms)" />
                            </LineChart>
                        </ResponsiveContainer>
                    </Box>
                </CardContent>
            </Card>

            {/* Alert Rule Dialog */}
            <Dialog open={alertRuleDialogOpen} onClose={() => setAlertRuleDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Create Alert Rule</DialogTitle>
                <DialogContent>
                    <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                fullWidth
                                label="Rule Name"
                                value={newAlertRule.name || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, name: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                fullWidth
                                label="Metric Name"
                                value={newAlertRule.metricName || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, metricName: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Description"
                                multiline
                                rows={2}
                                value={newAlertRule.description || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, description: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                label="Warning Threshold"
                                type="number"
                                value={newAlertRule.warningThreshold || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, warningThreshold: parseFloat(e.target.value) })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                label="Critical Threshold"
                                type="number"
                                value={newAlertRule.criticalThreshold || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, criticalThreshold: parseFloat(e.target.value) })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                label="Emergency Threshold"
                                type="number"
                                value={newAlertRule.emergencyThreshold || ''}
                                onChange={(e) => setNewAlertRule({ ...newAlertRule, emergencyThreshold: parseFloat(e.target.value) })}
                            />
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setAlertRuleDialogOpen(false)}>Cancel</Button>
                    <Button onClick={createAlertRule} variant="contained">Create</Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbarOpen}
                autoHideDuration={6000}
                onClose={() => setSnackbarOpen(false)}
                message={snackbarMessage}
            />
        </Box>
    );
};

export default PerformanceMonitoringDashboard;