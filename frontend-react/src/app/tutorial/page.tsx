'use client';

import React, { useState } from 'react';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import FeatureWalkthrough from '@/components/FeatureWalkthrough';
import InteractiveTutorial from '@/components/InteractiveTutorial';
import {
    Box,
    Typography,
    Button,
    Container,
    Paper,
    Grid,
    Card,
    CardContent,
    Avatar,
    useTheme,
    Chip,
} from '@mui/material';
import {
    PlayArrow,
    School,
    QuestionAnswer,
    MenuBook,
    VideoLibrary,
    Support,
} from '@mui/icons-material';

export default function TutorialPage() {
    const theme = useTheme();
    const [tutorialOpen, setTutorialOpen] = useState(false);

    const learningOptions = [
        {
            title: 'Interactive Tutorial',
            description: 'Step-by-step guided tour of all features',
            icon: <PlayArrow />,
            color: theme.palette.primary.main,
            action: () => setTutorialOpen(true),
            duration: '15 minutes',
        },
        {
            title: 'Quick Start Guide',
            description: 'Essential features to get you started',
            icon: <School />,
            color: theme.palette.secondary.main,
            action: () => {
                document.getElementById('quick-start')?.scrollIntoView({ behavior: 'smooth' });
            },
            duration: '5 minutes',
        },
        {
            title: 'Video Demos',
            description: 'Watch feature demonstrations',
            icon: <VideoLibrary />,
            color: theme.palette.success.main,
            action: () => alert('Video demos coming soon!'),
            duration: 'Various',
        },
        {
            title: 'Documentation',
            description: 'Comprehensive feature documentation',
            icon: <MenuBook />,
            color: theme.palette.info.main,
            action: () => alert('Documentation portal coming soon!'),
            duration: 'Reference',
        },
        {
            title: 'Live Support',
            description: 'Get help from our experts',
            icon: <Support />,
            color: theme.palette.warning.main,
            action: () => alert('Support chat coming soon!'),
            duration: 'Real-time',
        },
        {
            title: 'FAQ',
            description: 'Frequently asked questions',
            icon: <QuestionAnswer />,
            color: theme.palette.error.main,
            action: () => alert('FAQ section coming soon!'),
            duration: 'Quick',
        },
    ];

    return (
        <ResponsiveLayout title="Tutorial & Help">
            <Container maxWidth="lg" sx={{ py: 4 }}>
                {/* Header */}
                <Box sx={{ textAlign: 'center', mb: 6 }}>
                    <Typography variant="h3" fontWeight={700} gutterBottom>
                        Learn Infra Mind
                    </Typography>
                    <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
                        Get up to speed quickly with our comprehensive learning resources and tutorials
                    </Typography>
                </Box>

                {/* Learning Options */}
                <Grid container spacing={3} sx={{ mb: 6 }}>
                    {learningOptions.map((option, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                            <Card
                                sx={{
                                    height: '100%',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-4px)',
                                        boxShadow: 4,
                                    }
                                }}
                                onClick={option.action}
                            >
                                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                                    <Avatar
                                        sx={{
                                            bgcolor: option.color,
                                            width: 64,
                                            height: 64,
                                            mx: 'auto',
                                            mb: 2,
                                        }}
                                    >
                                        {option.icon}
                                    </Avatar>
                                    <Typography variant="h6" fontWeight={600} gutterBottom>
                                        {option.title}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                        {option.description}
                                    </Typography>
                                    <Chip
                                        label={option.duration}
                                        size="small"
                                        sx={{
                                            bgcolor: `${option.color}15`,
                                            color: option.color,
                                            fontWeight: 500,
                                        }}
                                    />
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>

                {/* Quick Start Section */}
                <Paper
                    id="quick-start"
                    sx={{
                        p: 4,
                        bgcolor: 'background.paper',
                        borderRadius: 3,
                        border: '1px solid',
                        borderColor: 'divider',
                    }}
                >
                    <FeatureWalkthrough />
                </Paper>

                {/* Call to Action */}
                <Box
                    sx={{
                        textAlign: 'center',
                        mt: 6,
                        p: 4,
                        background: `linear-gradient(135deg, ${theme.palette.primary.main}15, ${theme.palette.secondary.main}15)`,
                        borderRadius: 3,
                        border: `1px solid ${theme.palette.primary.main}30`,
                    }}
                >
                    <Typography variant="h5" fontWeight={600} gutterBottom>
                        Ready to Start?
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                        Jump right into your dashboard and start exploring your infrastructure insights
                    </Typography>
                    <Button
                        variant="contained"
                        size="large"
                        href="/dashboard"
                        sx={{
                            borderRadius: 3,
                            px: 4,
                            py: 1.5,
                            fontSize: '1.1rem',
                            textTransform: 'none',
                            fontWeight: 600,
                        }}
                    >
                        Go to Dashboard
                    </Button>
                </Box>
            </Container>

            {/* Interactive Tutorial Modal */}
            <InteractiveTutorial
                open={tutorialOpen}
                onClose={() => setTutorialOpen(false)}
            />
        </ResponsiveLayout>
    );
}