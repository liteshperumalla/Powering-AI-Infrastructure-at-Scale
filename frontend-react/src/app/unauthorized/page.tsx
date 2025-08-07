'use client';

import React from 'react';
import {
    Container,
    Box,
    Typography,
    Button,
    Card,
    CardContent,
} from '@mui/material';
import {
    Block,
    Home,
    ArrowBack,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

export default function UnauthorizedPage() {
    const router = useRouter();

    return (
        <Container maxWidth="sm">
            <Box
                sx={{
                    minHeight: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <Card>
                    <CardContent sx={{ textAlign: 'center', p: 6 }}>
                        <Block 
                            sx={{ 
                                fontSize: 80, 
                                color: 'error.main', 
                                mb: 3 
                            }} 
                        />
                        
                        <Typography variant="h4" gutterBottom>
                            Access Denied
                        </Typography>
                        
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            401 - Unauthorized
                        </Typography>
                        
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                            You don't have permission to access this page. This could be because:
                        </Typography>

                        <Box sx={{ textAlign: 'left', mb: 4, maxWidth: 400, mx: 'auto' }}>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                • You're not logged in
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                • Your session has expired
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                • You don't have the required permissions
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                • The page requires a different user role
                            </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                            <Button
                                variant="outlined"
                                startIcon={<ArrowBack />}
                                onClick={() => router.back()}
                            >
                                Go Back
                            </Button>
                            
                            <Button
                                variant="contained"
                                startIcon={<Home />}
                                onClick={() => router.push('/')}
                            >
                                Home
                            </Button>
                            
                            <Button
                                variant="contained"
                                color="secondary"
                                onClick={() => router.push('/auth/login')}
                            >
                                Sign In
                            </Button>
                        </Box>

                        <Typography variant="body2" color="text.secondary" sx={{ mt: 4 }}>
                            If you believe this is an error, please contact your administrator.
                        </Typography>
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
}