'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Grid,
    Paper,
    Typography,
    Card,
    CardContent,
    Chip,
    Button,
    CircularProgress,
    Alert,
    Tabs,
    Tab,
    LinearProgress,
    Divider,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    TrendingUp,
    Security,
    Assessment,
    AttachMoney,
    Speed,
    CheckCircle,
    Warning,
    Error,
    Info,
    Download,
    Refresh,
    Dashboard as DashboardIcon,
    Business,
    Engineering,
    AccountBalance
} from '@mui/icons-material';
import { 
    Chart as ChartJS, 
    CategoryScale, 
    LinearScale, 
    BarElement, 
    LineElement, 
    PointElement, 
    Title, 
    Tooltip as ChartTooltip, 
    Legend,
    ArcElement
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    ChartTooltip,
    Legend,
    ArcElement
);

interface ProfessionalDashboardProps {
    assessmentId: string;
    userRole?: 'cto' | 'cfo' | 'ciso' | 'engineering_lead' | 'operations_team';
}

interface DashboardData {
    assessment_overview: {
        assessment_id: string;
        organization_name: string;
        status: string;
        created_at: string;
        progress: number;
    };
    executive_kpis: {
        compliance_score: number;
        cost_optimization_potential: number;
        security_rating: string;
        implementation_readiness: number;
    };
    compliance_overview: {
        frameworks_assessed: number;
        average_score: number;
        critical_gaps: number;
        medium_gaps: number;
        estimated_remediation_timeline: string;
    };
    cost_insights: {
        current_monthly_cost: number;
        projected_annual_savings: number;
        optimization_opportunities: number;
        roi_timeline: string;
    };
    technical_metrics: {
        architecture_score: number;
        security_posture: number;
        scalability_rating: number;
        performance_index: number;
    };
    recommendations_summary: {
        critical_priority: number;
        high_priority: number;
        medium_priority: number;
        total_recommendations: number;
    };
}

const ProfessionalDashboard: React.FC<ProfessionalDashboardProps> = ({ 
    assessmentId, 
    userRole = 'cto' 
}) => {
    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTab, setSelectedTab] = useState(0);

    useEffect(() => {
        loadDashboardData();
    }, [assessmentId]);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            // In a real implementation, this would call the professional API endpoint
            const response = await fetch(`/api/assessments/${assessmentId}/dashboard-data`);
            
            if (!response.ok) {
                throw new Error('Failed to load dashboard data');
            }

            const data = await response.json();
            setDashboardData(data.dashboard_data);
        } catch (err) {
            console.error('Error loading dashboard data:', err);
            setError(err instanceof Error ? err.message : 'An error occurred');
            
            // Fallback to mock data for demonstration
            setDashboardData({
                assessment_overview: {
                    assessment_id: assessmentId,
                    organization_name: 'Novatech Industries',
                    status: 'completed',
                    created_at: new Date().toISOString(),
                    progress: 100
                },
                executive_kpis: {
                    compliance_score: 87.5,
                    cost_optimization_potential: 32.0,
                    security_rating: 'Good',
                    implementation_readiness: 85.0
                },
                compliance_overview: {
                    frameworks_assessed: 4,
                    average_score: 84.2,
                    critical_gaps: 3,
                    medium_gaps: 7,
                    estimated_remediation_timeline: '12-18 months'
                },
                cost_insights: {
                    current_monthly_cost: 12500,
                    projected_annual_savings: 186000,
                    optimization_opportunities: 8,
                    roi_timeline: '6-9 months'
                },
                technical_metrics: {
                    architecture_score: 78.0,
                    security_posture: 82.0,
                    scalability_rating: 89.0,
                    performance_index: 75.0
                },
                recommendations_summary: {
                    critical_priority: 5,
                    high_priority: 14,
                    medium_priority: 23,
                    total_recommendations: 42
                }
            });
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setSelectedTab(newValue);
    };

    const getRoleSpecificContent = () => {
        switch (userRole) {
            case 'cfo':
                return renderCFOView();
            case 'ciso':
                return renderCISOView();
            case 'engineering_lead':
                return renderEngineeringView();
            default:
                return renderCTOView();
        }
    };

    const renderExecutiveKPIs = () => {
        if (!dashboardData) return null;

        const kpis = [
            {
                title: 'Compliance Score',
                value: `${dashboardData.executive_kpis.compliance_score}%`,
                icon: <CheckCircle />,
                color: dashboardData.executive_kpis.compliance_score > 85 ? 'success' : 'warning',
                subtitle: 'Multi-framework assessment'
            },
            {
                title: 'Cost Optimization',
                value: `${dashboardData.executive_kpis.cost_optimization_potential}%`,
                icon: <AttachMoney />,
                color: 'primary',
                subtitle: 'Potential savings identified'
            },
            {
                title: 'Security Rating',
                value: dashboardData.executive_kpis.security_rating,
                icon: <Security />,
                color: 'info',
                subtitle: 'Overall security posture'
            },
            {
                title: 'Implementation Readiness',
                value: `${dashboardData.executive_kpis.implementation_readiness}%`,
                icon: <Speed />,
                color: 'secondary',
                subtitle: 'Ready for deployment'
            }
        ];

        return (
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {kpis.map((kpi, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                        <Card elevation={2}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <Box sx={{ 
                                        p: 1, 
                                        borderRadius: 1, 
                                        bgcolor: `${kpi.color}.light`,
                                        color: `${kpi.color}.dark`,
                                        mr: 2 
                                    }}>
                                        {kpi.icon}
                                    </Box>
                                    <Typography variant="h4" fontWeight="bold">
                                        {kpi.value}
                                    </Typography>
                                </Box>
                                <Typography variant="h6" gutterBottom>
                                    {kpi.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {kpi.subtitle}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        );
    };

    const renderComplianceChart = () => {
        if (!dashboardData) return null;

        const data = {
            labels: ['SOC2', 'ISO 27001', 'PCI-DSS', 'NIST'],
            datasets: [
                {
                    label: 'Compliance Score',
                    data: [89, 82, 78, 87],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 205, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                    ],
                    borderWidth: 1,
                },
            ],
        };

        const options = {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top' as const,
                },
                title: {
                    display: true,
                    text: 'Compliance Framework Scores',
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                },
            },
        };

        return <Bar data={data} options={options} />;
    };

    const renderCostProjectionsChart = () => {
        if (!dashboardData) return null;

        const data = {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [
                {
                    label: 'Current Costs',
                    data: [12500, 12800, 12600, 13200, 13100, 12900, 13400, 13600, 13300, 13800, 13500, 13900],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1,
                },
                {
                    label: 'Optimized Costs',
                    data: [12500, 12200, 11800, 11400, 11000, 10600, 10200, 9800, 9400, 9000, 8600, 8200],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.1,
                }
            ],
        };

        const options = {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top' as const,
                },
                title: {
                    display: true,
                    text: 'Cost Optimization Projections',
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value: any) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
            },
        };

        return <Line data={data} options={options} />;
    };

    const renderCTOView = () => (
        <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Compliance Framework Assessment
                    </Typography>
                    {renderComplianceChart()}
                </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Strategic Priorities
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            Critical Issues
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                            <Typography variant="h4" color="error">
                                {dashboardData?.recommendations_summary.critical_priority}
                            </Typography>
                            <Chip 
                                label="Immediate Action" 
                                color="error" 
                                size="small" 
                                sx={{ ml: 2 }} 
                            />
                        </Box>
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Box>
                        <Typography variant="body2" color="text.secondary">
                            Implementation Timeline
                        </Typography>
                        <Typography variant="h6">
                            {dashboardData?.compliance_overview.estimated_remediation_timeline}
                        </Typography>
                    </Box>
                </Paper>
            </Grid>
            <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Cost Optimization Projections
                    </Typography>
                    {renderCostProjectionsChart()}
                </Paper>
            </Grid>
        </Grid>
    );

    const renderCFOView = () => (
        <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Financial Impact Analysis
                    </Typography>
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            Current Monthly Spend
                        </Typography>
                        <Typography variant="h4" color="primary">
                            ${dashboardData?.cost_insights.current_monthly_cost.toLocaleString()}
                        </Typography>
                    </Box>
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            Projected Annual Savings
                        </Typography>
                        <Typography variant="h4" color="success.main">
                            ${dashboardData?.cost_insights.projected_annual_savings.toLocaleString()}
                        </Typography>
                    </Box>
                    <Box>
                        <Typography variant="body2" color="text.secondary">
                            ROI Timeline
                        </Typography>
                        <Typography variant="h6">
                            {dashboardData?.cost_insights.roi_timeline}
                        </Typography>
                    </Box>
                </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Investment Requirements
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2">
                            Phase 1: Critical Infrastructure
                        </Typography>
                        <LinearProgress 
                            variant="determinate" 
                            value={75} 
                            sx={{ mt: 1, mb: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                            $125,000 estimated
                        </Typography>
                    </Box>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2">
                            Phase 2: Optimization Implementation
                        </Typography>
                        <LinearProgress 
                            variant="determinate" 
                            value={45} 
                            sx={{ mt: 1, mb: 1 }}
                        />
                        <Typography variant="body2" color="text.secondary">
                            $85,000 estimated
                        </Typography>
                    </Box>
                </Paper>
            </Grid>
        </Grid>
    );

    const renderCISOView = () => (
        <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Security Compliance Overview
                    </Typography>
                    {renderComplianceChart()}
                </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Security Metrics
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            Security Posture Score
                        </Typography>
                        <Typography variant="h4">
                            {dashboardData?.technical_metrics.security_posture}%
                        </Typography>
                        <LinearProgress 
                            variant="determinate" 
                            value={dashboardData?.technical_metrics.security_posture || 0} 
                            sx={{ mt: 1 }}
                        />
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Box>
                        <Typography variant="body2" color="text.secondary">
                            Critical Security Gaps
                        </Typography>
                        <Typography variant="h4" color="error">
                            {dashboardData?.compliance_overview.critical_gaps}
                        </Typography>
                    </Box>
                </Paper>
            </Grid>
        </Grid>
    );

    const renderEngineeringView = () => (
        <Grid container spacing={3}>
            <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                        Technical Architecture Metrics
                    </Typography>
                    <Grid container spacing={3}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box textAlign="center">
                                <Typography variant="h4" color="primary">
                                    {dashboardData?.technical_metrics.architecture_score}%
                                </Typography>
                                <Typography variant="body2">Architecture Score</Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box textAlign="center">
                                <Typography variant="h4" color="secondary">
                                    {dashboardData?.technical_metrics.scalability_rating}%
                                </Typography>
                                <Typography variant="body2">Scalability Rating</Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box textAlign="center">
                                <Typography variant="h4" color="info.main">
                                    {dashboardData?.technical_metrics.performance_index}%
                                </Typography>
                                <Typography variant="body2">Performance Index</Typography>
                            </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Box textAlign="center">
                                <Typography variant="h4" color="success.main">
                                    {dashboardData?.recommendations_summary.total_recommendations}
                                </Typography>
                                <Typography variant="body2">Total Recommendations</Typography>
                            </Box>
                        </Grid>
                    </Grid>
                </Paper>
            </Grid>
        </Grid>
    );

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
                <CircularProgress />
                <Typography variant="h6" sx={{ ml: 2 }}>
                    Loading Professional Dashboard...
                </Typography>
            </Box>
        );
    }

    if (error && !dashboardData) {
        return (
            <Alert severity="error" sx={{ mb: 3 }}>
                {error}
                <Button onClick={loadDashboardData} sx={{ ml: 2 }}>
                    Retry
                </Button>
            </Alert>
        );
    }

    return (
        <Container maxWidth="xl" sx={{ py: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                    <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Professional Infrastructure Dashboard
                    </Typography>
                    <Typography variant="h6" color="text.secondary">
                        {dashboardData?.assessment_overview.organization_name} • {userRole.toUpperCase()} View
                    </Typography>
                </Box>
                <Box>
                    <Tooltip title="Refresh Data">
                        <IconButton onClick={loadDashboardData} disabled={loading}>
                            <Refresh />
                        </IconButton>
                    </Tooltip>
                    <Button
                        variant="outlined"
                        startIcon={<Download />}
                        sx={{ ml: 2 }}
                    >
                        Export Report
                    </Button>
                </Box>
            </Box>

            {/* Executive KPIs */}
            {renderExecutiveKPIs()}

            {/* Role-specific Content */}
            <Box sx={{ width: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                    <Tabs value={selectedTab} onChange={handleTabChange}>
                        <Tab icon={<DashboardIcon />} label="Overview" />
                        <Tab icon={<Business />} label="Strategic" />
                        <Tab icon={<Engineering />} label="Technical" />
                        <Tab icon={<AccountBalance />} label="Compliance" />
                    </Tabs>
                </Box>
                
                <Box>
                    {selectedTab === 0 && getRoleSpecificContent()}
                    {selectedTab === 1 && renderCTOView()}
                    {selectedTab === 2 && renderEngineeringView()}
                    {selectedTab === 3 && renderCISOView()}
                </Box>
            </Box>
        </Container>
    );
};

export default ProfessionalDashboard;