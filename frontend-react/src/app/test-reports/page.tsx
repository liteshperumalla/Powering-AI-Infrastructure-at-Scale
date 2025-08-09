'use client';

import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Card, CardContent, Button } from '@mui/material';

interface ReportData {
    id: string;
    assessment_id: string;
    title: string;
    status: string;
    created_at: string;
    completed_at: string;
}

export default function TestReportsPage() {
    const [reports, setReports] = useState<ReportData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchReports = async () => {
        setLoading(true);
        setError(null);
        
        try {
            console.log('🔄 Fetching reports directly...');
            
            // Step 1: Get assessments
            const assessmentsResponse = await fetch('http://localhost:8000/api/v1/assessments/');
            if (!assessmentsResponse.ok) {
                throw new Error(`Assessments API error: ${assessmentsResponse.status}`);
            }
            
            const assessmentsData = await assessmentsResponse.json();
            const assessments = assessmentsData.assessments || [];
            
            console.log(`Found ${assessments.length} assessments`);
            
            // Step 2: Get reports for each assessment
            const allReports: ReportData[] = [];
            
            for (const assessment of assessments) {
                const reportsResponse = await fetch(`http://localhost:8000/api/v1/reports/${assessment.id}`);
                
                if (reportsResponse.ok) {
                    const reportsData = await reportsResponse.json();
                    const reports = reportsData.reports || [];
                    allReports.push(...reports);
                }
            }
            
            console.log(`✅ Found ${allReports.length} total reports`);
            setReports(allReports);
            
        } catch (err) {
            console.error('❌ Error fetching reports:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, []);

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <Typography variant="h4" gutterBottom>
                    🧪 Test Reports API
                </Typography>
                
                <Typography variant="body1" sx={{ mb: 3 }}>
                    This page directly tests the reports API to verify backend connectivity.
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                    <Button 
                        variant="contained" 
                        onClick={fetchReports}
                        disabled={loading}
                    >
                        {loading ? 'Loading...' : 'Refresh Reports'}
                    </Button>
                </Box>
                
                {error && (
                    <Card sx={{ mb: 3, bgcolor: '#ffebee' }}>
                        <CardContent>
                            <Typography color="error">
                                ❌ Error: {error}
                            </Typography>
                        </CardContent>
                    </Card>
                )}
                
                {loading ? (
                    <Card>
                        <CardContent>
                            <Typography>🔄 Loading reports...</Typography>
                        </CardContent>
                    </Card>
                ) : reports.length === 0 ? (
                    <Card>
                        <CardContent>
                            <Typography>
                                {error ? 'Failed to load reports.' : '📭 No reports found.'}
                            </Typography>
                        </CardContent>
                    </Card>
                ) : (
                    <Box>
                        <Typography variant="h6" sx={{ mb: 2 }}>
                            ✅ Found {reports.length} reports:
                        </Typography>
                        
                        {reports.map((report, index) => (
                            <Card key={report.id} sx={{ mb: 2 }}>
                                <CardContent>
                                    <Typography variant="h6">
                                        {index + 1}. {report.title}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        ID: {report.id}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Assessment: {report.assessment_id}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Status: <strong>{report.status}</strong>
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Completed: {new Date(report.completed_at).toLocaleString()}
                                    </Typography>
                                </CardContent>
                            </Card>
                        ))}
                    </Box>
                )}
            </Box>
        </Container>
    );
}