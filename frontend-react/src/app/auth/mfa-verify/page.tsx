'use client';

import React, { useState, useEffect } from 'react';
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
    Grid,
    Card,
    CardContent,
    Divider,
} from '@mui/material';
import { 
    Security, 
    ArrowBack,
    Smartphone,
    VpnKey,
    Login
} from '@mui/icons-material';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { clearError } from '@/store/slices/authSlice';
import ResponsiveLayout from '@/components/ResponsiveLayout';

function MFAVerifyPageComponent() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const searchParams = useSearchParams();
    const tempToken = searchParams.get('token'); // Temporary token from login
    
    const [totpCode, setTotpCode] = useState('');
    const [backupCode, setBackupCode] = useState('');
    const [useBackupCode, setUseBackupCode] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!tempToken) {
            router.push('/auth/login');
        }
        dispatch(clearError());
    }, [tempToken, router, dispatch]);

    const handleTotpSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!totpCode || totpCode.length !== 6) {
            setError('Please enter a valid 6-digit code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/mfa/verify-login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    temp_token: tempToken,
                    totp_code: totpCode 
                }),
            });

            if (response.ok) {
                const data = await response.json();
                // Store the real access token
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('refreshToken', data.refresh_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                router.push('/dashboard');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Invalid verification code');
            }
        } catch (error) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleBackupCodeSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!backupCode || backupCode.length !== 8) {
            setError('Please enter a valid 8-character backup code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/mfa/verify-backup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    temp_token: tempToken,
                    backup_code: backupCode 
                }),
            });

            if (response.ok) {
                const data = await response.json();
                // Store the real access token
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('refreshToken', data.refresh_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                router.push('/dashboard');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Invalid backup code');
            }
        } catch (error) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.replace(/\D/g, '').slice(0, 6);
        setTotpCode(value);
        setError('');
    };

    const handleBackupCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.replace(/[^A-Za-z0-9]/g, '').slice(0, 8).toUpperCase();
        setBackupCode(value);
        setError('');
    };

    if (!tempToken) {
        return (
            <Container component="main" maxWidth="sm">
                <Alert severity="error" sx={{ mt: 4 }}>
                    Invalid session. Please log in again.
                </Alert>
            </Container>
        );
    }

    return (
        <ResponsiveLayout title="Multi-Factor Authentication">
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
                <Container component="main" maxWidth="md">
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
                                background: 'rgba(255, 255, 255, 0.95)',
                                backdropFilter: 'blur(10px)',
                                border: '1px solid rgba(255, 255, 255, 0.3)',
                                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
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
                                <Security sx={{ color: 'white', fontSize: '2rem' }} />
                            </Box>
                            
                            <Typography 
                                component="h1" 
                                variant="h4" 
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
                                Two-Factor Authentication
                            </Typography>
                            
                            <Typography 
                                variant="body1" 
                                color="text.secondary" 
                                sx={{
                                    textAlign: 'center',
                                    mb: 4,
                                    maxWidth: 500,
                                }}
                            >
                                Please enter the verification code from your authenticator app to complete your sign in.
                            </Typography>

                            {error && (
                                <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
                                    {error}
                                </Alert>
                            )}

                            <Grid container spacing={3} sx={{ width: '100%' }}>
                                {/* TOTP Code Section */}
                                <Grid item xs={12} md={6}>
                                    <Card 
                                        sx={{ 
                                            height: '100%',
                                            border: !useBackupCode ? '2px solid' : '1px solid',
                                            borderColor: !useBackupCode ? 'primary.main' : 'divider',
                                            transition: 'all 0.2s ease-in-out',
                                        }}
                                    >
                                        <CardContent sx={{ p: 3 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                                <Smartphone sx={{ fontSize: 32, mr: 2, color: 'primary.main' }} />
                                                <Typography variant="h6" fontWeight="bold">
                                                    Authenticator App
                                                </Typography>
                                            </Box>
                                            
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                                Enter the 6-digit code from your authenticator app
                                            </Typography>
                                            
                                            <Box component="form" onSubmit={handleTotpSubmit}>
                                                <TextField
                                                    fullWidth
                                                    label="6-Digit Code"
                                                    value={totpCode}
                                                    onChange={handleCodeChange}
                                                    placeholder="123456"
                                                    disabled={useBackupCode}
                                                    inputProps={{
                                                        maxLength: 6,
                                                        style: { 
                                                            textAlign: 'center', 
                                                            fontSize: '1.5rem',
                                                            letterSpacing: '0.5rem'
                                                        }
                                                    }}
                                                    sx={{ 
                                                        mb: 2,
                                                        '& .MuiOutlinedInput-root': {
                                                            borderRadius: 2,
                                                        }
                                                    }}
                                                    InputProps={{
                                                        startAdornment: (
                                                            <InputAdornment position="start">
                                                                <VpnKey sx={{ color: 'text.secondary' }} />
                                                            </InputAdornment>
                                                        ),
                                                    }}
                                                />
                                                
                                                <Button
                                                    type="submit"
                                                    fullWidth
                                                    variant="contained"
                                                    disabled={loading || totpCode.length !== 6 || useBackupCode}
                                                    sx={{
                                                        py: 1.5,
                                                        borderRadius: 2,
                                                        fontSize: '1rem',
                                                        fontWeight: 600,
                                                        textTransform: 'none',
                                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                        '&:hover': {
                                                            background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                                                        },
                                                    }}
                                                >
                                                    {loading ? 'Verifying...' : 'Verify & Sign In'}
                                                </Button>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                </Grid>

                                {/* Backup Code Section */}
                                <Grid item xs={12} md={6}>
                                    <Card 
                                        sx={{ 
                                            height: '100%',
                                            border: useBackupCode ? '2px solid' : '1px solid',
                                            borderColor: useBackupCode ? 'primary.main' : 'divider',
                                            transition: 'all 0.2s ease-in-out',
                                        }}
                                    >
                                        <CardContent sx={{ p: 3 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                                <VpnKey sx={{ fontSize: 32, mr: 2, color: 'warning.main' }} />
                                                <Typography variant="h6" fontWeight="bold">
                                                    Backup Code
                                                </Typography>
                                            </Box>
                                            
                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                                Can't access your authenticator? Use a backup code instead
                                            </Typography>
                                            
                                            <Box component="form" onSubmit={handleBackupCodeSubmit}>
                                                <TextField
                                                    fullWidth
                                                    label="8-Character Backup Code"
                                                    value={backupCode}
                                                    onChange={handleBackupCodeChange}
                                                    placeholder="ABCD1234"
                                                    disabled={!useBackupCode}
                                                    inputProps={{
                                                        maxLength: 8,
                                                        style: { 
                                                            textAlign: 'center', 
                                                            fontSize: '1.2rem',
                                                            letterSpacing: '0.2rem'
                                                        }
                                                    }}
                                                    sx={{ 
                                                        mb: 2,
                                                        '& .MuiOutlinedInput-root': {
                                                            borderRadius: 2,
                                                        }
                                                    }}
                                                />
                                                
                                                <Button
                                                    type="submit"
                                                    fullWidth
                                                    variant={useBackupCode ? "contained" : "outlined"}
                                                    disabled={loading || (useBackupCode && backupCode.length !== 8)}
                                                    onClick={() => {
                                                        if (!useBackupCode) {
                                                            setUseBackupCode(true);
                                                            setTotpCode('');
                                                            setError('');
                                                        }
                                                    }}
                                                    sx={{
                                                        py: 1.5,
                                                        borderRadius: 2,
                                                        fontSize: '1rem',
                                                        fontWeight: 600,
                                                        textTransform: 'none',
                                                        ...(useBackupCode && {
                                                            background: 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)',
                                                            '&:hover': {
                                                                background: 'linear-gradient(135deg, #d68910 0%, #ca6f1e 100%)',
                                                            },
                                                        })
                                                    }}
                                                >
                                                    {useBackupCode ? 
                                                        (loading ? 'Verifying...' : 'Use Backup Code') : 
                                                        'Use Backup Code Instead'
                                                    }
                                                </Button>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            </Grid>

                            {useBackupCode && (
                                <Box sx={{ mt: 3, textAlign: 'center' }}>
                                    <Button
                                        variant="text"
                                        onClick={() => {
                                            setUseBackupCode(false);
                                            setBackupCode('');
                                            setError('');
                                        }}
                                        startIcon={<ArrowBack />}
                                        sx={{
                                            color: 'text.secondary',
                                            textTransform: 'none',
                                            '&:hover': {
                                                color: 'primary.main',
                                            }
                                        }}
                                    >
                                        Back to Authenticator App
                                    </Button>
                                </Box>
                            )}

                            <Divider sx={{ width: '100%', my: 3 }} />

                            <Box textAlign="center">
                                <Link
                                    component="button"
                                    variant="body2"
                                    onClick={() => router.push('/auth/login')}
                                    type="button"
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
                                    <Login fontSize="small" />
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

export default function MFAVerifyPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <MFAVerifyPageComponent />
        </Suspense>
    );
}