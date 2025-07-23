import React from 'react';
import { render, screen } from '@testing-library/react';
import CostComparisonChart from '../charts/CostComparisonChart';
import RecommendationScoreChart from '../charts/RecommendationScoreChart';
import AssessmentResultsChart from '../charts/AssessmentResultsChart';
import RecommendationTable from '../RecommendationTable';
import ReportPreview from '../ReportPreview';

// Mock Recharts components
jest.mock('recharts', () => ({
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
    BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
    Bar: () => <div data-testid="bar" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
    Legend: () => <div data-testid="legend" />,
    PieChart: ({ children }: { children: React.ReactNode }) => <div data-testid="pie-chart">{children}</div>,
    Pie: () => <div data-testid="pie" />,
    Cell: () => <div data-testid="cell" />,
    RadarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="radar-chart">{children}</div>,
    PolarGrid: () => <div data-testid="polar-grid" />,
    PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
    PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
    Radar: () => <div data-testid="radar" />,
    LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
    Line: () => <div data-testid="line" />,
    AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
    Area: () => <div data-testid="area" />,
}));

describe('Data Visualization Components', () => {
    const mockCostData = [
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
        }
    ];

    const mockScoreData = [
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
        }
    ];

    const mockAssessmentData = [
        {
            category: 'Infrastructure Readiness',
            currentScore: 75,
            targetScore: 90,
            improvement: 15,
            color: '#8884d8'
        }
    ];

    const mockRecommendations = [
        {
            id: '1',
            serviceName: 'Amazon EC2 t3.large',
            provider: 'AWS' as const,
            serviceType: 'Compute',
            costEstimate: 67.32,
            confidenceScore: 92,
            businessAlignment: 88,
            implementationComplexity: 'Low' as const,
            pros: ['High availability', 'Auto-scaling capabilities'],
            cons: ['Higher cost than alternatives'],
            status: 'recommended' as const
        }
    ];

    const mockReport = {
        id: 'report-1',
        title: 'Test Report',
        generatedDate: '2024-01-15T10:30:00Z',
        status: 'final' as const,
        sections: [
            {
                title: 'Executive Summary',
                content: 'Test content',
                type: 'executive' as const
            }
        ],
        keyFindings: ['Test finding'],
        recommendations: ['Test recommendation'],
        estimatedSavings: 45000,
        complianceScore: 98
    };

    test('CostComparisonChart renders correctly', () => {
        render(<CostComparisonChart data={mockCostData} />);
        expect(screen.getByText('Cost Comparison')).toBeInTheDocument();
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    test('RecommendationScoreChart renders correctly', () => {
        render(<RecommendationScoreChart data={mockScoreData} />);
        expect(screen.getByText('Service Recommendation Scores')).toBeInTheDocument();
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    test('AssessmentResultsChart renders correctly', () => {
        render(<AssessmentResultsChart data={mockAssessmentData} />);
        expect(screen.getByText('Assessment Results')).toBeInTheDocument();
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    test('RecommendationTable renders correctly', () => {
        render(<RecommendationTable recommendations={mockRecommendations} />);
        expect(screen.getByText('Service Recommendations')).toBeInTheDocument();
        expect(screen.getByText('Amazon EC2 t3.large')).toBeInTheDocument();
    });

    test('ReportPreview renders correctly', () => {
        render(<ReportPreview report={mockReport} />);
        expect(screen.getByText('Test Report')).toBeInTheDocument();
        expect(screen.getByText('$45,000')).toBeInTheDocument();
        expect(screen.getByText('98%')).toBeInTheDocument();
    });
});