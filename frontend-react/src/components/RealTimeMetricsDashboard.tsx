import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
    Switch,
    FormControlLabel,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Badge,
    Paper
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Pause as PauseIcon,
    PlayArrow as PlayIcon,
    Settings as SettingsIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    Warning as WarningIcon,
    Error as ErrorIcon,
    CheckCircle as CheckCircleIcon,
    Speed as SpeedIcon,
    Memory as MemoryIcon,
    Storage as StorageIcon,
    NetworkCheck as NetworkIcon,
    Timer as TimerIcon,
    People as PeopleIcon
} from '@mui/icons-material';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface MetricData {
    timestamp: number;
    value: number;
    label?: string;
}

interface SystemHealth {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    network_latency_ms: number;
    error_rate_percent: number;
    active_connections: number;
    response_time_ms: number;
}

interface WorkflowMetrics {
    active_workflows: number;
    completed_workflows: number;
    failed_workflows: number;
    average_duration_ms: number;
    agent_performance: Record<string, {
        success_rate: number;
        avg_response_time: number;
        total_executions: number;
    }>;
}

interface AlertData {
    id: string;
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    timestamp: number;
    resolved: boolean;
}

interface RealTimeMetricsDashboardProps {
    websocket?: WebSocket | null;
    refreshInterval?: number;
    maxDataPoints?: number;
}

const RealTimeMetricsDashboard: React.FC<RealTimeMetricsDashboardProps> = ({
    websocket,
    refreshInterval = 5000,
    maxDataPoints = 50
}) => {
    // State management
    const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(true);
    const [systemHealth, setSystemHealth] = useState<SystemHealth>({
        cpu_usage_percent: 0,
        memory_usage_percent: 0,
        disk_usage_percent: 0,
        network_latency_ms: 0,
        error_rate_percent: 0,
        active_connections: 0,
        response_time_ms: 0
    });

    const [workflowMetrics, setWorkflowMetrics] = useState<WorkflowMetrics>({
        active_workflows: 0,
        completed_workflows: 0,
        failed_workflows: 0,
        average_duration_ms: 0,
        agent_performance: {}
    });

    const [alerts, setAlerts] = useState<AlertData[]>([]);
    const [historicalData, setHistoricalData] = useState<{
        cpu: MetricData[];
        memory: MetricData[];
        responseTime: MetricData[];
        errorRate: MetricData[];
    }>({
        cpu: [],
        memory: [],
        responseTime: [],
        errorRate: []
    });

    const [selectedTimeRange, setSelectedTimeRange] = useState<'5m' | '15m' | '1h' | '6h' | '24h'>('15m');
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

    // WebSocket message handler
    const handleWebSocketMessage = useCallback((event: MessageEvent) => {
        try {
            const message = JSON.parse(event.data);
            const timestamp = Date.now();

            if (message.type === 'metrics_update') {
                const data = message.data;

                // Update system health
                if (data.system_health) {
                    setSystemHealth(data.system_health);

                    // Add to historical data
                    setHistoricalData(prev => ({
                        cpu: [...prev.cpu, { timestamp, value: data.system_health.cpu_usage_percent }].slice(-maxDataPoints),
                        memory: [...prev.memory, { timestamp, value: data.system_health.memory_usage_percent }].slice(-maxDataPoints),
                        responseTime: [...prev.responseTime, { timestamp, value: data.system_health.response_time_ms }].slice(-maxDataPoints),
                        errorRate: [...prev.errorRate, { timestamp, value: data.system_health.error_rate_percent }].slice(-maxDataPoints)
                    }));
                }

                // Update workflow metrics
                if (data.workflow_metrics) {
                    setWorkflowMetrics(data.workflow_metrics);
                }

                setLastUpdate(new Date());
            } else if (message.type === 'alert') {
                // Add new alert
                const alert: AlertData = {
                    id: message.data.alert_id,
                    type: message.data.alert_type,
                    severity: message.data.severity,
                    message: message.data.message,
                    timestamp: new Date(message.timestamp).getTime(),
                    resolved: false
                };

                setAlerts(prev => [alert, ...prev.filter(a => a.id !== alert.id)].slice(0, 20));
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }, [maxDataPoints]);

    // Setup WebSocket listener
    useEffect(() => {
        if (websocket && isRealTimeEnabled) {
            websocket.addEventListener('message', handleWebSocketMessage);

            return () => {
                websocket.removeEventListener('message', handleWebSocketMessage);
            };
        }
    }, [websocket, isRealTimeEnabled, handleWebSocketMessage]);

    // Periodic data refresh
    useEffect(() => {
        if (!isRealTimeEnabled) return;

        const interval = setInterval(async () => {
            try {
                // Fetch latest metrics from API
                const response = await fetch('/api/metrics/current');
                if (response.ok) {
                    const data = await response.json();
                    const timestamp = Date.now();

                    if (data.system_health) {
                        setSystemHealth(data.system_health);

                        setHistoricalData(prev => ({
                            cpu: [...prev.cpu, { timestamp, value: data.system_health.cpu_usage_percent }].slice(-maxDataPoints),
                            memory: [...prev.memory, { timestamp, value: data.system_health.memory_usage_percent }].slice(-maxDataPoints),
                            responseTime: [...prev.responseTime, { timestamp, value: data.system_health.response_time_ms }].slice(-maxDataPoints),
                            errorRate: [...prev.errorRate, { timestamp, value: data.system_health.error_rate_percent }].slice(-maxDataPoints)
                        }));
                    }

                    if (data.workflow_metrics) {
                        setWorkflowMetrics(data.workflow_metrics);
                    }

                    setLastUpdate(new Date());
                }
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
        }, refreshInterval);

        return () => clearInterval(interval);
    }, [isRealTimeEnabled, refreshInterval, maxDataPoints]);

    // Helper functions
    const getHealthColor = (value: number, thresholds: { warning: number; critical: number }) => {
        if (value >= thresholds.critical) return 'error';
        if (value >= thresholds.warning) return 'warning';
        return 'success';
    };

    const formatDuration = (ms: number) => {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    };

    const formatTimestamp = (timestamp: number) => {
        return new Date(timestamp).toLocaleTimeString();
    };

    const getAlertIcon = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <ErrorIcon color="error" />;
            case 'high':
                return <ErrorIcon color="error" />;
            case 'medium':
                return <WarningIcon color="warning" />;
            default:
                return <WarningIcon color="info" />;
        }
    };

    const activeAlerts = useMemo(() => alerts.filter(a => !a.resolved), [alerts]);
    const criticalAlerts = useMemo(() => activeAlerts.filter(a => a.severity === 'critical'), [activeAlerts]);

    // Chart colors
    const chartColors = {
        primary: '#1976d2',
        secondary: '#dc004e',
        success: '#2e7d32',
        warning: '#ed6c02',
        error: '#d32f2f'
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h4" component="h1">
                    Real-Time Metrics Dashboard
                </Typography>

                <Stack direction="row" spacing={2} alignItems="center">
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Time Range</InputLabel>
                        <Select
                            value={selectedTimeRange}
                            label="Time Range"
                            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
                        >
                            <MenuItem value="5m">5 minutes</MenuItem>
                            <MenuItem value="15m">15 minutes</MenuItem>
                            <MenuItem value="1h">1 hour</MenuItem>
                            <MenuItem value="6h">6 hours</MenuItem>
                            <MenuItem value="24h">24 hours</MenuItem>
                        </Select>
                    </FormControl>

                    <FormControlLabel
                        control={
                            <Switch
                                checked={isRealTimeEnabled}
                                onChange={(e) => setIsRealTimeEnabled(e.target.checked)}
                            />
                        }
                        label="Real-time"
                    />

                    <Tooltip title={isRealTimeEnabled ? "Pause updates" : "Resume updates"}>
                        <IconButton onClick={() => setIsRealTimeEnabled(!isRealTimeEnabled)}>
                            {isRealTimeEnabled ? <PauseIcon /> : <PlayIcon />}
                        </IconButton>
                    </Tooltip>

                    <Typography variant="caption" color="text.secondary">
                        Last updated: {lastUpdate.toLocaleTimeString()}
                    </Typography>
                </Stack>
            </Stack>

            {/* Critical Alerts Banner */}
            {criticalAlerts.length > 0 && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    <Typography variant="subtitle1">
                        {criticalAlerts.length} Critical Alert{criticalAlerts.length > 1 ? 's' : ''}
                    </Typography>
                    {criticalAlerts.slice(0, 3).map(alert => (
                        <Typography key={alert.id} variant="body2">
                            • {alert.message}
                        </Typography>
                    ))}
                </Alert>
            )}

            {/* System Health Overview */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" alignItems="center" spacing={2}>
                                <SpeedIcon color={getHealthColor(systemHealth.cpu_usage_percent, { warning: 70, critical: 85 })} />
                                <Box sx={{ flexGrow: 1 }}>
                                    <Typography variant="h6">
                                        {systemHealth.cpu_usage_percent.toFixed(1)}%
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        CPU Usage
                                    </Typography>
                                    <LinearProgress
                                        variant="determinate"
                                        value={systemHealth.cpu_usage_percent}
                                        color={getHealthColor(systemHealth.cpu_usage_percent, { warning: 70, critical: 85 })}
                                        sx={{ mt: 1 }}
                                    />
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" alignItems="center" spacing={2}>
                                <MemoryIcon color={getHealthColor(systemHealth.memory_usage_percent, { warning: 80, critical: 90 })} />
                                <Box sx={{ flexGrow: 1 }}>
                                    <Typography variant="h6">
                                        {systemHealth.memory_usage_percent.toFixed(1)}%
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Memory Usage
                                    </Typography>
                                    <LinearProgress
                                        variant="determinate"
                                        value={systemHealth.memory_usage_percent}
                                        color={getHealthColor(systemHealth.memory_usage_percent, { warning: 80, critical: 90 })}
                                        sx={{ mt: 1 }}
                                    />
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" alignItems="center" spacing={2}>
                                <TimerIcon color={getHealthColor(systemHealth.response_time_ms, { warning: 1000, critical: 3000 })} />
                                <Box sx={{ flexGrow: 1 }}>
                                    <Typography variant="h6">
                                        {formatDuration(systemHealth.response_time_ms)}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Response Time
                                    </Typography>
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" alignItems="center" spacing={2}>
                                <PeopleIcon color="primary" />
                                <Box sx={{ flexGrow: 1 }}>
                                    <Typography variant="h6">
                                        {systemHealth.active_connections}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Active Connections
                                    </Typography>
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                System Performance
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={historicalData.cpu.map((cpu, index) => ({
                                    timestamp: cpu.timestamp,
                                    cpu: cpu.value,
                                    memory: historicalData.memory[index]?.value || 0,
                                    time: formatTimestamp(cpu.timestamp)
                                }))}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="time" />
                                    <YAxis domain={[0, 100]} />
                                    <RechartsTooltip />
                                    <Line
                                        type="monotone"
                                        dataKey="cpu"
                                        stroke={chartColors.primary}
                                        strokeWidth={2}
                                        name="CPU %"
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="memory"
                                        stroke={chartColors.secondary}
                                        strokeWidth={2}
                                        name="Memory %"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Response Time & Error Rate
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={historicalData.responseTime.map((rt, index) => ({
                                    timestamp: rt.timestamp,
                                    responseTime: rt.value,
                                    errorRate: historicalData.errorRate[index]?.value || 0,
                                    time: formatTimestamp(rt.timestamp)
                                }))}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="time" />
                                    <YAxis yAxisId="left" />
                                    <YAxis yAxisId="right" orientation="right" />
                                    <RechartsTooltip />
                                    <Line
                                        yAxisId="left"
                                        type="monotone"
                                        dataKey="responseTime"
                                        stroke={chartColors.warning}
                                        strokeWidth={2}
                                        name="Response Time (ms)"
                                    />
                                    <Line
                                        yAxisId="right"
                                        type="monotone"
                                        dataKey="errorRate"
                                        stroke={chartColors.error}
                                        strokeWidth={2}
                                        name="Error Rate %"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Workflow Metrics and Alerts */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Workflow Status
                            </Typography>

                            <Grid container spacing={2} sx={{ mb: 2 }}>
                                <Grid item xs={4}>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="h4" color="primary">
                                            {workflowMetrics.active_workflows}
                                        </Typography>
                                        <Typography variant="body2">Active</Typography>
                                    </Paper>
                                </Grid>
                                <Grid item xs={4}>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="h4" color="success.main">
                                            {workflowMetrics.completed_workflows}
                                        </Typography>
                                        <Typography variant="body2">Completed</Typography>
                                    </Paper>
                                </Grid>
                                <Grid item xs={4}>
                                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                                        <Typography variant="h4" color="error.main">
                                            {workflowMetrics.failed_workflows}
                                        </Typography>
                                        <Typography variant="body2">Failed</Typography>
                                    </Paper>
                                </Grid>
                            </Grid>

                            <Typography variant="subtitle1" gutterBottom>
                                Agent Performance
                            </Typography>

                            {Object.entries(workflowMetrics.agent_performance).map(([agentName, performance]) => (
                                <Box key={agentName} sx={{ mb: 2 }}>
                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                        <Typography variant="body1">{agentName}</Typography>
                                        <Stack direction="row" spacing={2}>
                                            <Chip
                                                label={`${(performance.success_rate * 100).toFixed(1)}% success`}
                                                color={performance.success_rate > 0.9 ? 'success' : performance.success_rate > 0.7 ? 'warning' : 'error'}
                                                size="small"
                                            />
                                            <Chip
                                                label={`${formatDuration(performance.avg_response_time)} avg`}
                                                variant="outlined"
                                                size="small"
                                            />
                                        </Stack>
                                    </Stack>
                                    <LinearProgress
                                        variant="determinate"
                                        value={performance.success_rate * 100}
                                        color={performance.success_rate > 0.9 ? 'success' : performance.success_rate > 0.7 ? 'warning' : 'error'}
                                        sx={{ mt: 1 }}
                                    />
                                </Box>
                            ))}
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                                <Typography variant="h6">
                                    Active Alerts
                                </Typography>
                                <Badge badgeContent={activeAlerts.length} color="error">
                                    <WarningIcon />
                                </Badge>
                            </Stack>

                            <List dense>
                                {activeAlerts.length === 0 ? (
                                    <ListItem>
                                        <ListItemIcon>
                                            <CheckCircleIcon color="success" />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary="All systems normal"
                                            secondary="No active alerts"
                                        />
                                    </ListItem>
                                ) : (
                                    activeAlerts.slice(0, 10).map((alert) => (
                                        <ListItem key={alert.id}>
                                            <ListItemIcon>
                                                {getAlertIcon(alert.severity)}
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={alert.message}
                                                secondary={`${alert.type} • ${formatTimestamp(alert.timestamp)}`}
                                            />
                                        </ListItem>
                                    ))
                                )}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default RealTimeMetricsDashboard;