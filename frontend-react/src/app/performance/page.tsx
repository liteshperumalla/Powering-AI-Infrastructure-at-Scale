'use client';

import React from 'react';
import { Container } from '@mui/material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import PerformanceMonitoringDashboard from '@/components/PerformanceMonitoringDashboard';

export default function PerformancePage() {
    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Performance">
                <Container maxWidth="lg" sx={{ mt: 3 }}>
                    <PerformanceMonitoringDashboard />
                </Container>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}