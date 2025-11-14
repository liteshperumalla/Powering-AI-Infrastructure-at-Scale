'use client';

import React from 'react';
import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
} from 'recharts';
import { Card, CardContent, Typography, Box, ToggleButton, ToggleButtonGroup } from '@mui/material';

interface ScoreData {
    service: string;
    costEfficiency: number;
    performance: number;
    scalability: number;
    security: number;
    compliance: number;
    businessAlignment: number;
    provider: string;
    color: string;
}

interface RecommendationScoreChartProps {
    data: ScoreData[];
    title?: string;
}

const RecommendationScoreChart: React.FC<RecommendationScoreChartProps> = ({
    data,
    title = "Service Recommendation Scores"
}) => {
    const [viewType, setViewType] = React.useState<'radar' | 'line'>('radar');

    const handleViewChange = (
        _event: React.MouseEvent<HTMLElement>,
        newView: 'radar' | 'line' | null,
    ) => {
        if (newView !== null) {
            setViewType(newView);
        }
    };

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
                            No Performance Scores Available
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Complete an assessment to see service performance comparisons.
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    // Transform data for radar chart
    const radarData = [
        { subject: 'Cost Efficiency', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.costEfficiency }), {}) },
        { subject: 'Performance', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.performance }), {}) },
        { subject: 'Scalability', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.scalability }), {}) },
        { subject: 'Security', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.security }), {}) },
        { subject: 'Compliance', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.compliance }), {}) },
        { subject: 'Business Alignment', ...data.reduce((acc, item) => ({ ...acc, [item.service]: item.businessAlignment }), {}) },
    ];

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
                            {entry.name}: {entry.value}/100
                        </Typography>
                    ))}
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
                        <ToggleButton value="radar">
                            Radar
                        </ToggleButton>
                        <ToggleButton value="line">
                            Trend
                        </ToggleButton>
                    </ToggleButtonGroup>
                </Box>

                <Box sx={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                        {viewType === 'radar' ? (
                            <RadarChart data={radarData} margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
                                <PolarGrid />
                                <PolarAngleAxis dataKey="subject" />
                                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                                {data.map((item) => (
                                    <Radar
                                        key={item.service}
                                        name={item.service}
                                        dataKey={item.service}
                                        stroke={item.color}
                                        fill={item.color}
                                        fillOpacity={0.1}
                                        strokeWidth={2}
                                    />
                                ))}
                                <Legend />
                                <Tooltip content={<CustomTooltip />} />
                            </RadarChart>
                        ) : (
                            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="service" />
                                <YAxis domain={[0, 100]} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="businessAlignment"
                                    stroke="#8884d8"
                                    strokeWidth={2}
                                    name="Business Alignment"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="costEfficiency"
                                    stroke="#82ca9d"
                                    strokeWidth={2}
                                    name="Cost Efficiency"
                                />
                            </LineChart>
                        )}
                    </ResponsiveContainer>
                </Box>

                {/* Score Legend */}
                <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Services Compared
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        {data.map((item) => (
                            <Box
                                key={item.service}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    p: 1,
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 1,
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
                                        {item.service}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {item.provider}
                                    </Typography>
                                </Box>
                            </Box>
                        ))}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
};

export default RecommendationScoreChart;