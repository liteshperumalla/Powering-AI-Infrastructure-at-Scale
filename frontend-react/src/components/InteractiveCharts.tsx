'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Stack,
    ToggleButton,
    ToggleButtonGroup,
    IconButton,
    Menu,
    Popover,
    Slider,
    Switch,
    FormControlLabel,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Tooltip,
    Paper,
    Divider,
} from '@mui/material';
import {
    FilterList as FilterIcon,
    Download as DownloadIcon,
    Fullscreen as FullscreenIcon,
    Refresh as RefreshIcon,
    ZoomIn as ZoomInIcon,
    ZoomOut as ZoomOutIcon,
    Settings as SettingsIcon,
    Timeline as TimelineIcon,
    BarChart as BarChartIcon,
    PieChart as PieChartIcon,
    ShowChart as LineChartIcon,
    Close as CloseIcon,
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
    ResponsiveContainer,
    Brush,
    ReferenceLine,
    ComposedChart,
    Scatter,
    ScatterChart,
} from 'recharts';
import { useTheme } from '@mui/material/styles';

interface DataPoint {
    name: string;
    value: number;
    category?: string;
    timestamp?: string;
    [key: string]: any;
}

interface ChartConfig {
    type: 'line' | 'area' | 'bar' | 'pie' | 'scatter' | 'composed';
    title: string;
    data: DataPoint[];
    xAxis?: string;
    yAxis?: string[];
    colors?: string[];
    showLegend?: boolean;
    showGrid?: boolean;
    showTooltip?: boolean;
    showBrush?: boolean;
    interactive?: boolean;
    clickable?: boolean;
    zoomable?: boolean;
}

interface FilterConfig {
    dateRange?: [string, string];
    categories?: string[];
    valueRange?: [number, number];
    customFilters?: Record<string, any>;
}

interface InteractiveChartsProps {
    config: ChartConfig;
    height?: number;
    onDataClick?: (data: DataPoint) => void;
    onFilterChange?: (filters: FilterConfig) => void;
    exportable?: boolean;
    fullscreenMode?: boolean;
}

const InteractiveCharts: React.FC<InteractiveChartsProps> = ({
    config,
    height = 400,
    onDataClick,
    onFilterChange,
    exportable = true,
    fullscreenMode = false,
}) => {
    const theme = useTheme();
    const [filters, setFilters] = useState<FilterConfig>({});
    const [chartType, setChartType] = useState<ChartConfig['type']>(config.type);
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [dateRange, setDateRange] = useState<[number, number]>([0, 100]);
    const [showSettings, setShowSettings] = useState(false);
    const [fullscreen, setFullscreen] = useState(fullscreenMode);
    const [zoomDomain, setZoomDomain] = useState<{x?: [number, number], y?: [number, number]}>({});
    
    // Anchors for menus
    const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);
    const [settingsMenuAnchor, setSettingsMenuAnchor] = useState<null | HTMLElement>(null);

    // Chart settings
    const [chartSettings, setChartSettings] = useState({
        showGrid: config.showGrid ?? true,
        showLegend: config.showLegend ?? true,
        showTooltip: config.showTooltip ?? true,
        showBrush: config.showBrush ?? false,
        animated: true,
        smoothLines: true,
    });

    // Get unique categories from data
    const categories = useMemo(() => {
        return Array.from(new Set(config.data.map(d => d.category).filter(Boolean)));
    }, [config.data]);

    // Filter data based on current filters
    const filteredData = useMemo(() => {
        return config.data.filter(item => {
            // Category filter
            if (selectedCategories.length > 0 && !selectedCategories.includes(item.category || '')) {
                return false;
            }
            
            // Date range filter (assuming data has timestamp or index)
            if (filters.dateRange) {
                const itemDate = new Date(item.timestamp || 0).getTime();
                const [startDate, endDate] = filters.dateRange.map(d => new Date(d).getTime());
                if (itemDate < startDate || itemDate > endDate) {
                    return false;
                }
            }
            
            // Value range filter
            if (filters.valueRange) {
                const [min, max] = filters.valueRange;
                if (item.value < min || item.value > max) {
                    return false;
                }
            }
            
            return true;
        });
    }, [config.data, selectedCategories, filters]);

    // Color palette
    const colors = config.colors || [
        theme.palette.primary.main,
        theme.palette.secondary.main,
        theme.palette.error.main,
        theme.palette.warning.main,
        theme.palette.success.main,
        theme.palette.info.main,
    ];

    // Handle data point clicks
    const handleDataClick = useCallback((data: any) => {
        if (config.clickable && onDataClick) {
            onDataClick(data);
        }
    }, [config.clickable, onDataClick]);

    // Export chart data
    const exportData = useCallback((format: 'csv' | 'json' | 'image') => {
        const dataToExport = filteredData;
        
        switch (format) {
            case 'csv':
                const csvHeaders = Object.keys(dataToExport[0] || {}).join(',');
                const csvData = dataToExport.map(row => 
                    Object.values(row).map(val => `"${val}"`).join(',')
                ).join('\n');
                const csvContent = `${csvHeaders}\n${csvData}`;
                downloadFile(csvContent, `${config.title}.csv`, 'text/csv');
                break;
                
            case 'json':
                const jsonContent = JSON.stringify(dataToExport, null, 2);
                downloadFile(jsonContent, `${config.title}.json`, 'application/json');
                break;
                
            case 'image':
                // This would need canvas export functionality
                console.log('Image export not implemented yet');
                break;
        }
    }, [filteredData, config.title]);

    const downloadFile = (content: string, filename: string, contentType: string) => {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    // Render chart based on type
    const renderChart = () => {
        const commonProps = {
            data: filteredData,
            onClick: handleDataClick,
            margin: { top: 20, right: 30, left: 20, bottom: 20 },
        };

        switch (chartType) {
            case 'line':
                return (
                    <LineChart {...commonProps}>
                        {chartSettings.showGrid && <CartesianGrid strokeDasharray="3 3" />}
                        <XAxis dataKey={config.xAxis || 'name'} />
                        <YAxis />
                        {chartSettings.showTooltip && <RechartsTooltip />}
                        {chartSettings.showLegend && <Legend />}
                        {config.yAxis?.map((key, index) => (
                            <Line
                                key={key}
                                type={chartSettings.smoothLines ? 'monotone' : 'linear'}
                                dataKey={key}
                                stroke={colors[index % colors.length]}
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                                animationDuration={chartSettings.animated ? 1000 : 0}
                            />
                        )) || (
                            <Line
                                type={chartSettings.smoothLines ? 'monotone' : 'linear'}
                                dataKey="value"
                                stroke={colors[0]}
                                strokeWidth={2}
                                dot={{ r: 4 }}
                                activeDot={{ r: 6 }}
                                animationDuration={chartSettings.animated ? 1000 : 0}
                            />
                        )}
                        {chartSettings.showBrush && <Brush dataKey="name" height={30} />}
                    </LineChart>
                );

            case 'area':
                return (
                    <AreaChart {...commonProps}>
                        {chartSettings.showGrid && <CartesianGrid strokeDasharray="3 3" />}
                        <XAxis dataKey={config.xAxis || 'name'} />
                        <YAxis />
                        {chartSettings.showTooltip && <RechartsTooltip />}
                        {chartSettings.showLegend && <Legend />}
                        <Area
                            type={chartSettings.smoothLines ? 'monotone' : 'linear'}
                            dataKey="value"
                            stroke={colors[0]}
                            fill={colors[0]}
                            fillOpacity={0.3}
                            animationDuration={chartSettings.animated ? 1000 : 0}
                        />
                        {chartSettings.showBrush && <Brush dataKey="name" height={30} />}
                    </AreaChart>
                );

            case 'bar':
                return (
                    <BarChart {...commonProps}>
                        {chartSettings.showGrid && <CartesianGrid strokeDasharray="3 3" />}
                        <XAxis dataKey={config.xAxis || 'name'} />
                        <YAxis />
                        {chartSettings.showTooltip && <RechartsTooltip />}
                        {chartSettings.showLegend && <Legend />}
                        <Bar
                            dataKey="value"
                            fill={colors[0]}
                            radius={[4, 4, 0, 0]}
                            animationDuration={chartSettings.animated ? 1000 : 0}
                        />
                        {chartSettings.showBrush && <Brush dataKey="name" height={30} />}
                    </BarChart>
                );

            case 'pie':
                return (
                    <PieChart {...commonProps}>
                        <Pie
                            data={filteredData}
                            cx="50%"
                            cy="50%"
                            outerRadius={120}
                            fill={colors[0]}
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            animationDuration={chartSettings.animated ? 1000 : 0}
                        >
                            {filteredData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                            ))}
                        </Pie>
                        {chartSettings.showTooltip && <RechartsTooltip />}
                        {chartSettings.showLegend && <Legend />}
                    </PieChart>
                );

            case 'scatter':
                return (
                    <ScatterChart {...commonProps}>
                        {chartSettings.showGrid && <CartesianGrid strokeDasharray="3 3" />}
                        <XAxis dataKey={config.xAxis || 'name'} />
                        <YAxis />
                        {chartSettings.showTooltip && <RechartsTooltip />}
                        {chartSettings.showLegend && <Legend />}
                        <Scatter
                            data={filteredData}
                            fill={colors[0]}
                            animationDuration={chartSettings.animated ? 1000 : 0}
                        />
                    </ScatterChart>
                );

            default:
                return null;
        }
    };

    return (
        <Card sx={{ height: fullscreen ? '100vh' : 'auto' }}>
            <CardContent sx={{ p: 2 }}>
                {/* Chart Header */}
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                    <Typography variant="h6" component="h2">
                        {config.title}
                    </Typography>
                    
                    <Stack direction="row" spacing={1}>
                        {/* Chart Type Toggle */}
                        <ToggleButtonGroup
                            value={chartType}
                            exclusive
                            onChange={(e, newType) => newType && setChartType(newType)}
                            size="small"
                        >
                            <ToggleButton value="line">
                                <Tooltip title="Line Chart">
                                    <LineChartIcon />
                                </Tooltip>
                            </ToggleButton>
                            <ToggleButton value="bar">
                                <Tooltip title="Bar Chart">
                                    <BarChartIcon />
                                </Tooltip>
                            </ToggleButton>
                            <ToggleButton value="pie">
                                <Tooltip title="Pie Chart">
                                    <PieChartIcon />
                                </Tooltip>
                            </ToggleButton>
                        </ToggleButtonGroup>

                        <Divider orientation="vertical" flexItem />

                        {/* Filter Button */}
                        <Tooltip title="Filters">
                            <IconButton
                                size="small"
                                onClick={(e) => setFilterMenuAnchor(e.currentTarget)}
                                color={selectedCategories.length > 0 ? 'primary' : 'default'}
                            >
                                <FilterIcon />
                            </IconButton>
                        </Tooltip>

                        {/* Settings Button */}
                        <Tooltip title="Chart Settings">
                            <IconButton
                                size="small"
                                onClick={(e) => setSettingsMenuAnchor(e.currentTarget)}
                            >
                                <SettingsIcon />
                            </IconButton>
                        </Tooltip>

                        {/* Export Button */}
                        {exportable && (
                            <Tooltip title="Export Data">
                                <IconButton size="small" onClick={() => exportData('csv')}>
                                    <DownloadIcon />
                                </IconButton>
                            </Tooltip>
                        )}

                        {/* Fullscreen Toggle */}
                        <Tooltip title={fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
                            <IconButton
                                size="small"
                                onClick={() => setFullscreen(!fullscreen)}
                            >
                                <FullscreenIcon />
                            </IconButton>
                        </Tooltip>
                    </Stack>
                </Stack>

                {/* Active Filters */}
                {selectedCategories.length > 0 && (
                    <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
                        {selectedCategories.map((category) => (
                            <Chip
                                key={category}
                                label={category}
                                size="small"
                                color="primary"
                                variant="outlined"
                                onDelete={() => setSelectedCategories(prev => 
                                    prev.filter(c => c !== category)
                                )}
                            />
                        ))}
                    </Stack>
                )}

                {/* Chart Container */}
                <Box sx={{ height: fullscreen ? 'calc(100vh - 200px)' : height, width: '100%' }}>
                    <ResponsiveContainer>
                        {renderChart()}
                    </ResponsiveContainer>
                </Box>

                {/* Data Summary */}
                <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                        Showing {filteredData.length} of {config.data.length} data points
                    </Typography>
                    {selectedCategories.length > 0 && (
                        <Typography variant="caption" color="primary">
                            Filtered by {selectedCategories.length} categories
                        </Typography>
                    )}
                </Stack>
            </CardContent>

            {/* Filter Menu */}
            <Popover
                open={Boolean(filterMenuAnchor)}
                anchorEl={filterMenuAnchor}
                onClose={() => setFilterMenuAnchor(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <Paper sx={{ p: 2, minWidth: 250 }}>
                    <Typography variant="subtitle2" sx={{ mb: 2 }}>
                        Filter Options
                    </Typography>
                    
                    {/* Category Filter */}
                    {categories.length > 0 && (
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>Categories</InputLabel>
                            <Select
                                multiple
                                value={selectedCategories}
                                onChange={(e) => setSelectedCategories(e.target.value as string[])}
                                label="Categories"
                                renderValue={(selected) => (
                                    <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap' }}>
                                        {(selected as string[]).map((value) => (
                                            <Chip key={value} label={value} size="small" />
                                        ))}
                                    </Stack>
                                )}
                            >
                                {categories.map((category) => (
                                    <MenuItem key={category} value={category}>
                                        {category}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    )}

                    {/* Clear Filters */}
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                            setSelectedCategories([]);
                            setFilters({});
                            onFilterChange?.({});
                        }}
                        fullWidth
                    >
                        Clear All Filters
                    </Button>
                </Paper>
            </Popover>

            {/* Settings Menu */}
            <Popover
                open={Boolean(settingsMenuAnchor)}
                anchorEl={settingsMenuAnchor}
                onClose={() => setSettingsMenuAnchor(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <Paper sx={{ p: 2, minWidth: 200 }}>
                    <Typography variant="subtitle2" sx={{ mb: 2 }}>
                        Chart Settings
                    </Typography>
                    
                    <Stack spacing={1}>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={chartSettings.showGrid}
                                    onChange={(e) => setChartSettings(prev => ({ 
                                        ...prev, 
                                        showGrid: e.target.checked 
                                    }))}
                                />
                            }
                            label="Show Grid"
                        />
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={chartSettings.showLegend}
                                    onChange={(e) => setChartSettings(prev => ({ 
                                        ...prev, 
                                        showLegend: e.target.checked 
                                    }))}
                                />
                            }
                            label="Show Legend"
                        />
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={chartSettings.showTooltip}
                                    onChange={(e) => setChartSettings(prev => ({ 
                                        ...prev, 
                                        showTooltip: e.target.checked 
                                    }))}
                                />
                            }
                            label="Show Tooltips"
                        />
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={chartSettings.animated}
                                    onChange={(e) => setChartSettings(prev => ({ 
                                        ...prev, 
                                        animated: e.target.checked 
                                    }))}
                                />
                            }
                            label="Animations"
                        />
                        {(chartType === 'line' || chartType === 'area') && (
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={chartSettings.smoothLines}
                                        onChange={(e) => setChartSettings(prev => ({ 
                                            ...prev, 
                                            smoothLines: e.target.checked 
                                        }))}
                                    />
                                }
                                label="Smooth Lines"
                            />
                        )}
                    </Stack>
                </Paper>
            </Popover>

            {/* Fullscreen Dialog */}
            <Dialog
                open={fullscreen}
                onClose={() => setFullscreen(false)}
                maxWidth={false}
                fullScreen
                PaperProps={{ sx: { bgcolor: 'background.default' } }}
            >
                <DialogTitle>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="h5">{config.title}</Typography>
                        <IconButton onClick={() => setFullscreen(false)}>
                            <CloseIcon />
                        </IconButton>
                    </Stack>
                </DialogTitle>
                <DialogContent sx={{ p: 3 }}>
                    <Box sx={{ height: 'calc(100vh - 150px)', width: '100%' }}>
                        <ResponsiveContainer>
                            {renderChart()}
                        </ResponsiveContainer>
                    </Box>
                </DialogContent>
            </Dialog>
        </Card>
    );
};

export default InteractiveCharts;