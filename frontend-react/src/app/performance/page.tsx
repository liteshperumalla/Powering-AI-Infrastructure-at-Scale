'use client';

import React from 'react';
import { useSearchParams } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { Container } from '@mui/material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import PerformanceMonitoringDashboard from '@/components/PerformanceMonitoringDashboard';

export default function PerformancePage() {
    const searchParams = useSearchParams();
    const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

    // Priority: URL param > Redux state
    const urlAssessmentId = searchParams?.get('assessment_id');
    const assessmentId = urlAssessmentId || currentAssessment?.id;

    // No redirect - just handle the case when there's no assessment

    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Performance">
                <Container maxWidth="lg" sx={{ mt: 3 }}>
                    <PerformanceMonitoringDashboard assessmentId={assessmentId} />
                </Container>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}