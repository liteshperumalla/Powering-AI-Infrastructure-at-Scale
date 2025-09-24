'use client';

import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Alert,
    Card,
    CardContent,
    Chip,
    Grid,
    Button,
    CircularProgress,
} from '@mui/material';
import {
    Refresh,
    MonitorHeart,
    CloudQueue,
} from '@mui/icons-material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ApiTester from '@/components/ApiTester';
import ProtectedRoute from '@/components/ProtectedRoute';
import RoleProtectedRoute from '@/components/RoleProtectedRoute';
import { apiClient } from '@/services/api';

export default function SystemStatusPage() {
    const [systemHealth, setSystemHealth] = useState<any>(null);
    const [systemMetrics, setSystemMetrics] = useState<any>(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState(new Date());

    const loadSystemData = async () => {
        setLoading(true);
        try {
            // Load system health
            const healthData = await apiClient.getSystemHealth();
            setSystemHealth(healthData);

            // Load system metrics
            const metricsData = await apiClient.getSystemMetrics();
            setSystemMetrics(metricsData);

            // Check WebSocket connection
            setWsConnected(true); // You can implement actual WebSocket check here
            
            setLastRefresh(new Date());
        } catch (error) {
            console.error('Failed to load system data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSystemData();
        
        // Auto-refresh every 30 seconds
        const interval = setInterval(loadSystemData, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <ProtectedRoute>
            <RoleProtectedRoute
                allowedRoles={['admin', 'manager']}
                fallbackMessage="System Status is only available to administrators and managers."
            >
                <ResponsiveLayout title="Admin System Status">
                <Container maxWidth="lg" sx={{ mt: 3 }}>
                    <Box sx={{ mb: 4 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <MonitorHeart sx={{ fontSize: 32, color: 'primary.main' }} />
                            <Typography variant="h4" gutterBottom sx={{ mb: 0 }}>
                                Admin System Status
                            </Typography>
                            <Button
                                variant="outlined"
                                size="small"
                                startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
                                onClick={loadSystemData}
                                disabled={loading}
                                sx={{ ml: 'auto' }}
                            >
                                {loading ? 'Refreshing...' : 'Refresh'}
                            </Button>
                        </Box>
                        <Typography variant="body1" color="text.secondary">
                            Monitor system health, active workflows, and test API connectivity across all endpoints.
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Last updated: {lastRefresh.toLocaleTimeString()}
                        </Typography>
                    </Box>

                    {/* System Health Overview */}
                    <Grid container spacing={3} sx={{ mb: 4 }}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <CloudQueue color="primary" />
                                        <Box>
                                            <Typography variant="h6">System Health</Typography>
                                            {systemHealth ? (
                                                <Chip
                                                    label={systemHealth.status || 'Unknown'}
                                                    color={systemHealth.status === 'healthy' ? 'success' : 'error'}
                                                    size="small"
                                                />
                                            ) : (
                                                <Chip label="Loading..." color="default" size="small" />
                                            )}
                                        </Box>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={3}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <MonitorHeart color="primary" />
                                        <Box>
                                            <Typography variant="h6">Active Workflows</Typography>
                                            <Typography variant="h4" color="primary.main">
                                                {systemMetrics?.active_workflows || '0'}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>

                        <Grid item xs={12} sm={6} md={3}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <CloudQueue color="primary" />
                                        <Box>
                                            <Typography variant="h6">WebSocket</Typography>
                                            <Chip
                                                label={wsConnected ? 'Connected' : 'Disconnected'}
                                                color={wsConnected ? 'success' : 'error'}
                                                size="small"
                                            />
                                        </Box>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>

                        <Grid item xs={12} sm={6} md={3}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <MonitorHeart color="primary" />
                                        <Box>
                                            <Typography variant="h6">Database</Typography>
                                            <Chip
                                                label={systemHealth?.database_status || 'Unknown'}
                                                color={systemHealth?.database_status === 'connected' ? 'success' : 'warning'}
                                                size="small"
                                            />
                                        </Box>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>

                    {/* Detailed System Information */}
                    {systemHealth && (
                        <Card sx={{ mb: 4 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    System Details
                                </Typography>
                                <Grid container spacing={2}>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">CPU Usage</Typography>
                                        <Typography variant="body1">{systemHealth.cpu_usage || 'N/A'}%</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">Memory Usage</Typography>
                                        <Typography variant="body1">{systemHealth.memory_usage || 'N/A'}%</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">Disk Usage</Typography>
                                        <Typography variant="body1">{systemHealth.disk_usage || 'N/A'}%</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">Uptime</Typography>
                                        <Typography variant="body1">{systemHealth.uptime || 'N/A'}</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">Load Average</Typography>
                                        <Typography variant="body1">{systemHealth.load_average || 'N/A'}</Typography>
                                    </Grid>
                                    <Grid item xs={12} sm={6} md={4}>
                                        <Typography variant="body2" color="text.secondary">Active Connections</Typography>
                                        <Typography variant="body1">{systemHealth.active_connections || 'N/A'}</Typography>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    )}

                    <Alert severity="info" sx={{ mb: 4 }}>
                        <Typography variant="subtitle2" gutterBottom>Admin Features</Typography>
                        This page provides comprehensive system monitoring and API testing capabilities.
                        Use the API test suite below to diagnose connectivity issues between frontend and backend services.
                    </Alert>

                    <ApiTester />
                </Container>
                </ResponsiveLayout>
            </RoleProtectedRoute>
        </ProtectedRoute>
    );
}