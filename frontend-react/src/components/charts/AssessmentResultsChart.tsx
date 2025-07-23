'use client';

import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    Legend,
    PieChart,
    Pie,
    Cell,
} from 'recharts';
import { Card, CardContent, Typography, Box, ToggleButton, ToggleButtonGroup } from '@mui/material';

interface AssessmentData {
    category: string;
    currentScore: number;
    targetScore: number;
    improvement: number;
    color: string;
}

interface AssessmentResultsChartProps {
    data: AssessmentData[];
    title?: string;
    showComparison?: boolean;
}

const AssessmentResultsChart: React.FC<AssessmentResultsChartProps> = ({
    data,
    title = "Assessment Results",
    showComparison = true
}) => {
    const [viewType, setViewType] = React.useState<'bar' | 'area' | 'pie'>('bar');

    const handleViewChange = (
        _event: React.MouseEvent<HTMLElement>,
        newView: 'bar' | 'area' | 'pie' | null,
    ) => {
        if (newView !== null) {
            setViewType(newView);
        }
    };

    const formatScore = (value: number) => `${value}%`;

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
                            {entry.name}: {formatScore(entry.value)}
                        </Typography>
                    ))}
                </Box>
            );
        }
        return null;
    };

    const PieTooltip = ({ active, payload }: {
        active?: boolean;
        payload?: Array<{ payload: { category: string; currentScore: number } }>;
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
                        {data.category}
                    </Typography>
                    <Typography variant="body2">
                        Score: {formatScore(data.currentScore)}
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
                    <Typography variant="h6">
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
                        <ToggleButton value="area">
                            Area Chart
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
                                <XAxis dataKey="category" />
                                <YAxis tickFormatter={formatScore} domain={[0, 100]} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Bar dataKey="currentScore" fill="#8884d8" name="Current Score" />
                                {showComparison && (
                                    <Bar dataKey="targetScore" fill="#82ca9d" name="Target Score" />
                                )}
                            </BarChart>
                        ) : viewType === 'area' ? (
                            <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="category" />
                                <YAxis tickFormatter={formatScore} domain={[0, 100]} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Area
                                    type="monotone"
                                    dataKey="currentScore"
                                    stackId="1"
                                    stroke="#8884d8"
                                    fill="#8884d8"
                                    name="Current Score"
                                />
                                {showComparison && (
                                    <Area
                                        type="monotone"
                                        dataKey="targetScore"
                                        stackId="2"
                                        stroke="#82ca9d"
                                        fill="#82ca9d"
                                        name="Target Score"
                                    />
                                )}
                            </AreaChart>
                        ) : (
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ category, currentScore }) => `${category}: ${formatScore(currentScore)}`}
                                    outerRadius={120}
                                    fill="#8884d8"
                                    dataKey="currentScore"
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

                {/* Assessment Summary */}
                <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Assessment Summary
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        {data.map((item) => (
                            <Box
                                key={item.category}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    p: 1,
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 1,
                                    minWidth: 150,
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
                                        {item.category}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {formatScore(item.currentScore)}
                                        {showComparison && item.improvement > 0 && (
                                            <span style={{ color: '#4caf50', marginLeft: 4 }}>
                                                (+{item.improvement}%)
                                            </span>
                                        )}
                                    </Typography>
                                </Box>
                            </Box>
                        ))}
                    </Box>
                </Box>

                {/* Overall Score */}
                <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Overall Assessment Score
                    </Typography>
                    <Typography variant="h4" color="primary.main">
                        {Math.round(data.reduce((sum, item) => sum + item.currentScore, 0) / data.length)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Based on {data.length} assessment categories
                    </Typography>
                </Box>
            </CardContent>
        </Card>
    );
};

export default AssessmentResultsChart;