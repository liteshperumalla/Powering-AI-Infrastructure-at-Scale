'use client';

import React from 'react';
import { Container, Typography, Box } from '@mui/material';

export default function MFATestPage() {
    return (
        <Container maxWidth="sm">
            <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Typography variant="h4" gutterBottom>
                    MFA Test Page
                </Typography>
                <Typography variant="body1">
                    This is a simple test to verify MFA pages are working.
                </Typography>
            </Box>
        </Container>
    );
}