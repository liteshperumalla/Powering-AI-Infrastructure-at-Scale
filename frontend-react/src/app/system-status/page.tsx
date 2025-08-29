'use client';

import React from 'react';
import {
    Container,
    Typography,
    Box,
    Alert,
} from '@mui/material';
import Navigation from '@/components/Navigation';
import ApiTester from '@/components/ApiTester';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function SystemStatusPage() {
    return (
        <ProtectedRoute allowedRoles={['admin']}>
            <Navigation title="System Status">
                <Container maxWidth="lg">
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h4" gutterBottom>
                            System Status & API Testing
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Monitor system health and test API connectivity across all endpoints.
                        </Typography>
                    </Box>

                    <Alert severity="info" sx={{ mb: 4 }}>
                        This page helps diagnose connectivity issues between the frontend and backend services.
                        Run the test suite to verify all API endpoints are functioning correctly.
                    </Alert>

                    <ApiTester />
                </Container>
            </Navigation>
        </ProtectedRoute>
    );
}