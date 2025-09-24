'use client';

import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    Stepper,
    Step,
    StepLabel,
    StepContent,
    Card,
    CardContent,
    IconButton,
    Chip,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Divider,
    useTheme,
    useMediaQuery,
    Fade,
    Slide,
    Avatar,
    Paper,
    Grid,
} from '@mui/material';
import {
    Close,
    PlayArrow,
    Assessment,
    Analytics,
    CloudQueue,
    Security,
    Speed,
    AutoFixHigh,
    TrendingUp,
    Insights,
    Timeline,
    CheckCircle,
    ArrowForward,
    Dashboard,
    Settings,
    Chat,
    Report,
    Notifications,
    Group,
    MonetizationOn,
    Shield,
    Rocket,
    Star,
} from '@mui/icons-material';

interface TutorialStep {
    id: string;
    title: string;
    description: string;
    icon: React.ReactNode;
    features: string[];
    benefits: string[];
    videoPlaceholder?: string;
    color: string;
}

interface InteractiveTutorialProps {
    open: boolean;
    onClose: () => void;
}

const tutorialSteps: TutorialStep[] = [
    {
        id: 'welcome',
        title: 'Welcome to Infra Mind',
        description: 'Your AI-powered infrastructure intelligence platform that helps you optimize, secure, and scale your cloud infrastructure.',
        icon: <Rocket />,
        features: [
            'AI-powered infrastructure analysis',
            'Multi-cloud support (AWS, Azure, GCP)',
            'Real-time monitoring and alerts',
            'Automated recommendations',
            'Cost optimization insights',
            'Security compliance monitoring'
        ],
        benefits: [
            'Reduce infrastructure costs by up to 50%',
            'Improve security posture automatically',
            'Scale efficiently with AI insights',
            '24/7 intelligent monitoring'
        ],
        color: '#667eea'
    },
    {
        id: 'assessments',
        title: 'AI-Powered Assessments',
        description: 'Create comprehensive infrastructure assessments using our advanced AI agents that analyze your current setup and provide detailed recommendations.',
        icon: <Assessment />,
        features: [
            'Multi-agent AI analysis system',
            'Comprehensive infrastructure scanning',
            'Automated recommendations generation',
            'Risk assessment and mitigation',
            'Performance bottleneck identification',
            'Cost optimization suggestions'
        ],
        benefits: [
            'Get expert-level insights instantly',
            'Identify hidden infrastructure issues',
            'Receive actionable recommendations',
            'Save thousands in consulting costs'
        ],
        videoPlaceholder: 'Assessment creation and AI analysis workflow',
        color: '#667eea'
    },
    {
        id: 'dashboard',
        title: 'Intelligent Dashboard',
        description: 'Monitor your entire infrastructure from a single, comprehensive dashboard with real-time metrics and AI-driven insights.',
        icon: <Dashboard />,
        features: [
            'Real-time infrastructure metrics',
            'Interactive charts and visualizations',
            'Custom dashboard widgets',
            'Alert and notification center',
            'Multi-cloud unified view',
            'Performance trending analysis'
        ],
        benefits: [
            'Single pane of glass visibility',
            'Proactive issue detection',
            'Data-driven decision making',
            'Reduced mean time to resolution'
        ],
        videoPlaceholder: 'Dashboard overview and navigation',
        color: '#764ba2'
    },
    {
        id: 'analytics',
        title: 'Advanced Analytics',
        description: 'Dive deep into your infrastructure data with powerful analytics tools that reveal patterns, trends, and optimization opportunities.',
        icon: <Analytics />,
        features: [
            'Cost analysis and forecasting',
            'Performance metrics tracking',
            'Usage pattern analysis',
            'Resource utilization optimization',
            'Predictive analytics',
            'Custom reporting capabilities'
        ],
        benefits: [
            'Understand your infrastructure deeply',
            'Predict future capacity needs',
            'Optimize resource allocation',
            'Generate executive reports'
        ],
        videoPlaceholder: 'Analytics features and report generation',
        color: '#28a745'
    },
    {
        id: 'recommendations',
        title: 'Smart Recommendations',
        description: 'Receive intelligent, AI-generated recommendations tailored to your specific infrastructure needs and business goals.',
        icon: <AutoFixHigh />,
        features: [
            'AI-generated optimization suggestions',
            'Cost reduction recommendations',
            'Security improvement proposals',
            'Performance enhancement tips',
            'Scalability planning advice',
            'Implementation priority scoring'
        ],
        benefits: [
            'Reduce costs systematically',
            'Improve security posture',
            'Enhance performance reliability',
            'Future-proof your infrastructure'
        ],
        videoPlaceholder: 'Recommendation system and implementation',
        color: '#ffc107'
    },
    {
        id: 'security',
        title: 'Security & Compliance',
        description: 'Ensure your infrastructure meets security best practices and compliance requirements with automated monitoring and alerts.',
        icon: <Security />,
        features: [
            'Automated security scanning',
            'Compliance framework monitoring',
            'Vulnerability assessment',
            'Security policy enforcement',
            'Audit trail management',
            'Threat detection and response'
        ],
        benefits: [
            'Maintain security compliance',
            'Reduce security vulnerabilities',
            'Automate security monitoring',
            'Meet regulatory requirements'
        ],
        videoPlaceholder: 'Security monitoring and compliance features',
        color: '#dc3545'
    },
    {
        id: 'automation',
        title: 'Intelligent Automation',
        description: 'Automate routine infrastructure tasks and implement AI-driven optimizations to reduce manual work and improve efficiency.',
        icon: <Speed />,
        features: [
            'Automated remediation workflows',
            'Intelligent scaling policies',
            'Cost optimization automation',
            'Performance tuning automation',
            'Backup and recovery automation',
            'Maintenance scheduling'
        ],
        benefits: [
            'Reduce manual operational overhead',
            'Improve system reliability',
            'Ensure consistent configurations',
            'Minimize human error'
        ],
        videoPlaceholder: 'Automation features and workflow setup',
        color: '#17a2b8'
    },
    {
        id: 'getting-started',
        title: 'Getting Started',
        description: 'Ready to transform your infrastructure? Here\'s how to get started with Infra Mind in just a few simple steps.',
        icon: <CheckCircle />,
        features: [
            'Quick 5-minute setup process',
            'Guided onboarding tutorial',
            'Sample assessments and templates',
            'Integration with existing tools',
            'Expert support and documentation',
            'Free trial with full features'
        ],
        benefits: [
            'Start seeing results immediately',
            'No complex setup required',
            'Risk-free evaluation',
            'Expert guidance available'
        ],
        videoPlaceholder: 'Onboarding process and first steps',
        color: '#28a745'
    }
];

export default function InteractiveTutorial({ open, onClose }: InteractiveTutorialProps) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const [activeStep, setActiveStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

    const handleNext = () => {
        setCompletedSteps(prev => new Set([...prev, activeStep]));
        if (activeStep < tutorialSteps.length - 1) {
            setActiveStep(prev => prev + 1);
        }
    };

    const handleBack = () => {
        if (activeStep > 0) {
            setActiveStep(prev => prev - 1);
        }
    };

    const handleStepClick = (step: number) => {
        setActiveStep(step);
    };

    const currentStep = tutorialSteps[activeStep];

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="lg"
            fullWidth
            fullScreen={isMobile}
            PaperProps={{
                sx: {
                    borderRadius: isMobile ? 0 : 2,
                    maxHeight: '90vh',
                    m: isMobile ? 0 : 2,
                }
            }}
        >
            <DialogTitle
                sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    color: 'white',
                    py: 3,
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                        <PlayArrow />
                    </Avatar>
                    <Typography variant="h5" fontWeight={600}>
                        Interactive Platform Tutorial
                    </Typography>
                </Box>
                <IconButton onClick={onClose} sx={{ color: 'white' }}>
                    <Close />
                </IconButton>
            </DialogTitle>

            <DialogContent sx={{ p: 0 }}>
                <Box sx={{ height: '70vh', display: 'flex' }}>
                    {/* Stepper Sidebar */}
                    <Box
                        sx={{
                            width: isMobile ? '100%' : 300,
                            bgcolor: 'grey.50',
                            borderRight: isMobile ? 'none' : '1px solid',
                            borderColor: 'divider',
                            display: isMobile && activeStep !== -1 ? 'none' : 'block',
                        }}
                    >
                        <Box sx={{ p: 2 }}>
                            <Typography variant="h6" gutterBottom fontWeight={600}>
                                Tutorial Steps
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                Learn about all the powerful features of Infra Mind
                            </Typography>
                        </Box>

                        <Stepper
                            activeStep={activeStep}
                            orientation="vertical"
                            sx={{
                                px: 2,
                                '& .MuiStepLabel-root': {
                                    cursor: 'pointer',
                                },
                            }}
                        >
                            {tutorialSteps.map((step, index) => (
                                <Step key={step.id} completed={completedSteps.has(index)}>
                                    <StepLabel
                                        onClick={() => handleStepClick(index)}
                                        StepIconComponent={() => (
                                            <Avatar
                                                sx={{
                                                    width: 32,
                                                    height: 32,
                                                    bgcolor: activeStep === index ? step.color : 'grey.300',
                                                    color: 'white',
                                                    fontSize: '0.8rem',
                                                }}
                                            >
                                                {completedSteps.has(index) ? (
                                                    <CheckCircle sx={{ fontSize: 18 }} />
                                                ) : (
                                                    step.icon
                                                )}
                                            </Avatar>
                                        )}
                                    >
                                        <Typography
                                            variant="body2"
                                            fontWeight={activeStep === index ? 600 : 400}
                                            sx={{ ml: 1 }}
                                        >
                                            {step.title}
                                        </Typography>
                                    </StepLabel>
                                </Step>
                            ))}
                        </Stepper>
                    </Box>

                    {/* Content Area */}
                    {!isMobile || activeStep !== -1 ? (
                        <Box sx={{ flex: 1, overflow: 'auto' }}>
                            <Fade in key={activeStep} timeout={300}>
                                <Box sx={{ p: 4 }}>
                                    {/* Step Header */}
                                    <Box sx={{ mb: 4 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                                            <Avatar
                                                sx={{
                                                    bgcolor: currentStep.color,
                                                    width: 56,
                                                    height: 56,
                                                }}
                                            >
                                                {currentStep.icon}
                                            </Avatar>
                                            <Box>
                                                <Typography variant="h4" fontWeight={700} gutterBottom>
                                                    {currentStep.title}
                                                </Typography>
                                                <Chip
                                                    label={`Step ${activeStep + 1} of ${tutorialSteps.length}`}
                                                    size="small"
                                                    sx={{ bgcolor: currentStep.color, color: 'white' }}
                                                />
                                            </Box>
                                        </Box>
                                        <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600 }}>
                                            {currentStep.description}
                                        </Typography>
                                    </Box>

                                    <Grid container spacing={4}>
                                        {/* Features */}
                                        <Grid item xs={12} md={6}>
                                            <Card elevation={2}>
                                                <CardContent>
                                                    <Typography variant="h6" gutterBottom fontWeight={600}>
                                                        <Star sx={{ mr: 1, verticalAlign: 'middle', color: currentStep.color }} />
                                                        Key Features
                                                    </Typography>
                                                    <List dense>
                                                        {currentStep.features.map((feature, index) => (
                                                            <ListItem key={index} sx={{ px: 0 }}>
                                                                <ListItemIcon sx={{ minWidth: 36 }}>
                                                                    <CheckCircle
                                                                        sx={{
                                                                            color: currentStep.color,
                                                                            fontSize: 20
                                                                        }}
                                                                    />
                                                                </ListItemIcon>
                                                                <ListItemText
                                                                    primary={feature}
                                                                    primaryTypographyProps={{ variant: 'body2' }}
                                                                />
                                                            </ListItem>
                                                        ))}
                                                    </List>
                                                </CardContent>
                                            </Card>
                                        </Grid>

                                        {/* Benefits */}
                                        <Grid item xs={12} md={6}>
                                            <Card elevation={2}>
                                                <CardContent>
                                                    <Typography variant="h6" gutterBottom fontWeight={600}>
                                                        <TrendingUp sx={{ mr: 1, verticalAlign: 'middle', color: currentStep.color }} />
                                                        Benefits
                                                    </Typography>
                                                    <List dense>
                                                        {currentStep.benefits.map((benefit, index) => (
                                                            <ListItem key={index} sx={{ px: 0 }}>
                                                                <ListItemIcon sx={{ minWidth: 36 }}>
                                                                    <ArrowForward
                                                                        sx={{
                                                                            color: currentStep.color,
                                                                            fontSize: 20
                                                                        }}
                                                                    />
                                                                </ListItemIcon>
                                                                <ListItemText
                                                                    primary={benefit}
                                                                    primaryTypographyProps={{ variant: 'body2' }}
                                                                />
                                                            </ListItem>
                                                        ))}
                                                    </List>
                                                </CardContent>
                                            </Card>
                                        </Grid>

                                        {/* Video Placeholder */}
                                        {currentStep.videoPlaceholder && (
                                            <Grid item xs={12}>
                                                <Card elevation={2}>
                                                    <CardContent>
                                                        <Typography variant="h6" gutterBottom fontWeight={600}>
                                                            <PlayArrow sx={{ mr: 1, verticalAlign: 'middle', color: currentStep.color }} />
                                                            Video Demonstration
                                                        </Typography>
                                                        <Paper
                                                            sx={{
                                                                height: 250,
                                                                bgcolor: 'grey.100',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                borderRadius: 2,
                                                                position: 'relative',
                                                                background: `linear-gradient(135deg, ${currentStep.color}15, ${currentStep.color}05)`,
                                                                border: `2px dashed ${currentStep.color}40`,
                                                            }}
                                                        >
                                                            <Box sx={{ textAlign: 'center', p: 4 }}>
                                                                <Avatar
                                                                    sx={{
                                                                        bgcolor: currentStep.color,
                                                                        width: 64,
                                                                        height: 64,
                                                                        mx: 'auto',
                                                                        mb: 2,
                                                                    }}
                                                                >
                                                                    <PlayArrow sx={{ fontSize: 32 }} />
                                                                </Avatar>
                                                                <Typography variant="h6" gutterBottom>
                                                                    Interactive Demo Coming Soon
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    {currentStep.videoPlaceholder}
                                                                </Typography>
                                                                <Button
                                                                    variant="contained"
                                                                    startIcon={<PlayArrow />}
                                                                    sx={{
                                                                        mt: 2,
                                                                        bgcolor: currentStep.color,
                                                                        '&:hover': {
                                                                            bgcolor: currentStep.color,
                                                                            opacity: 0.9,
                                                                        }
                                                                    }}
                                                                    onClick={() => {
                                                                        // TODO: Implement video player or guided tour
                                                                        alert('Video demo will be available soon!');
                                                                    }}
                                                                >
                                                                    Watch Demo
                                                                </Button>
                                                            </Box>
                                                        </Paper>
                                                    </CardContent>
                                                </Card>
                                            </Grid>
                                        )}
                                    </Grid>
                                </Box>
                            </Fade>
                        </Box>
                    ) : null}
                </Box>
            </DialogContent>

            <DialogActions sx={{ p: 3, bgcolor: 'grey.50' }}>
                <Box sx={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Button
                        onClick={handleBack}
                        disabled={activeStep === 0}
                        variant="outlined"
                    >
                        Previous
                    </Button>

                    <Typography variant="body2" color="text.secondary">
                        {activeStep + 1} of {tutorialSteps.length}
                    </Typography>

                    {activeStep === tutorialSteps.length - 1 ? (
                        <Button
                            onClick={onClose}
                            variant="contained"
                            sx={{ bgcolor: currentStep.color }}
                        >
                            Get Started
                        </Button>
                    ) : (
                        <Button
                            onClick={handleNext}
                            variant="contained"
                            endIcon={<ArrowForward />}
                            sx={{ bgcolor: currentStep.color }}
                        >
                            Next
                        </Button>
                    )}
                </Box>
            </DialogActions>
        </Dialog>
    );
}