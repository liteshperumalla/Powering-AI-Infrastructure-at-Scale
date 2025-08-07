'use client';

import React from 'react';
import { Box, Typography, Container, IconButton, Breadcrumbs, Link } from '@mui/material';
import { ArrowBack, Home, Security } from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import ComplianceDashboard from '@/components/ComplianceDashboard';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navigation from '@/components/Navigation';

export default function CompliancePage() {
    const router = useRouter();

    return (
        <ProtectedRoute>
            <Navigation title="Compliance Management">
                <Container maxWidth="lg">
                    {/* Breadcrumbs and Back Button */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
                        <IconButton 
                            onClick={() => router.back()} 
                            sx={{ 
                                color: 'primary.main',
                                '&:hover': { backgroundColor: 'primary.light', opacity: 0.1 }
                            }}
                        >
                            <ArrowBack />
                        </IconButton>
                        <Breadcrumbs aria-label="breadcrumb">
                            <Link 
                                underline="hover" 
                                color="inherit" 
                                href="/dashboard"
                                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                            >
                                <Home fontSize="inherit" />
                                Dashboard
                            </Link>
                            <Typography 
                                color="text.primary" 
                                sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                            >
                                <Security fontSize="inherit" />
                                Compliance
                            </Typography>
                        </Breadcrumbs>
                    </Box>

                    {/* Page Header */}
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h4" component="h1" gutterBottom>
                            Compliance Management
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Manage your data privacy settings, consent preferences, and exercise your data rights.
                        </Typography>
                    </Box>
                    
                    {/* Main Content */}
                    <ComplianceDashboard />
                </Container>
            </Navigation>
        </ProtectedRoute>
    );
}