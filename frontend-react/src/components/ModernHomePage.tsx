'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Button,
    Container,
    Card,
    CardContent,
    Avatar,
    Chip,
    IconButton,
    useTheme,
    useMediaQuery,
    Fade,
    Slide,
    Zoom,
    Grid,
    Stack,
    Paper,
    Divider,
} from '@mui/material';
import {
    CloudQueue,
    Assessment,
    Analytics,
    Security,
    Speed,
    TrendingUp,
    AutoFixHigh,
    Insights,
    ArrowForward,
    PlayArrow,
    Star,
    CheckCircle,
    Rocket,
    Shield,
    Timeline,
} from '@mui/icons-material';
import ResponsiveGrid from './ResponsiveGrid';
import ResponsiveCard from './ResponsiveCard';
import InteractiveTutorial from './InteractiveTutorial';
import { useRouter } from 'next/navigation';

interface FeatureCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    color: string;
    delay: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, color, delay }) => {
    const [visible, setVisible] = useState(false);
    
    useEffect(() => {
        const timer = setTimeout(() => setVisible(true), delay);
        return () => clearTimeout(timer);
    }, [delay]);

    return (
        <Fade in={visible} timeout={1000}>
            <Card 
                sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: 4,
                    }
                }}
            >
                <CardContent sx={{ flex: 1, textAlign: 'center', p: 3 }}>
                    <Avatar 
                        sx={{ 
                            bgcolor: color, 
                            width: 64, 
                            height: 64, 
                            mx: 'auto', 
                            mb: 2 
                        }}
                    >
                        {icon}
                    </Avatar>
                    <Typography variant="h6" gutterBottom fontWeight={600}>
                        {title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        {description}
                    </Typography>
                </CardContent>
            </Card>
        </Fade>
    );
};

interface StatCardProps {
    value: string;
    label: string;
    icon: React.ReactNode;
    color: string;
    delay: number;
}

const StatCard: React.FC<StatCardProps> = ({ value, label, icon, color, delay }) => {
    const [visible, setVisible] = useState(false);
    const [animate, setAnimate] = useState(false);
    
    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(true);
            setTimeout(() => setAnimate(true), 200);
        }, delay);
        return () => clearTimeout(timer);
    }, [delay]);

    return (
        <Zoom in={visible} timeout={800}>
            <Paper 
                elevation={2}
                sx={{
                    p: 3,
                    textAlign: 'center',
                    borderRadius: 3,
                    background: `linear-gradient(135deg, ${color}15, ${color}05)`,
                    border: `1px solid ${color}30`,
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                        transform: 'scale(1.05)',
                        boxShadow: 3,
                    }
                }}
            >
                <Box sx={{ color, mb: 1 }}>
                    {icon}
                </Box>
                <Typography 
                    variant="h4" 
                    fontWeight={700} 
                    color={color}
                    sx={{
                        transform: animate ? 'scale(1)' : 'scale(0.8)',
                        transition: 'transform 0.5s ease-out',
                    }}
                >
                    {value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {label}
                </Typography>
            </Paper>
        </Zoom>
    );
};

export default function ModernHomePage() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const isTablet = useMediaQuery(theme.breakpoints.down('md'));
    const router = useRouter();

    const [heroVisible, setHeroVisible] = useState(false);
    const [tutorialOpen, setTutorialOpen] = useState(false);

    useEffect(() => {
        setHeroVisible(true);
    }, []);

    const features = [
        {
            icon: <Assessment />,
            title: 'AI-Powered Assessments',
            description: 'Comprehensive infrastructure analysis using advanced AI agents with real-time recommendations.',
            color: theme.palette.primary.main,
        },
        {
            icon: <Analytics />,
            title: 'Advanced Analytics',
            description: 'Deep insights into your infrastructure performance, costs, and optimization opportunities.',
            color: theme.palette.secondary.main,
        },
        {
            icon: <Security />,
            title: 'Security & Compliance',
            description: 'Automated security scanning and compliance monitoring across all cloud environments.',
            color: theme.palette.success.main,
        },
        {
            icon: <Speed />,
            title: 'Performance Optimization',
            description: 'Real-time performance monitoring with intelligent scaling and optimization suggestions.',
            color: theme.palette.warning.main,
        },
        {
            icon: <CloudQueue />,
            title: 'Multi-Cloud Support',
            description: 'Unified management across AWS, Azure, GCP, and hybrid cloud environments.',
            color: theme.palette.info.main,
        },
        {
            icon: <AutoFixHigh />,
            title: 'Automated Remediation',
            description: 'Intelligent automation for common infrastructure issues and optimization tasks.',
            color: theme.palette.error.main,
        },
    ];

    const stats = [
        {
            value: '99.9%',
            label: 'Uptime Guarantee',
            icon: <Shield fontSize="large" />,
            color: theme.palette.success.main,
        },
        {
            value: '50%',
            label: 'Cost Reduction',
            icon: <TrendingUp fontSize="large" />,
            color: theme.palette.primary.main,
        },
        {
            value: '24/7',
            label: 'AI Monitoring',
            icon: <Insights fontSize="large" />,
            color: theme.palette.secondary.main,
        },
        {
            value: '10x',
            label: 'Faster Deployments',
            icon: <Rocket fontSize="large" />,
            color: theme.palette.warning.main,
        },
    ];

    return (
        <Box sx={{ minHeight: '100vh', overflow: 'hidden' }}>
            {/* Hero Section */}
            <Box 
                sx={{
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}10, ${theme.palette.secondary.main}10)`,
                    minHeight: { xs: '80vh', md: '90vh' },
                    display: 'flex',
                    alignItems: 'center',
                    position: 'relative',
                    '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'radial-gradient(circle at 30% 40%, rgba(59, 130, 246, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
                        pointerEvents: 'none',
                    }
                }}
            >
                <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
                    <Grid container alignItems="center" spacing={4}>
                        <Grid item xs={12} md={6}>
                            <Slide direction="right" in={heroVisible} timeout={1000}>
                                <Box>
                                    <Chip 
                                        label="AI-Powered Infrastructure" 
                                        color="primary" 
                                        sx={{ mb: 2 }}
                                    />
                                    <Typography
                                        variant={isMobile ? "h3" : "h1"}
                                        component="h1"
                                        fontWeight={700}
                                        gutterBottom
                                        sx={{
                                            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                                            backgroundClip: 'text',
                                            WebkitBackgroundClip: 'text',
                                            WebkitTextFillColor: 'transparent',
                                            mb: 3,
                                        }}
                                    >
                                        Scale Your Infrastructure with AI Intelligence
                                    </Typography>
                                    <Typography 
                                        variant={isMobile ? "body1" : "h6"} 
                                        color="text.secondary"
                                        sx={{ mb: 4, maxWidth: 500 }}
                                    >
                                        Harness the power of AI to optimize, secure, and scale your cloud infrastructure. 
                                        Get intelligent recommendations from our multi-agent AI system.
                                    </Typography>
                                    <Stack 
                                        direction={isMobile ? "column" : "row"}
                                        spacing={2}
                                        alignItems={isMobile ? "stretch" : "center"}
                                    >
                                        <Button
                                            variant="contained"
                                            size="large"
                                            endIcon={<ArrowForward />}
                                            onClick={() => router.push('/auth/login')}
                                            sx={{
                                                borderRadius: 3,
                                                px: 4,
                                                py: 1.5,
                                                fontSize: '1.1rem',
                                                textTransform: 'none',
                                                fontWeight: 600,
                                            }}
                                        >
                                            Start Assessment
                                        </Button>
                                        <Button
                                            variant="outlined"
                                            size="large"
                                            startIcon={<PlayArrow />}
                                            onClick={() => setTutorialOpen(true)}
                                            sx={{
                                                borderRadius: 3,
                                                px: 4,
                                                py: 1.5,
                                                fontSize: '1.1rem',
                                                textTransform: 'none',
                                                fontWeight: 600,
                                            }}
                                        >
                                            Interactive Tutorial
                                        </Button>
                                    </Stack>
                                </Box>
                            </Slide>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Slide direction="left" in={heroVisible} timeout={1200}>
                                <Box
                                    sx={{
                                        display: { xs: 'none', md: 'flex' },
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        height: 400,
                                        position: 'relative',
                                    }}
                                >
                                    {/* Simple clean design */}
                                    <Box
                                        sx={{
                                            width: 300,
                                            height: 200,
                                            background: `linear-gradient(135deg, ${theme.palette.primary.main}20, ${theme.palette.secondary.main}20)`,
                                            borderRadius: 4,
                                            border: `2px solid ${theme.palette.primary.main}40`,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            backdropFilter: 'blur(10px)',
                                        }}
                                    >
                                        <Typography
                                            variant="h4"
                                            sx={{
                                                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                                                backgroundClip: 'text',
                                                WebkitBackgroundClip: 'text',
                                                WebkitTextFillColor: 'transparent',
                                                fontWeight: 700,
                                                textAlign: 'center',
                                            }}
                                        >
                                            Infra Mind
                                        </Typography>
                                    </Box>
                                </Box>
                            </Slide>
                        </Grid>
                    </Grid>
                </Container>
            </Box>

            {/* Stats Section */}
            <Container maxWidth="lg" sx={{ py: 8 }}>
                <Typography 
                    variant="h3" 
                    align="center" 
                    fontWeight={600} 
                    gutterBottom
                    sx={{ mb: 6 }}
                >
                    Proven Results
                </Typography>
                <ResponsiveGrid 
                    columns={{ xs: 2, sm: 2, md: 4, lg: 4 }}
                    spacing={3}
                    container={false}
                >
                    {stats.map((stat, index) => (
                        <StatCard 
                            key={index}
                            {...stat}
                            delay={index * 200}
                        />
                    ))}
                </ResponsiveGrid>
            </Container>

            {/* Features Section */}
            <Box sx={{ bgcolor: 'background.default', py: 8 }}>
                <Container maxWidth="lg">
                    <Typography 
                        variant="h3" 
                        align="center" 
                        fontWeight={600} 
                        gutterBottom
                        sx={{ mb: 2 }}
                    >
                        Powerful Features
                    </Typography>
                    <Typography 
                        variant="h6" 
                        align="center" 
                        color="text.secondary"
                        sx={{ mb: 6, maxWidth: 600, mx: 'auto' }}
                    >
                        Everything you need to manage and optimize your cloud infrastructure with AI intelligence
                    </Typography>
                    
                    <ResponsiveGrid 
                        columns={{ xs: 1, sm: 2, md: 3, lg: 3 }}
                        spacing={4}
                        container={false}
                    >
                        {features.map((feature, index) => (
                            <FeatureCard
                                key={index}
                                {...feature}
                                delay={index * 150}
                            />
                        ))}
                    </ResponsiveGrid>
                </Container>
            </Box>

            {/* CTA Section */}
            <Box 
                sx={{
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    color: 'white',
                    py: 8,
                }}
            >
                <Container maxWidth="md" sx={{ textAlign: 'center' }}>
                    <Typography variant="h3" fontWeight={600} gutterBottom>
                        Ready to Transform Your Infrastructure?
                    </Typography>
                    <Typography variant="h6" sx={{ mb: 4, opacity: 0.9 }}>
                        Join thousands of companies already using AI to optimize their cloud infrastructure
                    </Typography>
                    <Stack 
                        direction={isMobile ? "column" : "row"}
                        spacing={3}
                        justifyContent="center"
                        alignItems="center"
                    >
                        <Button
                            variant="contained"
                            size="large"
                            endIcon={<ArrowForward />}
                            onClick={() => router.push('/auth/login')}
                            sx={{
                                bgcolor: 'white',
                                color: theme.palette.primary.main,
                                borderRadius: 3,
                                px: 4,
                                py: 1.5,
                                fontSize: '1.1rem',
                                textTransform: 'none',
                                fontWeight: 600,
                                '&:hover': {
                                    bgcolor: 'grey.100',
                                }
                            }}
                        >
                            Start Free Assessment
                        </Button>
                        <Button
                            variant="outlined"
                            size="large"
                            startIcon={<PlayArrow />}
                            onClick={() => setTutorialOpen(true)}
                            sx={{
                                borderColor: 'white',
                                color: 'white',
                                borderRadius: 3,
                                px: 4,
                                py: 1.5,
                                fontSize: '1.1rem',
                                textTransform: 'none',
                                fontWeight: 600,
                                '&:hover': {
                                    borderColor: 'white',
                                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                                }
                            }}
                        >
                            Watch Tutorial
                        </Button>
                    </Stack>
                </Container>
            </Box>

            {/* Footer */}
            <Box sx={{ bgcolor: 'grey.900', color: 'white', py: 4, mt: 2 }}>
                <Container maxWidth="lg">
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: { xs: 'column', md: 'row' },
                            justifyContent: 'space-between',
                            alignItems: { xs: 'flex-start', md: 'center' },
                            gap: 2,
                        }}
                    >
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                Infra Mind
                            </Typography>
                            <Typography variant="body2" color="grey.400">
                                Empowering businesses to strategically plan and scale their AI infrastructure with confidence.
                            </Typography>
                        </Box>
                        <Typography variant="body2" color="grey.400">
                            © 2025 Infra Mind. All rights reserved.
                        </Typography>
                    </Box>
                </Container>
            </Box>

            {/* Interactive Tutorial */}
            <InteractiveTutorial
                open={tutorialOpen}
                onClose={() => setTutorialOpen(false)}
            />
        </Box>
    );
}