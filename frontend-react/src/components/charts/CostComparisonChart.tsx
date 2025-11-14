'use client';

import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts';
import { Card, CardContent, Typography, Box, ToggleButton, ToggleButtonGroup } from '@mui/material';

interface CostData {
    provider: string;
    compute: number;
    storage: number;
    networking: number;
    total: number;
    color: string;
}

interface CostComparisonChartProps {
    data: CostData[];
    title?: string;
    showBreakdown?: boolean;
}

const CostComparisonChart: React.FC<CostComparisonChartProps> = ({
    data,
    title = "Cost Comparison",
    showBreakdown = true
}) => {
    const [viewType, setViewType] = React.useState<'bar' | 'pie'>('bar');

    const handleViewChange = (
        _event: React.MouseEvent<HTMLElement>,
        newView: 'bar' | 'pie' | null,
    ) => {
        if (newView !== null) {
            setViewType(newView);
        }
    };

    const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

    // Handle empty data state
    if (!data || data.length === 0) {
        return (
            <Card>
                <CardContent>
                    <Typography variant="h6" color="text.primary" gutterBottom>
                        {title}
                    </Typography>
                    <Box sx={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        py: 6,
                        textAlign: 'center'
                    }}>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            No Cost Data Available
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Complete an assessment to see cost comparisons across cloud providers.
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    const CustomTooltip = ({ active, payload, label }: {
        active?: boolean;
        payload?: Array<{ name: string; value: number; color: string }>;
        label?: string;
    }) => {
        if (active && payload && payload.length) {
            return (
                <Box
                    sx={{
                        backgroundColor: 'background.paper',
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        p: 1,
                        boxShadow: 2,
                    }}
                >
                    <Typography variant="body2" fontWeight="medium">
                        {label}
                    </Typography>
                    {payload.map((entry: { name: string; value: number; color: string }, index: number) => (
                        <Typography
                            key={index}
                            variant="body2"
                            sx={{ color: entry.color }}
                        >
                            {entry.name}: {formatCurrency(entry.value)}
                        </Typography>
                    ))}
                </Box>
            );
        }
        return null;
    };

    const PieTooltip = ({ active, payload }: {
        active?: boolean;
        payload?: Array<{ payload: { provider: string; total: number } }>;
    }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <Box
                    sx={{
                        backgroundColor: 'background.paper',
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        p: 1,
                        boxShadow: 2,
                    }}
                >
                    <Typography variant="body2" fontWeight="medium">
                        {data.provider}
                    </Typography>
                    <Typography variant="body2">
                        Total: {formatCurrency(data.total)}
                    </Typography>
                </Box>
            );
        }
        return null;
    };

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" color="text.primary">
                        {title}
                    </Typography>
                    <ToggleButtonGroup
                        value={viewType}
                        exclusive
                        onChange={handleViewChange}
                        aria-label="chart view toggle"
                        size="small"
                    >
                        <ToggleButton value="bar">
                            Bar Chart
                        </ToggleButton>
                        <ToggleButton value="pie">
                            Pie Chart
                        </ToggleButton>
                    </ToggleButtonGroup>
                </Box>

                <Box sx={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                        {viewType === 'bar' ? (
                            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="provider" />
                                <YAxis tickFormatter={formatCurrency} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                {showBreakdown ? (
                                    <>
                                        <Bar dataKey="compute" stackId="a" fill="#8884d8" name="Compute" />
                                        <Bar dataKey="storage" stackId="a" fill="#82ca9d" name="Storage" />
                                        <Bar dataKey="networking" stackId="a" fill="#ffc658" name="Networking" />
                                    </>
                                ) : (
                                    <Bar dataKey="total" name="Total Cost">
                                        {data.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                )}
                            </BarChart>
                        ) : (
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ provider, total }) => `${provider}: ${formatCurrency(total)}`}
                                    outerRadius={120}
                                    fill="#8884d8"
                                    dataKey="total"
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip content={<PieTooltip />} />
                            </PieChart>
                        )}
                    </ResponsiveContainer>
                </Box>

                {/* Cost Summary */}
                <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {data.map((item) => (
                        <Box
                            key={item.provider}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 1,
                                p: 1,
                                border: 1,
                                borderColor: 'divider',
                                borderRadius: 1,
                                minWidth: 120,
                            }}
                        >
                            <Box
                                sx={{
                                    width: 12,
                                    height: 12,
                                    backgroundColor: item.color,
                                    borderRadius: '50%',
                                }}
                            />
                            <Box>
                                <Typography variant="body2" fontWeight="medium">
                                    {item.provider}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {formatCurrency(item.total)}
                                </Typography>
                            </Box>
                        </Box>
                    ))}
                </Box>
            </CardContent>
        </Card>
    );
};

export default CostComparisonChart;