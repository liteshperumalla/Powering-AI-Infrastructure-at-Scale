'use client';

import React, { useState } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Typography,
    Box,
    Link,
    Alert,
    InputAdornment,
    useTheme,
} from '@mui/material';
import { Email, ArrowBack } from '@mui/icons-material';
import NextLink from 'next/link';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import { useApiMutation } from '@/hooks/useOptimizedApi';

export default function ForgotPasswordPage() {
    const theme = useTheme();
    const [email, setEmail] = useState('');
    const [success, setSuccess] = useState(false);
    const [validationError, setValidationError] = useState('');

    // ✅ Use optimized mutation hook
    const { mutate, loading, error: apiError } = useApiMutation<any, { email: string }>(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/forgot-password`,
        'POST'
    );

    const error = apiError?.message || '';

    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!email) {
            setValidationError('Email is required');
            return;
        }

        if (!validateEmail(email)) {
            setValidationError('Please enter a valid email address');
            return;
        }

        setValidationError('');

        // ✅ Use mutation hook
        const result = await mutate({ email });
        if (result) {
            setSuccess(true);
        }
    };

    const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEmail(e.target.value);
        if (validationError) {
            setValidationError('');
        }
        if (error) {
            setError('');
        }
    };

    return (
        <ResponsiveLayout title="Forgot Password">
            <Box
                sx={{
                    minHeight: '100vh',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 2,
                }}
            >
                <Container component="main" maxWidth="sm">
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                        }}
                    >
                        <Paper
                            elevation={24}
                            sx={{
                                padding: { xs: 3, sm: 4, md: 5 },
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                width: '100%',
                                borderRadius: 3,
                                background: theme.palette.mode === 'dark' ? 'rgba(30, 30, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                                backdropFilter: 'blur(10px)',
                                border: theme.palette.mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(255, 255, 255, 0.3)',
                                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
                                transition: 'all 0.3s ease-in-out',
                                '&:hover': {
                                    transform: 'translateY(-2px)',
                                    boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
                                }
                            }}
                        >
                            <Box
                                sx={{
                                    mb: 3,
                                    p: 2,
                                    borderRadius: '50%',
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 80,
                                    height: 80,
                                    boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)',
                                }}
                            >
                                <Email sx={{ color: 'white', fontSize: '2rem' }} />
                            </Box>
                            
                            <Typography 
                                component="h1" 
                                variant="h4" color="text.primary" 
                                gutterBottom
                                sx={{
                                    fontWeight: 700,
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    backgroundClip: 'text',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    textAlign: 'center',
                                    mb: 1,
                                }}
                            >
                                Forgot Password?
                            </Typography>
                            
                            {!success ? (
                                <>
                                    <Typography 
                                        variant="body1" 
                                        color="text.secondary" 
                                        sx={{
                                            textAlign: 'center',
                                            mb: 4,
                                            fontWeight: 400,
                                        }}
                                    >
                                        Don't worry! Enter your email and we'll send you a reset link.
                                    </Typography>

                                    {error && (
                                        <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                                            {error}
                                        </Alert>
                                    )}

                                    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
                                        <TextField
                                            margin="normal"
                                            required
                                            fullWidth
                                            id="email"
                                            label="Email Address"
                                            name="email"
                                            autoComplete="email"
                                            autoFocus
                                            value={email}
                                            onChange={handleEmailChange}
                                            error={!!validationError}
                                            helperText={validationError}
                                            sx={{
                                                mb: 3,
                                                '& .MuiOutlinedInput-root': {
                                                    borderRadius: 2,
                                                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                                                    '&:hover': {
                                                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                                    },
                                                    '&.Mui-focused': {
                                                        backgroundColor: 'rgba(255, 255, 255, 1)',
                                                        boxShadow: '0 0 0 3px rgba(102, 126, 234, 0.1)',
                                                    }
                                                },
                                                '& .MuiInputLabel-root': {
                                                    fontWeight: 500,
                                                }
                                            }}
                                            InputProps={{
                                                startAdornment: (
                                                    <InputAdornment position="start">
                                                        <Email sx={{ color: 'text.secondary' }} />
                                                    </InputAdornment>
                                                ),
                                            }}
                                        />
                                        
                                        <Button
                                            type="submit"
                                            fullWidth
                                            variant="contained"
                                            disabled={loading}
                                            sx={{ 
                                                mb: 3,
                                                py: 1.5,
                                                borderRadius: 2,
                                                fontSize: '1.1rem',
                                                fontWeight: 600,
                                                textTransform: 'none',
                                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                boxShadow: '0 8px 20px rgba(102, 126, 234, 0.3)',
                                                '&:hover': {
                                                    background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                                                    boxShadow: '0 12px 30px rgba(102, 126, 234, 0.4)',
                                                    transform: 'translateY(-1px)',
                                                },
                                                '&:disabled': {
                                                    background: 'linear-gradient(135deg, #a0aec0 0%, #cbd5e0 100%)',
                                                    color: 'white',
                                                }
                                            }}
                                        >
                                            {loading ? 'Sending...' : 'Send Reset Link'}
                                        </Button>
                                    </Box>
                                </>
                            ) : (
                                <Box sx={{ textAlign: 'center', width: '100%' }}>
                                    <Alert severity="success" sx={{ mb: 3 }}>
                                        Check your email! We've sent you a password reset link.
                                    </Alert>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                        Didn't receive the email? Check your spam folder or try again.
                                    </Typography>
                                </Box>
                            )}
                            
                            <Box textAlign="center" sx={{ mt: 2 }}>
                                <Link
                                    component={NextLink}
                                    href="/auth/login"
                                    variant="body2"
                                    sx={{
                                        fontWeight: 500,
                                        color: 'text.secondary',
                                        textDecoration: 'none',
                                        transition: 'all 0.2s ease-in-out',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: 1,
                                        '&:hover': {
                                            color: 'primary.main',
                                            textDecoration: 'underline',
                                        }
                                    }}
                                >
                                    <ArrowBack fontSize="small" />
                                    Back to Sign In
                                </Link>
                            </Box>
                        </Paper>
                    </Box>
                </Container>
            </Box>
        </ResponsiveLayout>
    );
}
