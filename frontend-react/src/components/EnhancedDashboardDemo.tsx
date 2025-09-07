'use client';

import React, { useState, useMemo } from 'react';
import {
    Box,
    Grid,
    Typography,
    Card,
    CardContent,
    Stack,
    Chip,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Divider,
} from '@mui/material';
import {
    TrendingUp,
    Assessment,
    CloudQueue,
    AttachMoney,
    Speed,
    Security,
} from '@mui/icons-material';
import InteractiveCharts from './InteractiveCharts';
import { useBackgroundSync } from '../services/backgroundSync';

// Sample data for different chart types
const generateSampleData = (type: string) => {
    const baseData = [
        { name: 'Jan', value: 400, category: 'AWS', timestamp: '2024-01-01' },
        { name: 'Feb', value: 300, category: 'Azure', timestamp: '2024-02-01' },
        { name: 'Mar', value: 500, category: 'GCP', timestamp: '2024-03-01' },
        { name: 'Apr', value: 280, category: 'AWS', timestamp: '2024-04-01' },
        { name: 'May', value: 590, category: 'Azure', timestamp: '2024-05-01' },
        { name: 'Jun', value: 320, category: 'GCP', timestamp: '2024-06-01' },
        { name: 'Jul', value: 450, category: 'AWS', timestamp: '2024-07-01' },
        { name: 'Aug', value: 380, category: 'Azure', timestamp: '2024-08-01' },
        { name: 'Sep', value: 520, category: 'GCP', timestamp: '2024-09-01' },
        { name: 'Oct', value: 410, category: 'AWS', timestamp: '2024-10-01' },
        { name: 'Nov', value: 460, category: 'Azure', timestamp: '2024-11-01' },
        { name: 'Dec', value: 520, category: 'GCP', timestamp: '2024-12-01' },
    ];

    switch (type) {
        case 'cost':
            return baseData.map(item => ({ ...item, value: item.value * 100 }));
        case 'performance':
            return baseData.map(item => ({ ...item, value: Math.random() * 100 }));
        case 'security':
            return baseData.map(item => ({ ...item, value: Math.floor(Math.random() * 10) }));
        default:
            return baseData;
    }
};

const chartConfigs = [
    {
        id: 'cost-analysis',
        type: 'line' as const,
        title: 'Monthly Cost Analysis',
        data: generateSampleData('cost'),
        icon: <AttachMoney />,
        color: '#4caf50',
    },
    {
        id: 'performance-metrics',
        type: 'area' as const,
        title: 'Performance Metrics',
        data: generateSampleData('performance'),
        icon: <Speed />,
        color: '#2196f3',
    },
    {
        id: 'security-events',
        type: 'bar' as const,
        title: 'Security Events',
        data: generateSampleData('security'),
        icon: <Security />,
        color: '#f44336',
    },
    {
        id: 'provider-distribution',
        type: 'pie' as const,
        title: 'Cloud Provider Distribution',
        data: [
            { name: 'AWS', value: 45, category: 'cloud' },
            { name: 'Azure', value: 30, category: 'cloud' },
            { name: 'GCP', value: 25, category: 'cloud' },
        ],
        icon: <CloudQueue />,
        color: '#ff9800',
    },
];

const EnhancedDashboardDemo: React.FC = () => {
    const [selectedTimeRange, setSelectedTimeRange] = useState('1month');
    const [selectedProvider, setSelectedProvider] = useState('all');
    
    const { isOnline, isSyncing, queueLength } = useBackgroundSync();

    // Filter data based on selections
    const filteredChartConfigs = useMemo(() => {
        return chartConfigs.map(config => {
            let filteredData = config.data;
            
            if (selectedProvider !== 'all') {
                filteredData = filteredData.filter(item => 
                    item.category === selectedProvider
                );
            }
            
            // Apply time range filter (simplified)
            if (selectedTimeRange === '1week') {
                filteredData = filteredData.slice(-7);
            } else if (selectedTimeRange === '1month') {
                filteredData = filteredData.slice(-30);
            }
            
            return {
                ...config,
                data: filteredData,
            };
        });
    }, [selectedTimeRange, selectedProvider]);

    const handleChartDataClick = (chartId: string, data: any) => {
        console.log(`Clicked on ${chartId}:`, data);
        // Here you could open a drill-down modal, navigate to details, etc.
    };

    const handleFilterChange = (chartId: string, filters: any) => {
        console.log(`Filters changed for ${chartId}:`, filters);
        // Handle filter changes for individual charts
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Dashboard Header */}
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <div>
                    <Typography variant="h4" fontWeight={600} sx={{ mb: 1 }}>
                        Enhanced Analytics Dashboard
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Interactive charts with real-time data visualization
                    </Typography>
                </div>
                
                {/* Sync Status */}
                <Stack direction="row" spacing={2} alignItems="center">
                    <Chip
                        icon={<TrendingUp />}
                        label={
                            isSyncing ? 'Syncing...' : 
                            !isOnline ? 'Offline' :
                            queueLength > 0 ? `${queueLength} pending` :
                            'Live Data'
                        }
                        color={
                            isSyncing ? 'primary' :
                            !isOnline ? 'error' :
                            queueLength > 0 ? 'warning' :
                            'success'
                        }
                        variant="outlined"
                    />
                </Stack>
            </Stack>

            {/* Global Filters */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                        Dashboard Filters
                    </Typography>
                    <Stack direction="row" spacing={2}>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Time Range</InputLabel>
                            <Select
                                value={selectedTimeRange}
                                label="Time Range"
                                onChange={(e) => setSelectedTimeRange(e.target.value)}
                            >
                                <MenuItem value="1week">Last Week</MenuItem>
                                <MenuItem value="1month">Last Month</MenuItem>
                                <MenuItem value="3months">Last 3 Months</MenuItem>
                                <MenuItem value="1year">Last Year</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Provider</InputLabel>
                            <Select
                                value={selectedProvider}
                                label="Provider"
                                onChange={(e) => setSelectedProvider(e.target.value)}
                            >
                                <MenuItem value="all">All Providers</MenuItem>
                                <MenuItem value="AWS">AWS</MenuItem>
                                <MenuItem value="Azure">Azure</MenuItem>
                                <MenuItem value="GCP">Google Cloud</MenuItem>
                            </Select>
                        </FormControl>
                    </Stack>
                </CardContent>
            </Card>

            {/* Interactive Charts Grid */}
            <Grid container spacing={3}>
                {filteredChartConfigs.map((config, index) => (
                    <Grid item xs={12} lg={6} key={config.id}>
                        <InteractiveCharts
                            config={{
                                type: config.type,
                                title: config.title,
                                data: config.data,
                                colors: [config.color],
                                interactive: true,
                                clickable: true,
                                zoomable: true,
                                showLegend: true,
                                showGrid: true,
                                showTooltip: true,
                                showBrush: config.type !== 'pie',
                            }}
                            height={400}
                            onDataClick={(data) => handleChartDataClick(config.id, data)}
                            onFilterChange={(filters) => handleFilterChange(config.id, filters)}
                            exportable={true}
                            fullscreenMode={false}
                        />
                    </Grid>
                ))}
            </Grid>

            {/* Feature Highlights */}
            <Card sx={{ mt: 3 }}>
                <CardContent>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                        🚀 Enhanced Features Demonstrated
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12} md={4}>
                            <Stack spacing={1}>
                                <Typography variant="subtitle2" color="primary">
                                    📊 Interactive Charts
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    • Click data points for details
                                    • Filter by categories
                                    • Multiple chart types (line, bar, pie, area)
                                    • Fullscreen mode
                                    • Export functionality (CSV, JSON)
                                </Typography>
                            </Stack>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Stack spacing={1}>
                                <Typography variant="subtitle2" color="primary">
                                    🔔 Live Notifications
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    • Real-time WebSocket notifications
                                    • Sound alerts (when enabled)
                                    • Desktop notifications
                                    • Categorized by priority
                                    • Progress tracking
                                </Typography>
                            </Stack>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Stack spacing={1}>
                                <Typography variant="subtitle2" color="primary">
                                    🔄 Background Sync
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    • Offline-first architecture
                                    • Queue management
                                    • Automatic retry with backoff
                                    • Real-time sync status
                                    • Data integrity protection
                                </Typography>
                            </Stack>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        </Box>
    );
};

export default EnhancedDashboardDemo;