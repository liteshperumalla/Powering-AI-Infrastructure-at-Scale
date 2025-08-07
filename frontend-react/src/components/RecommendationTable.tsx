'use client';

import React from 'react';
import {
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Box,
    Rating,
    Button,
    Collapse,
    IconButton,
    List,
    ListItem,
    ListItemText,
    Divider,
    LinearProgress,
} from '@mui/material';
import {
    CheckCircle,
    Warning,
    Info,
    ExpandMore,
    ExpandLess,
    TrendingUp,
    TrendingDown,
    Remove,
} from '@mui/icons-material';

interface ServiceRecommendation {
    id: string;
    serviceName: string;
    provider: 'AWS' | 'Azure' | 'GCP';
    serviceType: string;
    costEstimate: number;
    confidenceScore: number;
    businessAlignment: number;
    implementationComplexity: 'Low' | 'Medium' | 'High';
    pros: string[];
    cons: string[];
    status: 'recommended' | 'alternative' | 'not-recommended';
}

interface RecommendationTableProps {
    recommendations: ServiceRecommendation[];
    title?: string;
}

const getProviderColor = (provider: string) => {
    switch (provider) {
        case 'AWS': return '#FF9900';
        case 'Azure': return '#0078D4';
        case 'GCP': return '#4285F4';
        default: return '#666';
    }
};

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'recommended': return <CheckCircle color="success" />;
        case 'alternative': return <Info color="info" />;
        case 'not-recommended': return <Warning color="warning" />;
        default: return null;
    }
};

const getComplexityColor = (complexity: string) => {
    switch (complexity) {
        case 'Low': return 'success';
        case 'Medium': return 'warning';
        case 'High': return 'error';
        default: return 'default';
    }
};

const RecommendationTable: React.FC<RecommendationTableProps> = ({
    recommendations,
    title = "Service Recommendations"
}) => {
    const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

    const toggleRowExpansion = (id: string) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    const getCostTrend = (cost: number, avgCost: number) => {
        const diff = ((cost - avgCost) / avgCost) * 100;
        if (Math.abs(diff) < 5) return <Remove color="action" />;
        return diff > 0 ? <TrendingUp color="error" /> : <TrendingDown color="success" />;
    };

    const avgCost = recommendations.length > 0 
        ? recommendations.reduce((sum, rec) => sum + rec.costEstimate, 0) / recommendations.length 
        : 0;

    // Handle empty state
    if (recommendations.length === 0) {
        return (
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">
                            {title}
                        </Typography>
                    </Box>
                    <Box sx={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        py: 6,
                        textAlign: 'center'
                    }}>
                        <Info sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            No Recommendations Available
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Complete an assessment to see personalized service recommendations.
                        </Typography>
                        <Button 
                            variant="contained" 
                            sx={{ mt: 2 }}
                            onClick={() => window.location.href = '/assessment'}
                        >
                            Start Assessment
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                        {title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {recommendations.length} services compared
                    </Typography>
                </Box>

                {/* Quick Stats */}
                <Box sx={{ display: 'flex', gap: 2, mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                            Average Cost
                        </Typography>
                        <Typography variant="h6">
                            ${avgCost.toFixed(2)}/month
                        </Typography>
                    </Box>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                            Best Value
                        </Typography>
                        <Typography variant="h6" color="success.main">
                            {recommendations.find(r => r.status === 'recommended')?.serviceName || 'N/A'}
                        </Typography>
                    </Box>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                            Avg Confidence
                        </Typography>
                        <Typography variant="h6">
                            {recommendations.length > 0 
                                ? (recommendations.reduce((sum, r) => sum + r.confidenceScore, 0) / recommendations.length).toFixed(1)
                                : '0'}%
                        </Typography>
                    </Box>
                </Box>

                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell width={40}></TableCell>
                                <TableCell>Service</TableCell>
                                <TableCell>Provider</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell align="right">Cost/Month</TableCell>
                                <TableCell align="center">Confidence</TableCell>
                                <TableCell align="center">Business Fit</TableCell>
                                <TableCell align="center">Complexity</TableCell>
                                <TableCell align="center">Status</TableCell>
                                <TableCell align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {recommendations.map((rec) => (
                                <React.Fragment key={rec.id}>
                                    <TableRow hover>
                                        <TableCell>
                                            <IconButton
                                                size="small"
                                                onClick={() => toggleRowExpansion(rec.id)}
                                            >
                                                {expandedRows.has(rec.id) ? <ExpandLess /> : <ExpandMore />}
                                            </IconButton>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" fontWeight="medium">
                                                {rec.serviceName}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={rec.provider}
                                                size="small"
                                                sx={{
                                                    backgroundColor: getProviderColor(rec.provider),
                                                    color: 'white',
                                                    fontWeight: 'bold'
                                                }}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" color="text.secondary">
                                                {rec.serviceType}
                                            </Typography>
                                        </TableCell>
                                        <TableCell align="right">
                                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                                                <Typography variant="body2" fontWeight="medium">
                                                    ${rec.costEstimate.toFixed(2)}
                                                </Typography>
                                                {getCostTrend(rec.costEstimate, avgCost)}
                                            </Box>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Box>
                                                <Rating
                                                    value={rec.confidenceScore / 20}
                                                    readOnly
                                                    size="small"
                                                    precision={0.1}
                                                />
                                                <Typography variant="caption" display="block">
                                                    {rec.confidenceScore}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Box>
                                                <LinearProgress
                                                    variant="determinate"
                                                    value={rec.businessAlignment}
                                                    sx={{ width: 60, height: 6, borderRadius: 3 }}
                                                />
                                                <Typography variant="caption" display="block">
                                                    {rec.businessAlignment}%
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Chip
                                                label={rec.implementationComplexity}
                                                size="small"
                                                color={getComplexityColor(rec.implementationComplexity) as 'success' | 'warning' | 'error' | 'default'}
                                                variant="outlined"
                                            />
                                        </TableCell>
                                        <TableCell align="center">
                                            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                                                {getStatusIcon(rec.status)}
                                            </Box>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                onClick={() => {
                                                    console.log('View details for:', rec.serviceName);
                                                }}
                                            >
                                                Details
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                                            <Collapse in={expandedRows.has(rec.id)} timeout="auto" unmountOnExit>
                                                <Box sx={{ margin: 1, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                                    <Typography variant="subtitle2" gutterBottom>
                                                        Detailed Analysis
                                                    </Typography>
                                                    <Box sx={{ display: 'flex', gap: 4 }}>
                                                        <Box sx={{ flex: 1 }}>
                                                            <Typography variant="body2" color="success.main" fontWeight="medium">
                                                                Pros
                                                            </Typography>
                                                            <List dense>
                                                                {rec.pros.map((pro, index) => (
                                                                    <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                                                                        <ListItemText
                                                                            primary={
                                                                                <Typography variant="body2">
                                                                                    {pro}
                                                                                </Typography>
                                                                            }
                                                                        />
                                                                    </ListItem>
                                                                ))}
                                                            </List>
                                                        </Box>
                                                        <Divider orientation="vertical" flexItem />
                                                        <Box sx={{ flex: 1 }}>
                                                            <Typography variant="body2" color="warning.main" fontWeight="medium">
                                                                Cons
                                                            </Typography>
                                                            <List dense>
                                                                {rec.cons.map((con, index) => (
                                                                    <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                                                                        <ListItemText
                                                                            primary={
                                                                                <Typography variant="body2">
                                                                                    {con}
                                                                                </Typography>
                                                                            }
                                                                        />
                                                                    </ListItem>
                                                                ))}
                                                            </List>
                                                        </Box>
                                                    </Box>
                                                </Box>
                                            </Collapse>
                                        </TableCell>
                                    </TableRow>
                                </React.Fragment>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </CardContent>
        </Card>
    );
};

export default RecommendationTable;