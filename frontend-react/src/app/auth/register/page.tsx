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
    FormControlLabel,
    Checkbox,
    Divider,
    Stack,
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    Email,
    Lock,
    Person,
    Business,
    Google,
} from '@mui/icons-material';
import { GoogleLogin } from '@react-oauth/google';
import { useRouter } from 'next/navigation';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { register, clearError, googleLogin } from '@/store/slices/authSlice';
import ResponsiveLayout from '@/components/ResponsiveLayout';

export default function RegisterPage() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const { loading, error, isAuthenticated } = useAppSelector(state => state.auth);

    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        company: '',
        jobTitle: '',
        password: '',
        confirmPassword: '',
        agreeToTerms: false,
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [validationError, setValidationError] = useState('');
    const [showSuccess, setShowSuccess] = useState(false);

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

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, checked, type } = e.target;
        setFormData({
            ...formData,
            [name]: type === 'checkbox' ? checked : value,
        });
        setValidationError('');
        if (error) {
            dispatch(clearError());
        }
    };

    const validateEmail = (email: string) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const validateForm = () => {
        if (!formData.fullName || !formData.email || !formData.jobTitle || !formData.password || !formData.confirmPassword) {
            return 'Please fill in all required fields';
        }
        if (!validateEmail(formData.email)) {
            return 'Please enter a valid email address';
        }
        if (formData.password !== formData.confirmPassword) {
            return 'Passwords do not match';
        }
        if (formData.password.length < 8) {
            return 'Password must be at least 8 characters long';
        }
        if (!/(?=.*[a-z])/.test(formData.password)) {
            return 'Password must contain at least one lowercase letter';
        }
        if (!/(?=.*[A-Z])/.test(formData.password)) {
            return 'Password must contain at least one uppercase letter';
        }
        if (!/(?=.*\d)/.test(formData.password)) {
            return 'Password must contain at least one number';
        }
        if (!/(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?])/.test(formData.password)) {
            return 'Password must contain at least one special character';
        }
        if (!formData.agreeToTerms) {
            return 'Please agree to the terms and conditions';
        }
        return null;
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
            console.error('Google signup failed:', error);
            // The error will be handled by the Redux slice and displayed via the error state
        }
    };

    const handleGoogleError = () => {
        console.log('Google Sign Up Failed');
        setValidationError('Google sign-up was cancelled or failed. Please try again or use the email registration form.');
    };

    const getErrorMessage = (error: string) => {
        const errorMap: Record<string, string> = {
            'Email already exists': 'An account with this email already exists. Please sign in instead or use a different email.',
            'Email already registered': 'An account with this email already exists. Please sign in instead or use a different email.',
            'Invalid email format': 'Please enter a valid email address.',
            'Password too weak': 'Your password is too weak. Please use a stronger password with uppercase, lowercase, numbers, and special characters.',
            'Username already taken': 'This username is already taken. Please choose a different one.',
            'Network error': 'Unable to connect to the server. Please check your internet connection.',
            'Server error': 'We\'re experiencing technical difficulties. Please try again later.',
            'Validation failed': 'Please check your input and try again.',
            'Google OAuth not configured': 'Google sign-up is temporarily unavailable. Please use the email registration form.',
            'Invalid Google credential': 'Google sign-up failed. Please try again or use the email registration form.',
            'Email not provided by Google': 'Google sign-up couldn\'t retrieve your email. Please try again or use the email registration form.',
            'Google authentication failed': 'Google sign-up encountered an error. Please try again or use the email registration form.',
            'Google login failed': 'Google sign-up failed. Please try again or use the email registration form.',
        };

        return errorMap[error] || error;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const validationErr = validateForm();
        if (validationErr) {
            setValidationError(validationErr);
            return;
        }

        try {
            const result = await dispatch(register({
                email: formData.email,
                password: formData.password,
                full_name: formData.fullName,
                company: formData.company || undefined,
                job_title: formData.jobTitle,
            })).unwrap();

            // Registration successful, show success message briefly then redirect
            setShowSuccess(true);
            setTimeout(() => {
                router.push('/dashboard');
            }, 2000);
        } catch (error) {
            // Error is handled by Redux state
            console.error('Registration failed:', error);
        }
    };

    return (
        <ResponsiveLayout title="Sign Up">
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
                                Infra Mind
                            </Typography>
                            <Typography
                                variant="h6" color="text.secondary"
                                gutterBottom
                                sx={{
                                    textAlign: 'center',
                                    mb: 4,
                                    fontWeight: 400,
                                }}
                            >
                                Create your account
                            </Typography>

                    {(error || validationError) && (
                        <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                            {error ? getErrorMessage(error) : validationError}
                        </Alert>
                    )}

                    {showSuccess && (
                        <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
                            Account created successfully! Redirecting to your dashboard...
                        </Alert>
                    )}

                    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            id="fullName"
                            label="Full Name"
                            name="fullName"
                            autoComplete="name"
                            autoFocus
                            value={formData.fullName}
                            onChange={handleChange}
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
                                        <Person sx={{ color: 'text.secondary' }} />
                                    </InputAdornment>
                                ),
                            }}
                        />
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            id="email"
                            label="Email Address"
                            name="email"
                            autoComplete="email"
                            value={formData.email}
                            onChange={handleChange}
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
                            fullWidth
                            id="company"
                            label="Company (Optional)"
                            name="company"
                            autoComplete="organization"
                            value={formData.company}
                            onChange={handleChange}
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
                                        <Business sx={{ color: 'text.secondary' }} />
                                    </InputAdornment>
                                ),
                            }}
                        />
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            id="jobTitle"
                            label="Job Title / Profession"
                            name="jobTitle"
                            autoComplete="job-title"
                            value={formData.jobTitle}
                            onChange={handleChange}
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
                                        <Person sx={{ color: 'text.secondary' }} />
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
                            autoComplete="new-password"
                            value={formData.password}
                            onChange={handleChange}
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
                        <TextField
                            margin="normal"
                            required
                            fullWidth
                            name="confirmPassword"
                            label="Confirm Password"
                            type={showConfirmPassword ? 'text' : 'password'}
                            id="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
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
                                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                            edge="end"
                                            sx={{ color: 'text.secondary' }}
                                        >
                                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                            }}
                        />
                        <FormControlLabel
                            control={
                                <Checkbox
                                    name="agreeToTerms"
                                    checked={formData.agreeToTerms}
                                    onChange={handleChange}
                                    color="primary"
                                />
                            }
                            label="I agree to the Terms and Conditions"
                            sx={{ mt: 2 }}
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
                            {loading ? 'Creating Account...' : 'Sign Up'}
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

                        {/* Google Sign Up */}
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
                                    text="signup_with"
                                    size="large"
                                    width={300}
                                    theme="outline"
                                />
                            </Box>
                        )}
                        
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
                                    '&:hover': {
                                        color: 'primary.main',
                                        textDecoration: 'underline',
                                    }
                                }}
                            >
                                Already have an account? <Box component="span" sx={{ color: 'primary.main', fontWeight: 600 }}>Sign In</Box>
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