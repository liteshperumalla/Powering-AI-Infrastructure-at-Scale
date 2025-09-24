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
    IconButton,
    Divider,
    Stack,
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    Email,
    Lock,
    Google,
} from '@mui/icons-material';
import { GoogleLogin } from '@react-oauth/google';
// Apple Sign-In will be implemented with native Apple JS SDK
import { useRouter } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { login, clearError, googleLogin } from '@/store/slices/authSlice';
import ResponsiveLayout from '@/components/ResponsiveLayout';

export default function LoginPage() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const { loading, error, isAuthenticated } = useAppSelector(state => state.auth);

    const [formData, setFormData] = useState({
        email: '',
        password: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            router.push('/dashboard');
        }
    }, [isAuthenticated, router]);

    // Clear error when component mounts
    useEffect(() => {
        dispatch(clearError());
    }, [dispatch]);


    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const validateForm = () => {
        const errors: Record<string, string> = {};
        
        if (!formData.email) {
            errors.email = 'Email is required';
        } else if (!validateEmail(formData.email)) {
            errors.email = 'Please enter a valid email address';
        }
        
        if (!formData.password) {
            errors.password = 'Password is required';
        }
        
        setValidationErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
        
        // Clear validation errors for this field
        if (validationErrors[name]) {
            setValidationErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors[name];
                return newErrors;
            });
        }
        
        if (error) {
            dispatch(clearError());
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            if (!credentialResponse?.credential) {
                throw new Error('No credential received from Google');
            }

            const result = await dispatch(googleLogin({
                credential: credentialResponse.credential
            })).unwrap();

            router.push('/dashboard');
        } catch (error) {
            console.error('Google login failed:', error);
            // The error will be handled by the Redux slice and displayed via the error state
        }
    };

    const handleGoogleError = () => {
        console.log('Google Login Failed');
        // You can dispatch an error action here if needed
        dispatch(clearError());
        // Optionally show a custom error message
        setValidationErrors({
            ...validationErrors,
            google: 'Google sign-in was cancelled or failed. Please try again.'
        });
    };


    const getErrorMessage = (error: string) => {
        // Map backend error messages to user-friendly ones
        const errorMap: Record<string, string> = {
            'Invalid credentials': 'The email or password you entered is incorrect. Please try again.',
            'User not found': 'No account found with this email address. Please check your email or sign up.',
            'Incorrect password': 'The password you entered is incorrect. Please try again.',
            'Account disabled': 'Your account has been disabled. Please contact support for assistance.',
            'Too many login attempts': 'Too many failed login attempts. Please try again later.',
            'Network error': 'Unable to connect to the server. Please check your internet connection.',
            'Server error. Please try again later.': '🔧 We\'re experiencing technical difficulties. Please try again in a few moments.',
            'Google OAuth not configured': 'Google sign-in is temporarily unavailable. Please use email and password to sign in.',
            'Invalid Google credential': 'Google sign-in failed. Please try again or use email and password.',
            'Email not provided by Google': 'Google sign-in couldn\'t retrieve your email. Please try again or use email and password.',
            'Google authentication failed': 'Google sign-in encountered an error. Please try again or use email and password.',
            'Google login failed': 'Google sign-in failed. Please try again or use email and password.',
            'Login failed: "Server error. Please try again later."': '🔧 Authentication service is temporarily unavailable. Please try again in a few moments.'
        };

        return errorMap[error] || error;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        try {
            const result = await dispatch(login({
                email: formData.email.trim(),
                password: formData.password,
            })).unwrap();

            // Check if MFA is required
            if ('mfa_required' in result && result.mfa_required) {
                // Redirect to MFA verification page with temp token
                router.push(`/auth/mfa-verify?token=${result.temp_token}`);
                return;
            }

            // Login successful, redirect to dashboard
            router.push('/dashboard');
        } catch (error) {
            // Error is handled by Redux state
            console.error('Login failed:', error);
        }
    };


    return (
        <ResponsiveLayout title="Sign In" fullWidth>
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
                                background: 'rgba(255, 255, 255, 0.95)',
                                backdropFilter: 'blur(10px)',
                                border: '1px solid rgba(255, 255, 255, 0.3)',
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
                                <Typography 
                                    sx={{ 
                                        color: 'white', 
                                        fontWeight: 'bold', 
                                        fontSize: '1.5rem',
                                        textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                                    }}
                                >
                                    IM
                                </Typography>
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
                                Infra Mind
                            </Typography>
                            <Typography 
                                variant="h6" 
                                color="text.secondary" 
                                gutterBottom
                                sx={{
                                    textAlign: 'center',
                                    mb: 4,
                                    fontWeight: 400,
                                }}
                            >
                                Welcome back! Sign in to your account
                            </Typography>

                    {error && (
                        <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                            {getErrorMessage(error)}
                        </Alert>
                    )}

                    {validationErrors.google && (
                        <Alert severity="warning" sx={{ width: '100%', mb: 2 }}>
                            {validationErrors.google}
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
                                    value={formData.email}
                                    onChange={handleChange}
                                    error={!!validationErrors.email}
                                    helperText={validationErrors.email}
                                    sx={{
                                        mb: 2,
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
                                <TextField
                                    margin="normal"
                                    required
                                    fullWidth
                                    name="password"
                                    label="Password"
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    autoComplete="current-password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    error={!!validationErrors.password}
                                    helperText={validationErrors.password}
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
                                                <Lock sx={{ color: 'text.secondary' }} />
                                            </InputAdornment>
                                        ),
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    aria-label="toggle password visibility"
                                                    onClick={() => setShowPassword(!showPassword)}
                                                    edge="end"
                                                    sx={{ color: 'text.secondary' }}
                                                >
                                                    {showPassword ? <VisibilityOff /> : <Visibility />}
                                                </IconButton>
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
                                        mt: 1, 
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
                                    {loading ? 'Signing In...' : 'Sign In'}
                                </Button>
                                
                                <Divider sx={{ 
                                    my: 3,
                                    '&::before, &::after': {
                                        borderColor: 'rgba(0, 0, 0, 0.1)',
                                    }
                                }}>
                                    <Typography 
                                        variant="body2" 
                                        color="text.secondary"
                                        sx={{ 
                                            px: 2,
                                            fontWeight: 500,
                                            fontSize: '0.9rem'
                                        }}
                                    >
                                        or continue with
                                    </Typography>
                                </Divider>

                                {/* Google Login */}
                                {process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID && (
                                    <Box 
                                        sx={{ 
                                            display: 'flex', 
                                            justifyContent: 'center',
                                            mb: 3,
                                            '& > div': {
                                                borderRadius: '12px !important',
                                                transition: 'all 0.2s ease-in-out',
                                                '&:hover': {
                                                    transform: 'translateY(-1px)',
                                                    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.1)',
                                                }
                                            }
                                        }}
                                    >
                                        <GoogleLogin
                                            onSuccess={handleGoogleSuccess}
                                            onError={handleGoogleError}
                                            text="signin_with"
                                            size="large"
                                            width={300}
                                            theme="outline"
                                        />
                                    </Box>
                                )}
                                
                                <Box textAlign="center" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <Link
                                        component="button"
                                        variant="body2"
                                        onClick={() => router.push('/auth/forgot-password')}
                                        type="button"
                                        sx={{
                                            fontWeight: 500,
                                            color: 'text.secondary',
                                            textDecoration: 'none',
                                            transition: 'all 0.2s ease-in-out',
                                            '&:hover': {
                                                color: 'primary.main',
                                                textDecoration: 'underline',
                                            }
                                        }}
                                    >
                                        Forgot your password?
                                    </Link>
                                    
                                    <Link
                                        component="button"
                                        variant="body2"
                                        onClick={() => router.push('/auth/register')}
                                        type="button"
                                        sx={{
                                            fontWeight: 500,
                                            color: 'text.secondary',
                                            textDecoration: 'none',
                                            transition: 'all 0.2s ease-in-out',
                                            '&:hover': {
                                                color: 'primary.main',
                                                textDecoration: 'underline',
                                            }
                                        }}
                                    >
                                        Don&apos;t have an account? <Box component="span" sx={{ color: 'primary.main', fontWeight: 600 }}>Sign Up</Box>
                                    </Link>
                                </Box>
                            </Box>
                        </Paper>
                    </Box>
                </Container>
            </Box>
        </ResponsiveLayout>
    );
}