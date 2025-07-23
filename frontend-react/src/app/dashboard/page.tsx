'use client';

import React from 'react';
import {
    Container,
    Box,
    Card,
    CardContent,
    Button,
    Avatar,
    Typography,
    Chip,
    LinearProgress,
} from '@mui/material';
import {
    Assessment,
    GetApp,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import Navigation from '@/components/Navigation';
import CostComparisonChart from '@/components/charts/CostComparisonChart';
import RecommendationScoreChart from '@/components/charts/RecommendationScoreChart';
import AssessmentResultsChart from '@/components/charts/AssessmentResultsChart';
import RecommendationTable from '@/components/RecommendationTable';
import ReportPreview from '@/components/ReportPreview';

export default function DashboardPage() {
    const router = useRouter();

    return (
        <Navigation title="Dashboard">
            <Container maxWidth="lg">
                {/* Welcome Section */}
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        Welcome back!
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Here&apos;s an overview of your AI infrastructure assessment progress.
                    </Typography>
                </Box>

                {/* Quick Actions */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3, mb: 4 }}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Start Assessment
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Begin your AI infrastructure evaluation
                            </Typography>
                            <Button
                                variant="contained"
                                fullWidth
                                onClick={() => router.push('/assessment')}
                            >
                                Start Now
                            </Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                View Reports
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Access your generated reports
                            </Typography>
                            <Button
                                variant="outlined"
                                fullWidth
                                onClick={() => router.push('/reports')}
                            >
                                View Reports
                            </Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Cloud Services
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Explore cloud recommendations
                            </Typography>
                            <Button
                                variant="outlined"
                                fullWidth
                                onClick={() => router.push('/cloud-services')}
                            >
                                Explore
                            </Button>
                        </CardContent>
                    </Card>
                </Box>

                {/* Data Visualization Section */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
                    {/* Cost Comparison Chart */}
                    <Box>
                        <CostComparisonChart
                            data={[
                                {
                                    provider: 'AWS',
                                    compute: 1200,
                                    storage: 300,
                                    networking: 150,
                                    total: 1650,
                                    color: '#FF9900'
                                },
                                {
                                    provider: 'Azure',
                                    compute: 1100,
                                    storage: 280,
                                    networking: 120,
                                    total: 1500,
                                    color: '#0078D4'
                                },
                                {
                                    provider: 'GCP',
                                    compute: 1050,
                                    storage: 250,
                                    networking: 100,
                                    total: 1400,
                                    color: '#4285F4'
                                }
                            ]}
                            title="Monthly Cost Comparison"
                            showBreakdown={true}
                        />
                    </Box>

                    {/* Recommendation Score Chart */}
                    <Box>
                        <RecommendationScoreChart
                            data={[
                                {
                                    service: 'EC2 Instances',
                                    costEfficiency: 85,
                                    performance: 90,
                                    scalability: 95,
                                    security: 88,
                                    compliance: 92,
                                    businessAlignment: 87,
                                    provider: 'AWS',
                                    color: '#FF9900'
                                },
                                {
                                    service: 'Azure VMs',
                                    costEfficiency: 82,
                                    performance: 88,
                                    scalability: 90,
                                    security: 90,
                                    compliance: 95,
                                    businessAlignment: 85,
                                    provider: 'Azure',
                                    color: '#0078D4'
                                },
                                {
                                    service: 'Compute Engine',
                                    costEfficiency: 88,
                                    performance: 85,
                                    scalability: 92,
                                    security: 87,
                                    compliance: 90,
                                    businessAlignment: 89,
                                    provider: 'GCP',
                                    color: '#4285F4'
                                }
                            ]}
                            title="Service Performance Scores"
                        />
                    </Box>
                </Box>

                {/* Assessment Results Chart */}
                <Box sx={{ mb: 4 }}>
                    <AssessmentResultsChart
                        data={[
                            {
                                category: 'Infrastructure Readiness',
                                currentScore: 75,
                                targetScore: 90,
                                improvement: 15,
                                color: '#8884d8'
                            },
                            {
                                category: 'Security & Compliance',
                                currentScore: 82,
                                targetScore: 95,
                                improvement: 13,
                                color: '#82ca9d'
                            },
                            {
                                category: 'Cost Optimization',
                                currentScore: 68,
                                targetScore: 85,
                                improvement: 17,
                                color: '#ffc658'
                            },
                            {
                                category: 'Scalability',
                                currentScore: 71,
                                targetScore: 88,
                                improvement: 17,
                                color: '#ff7300'
                            },
                            {
                                category: 'Performance',
                                currentScore: 79,
                                targetScore: 92,
                                improvement: 13,
                                color: '#00ff88'
                            }
                        ]}
                        title="AI Infrastructure Assessment Results"
                        showComparison={true}
                    />
                </Box>

                {/* Recommendation Table */}
                <Box sx={{ mb: 4 }}>
                    <RecommendationTable
                        recommendations={[
                            {
                                id: '1',
                                serviceName: 'Amazon EC2 t3.large',
                                provider: 'AWS' as const,
                                serviceType: 'Compute',
                                costEstimate: 67.32,
                                confidenceScore: 92,
                                businessAlignment: 88,
                                implementationComplexity: 'Low' as const,
                                pros: ['High availability', 'Auto-scaling capabilities', 'Extensive documentation'],
                                cons: ['Higher cost than alternatives', 'Complex pricing model'],
                                status: 'recommended' as const
                            },
                            {
                                id: '2',
                                serviceName: 'Azure Standard_D4s_v3',
                                provider: 'Azure' as const,
                                serviceType: 'Compute',
                                costEstimate: 62.05,
                                confidenceScore: 89,
                                businessAlignment: 85,
                                implementationComplexity: 'Medium' as const,
                                pros: ['Good integration with Microsoft ecosystem', 'Competitive pricing'],
                                cons: ['Limited availability zones', 'Steeper learning curve'],
                                status: 'alternative' as const
                            },
                            {
                                id: '3',
                                serviceName: 'Google Cloud n1-standard-4',
                                provider: 'GCP' as const,
                                serviceType: 'Compute',
                                costEstimate: 58.90,
                                confidenceScore: 85,
                                businessAlignment: 82,
                                implementationComplexity: 'Medium' as const,
                                pros: ['Best price-performance ratio', 'Excellent machine learning integration'],
                                cons: ['Smaller market share', 'Limited enterprise support'],
                                status: 'alternative' as const
                            }
                        ]}
                        title="Top Service Recommendations"
                    />
                </Box>

                {/* Report Preview and Progress */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 4 }}>
                    {/* Report Preview */}
                    <Box>
                        <ReportPreview
                            report={{
                                id: 'report-1',
                                title: 'AI Infrastructure Strategy Report - Sample Corp',
                                generatedDate: '2024-01-15T10:30:00Z',
                                status: 'final' as const,
                                sections: [
                                    {
                                        title: 'Executive Summary',
                                        content: 'This report provides comprehensive recommendations for scaling AI infrastructure...',
                                        type: 'executive' as const
                                    },
                                    {
                                        title: 'Technical Architecture',
                                        content: 'Detailed technical specifications and implementation roadmap...',
                                        type: 'technical' as const
                                    },
                                    {
                                        title: 'Cost Analysis',
                                        content: 'Financial projections and ROI calculations for the proposed infrastructure...',
                                        type: 'financial' as const
                                    }
                                ],
                                keyFindings: [
                                    'Multi-cloud strategy can reduce costs by 23%',
                                    'Current infrastructure is over-provisioned by 35%',
                                    'Compliance gaps identified in data storage'
                                ],
                                recommendations: [
                                    'Implement hybrid AWS-Azure architecture',
                                    'Migrate to containerized workloads',
                                    'Establish automated compliance monitoring'
                                ],
                                estimatedSavings: 45000,
                                complianceScore: 98
                            }}
                            onDownload={(reportId) => console.log('Download report:', reportId)}
                            onView={(reportId) => console.log('View report:', reportId)}
                        />
                    </Box>

                    {/* Progress Overview */}
                    <Box>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Assessment Progress
                                </Typography>
                                <Box sx={{ mb: 2 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2">Overall Progress</Typography>
                                        <Typography variant="body2">65%</Typography>
                                    </Box>
                                    <LinearProgress variant="determinate" value={65} />
                                </Box>
                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 3 }}>
                                    <Chip label="Business Requirements" color="success" size="small" />
                                    <Chip label="Technical Assessment" color="primary" size="small" />
                                    <Chip label="Compliance Review" color="default" size="small" />
                                </Box>

                                <Typography variant="h6" gutterBottom>
                                    Recent Activity
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                            <Assessment />
                                        </Avatar>
                                        <Box>
                                            <Typography variant="body2">Assessment started</Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                2 hours ago
                                            </Typography>
                                        </Box>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'success.main' }}>
                                            <GetApp />
                                        </Avatar>
                                        <Box>
                                            <Typography variant="body2">Report generated</Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                1 day ago
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            </CardContent>
                        </Card>
                    </Box>
                </Box>
            </Container>
        </Navigation>
    );
}