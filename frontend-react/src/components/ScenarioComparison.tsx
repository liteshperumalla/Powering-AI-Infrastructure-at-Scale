'use client';

import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    LinearProgress,
    Divider,
    IconButton,
    Tooltip,
    Alert,
    Tabs,
    Tab,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
} from '@mui/material';
import {
    Compare,
    TrendingUp,
    TrendingDown,
    AttachMoney,
    Speed,
    Security,
    ScaleOutlined,
    Close,
    Add,
    Remove,
    SwapHoriz,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { addToComparison, removeFromComparison, clearComparison } from '@/store/slices/scenarioSlice';
import { closeModal } from '@/store/slices/uiSlice';
import type { Scenario } from '@/store/slices/scenarioSlice';

interface ScenarioComparisonProps {
    open: boolean;
    onClose: () => void;
}

// Helper function to get provider chip colors
const getProviderChipColor = (provider: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (provider) {
        case 'AWS': return 'warning';
        case 'Azure': return 'info';
        case 'GCP': return 'success';
        case 'Alibaba': return 'secondary';
        case 'IBM': return 'primary';
        default: return 'default';
    }
};

export default function ScenarioComparison({ open, onClose }: ScenarioComparisonProps) {
    const dispatch = useAppDispatch();
    const { scenarios, comparisonScenarios } = useAppSelector(state => state.scenario);
    const [activeTab, setActiveTab] = useState(0);
    const [selectedScenario, setSelectedScenario] = useState('');

    const availableScenarios = scenarios.filter(s =>
        s.status === 'completed' &&
        !comparisonScenarios.find(cs => cs.id === s.id)
    );

    const handleAddScenario = () => {
        const scenario = scenarios.find(s => s.id === selectedScenario);
        if (scenario) {
            dispatch(addToComparison(scenario));
            setSelectedScenario('');
        }
    };

    const handleQuickAddScenario = (scenario: Scenario) => {
        dispatch(addToComparison(scenario));
    };

    const handleRemoveScenario = (scenarioId: string) => {
        dispatch(removeFromComparison(scenarioId));
    };

    const handleClearAll = () => {
        dispatch(clearComparison());
    };

    const handleClose = () => {
        onClose();
    };

    const getScoreColor = (score: number) => {
        if (score >= 90) return '#4caf50';
        if (score >= 80) return '#8bc34a';
        if (score >= 70) return '#ffc107';
        if (score >= 60) return '#ff9800';
        return '#f44336';
    };

    const getChangeIcon = (current: number, previous: number) => {
        if (current > previous) return <TrendingUp color="success" />;
        if (current < previous) return <TrendingDown color="error" />;
        return null;
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const getComparisonData = () => {
        if (comparisonScenarios.length < 2) return [];

        return comparisonScenarios[0].result?.projections.map((_, index) => {
            const dataPoint: { [key: string]: number | string } = { month: index + 1 };
            comparisonScenarios.forEach((scenario, scenarioIndex) => {
                if (scenario.result?.projections[index]) {
                    dataPoint[`cost_${scenarioIndex}`] = scenario.result.projections[index].cost;
                    dataPoint[`performance_${scenarioIndex}`] = scenario.result.projections[index].performance;
                    dataPoint[`utilization_${scenarioIndex}`] = scenario.result.projections[index].utilization;
                }
            });
            return dataPoint;
        }) || [];
    };

    const getRadarData = () => {
        const metrics = ['Cost Efficiency', 'Performance', 'Scalability', 'Compliance', 'Reliability'];

        return metrics.map(metric => {
            const dataPoint: { [key: string]: string | number } = { metric };
            comparisonScenarios.forEach((scenario, index) => {
                // Simulate metric scores based on scenario results
                let score = 0;
                if (scenario.result) {
                    switch (metric) {
                        case 'Cost Efficiency':
                            score = Math.max(0, 100 - (scenario.result.totalCost / 200));
                            break;
                        case 'Performance':
                            score = scenario.result.performanceScore;
                            break;
                        case 'Scalability':
                            score = scenario.result.scalabilityScore;
                            break;
                        case 'Compliance':
                            score = scenario.result.complianceScore;
                            break;
                        case 'Reliability':
                            score = (scenario.result.performanceScore + scenario.result.scalabilityScore) / 2;
                            break;
                    }
                }
                dataPoint[`scenario_${index}`] = score;
            });
            return dataPoint;
        });
    };

    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="xl" fullWidth>
            <DialogTitle>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Compare />
                        Scenario Comparison
                        <Chip
                            label={`${comparisonScenarios.length} scenarios`}
                            size="small"
                            color="primary"
                        />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        {comparisonScenarios.length > 0 && (
                            <Button onClick={handleClearAll} size="small" color="error">
                                Clear All
                            </Button>
                        )}
                        <IconButton onClick={handleClose}>
                            <Close />
                        </IconButton>
                    </Box>
                </Box>
            </DialogTitle>

            <DialogContent>
                {comparisonScenarios.length === 0 ? (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        Select a scenario to view detailed analysis. You can add up to 2 additional scenarios for comparison.
                    </Alert>
                ) : comparisonScenarios.length === 1 ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                        Scenario loaded. Add one more scenario to enable comparison features.
                    </Alert>
                ) : null}

                {/* Available Scenarios Section */}
                {comparisonScenarios.length === 0 && availableScenarios.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            Available Scenarios
                        </Typography>
                        <Grid container spacing={2}>
                            {availableScenarios.slice(0, 6).map(scenario => (
                                <Grid item xs={12} md={6} key={scenario.id}>
                                    <Card sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                                        <CardContent>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                <Box sx={{ flex: 1 }}>
                                                    <Typography variant="h6" color="text.primary" gutterBottom>
                                                        {scenario.name}
                                                    </Typography>
                                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                                        {scenario.description}
                                                    </Typography>
                                                    {scenario.result && (
                                                        <Box sx={{ mt: 2 }}>
                                                            <Typography variant="h6" color="primary">
                                                                {formatCurrency(scenario.result.totalCost)}
                                                            </Typography>
                                                            <Typography variant="body2">
                                                                Performance: {scenario.result.performanceScore}%
                                                            </Typography>
                                                        </Box>
                                                    )}
                                                </Box>
                                                <Button
                                                    onClick={() => handleQuickAddScenario(scenario)}
                                                    variant="contained"
                                                    size="small"
                                                    startIcon={<Add />}
                                                >
                                                    Select
                                                </Button>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    </Box>
                )}

                {/* Add Additional Scenario Section */}
                {comparisonScenarios.length > 0 && comparisonScenarios.length < 3 && availableScenarios.length > 0 && (
                    <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                            <FormControl size="small" sx={{ minWidth: 300 }}>
                                <InputLabel>Add Another Scenario</InputLabel>
                                <Select
                                    value={selectedScenario}
                                    label="Add Another Scenario"
                                    onChange={(e) => setSelectedScenario(e.target.value)}
                                >
                                    {availableScenarios.map(scenario => (
                                        <MenuItem key={scenario.id} value={scenario.id}>
                                            {scenario.name}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <Button
                                onClick={handleAddScenario}
                                disabled={!selectedScenario}
                                variant="outlined"
                                startIcon={<Add />}
                            >
                                Add for Comparison
                            </Button>
                        </Box>
                    </Box>
                )}

                {comparisonScenarios.length > 0 && (
                    <>
                        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
                            <Tab label="Overview" />
                            <Tab label="Cost Analysis" />
                            <Tab label="Performance Metrics" />
                            <Tab label="Service Details" />
                        </Tabs>

                        {/* Overview Tab */}
                        {activeTab === 0 && (
                            <Box>
                                <Grid container spacing={3}>
                                    {comparisonScenarios.map((scenario, index) => (
                                        <Grid item xs={12} md={12 / comparisonScenarios.length} key={scenario.id}>
                                            <Card>
                                                <CardContent>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                                        <Box>
                                                            <Typography variant="h6" color="text.primary" gutterBottom>
                                                                {scenario.name}
                                                            </Typography>
                                                            <Typography variant="body2" color="text.secondary">
                                                                {scenario.description}
                                                            </Typography>
                                                        </Box>
                                                        <Tooltip title="Remove from comparison">
                                                            <IconButton
                                                                size="small"
                                                                onClick={() => handleRemoveScenario(scenario.id)}
                                                            >
                                                                <Remove />
                                                            </IconButton>
                                                        </Tooltip>
                                                    </Box>

                                                    <Divider sx={{ my: 2 }} />

                                                    {scenario.result && (
                                                        <Box>
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                                                <Typography variant="body2">Total Cost</Typography>
                                                                <Typography variant="h6" color="primary">
                                                                    {formatCurrency(scenario.result.totalCost)}
                                                                </Typography>
                                                            </Box>

                                                            <Box sx={{ mb: 2 }}>
                                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                                                    <Typography variant="body2">Performance</Typography>
                                                                    <Typography variant="body2">
                                                                        {scenario.result.performanceScore}%
                                                                    </Typography>
                                                                </Box>
                                                                <LinearProgress
                                                                    variant="determinate"
                                                                    value={scenario.result.performanceScore}
                                                                    sx={{
                                                                        height: 8,
                                                                        borderRadius: 4,
                                                                        '& .MuiLinearProgress-bar': {
                                                                            backgroundColor: getScoreColor(scenario.result.performanceScore),
                                                                        },
                                                                    }}
                                                                />
                                                            </Box>

                                                            <Box sx={{ mb: 2 }}>
                                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                                                    <Typography variant="body2">Compliance</Typography>
                                                                    <Typography variant="body2">
                                                                        {scenario.result.complianceScore}%
                                                                    </Typography>
                                                                </Box>
                                                                <LinearProgress
                                                                    variant="determinate"
                                                                    value={scenario.result.complianceScore}
                                                                    sx={{
                                                                        height: 8,
                                                                        borderRadius: 4,
                                                                        '& .MuiLinearProgress-bar': {
                                                                            backgroundColor: getScoreColor(scenario.result.complianceScore),
                                                                        },
                                                                    }}
                                                                />
                                                            </Box>

                                                            <Box sx={{ mb: 2 }}>
                                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                                                    <Typography variant="body2">Scalability</Typography>
                                                                    <Typography variant="body2">
                                                                        {scenario.result.scalabilityScore}%
                                                                    </Typography>
                                                                </Box>
                                                                <LinearProgress
                                                                    variant="determinate"
                                                                    value={scenario.result.scalabilityScore}
                                                                    sx={{
                                                                        height: 8,
                                                                        borderRadius: 4,
                                                                        '& .MuiLinearProgress-bar': {
                                                                            backgroundColor: getScoreColor(scenario.result.scalabilityScore),
                                                                        },
                                                                    }}
                                                                />
                                                            </Box>

                                                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                                <Chip
                                                                    icon={<AttachMoney />}
                                                                    label={`${scenario.parameters.timeHorizon}`}
                                                                    size="small"
                                                                />
                                                                <Chip
                                                                    icon={<ScaleOutlined />}
                                                                    label={`${scenario.parameters.scalingFactor}x scale`}
                                                                    size="small"
                                                                />
                                                                <Chip
                                                                    icon={<Security />}
                                                                    label={scenario.parameters.complianceLevel}
                                                                    size="small"
                                                                />
                                                            </Box>
                                                        </Box>
                                                    )}
                                                </CardContent>
                                            </Card>
                                        </Grid>
                                    ))}
                                </Grid>

                                {comparisonScenarios.length >= 2 && (
                                    <Box sx={{ mt: 4 }}>
                                        <Typography variant="h6" color="text.primary" gutterBottom>
                                            Performance Comparison
                                        </Typography>
                                        <Card>
                                            <CardContent>
                                                <ResponsiveContainer width="100%" height={300}>
                                                    <RadarChart data={getRadarData()}>
                                                        <PolarGrid />
                                                        <PolarAngleAxis dataKey="metric" />
                                                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                                                        {comparisonScenarios.map((scenario, index) => (
                                                            <Radar
                                                                key={scenario.id}
                                                                name={scenario.name}
                                                                dataKey={`scenario_${index}`}
                                                                stroke={colors[index]}
                                                                fill={colors[index]}
                                                                fillOpacity={0.1}
                                                            />
                                                        ))}
                                                        <Legend />
                                                    </RadarChart>
                                                </ResponsiveContainer>
                                            </CardContent>
                                        </Card>
                                    </Box>
                                )}
                            </Box>
                        )}

                        {/* Cost Analysis Tab */}
                        {activeTab === 1 && comparisonScenarios.length >= 2 && (
                            <Box>
                                <Typography variant="h6" color="text.primary" gutterBottom>
                                    Cost Projection Comparison
                                </Typography>
                                <Card>
                                    <CardContent>
                                        <ResponsiveContainer width="100%" height={400}>
                                            <LineChart data={getComparisonData()}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="month" />
                                                <YAxis />
                                                <RechartsTooltip formatter={(value: number) => formatCurrency(value)} />
                                                <Legend />
                                                {comparisonScenarios.map((scenario, index) => (
                                                    <Line
                                                        key={scenario.id}
                                                        type="monotone"
                                                        dataKey={`cost_${index}`}
                                                        stroke={colors[index]}
                                                        name={scenario.name}
                                                        strokeWidth={2}
                                                    />
                                                ))}
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </CardContent>
                                </Card>

                                <Box sx={{ mt: 3 }}>
                                    <Typography variant="h6" color="text.primary" gutterBottom>
                                        Cost Summary
                                    </Typography>
                                    <TableContainer component={Paper}>
                                        <Table>
                                            <TableHead>
                                                <TableRow>
                                                    <TableCell>Scenario</TableCell>
                                                    <TableCell align="right">Total Cost</TableCell>
                                                    <TableCell align="right">Monthly Average</TableCell>
                                                    <TableCell align="right">Cost per Performance Point</TableCell>
                                                    <TableCell align="right">Savings vs Highest</TableCell>
                                                </TableRow>
                                            </TableHead>
                                            <TableBody>
                                                {comparisonScenarios.map((scenario) => {
                                                    const highestCost = Math.max(...comparisonScenarios.map(s => s.result?.totalCost || 0));
                                                    const savings = highestCost - (scenario.result?.totalCost || 0);
                                                    const costPerPerformance = scenario.result
                                                        ? (scenario.result.totalCost / scenario.result.performanceScore)
                                                        : 0;

                                                    return (
                                                        <TableRow key={scenario.id}>
                                                            <TableCell>{scenario.name}</TableCell>
                                                            <TableCell align="right">
                                                                {scenario.result ? formatCurrency(scenario.result.totalCost) : 'N/A'}
                                                            </TableCell>
                                                            <TableCell align="right">
                                                                {scenario.result ? formatCurrency(scenario.result.totalCost / 12) : 'N/A'}
                                                            </TableCell>
                                                            <TableCell align="right">
                                                                {formatCurrency(costPerPerformance)}
                                                            </TableCell>
                                                            <TableCell align="right">
                                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                                                                    {formatCurrency(savings)}
                                                                    {savings > 0 && <TrendingDown color="success" sx={{ ml: 1 }} />}
                                                                </Box>
                                                            </TableCell>
                                                        </TableRow>
                                                    );
                                                })}
                                            </TableBody>
                                        </Table>
                                    </TableContainer>
                                </Box>
                            </Box>
                        )}

                        {/* Performance Metrics Tab */}
                        {activeTab === 2 && comparisonScenarios.length >= 2 && (
                            <Box>
                                <Typography variant="h6" color="text.primary" gutterBottom>
                                    Performance Trends
                                </Typography>
                                <Card>
                                    <CardContent>
                                        <ResponsiveContainer width="100%" height={400}>
                                            <LineChart data={getComparisonData()}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="month" />
                                                <YAxis />
                                                <RechartsTooltip />
                                                <Legend />
                                                {comparisonScenarios.map((scenario, index) => (
                                                    <Line
                                                        key={`perf_${scenario.id}`}
                                                        type="monotone"
                                                        dataKey={`performance_${index}`}
                                                        stroke={colors[index]}
                                                        name={`${scenario.name} Performance`}
                                                        strokeWidth={2}
                                                    />
                                                ))}
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </CardContent>
                                </Card>

                                <Box sx={{ mt: 3 }}>
                                    <Typography variant="h6" color="text.primary" gutterBottom>
                                        Utilization Comparison
                                    </Typography>
                                    <Card>
                                        <CardContent>
                                            <ResponsiveContainer width="100%" height={300}>
                                                <BarChart data={getComparisonData()}>
                                                    <CartesianGrid strokeDasharray="3 3" />
                                                    <XAxis dataKey="month" />
                                                    <YAxis />
                                                    <RechartsTooltip />
                                                    <Legend />
                                                    {comparisonScenarios.map((scenario, index) => (
                                                        <Bar
                                                            key={`util_${scenario.id}`}
                                                            dataKey={`utilization_${index}`}
                                                            fill={colors[index]}
                                                            name={`${scenario.name} Utilization`}
                                                        />
                                                    ))}
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </CardContent>
                                    </Card>
                                </Box>
                            </Box>
                        )}

                        {/* Service Details Tab */}
                        {activeTab === 3 && (
                            <Box>
                                <Typography variant="h6" color="text.primary" gutterBottom>
                                    Service Breakdown
                                </Typography>
                                {comparisonScenarios.map((scenario, scenarioIndex) => (
                                    <Card key={scenario.id} sx={{ mb: 2 }}>
                                        <CardContent>
                                            <Typography variant="h6" color="text.primary" gutterBottom>
                                                {scenario.name}
                                            </Typography>
                                            {scenario.result?.services && (
                                                <TableContainer>
                                                    <Table size="small">
                                                        <TableHead>
                                                            <TableRow>
                                                                <TableCell>Service</TableCell>
                                                                <TableCell>Provider</TableCell>
                                                                <TableCell>Type</TableCell>
                                                                <TableCell align="right">Monthly Cost</TableCell>
                                                                <TableCell align="right">Performance</TableCell>
                                                                <TableCell align="right">Scalability</TableCell>
                                                                <TableCell align="right">Compliance</TableCell>
                                                            </TableRow>
                                                        </TableHead>
                                                        <TableBody>
                                                            {scenario.result.services.map((service, serviceIndex) => (
                                                                <TableRow key={serviceIndex}>
                                                                    <TableCell>{service.name}</TableCell>
                                                                    <TableCell>
                                                                        <Chip
                                                                            label={service.provider}
                                                                            size="small"
                                                                            color={getProviderChipColor(service.provider)}
                                                                        />
                                                                    </TableCell>
                                                                    <TableCell>{service.type}</TableCell>
                                                                    <TableCell align="right">
                                                                        {formatCurrency(service.monthlyCost)}
                                                                    </TableCell>
                                                                    <TableCell align="right">{service.performance}%</TableCell>
                                                                    <TableCell align="right">{service.scalability}%</TableCell>
                                                                    <TableCell align="right">{service.compliance}%</TableCell>
                                                                </TableRow>
                                                            ))}
                                                        </TableBody>
                                                    </Table>
                                                </TableContainer>
                                            )}
                                        </CardContent>
                                    </Card>
                                ))}
                            </Box>
                        )}
                    </>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={handleClose}>Close</Button>
                {comparisonScenarios.length >= 2 && (
                    <Button variant="contained" onClick={() => {
                        // Export comparison report
                        console.log('Export comparison report');
                    }}>
                        Export Comparison
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
}