'use client';

import React, { useState } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Button,
    Box,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Chip,
    Avatar,
    Paper,
    IconButton,
    Collapse,
    useTheme,
} from '@mui/material';
import {
    PlayArrow,
    ExpandMore,
    ExpandLess,
    CheckCircle,
    Assessment,
    Dashboard,
    Analytics,
    Security,
    AutoFixHigh,
    Speed,
    CloudQueue,
    TrendingUp,
} from '@mui/icons-material';

interface FeatureGuideProps {
    compact?: boolean;
    showOnlyBasics?: boolean;
}

const quickStartGuides = [
    {
        id: 'dashboard',
        title: 'Navigate the Dashboard',
        description: 'Get familiar with your main control center',
        icon: <Dashboard />,
        color: '#667eea',
        steps: [
            'Explore real-time infrastructure metrics',
            'View system health indicators',
            'Check recent alerts and notifications',
            'Access quick action buttons'
        ],
        estimatedTime: '2 minutes'
    },
    {
        id: 'assessment',
        title: 'Create Your First Assessment',
        description: 'Let AI analyze your infrastructure',
        icon: <Assessment />,
        color: '#764ba2',
        steps: [
            'Click "New Assessment" button',
            'Select your cloud providers',
            'Configure assessment parameters',
            'Review AI-generated recommendations'
        ],
        estimatedTime: '5 minutes'
    },
    {
        id: 'analytics',
        title: 'Explore Analytics',
        description: 'Dive deep into your data insights',
        icon: <Analytics />,
        color: '#28a745',
        steps: [
            'Visit the Analytics dashboard',
            'Review cost analysis charts',
            'Check performance trends',
            'Generate custom reports'
        ],
        estimatedTime: '3 minutes'
    },
    {
        id: 'security',
        title: 'Security Monitoring',
        description: 'Keep your infrastructure secure',
        icon: <Security />,
        color: '#dc3545',
        steps: [
            'Check security compliance status',
            'Review vulnerability assessments',
            'Configure security alerts',
            'View audit logs and reports'
        ],
        estimatedTime: '4 minutes'
    }
];

const advancedFeatures = [
    {
        id: 'automation',
        title: 'Automation & Workflows',
        icon: <Speed />,
        color: '#17a2b8',
        description: 'Set up intelligent automation'
    },
    {
        id: 'recommendations',
        title: 'AI Recommendations',
        icon: <AutoFixHigh />,
        color: '#ffc107',
        description: 'Implement optimization suggestions'
    },
    {
        id: 'multicloud',
        title: 'Multi-Cloud Management',
        icon: <CloudQueue />,
        color: '#6f42c1',
        description: 'Manage multiple cloud providers'
    }
];

export default function FeatureWalkthrough({ compact = false, showOnlyBasics = false }: FeatureGuideProps) {
    const theme = useTheme();
    const [expandedGuide, setExpandedGuide] = useState<string | null>(null);

    const handleToggleGuide = (guideId: string) => {
        setExpandedGuide(expandedGuide === guideId ? null : guideId);
    };

    return (
        <Box>
            {/* Header */}
            {!compact && (
                <Box sx={{ mb: 4, textAlign: 'center' }}>
                    <Typography variant="h4" color="text.primary" fontWeight={700} gutterBottom>
                        Quick Start Guide
                    </Typography>
                    <Typography variant="h6" color="text.secondary">
                        Get up and running in minutes with these essential features
                    </Typography>
                </Box>
            )}

            {/* Quick Start Guides */}
            <Box sx={{ mb: showOnlyBasics ? 0 : 4 }}>
                {compact && (
                    <Typography variant="h6" color="text.primary" fontWeight={600} sx={{ mb: 2 }}>
                        Essential Features
                    </Typography>
                )}

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {quickStartGuides.map((guide) => (
                        <Card key={guide.id} elevation={2}>
                            <CardContent sx={{ p: compact ? 2 : 3 }}>
                                <Box
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        cursor: 'pointer'
                                    }}
                                    onClick={() => handleToggleGuide(guide.id)}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Avatar
                                            sx={{
                                                bgcolor: guide.color,
                                                width: compact ? 40 : 48,
                                                height: compact ? 40 : 48,
                                            }}
                                        >
                                            {guide.icon}
                                        </Avatar>
                                        <Box>
                                            <Typography variant="h6" color="text.primary" fontWeight={600}>
                                                {guide.title}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {guide.description}
                                            </Typography>
                                            <Chip
                                                label={guide.estimatedTime}
                                                size="small"
                                                sx={{
                                                    mt: 1,
                                                    bgcolor: `${guide.color}15`,
                                                    color: guide.color,
                                                    fontWeight: 500
                                                }}
                                            />
                                        </Box>
                                    </Box>
                                    <IconButton>
                                        {expandedGuide === guide.id ? <ExpandLess /> : <ExpandMore />}
                                    </IconButton>
                                </Box>

                                <Collapse in={expandedGuide === guide.id}>
                                    <Box sx={{ mt: 3, pl: compact ? 0 : 7 }}>
                                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                                            Steps to follow:
                                        </Typography>
                                        <List dense>
                                            {guide.steps.map((step, index) => (
                                                <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                                                    <ListItemIcon sx={{ minWidth: 32 }}>
                                                        <Box
                                                            sx={{
                                                                width: 24,
                                                                height: 24,
                                                                borderRadius: '50%',
                                                                bgcolor: guide.color,
                                                                color: 'white',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                fontSize: '0.75rem',
                                                                fontWeight: 600
                                                            }}
                                                        >
                                                            {index + 1}
                                                        </Box>
                                                    </ListItemIcon>
                                                    <ListItemText
                                                        primary={step}
                                                        primaryTypographyProps={{
                                                            variant: 'body2',
                                                            sx: { fontWeight: 500 }
                                                        }}
                                                    />
                                                </ListItem>
                                            ))}
                                        </List>

                                        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                                            <Button
                                                variant="contained"
                                                size="small"
                                                startIcon={<PlayArrow />}
                                                sx={{
                                                    bgcolor: guide.color,
                                                    '&:hover': {
                                                        bgcolor: guide.color,
                                                        opacity: 0.9
                                                    }
                                                }}
                                                onClick={() => {
                                                    // TODO: Implement guided tour for this feature
                                                    alert(`Starting guided tour for ${guide.title}`);
                                                }}
                                            >
                                                Start Guide
                                            </Button>
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                sx={{
                                                    borderColor: guide.color,
                                                    color: guide.color
                                                }}
                                                onClick={() => {
                                                    // TODO: Mark as completed
                                                    alert(`Marked ${guide.title} as completed`);
                                                }}
                                            >
                                                Mark Complete
                                            </Button>
                                        </Box>
                                    </Box>
                                </Collapse>
                            </CardContent>
                        </Card>
                    ))}
                </Box>
            </Box>

            {/* Advanced Features */}
            {!showOnlyBasics && (
                <Box>
                    <Typography variant="h6" color="text.primary" fontWeight={600} sx={{ mb: 2 }}>
                        Advanced Features
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Once you're comfortable with the basics, explore these powerful capabilities
                    </Typography>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {advancedFeatures.map((feature) => (
                            <Paper
                                key={feature.id}
                                sx={{
                                    p: 3,
                                    background: `linear-gradient(135deg, ${feature.color}08, ${feature.color}03)`,
                                    border: `1px solid ${feature.color}20`,
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        transform: 'translateY(-2px)',
                                        boxShadow: 2
                                    }
                                }}
                                onClick={() => {
                                    // TODO: Navigate to feature or open tutorial
                                    alert(`Opening ${feature.title} tutorial`);
                                }}
                            >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <Avatar
                                        sx={{
                                            bgcolor: feature.color,
                                            width: 48,
                                            height: 48,
                                        }}
                                    >
                                        {feature.icon}
                                    </Avatar>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="h6" color="text.primary" fontWeight={600}>
                                            {feature.title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {feature.description}
                                        </Typography>
                                    </Box>
                                    <Button
                                        variant="contained"
                                        size="small"
                                        sx={{
                                            bgcolor: feature.color,
                                            '&:hover': {
                                                bgcolor: feature.color,
                                                opacity: 0.9
                                            }
                                        }}
                                    >
                                        Learn More
                                    </Button>
                                </Box>
                            </Paper>
                        ))}
                    </Box>
                </Box>
            )}

            {/* Help Card */}
            {!compact && (
                <Card sx={{ mt: 4, bgcolor: 'primary.main', color: 'white' }}>
                    <CardContent>
                        <Typography variant="h6" color="text.primary" fontWeight={600} gutterBottom>
                            Need Help?
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                            Our support team is here to help you get the most out of Infra Mind.
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <Button
                                variant="contained"
                                size="small"
                                sx={{
                                    bgcolor: 'white',
                                    color: 'primary.main',
                                    '&:hover': {
                                        bgcolor: 'grey.100'
                                    }
                                }}
                                onClick={() => {
                                    // TODO: Open support chat or contact form
                                    alert('Opening support chat');
                                }}
                            >
                                Contact Support
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                sx={{
                                    borderColor: 'white',
                                    color: 'white',
                                    '&:hover': {
                                        borderColor: 'white',
                                        bgcolor: 'rgba(255,255,255,0.1)'
                                    }
                                }}
                                onClick={() => {
                                    // TODO: Open documentation
                                    alert('Opening documentation');
                                }}
                            >
                                View Docs
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}