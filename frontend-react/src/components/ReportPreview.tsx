'use client';

import React from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Divider,
    Chip,
    Button,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
} from '@mui/material';
import {
    GetApp,
    Visibility,
    TrendingUp,
    Security,
    CloudQueue,
    Assessment,
} from '@mui/icons-material';

interface ReportSection {
    title: string;
    content: string;
    type: 'executive' | 'technical' | 'financial' | 'compliance';
}

interface ReportData {
    id: string;
    title: string;
    generatedDate: string;
    status: 'draft' | 'final' | 'in-progress';
    sections: ReportSection[];
    keyFindings: string[];
    recommendations: string[];
    estimatedSavings?: number;
    complianceScore?: number;
}

interface ReportPreviewProps {
    report: ReportData;
    onDownload?: (reportId: string) => void;
    onView?: (reportId: string) => void;
}

const getSectionIcon = (type: string) => {
    switch (type) {
        case 'executive': return <TrendingUp />;
        case 'technical': return <CloudQueue />;
        case 'financial': return <Assessment />;
        case 'compliance': return <Security />;
        default: return <Visibility />;
    }
};

const getStatusColor = (status: string) => {
    switch (status) {
        case 'final': return 'success';
        case 'draft': return 'warning';
        case 'in-progress': return 'info';
        default: return 'default';
    }
};

const ReportPreview: React.FC<ReportPreviewProps> = ({
    report,
    onDownload,
    onView
}) => {
    return (
        <Card>
            <CardContent>
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            {report.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Generated: {new Date(report.generatedDate).toLocaleDateString()}
                        </Typography>
                    </Box>
                    <Chip
                        label={report.status.toUpperCase()}
                        color={getStatusColor(report.status) as 'success' | 'warning' | 'info' | 'default'}
                        size="small"
                    />
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Key Metrics */}
                {(report.estimatedSavings || report.complianceScore) && (
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        {report.estimatedSavings && (
                            <Card variant="outlined" sx={{ flex: 1 }}>
                                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Estimated Savings
                                    </Typography>
                                    <Typography variant="h6" color="success.main">
                                        ${report.estimatedSavings.toLocaleString()}
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                        {report.complianceScore && (
                            <Card variant="outlined" sx={{ flex: 1 }}>
                                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Compliance Score
                                    </Typography>
                                    <Typography variant="h6" color="primary.main">
                                        {report.complianceScore}%
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                    </Box>
                )}

                {/* Report Sections */}
                <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Report Sections
                    </Typography>
                    <List dense>
                        {report.sections.map((section, index) => (
                            <ListItem key={index} sx={{ pl: 0 }}>
                                <ListItemIcon sx={{ minWidth: 36 }}>
                                    {getSectionIcon(section.type)}
                                </ListItemIcon>
                                <ListItemText
                                    primary={section.title}
                                    secondary={section.content.substring(0, 100) + '...'}
                                />
                            </ListItem>
                        ))}
                    </List>
                </Box>

                {/* Key Findings */}
                {report.keyFindings.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Key Findings
                        </Typography>
                        <List dense>
                            {report.keyFindings.slice(0, 3).map((finding, index) => (
                                <ListItem key={index} sx={{ pl: 0 }}>
                                    <ListItemText
                                        primary={
                                            <Typography variant="body2">
                                                {finding}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                {/* Top Recommendations */}
                {report.recommendations.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Top Recommendations
                        </Typography>
                        <List dense>
                            {report.recommendations.slice(0, 3).map((rec, index) => (
                                <ListItem key={index} sx={{ pl: 0 }}>
                                    <ListItemText
                                        primary={
                                            <Typography variant="body2">
                                                {rec}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* Actions */}
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Button
                        variant="outlined"
                        startIcon={<Visibility />}
                        onClick={() => onView?.(report.id)}
                    >
                        View Full Report
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<GetApp />}
                        onClick={() => onDownload?.(report.id)}
                    >
                        Download PDF
                    </Button>
                </Box>
            </CardContent>
        </Card>
    );
};

export default ReportPreview;