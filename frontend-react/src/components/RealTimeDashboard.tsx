import React, { useEffect, useState, useCallback } from 'react';
import { safeSlice } from '../utils/numberUtils';
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
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material';
import {
    Refresh,
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
} from '@mui/icons-material';
import { useSystemWebSocket } from '@/hooks/useWebSocket';
import { useAppSelector } from '@/store/hooks';
import { apiClient } from '@/services/api';

interface SystemMetrics {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    network_io_mbps: number;
    active_connections: number;
    active_workflows: number;
    response_time_avg_ms: number;
    error_rate_percent: number;
    cache_hit_rate_percent: number;
    database_connections: number;
}

interface PerformanceAlert {
    id: string;
    type: 'cpu' | 'memory' | 'disk' | 'network' | 'response_time' | 'error_rate';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    value: number;
    threshold: number;
    timestamp: string;
}

interface WorkflowStatus {
    id: string;
    assessment_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    current_step: string;
    started_at: string;
    estimated_completion?: string;
}

export default function RealTimeDashboard() {
    const { user } = useAppSelector(state => state.auth);
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
    const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected');
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const [alertDialogOpen, setAlertDialogOpen] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState<PerformanceAlert | null>(null);

    // WebSocket connection for real-time updates
    const {
        isConnected,
        lastMessage,
        sendTypedMessage,
        error: wsError,
    } = useSystemWebSocket();

    // Update connection status
    useEffect(() => {
        if (isConnected) {
            setConnectionStatus('connected');
        } else if (wsError) {
            setConnectionStatus('disconnected');
        } else {
            setConnectionStatus('reconnecting');
        }
    }, [isConnected, wsError]);

    // Handle WebSocket messages
    useEffect(() => {
        if (lastMessage) {
            try {
                const message = JSON.parse(lastMessage.data);

                switch (message.type) {
                    case 'metrics_update':
                        setMetrics(message.data);
                        setLastUpdate(new Date());
                        break;

                    case 'workflow_progress':
                        setWorkflows(prev => {
                            const existing = prev.find(w => w.id === message.data.workflow_id);
                            if (existing) {
                                return prev.map(w =>
                                    w.id === message.data.workflow_id
                                        ? { ...w, ...message.data }
                                        : w
                                );
                            } else {
                                return [...prev, message.data];
                            }
                        });
                        break;

                    case 'alert':
                        const alert: PerformanceAlert = {
                            id: message.data.alert_id || Date.now().toString(),
                            type: message.data.alert_type,
                            severity: message.data.severity,
                            message: message.data.message,
                            value: message.data.metric_value,
                            threshold: message.data.threshold,
                            timestamp: message.timestamp || new Date().toISOString(),
                        };

                        setAlerts(prev => [alert, ...safeSlice(prev, 0, 9)]); // Keep last 10 alerts
                        break;
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        }
    }, [lastMessage]);

    // Load initial data
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [healthData, metricsData] = await Promise.all([
                    apiClient.checkHealth(),
                    apiClient.getSystemMetrics().catch(() => null),
                ]);

                if (metricsData) {
                    setMetrics(metricsData);
                    setLastUpdate(new Date());
                }
            } catch (error) {
                console.error('Failed to load initial data:', error);
            }
        };

        loadInitialData();
    }, []);

    // Subscribe to real-time updates when connected
    useEffect(() => {
        if (isConnected) {
            sendTypedMessage('subscribe', {
                types: ['metrics_update', 'workflow_progress', 'alert']
            });
        }
    }, [isConnected, sendTypedMessage]);

    const handleRefresh = useCallback(async () => {
        try {
            const metricsData = await apiClient.getSystemMetrics();
            setMetrics(metricsData);
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to refresh metrics:', error);
        }
    }, []);

    type ChipColor = 'success' | 'error' | 'warning' | 'default' | 'primary' | 'secondary' | 'info';

    const getStatusColor = (status: string): ChipColor => {
        switch (status) {
            case 'connected':
                return 'success';
            case 'disconnected':
                return 'error';
            case 'reconnecting':
                return 'warning';
            default:
                return 'default';
        }
    };

    const getSeverityColor = (severity: string): ChipColor => {
        switch (severity) {
            case 'critical':
                return 'error';
            case 'high':
                return 'error';
            case 'medium':
                return 'warning';
            case 'low':
                return 'info';
            default:
                return 'default';
        }
    };

    const getMetricColor = (value: number, thresholds: { warning: number; critical: number }): ChipColor => {
        if (value >= thresholds.critical) return 'error';
        if (value >= thresholds.warning) return 'warning';
        return 'success';
    };

    const formatBytes = (bytes: number) => {
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };

    const formatDuration = (ms: number) => {
        if (!ms || isNaN(ms)) return '0ms';
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    };

    const safeToFixed = (value: number | undefined | null, decimals: number = 1): string => {
        if (value === undefined || value === null || isNaN(value)) return '0';
        return value.toFixed(decimals);
    };

    return (
        <Box>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" gutterBottom>
                    Real-Time System Dashboard
                </Typography>

                <Stack direction="row" spacing={2} alignItems="center">
                    <Chip
                        label={connectionStatus}
                        color={getStatusColor(connectionStatus)}
                        size="small"
                        icon={connectionStatus === 'connected' ? <CheckCircle /> :
                            connectionStatus === 'disconnected' ? <Error /> : <Warning />}
                    />

                    {lastUpdate && (
                        <Typography variant="caption" color="text.secondary">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </Typography>
                    )}

                    <Tooltip title="Refresh">
                        <IconButton onClick={handleRefresh} size="small">
                            <Refresh />
                        </IconButton>
                    </Tooltip>
                </Stack>
            </Box>

            {/* System Metrics Grid */}
            {metrics && (
                <Grid container spacing={3} sx={{ mb: 3 }}>
                    {/* CPU Usage */}
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Stack direction="row" alignItems="center" spacing={1}>
                                    <Speed color="primary" />
                                    <Typography variant="h6">CPU</Typography>
                                </Stack>
                                <Typography variant="h4" color={getMetricColor(metrics.cpu_usage_percent, { warning: 70, critical: 90 })}>
                                    {safeToFixed(metrics.cpu_usage_percent, 1)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={metrics.cpu_usage_percent || 0}
                                    color={getMetricColor(metrics.cpu_usage_percent, { warning: 70, critical: 90 })}
                                    sx={{ mt: 1 }}
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Memory Usage */}
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Stack direction="row" alignItems="center" spacing={1}>
                                    <Memory color="primary" />
                                    <Typography variant="h6">Memory</Typography>
                                </Stack>
                                <Typography variant="h4" color={getMetricColor(metrics.memory_usage_percent, { warning: 80, critical: 95 })}>
                                    {safeToFixed(metrics.memory_usage_percent, 1)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={metrics.memory_usage_percent || 0}
                                    color={getMetricColor(metrics.memory_usage_percent, { warning: 80, critical: 95 })}
                                    sx={{ mt: 1 }}
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Disk Usage */}
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Stack direction="row" alignItems="center" spacing={1}>
                                    <Storage color="primary" />
                                    <Typography variant="h6">Disk</Typography>
                                </Stack>
                                <Typography variant="h4" color={getMetricColor(metrics.disk_usage_percent, { warning: 85, critical: 95 })}>
                                    {safeToFixed(metrics.disk_usage_percent, 1)}%
                                </Typography>
                                <LinearProgress
                                    variant="determinate"
                                    value={metrics.disk_usage_percent || 0}
                                    color={getMetricColor(metrics.disk_usage_percent, { warning: 85, critical: 95 })}
                                    sx={{ mt: 1 }}
                                />
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Network I/O */}
                    <Grid item xs={12} sm={6} md={3}>
                        <Card>
                            <CardContent>
                                <Stack direction="row" alignItems="center" spacing={1}>
                                    <NetworkCheck color="primary" />
                                    <Typography variant="h6">Network</Typography>
                                </Stack>
                                <Typography variant="h4">
                                    {safeToFixed(metrics.network_io_mbps, 1)} Mbps
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    I/O Throughput
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Performance Metrics */}
            {metrics && (
                <Grid container spacing={3} sx={{ mb: 3 }}>
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Performance Metrics
                                </Typography>

                                <Stack spacing={2}>
                                    <Box>
                                        <Stack direction="row" justifyContent="space-between">
                                            <Typography variant="body2">Response Time</Typography>
                                            <Typography variant="body2" fontWeight="bold">
                                                {formatDuration(metrics.response_time_avg_ms)}
                                            </Typography>
                                        </Stack>
                                        <LinearProgress
                                            variant="determinate"
                                            value={Math.min(metrics.response_time_avg_ms / 10, 100) || 0} // Scale to 1s max
                                            color={getMetricColor(metrics.response_time_avg_ms, { warning: 500, critical: 1000 })}
                                        />
                                    </Box>

                                    <Box>
                                        <Stack direction="row" justifyContent="space-between">
                                            <Typography variant="body2">Error Rate</Typography>
                                            <Typography variant="body2" fontWeight="bold">
                                                {safeToFixed(metrics.error_rate_percent, 2)}%
                                            </Typography>
                                        </Stack>
                                        <LinearProgress
                                            variant="determinate"
                                            value={metrics.error_rate_percent || 0}
                                            color={getMetricColor(metrics.error_rate_percent, { warning: 1, critical: 5 })}
                                        />
                                    </Box>

                                    <Box>
                                        <Stack direction="row" justifyContent="space-between">
                                            <Typography variant="body2">Cache Hit Rate</Typography>
                                            <Typography variant="body2" fontWeight="bold">
                                                {safeToFixed(metrics.cache_hit_rate_percent, 1)}%
                                            </Typography>
                                        </Stack>
                                        <LinearProgress
                                            variant="determinate"
                                            value={metrics.cache_hit_rate_percent || 0}
                                            color={metrics.cache_hit_rate_percent > 90 ? 'success' :
                                                metrics.cache_hit_rate_percent > 70 ? 'warning' : 'error'}
                                        />
                                    </Box>
                                </Stack>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    System Activity
                                </Typography>

                                <Stack spacing={2}>
                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                        <Stack direction="row" alignItems="center" spacing={1}>
                                            <People color="primary" />
                                            <Typography variant="body2">Active Connections</Typography>
                                        </Stack>
                                        <Chip label={metrics.active_connections} color="primary" size="small" />
                                    </Stack>

                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                        <Stack direction="row" alignItems="center" spacing={1}>
                                            <Assessment color="primary" />
                                            <Typography variant="body2">Active Workflows</Typography>
                                        </Stack>
                                        <Chip label={metrics.active_workflows} color="secondary" size="small" />
                                    </Stack>

                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                        <Stack direction="row" alignItems="center" spacing={1}>
                                            <Storage color="primary" />
                                            <Typography variant="body2">Database Connections</Typography>
                                        </Stack>
                                        <Chip label={metrics.database_connections} color="info" size="small" />
                                    </Stack>
                                </Stack>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* Active Workflows */}
            {workflows.length > 0 && (
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Active Workflows
                        </Typography>

                        <List>
                            {workflows.map((workflow, index) => (
                                <React.Fragment key={workflow.id}>
                                    <ListItem>
                                        <ListItemIcon>
                                            <Timeline color="primary" />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={`Assessment ${workflow.assessment_id}`}
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {workflow.current_step} - {workflow.progress}% complete
                                                    </Typography>
                                                    <LinearProgress
                                                        variant="determinate"
                                                        value={workflow.progress || 0}
                                                        sx={{ mt: 1, width: '100%' }}
                                                    />
                                                </Box>
                                            }
                                        />
                                        <Chip
                                            label={workflow.status}
                                            color={
                                                workflow.status === 'completed' ? 'success' :
                                                    workflow.status === 'failed' ? 'error' :
                                                        workflow.status === 'running' ? 'primary' : 'default'
                                            }
                                            size="small"
                                        />
                                    </ListItem>
                                    {index < workflows.length - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            )}

            {/* Recent Alerts */}
            {alerts.length > 0 && (
                <Card>
                    <CardContent>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                            <Typography variant="h6">
                                Recent Alerts
                            </Typography>
                            <Badge badgeContent={alerts.length} color="error">
                                <Notifications />
                            </Badge>
                        </Stack>

                        <List>
                            {safeSlice(alerts, 0, 5).map((alert, index) => (
                                <React.Fragment key={alert.id}>
                                    <ListItem
                                        button
                                        onClick={() => {
                                            setSelectedAlert(alert);
                                            setAlertDialogOpen(true);
                                        }}
                                    >
                                        <ListItemIcon>
                                            {alert.severity === 'critical' ? <Error color="error" /> :
                                                alert.severity === 'high' ? <Error color="error" /> :
                                                    alert.severity === 'medium' ? <Warning color="warning" /> :
                                                        <Info color="info" />}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={alert.message}
                                            secondary={
                                                <Stack direction="row" spacing={1} alignItems="center">
                                                    <Chip
                                                        label={alert.severity}
                                                        color={getSeverityColor(alert.severity)}
                                                        size="small"
                                                    />
                                                    <Typography variant="caption">
                                                        {new Date(alert.timestamp).toLocaleTimeString()}
                                                    </Typography>
                                                </Stack>
                                            }
                                        />
                                    </ListItem>
                                    {index < Math.min(alerts.length, 5) - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>

                        {alerts.length > 5 && (
                            <Button
                                fullWidth
                                variant="outlined"
                                sx={{ mt: 2 }}
                                onClick={() => {/* Open full alerts view */ }}
                            >
                                View All {alerts.length} Alerts
                            </Button>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Alert Detail Dialog */}
            <Dialog
                open={alertDialogOpen}
                onClose={() => setAlertDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="h6">Alert Details</Typography>
                        <IconButton onClick={() => setAlertDialogOpen(false)}>
                            <Close />
                        </IconButton>
                    </Stack>
                </DialogTitle>

                {selectedAlert && (
                    <DialogContent>
                        <Stack spacing={2}>
                            <Alert severity={getSeverityColor(selectedAlert.severity) as 'error' | 'warning' | 'info'}>
                                {selectedAlert.message}
                            </Alert>

                            <Box>
                                <Typography variant="subtitle2" gutterBottom>
                                    Alert Information
                                </Typography>
                                <Stack spacing={1}>
                                    <Stack direction="row" justifyContent="space-between">
                                        <Typography variant="body2">Type:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {selectedAlert.type}
                                        </Typography>
                                    </Stack>
                                    <Stack direction="row" justifyContent="space-between">
                                        <Typography variant="body2">Severity:</Typography>
                                        <Chip
                                            label={selectedAlert.severity}
                                            color={getSeverityColor(selectedAlert.severity)}
                                            size="small"
                                        />
                                    </Stack>
                                    <Stack direction="row" justifyContent="space-between">
                                        <Typography variant="body2">Current Value:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {selectedAlert.value}
                                        </Typography>
                                    </Stack>
                                    <Stack direction="row" justifyContent="space-between">
                                        <Typography variant="body2">Threshold:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {selectedAlert.threshold}
                                        </Typography>
                                    </Stack>
                                    <Stack direction="row" justifyContent="space-between">
                                        <Typography variant="body2">Time:</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {new Date(selectedAlert.timestamp).toLocaleString()}
                                        </Typography>
                                    </Stack>
                                </Stack>
                            </Box>
                        </Stack>
                    </DialogContent>
                )}

                <DialogActions>
                    <Button onClick={() => setAlertDialogOpen(false)}>
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
