'use client';

import React from 'react';
import {
    Container,
    Box,
    Typography,
    Paper,
    Divider,
} from '@mui/material';
import Navigation from '@/components/Navigation';
import CostComparisonChart from '@/components/charts/CostComparisonChart';
import RecommendationScoreChart from '@/components/charts/RecommendationScoreChart';
import AssessmentResultsChart from '@/components/charts/AssessmentResultsChart';
import RecommendationTable from '@/components/RecommendationTable';
import ReportPreview from '@/components/ReportPreview';

export default function VisualizationDemoPage() {
    // Sample data for demonstrations
    const costData = [
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
    ];

    const scoreData = [
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
    ];

    const assessmentData = [
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
    ];

    const recommendationData = [
        {
            id: '1',
            serviceName: 'Amazon EC2 t3.large',
            provider: 'AWS' as const,
            serviceType: 'Compute',
            costEstimate: 67.32,
            confidenceScore: 92,
            businessAlignment: 88,
            implementationComplexity: 'Low' as const,
            pros: ['High availability', 'Auto-scaling capabilities', 'Extensive documentation', 'Strong ecosystem'],
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
            pros: ['Good integration with Microsoft ecosystem', 'Competitive pricing', 'Hybrid cloud capabilities'],
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
            pros: ['Best price-performance ratio', 'Excellent machine learning integration', 'Sustainable infrastructure'],
            cons: ['Smaller market share', 'Limited enterprise support'],
            status: 'alternative' as const
        },
        {
            id: '4',
            serviceName: 'AWS RDS PostgreSQL',
            provider: 'AWS' as const,
            serviceType: 'Database',
            costEstimate: 145.20,
            confidenceScore: 94,
            businessAlignment: 91,
            implementationComplexity: 'Low' as const,
            pros: ['Managed service', 'Automatic backups', 'High availability', 'Performance insights'],
            cons: ['Vendor lock-in', 'Limited customization'],
            status: 'recommended' as const
        }
    ];

    const reportData = {
        id: 'report-demo',
        title: 'AI Infrastructure Strategy Report - Demo Company',
        generatedDate: '2024-01-15T10:30:00Z',
        status: 'final' as const,
        sections: [
            {
                title: 'Executive Summary',
                content: 'This comprehensive report provides strategic recommendations for scaling AI infrastructure across multi-cloud environments. Our analysis indicates significant opportunities for cost optimization and performance improvement through strategic service selection and architectural improvements.',
                type: 'executive' as const
            },
            {
                title: 'Technical Architecture',
                content: 'Detailed technical specifications and implementation roadmap for transitioning to a hybrid multi-cloud architecture. Includes container orchestration, microservices design patterns, and data pipeline optimization strategies.',
                type: 'technical' as const
            },
            {
                title: 'Cost Analysis & ROI',
                content: 'Financial projections and ROI calculations for the proposed infrastructure changes. Analysis shows potential 23% cost reduction while improving performance and scalability metrics.',
                type: 'financial' as const
            },
            {
                title: 'Compliance & Security',
                content: 'Comprehensive security assessment and compliance framework alignment for GDPR, HIPAA, and SOC 2 requirements. Includes data governance and privacy protection strategies.',
                type: 'compliance' as const
            }
        ],
        keyFindings: [
            'Multi-cloud strategy can reduce costs by 23% while improving resilience',
            'Current infrastructure is over-provisioned by 35% in compute resources',
            'Compliance gaps identified in data storage and access controls',
            'ML workloads can benefit from 40% performance improvement with optimized architecture',
            'Security posture can be enhanced with zero-trust implementation'
        ],
        recommendations: [
            'Implement hybrid AWS-Azure architecture for optimal cost-performance balance',
            'Migrate to containerized workloads using Kubernetes orchestration',
            'Establish automated compliance monitoring and reporting systems',
            'Deploy ML-optimized compute instances for AI workloads',
            'Implement comprehensive data governance framework'
        ],
        estimatedSavings: 125000,
        complianceScore: 94
    };

    return (
        <Navigation title="Data Visualization Demo">
            <Container maxWidth="xl">
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        Data Visualization Components Demo
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Comprehensive showcase of all data visualization components with interactive charts and tables.
                    </Typography>
                </Box>

                {/* Charts Section */}
                <Paper sx={{ p: 3, mb: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        Interactive Charts
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        All charts support multiple view types and interactive tooltips for detailed data exploration.
                    </Typography>

                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 3 }}>
                        {/* Cost Comparison Chart */}
                        <Box>
                            <CostComparisonChart
                                data={costData}
                                title="Multi-Cloud Cost Analysis"
                                showBreakdown={true}
                            />
                        </Box>

                        {/* Recommendation Score Chart */}
                        <Box>
                            <RecommendationScoreChart
                                data={scoreData}
                                title="Service Performance Comparison"
                            />
                        </Box>
                    </Box>

                    {/* Assessment Results Chart */}
                    <Box>
                        <AssessmentResultsChart
                            data={assessmentData}
                            title="AI Infrastructure Maturity Assessment"
                            showComparison={true}
                        />
                    </Box>
                </Paper>

                <Divider sx={{ my: 4 }} />

                {/* Tables Section */}
                <Paper sx={{ p: 3, mb: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        Interactive Data Tables
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Expandable tables with detailed service comparisons, ratings, and comprehensive analysis.
                    </Typography>

                    <RecommendationTable
                        recommendations={recommendationData}
                        title="Comprehensive Service Recommendations"
                    />
                </Paper>

                <Divider sx={{ my: 4 }} />

                {/* Report Preview Section */}
                <Paper sx={{ p: 3, mb: 4 }}>
                    <Typography variant="h5" gutterBottom>
                        Report Preview & Export
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Professional report preview with key metrics, findings, and export capabilities.
                    </Typography>

                    <ReportPreview
                        report={reportData}
                        onDownload={(reportId) => {
                            console.log('Download report:', reportId);
                            // In a real implementation, this would trigger PDF generation
                            alert('Report download would be triggered here');
                        }}
                        onView={(reportId) => {
                            console.log('View report:', reportId);
                            // In a real implementation, this would open the full report view
                            alert('Full report view would open here');
                        }}
                    />
                </Paper>

                {/* Features Summary */}
                <Paper sx={{ p: 3, mb: 4, bgcolor: 'grey.50' }}>
                    <Typography variant="h6" gutterBottom>
                        Visualization Features Summary
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                        <Box>
                            <Typography variant="subtitle2" gutterBottom>
                                Chart Types
                            </Typography>
                            <ul>
                                <li>Bar Charts with stacked data</li>
                                <li>Pie Charts with interactive segments</li>
                                <li>Radar Charts for multi-dimensional comparison</li>
                                <li>Line Charts for trend analysis</li>
                                <li>Area Charts for cumulative data</li>
                            </ul>
                        </Box>
                        <Box>
                            <Typography variant="subtitle2" gutterBottom>
                                Interactive Features
                            </Typography>
                            <ul>
                                <li>Toggle between chart types</li>
                                <li>Hover tooltips with detailed information</li>
                                <li>Expandable table rows</li>
                                <li>Color-coded provider identification</li>
                                <li>Real-time data updates</li>
                            </ul>
                        </Box>
                    </Box>
                </Paper>
            </Container>
        </Navigation>
    );
}