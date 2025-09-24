'use client';

import React, { useState, useEffect, Suspense } from 'react';
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
} from '@mui/material';
import { 
    Lock, 
    Visibility, 
    VisibilityOff, 
    ArrowBack,
    CheckCircle 
} from '@mui/icons-material';
import { useRouter, useSearchParams } from 'next/navigation';
import ResponsiveLayout from '@/components/ResponsiveLayout';

function ResetPasswordContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    
    const [formData, setFormData] = useState({
        newPassword: '',
        confirmPassword: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

    useEffect(() => {
        if (!token) {
            setError('Invalid or missing reset token');
        }
    }, [token]);

    const validatePassword = (password: string) => {
        const errors: string[] = [];
        if (password.length < 8) errors.push('at least 8 characters');
        if (!/[A-Z]/.test(password)) errors.push('one uppercase letter');
        if (!/[a-z]/.test(password)) errors.push('one lowercase letter');
        if (!/[0-9]/.test(password)) errors.push('one number');
        if (!/[^A-Za-z0-9]/.test(password)) errors.push('one special character');
        
        return errors.length > 0 ? `Password must contain ${errors.join(', ')}` : '';
    };

    const validateForm = () => {
        const errors: Record<string, string> = {};
        
        if (!formData.newPassword) {
            errors.newPassword = 'Password is required';
        } else {
            const passwordError = validatePassword(formData.newPassword);
            if (passwordError) {
                errors.newPassword = passwordError;
            }
        }
        
        if (!formData.confirmPassword) {
            errors.confirmPassword = 'Please confirm your password';
        } else if (formData.newPassword !== formData.confirmPassword) {
            errors.confirmPassword = 'Passwords do not match';
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
            setError('');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!token) {
            setError('Invalid or missing reset token');
            return;
        }
        
        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    token,
                    new_password: formData.newPassword 
                }),
            });

            if (response.ok) {
                setSuccess(true);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to reset password');
            }
        } catch (error) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <Container component="main" maxWidth="sm">
                <Alert severity="error" sx={{ mt: 4 }}>
                    Invalid or missing reset token. Please request a new password reset.
                </Alert>
            </Container>
        );
    }

    return (
        <ResponsiveLayout title="Reset Password">
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
                                    background: success 
                                        ? 'linear-gradient(135deg, #28a745 0%, #20c997 100%)'
                                        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 80,
                                    height: 80,
                                    boxShadow: success
                                        ? '0 10px 30px rgba(40, 167, 69, 0.3)'
                                        : '0 10px 30px rgba(102, 126, 234, 0.3)',
                                }}
                            >
                                {success ? (
                                    <CheckCircle sx={{ color: 'white', fontSize: '2rem' }} />
                                ) : (
                                    <Lock sx={{ color: 'white', fontSize: '2rem' }} />
                                )}
                            </Box>
                            
                            <Typography 
                                component="h1" 
                                variant="h4" 
                                gutterBottom
                                sx={{
                                    fontWeight: 700,
                                    background: success
                                        ? 'linear-gradient(135deg, #28a745 0%, #20c997 100%)'
                                        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    backgroundClip: 'text',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    textAlign: 'center',
                                    mb: 1,
                                }}
                            >
                                {success ? 'Password Reset!' : 'Reset Password'}
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
                                        Please enter your new password below.
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
                                            name="newPassword"
                                            label="New Password"
                                            type={showPassword ? 'text' : 'password'}
                                            id="newPassword"
                                            autoComplete="new-password"
                                            value={formData.newPassword}
                                            onChange={handleChange}
                                            error={!!validationErrors.newPassword}
                                            helperText={validationErrors.newPassword}
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
                                            label="Confirm New Password"
                                            type={showConfirmPassword ? 'text' : 'password'}
                                            id="confirmPassword"
                                            autoComplete="new-password"
                                            value={formData.confirmPassword}
                                            onChange={handleChange}
                                            error={!!validationErrors.confirmPassword}
                                            helperText={validationErrors.confirmPassword}
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
                                            {loading ? 'Resetting...' : 'Reset Password'}
                                        </Button>
                                    </Box>
                                </>
                            ) : (
                                <Box sx={{ textAlign: 'center', width: '100%' }}>
                                    <Alert severity="success" sx={{ mb: 3 }}>
                                        Your password has been successfully reset!
                                    </Alert>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                        You can now sign in with your new password.
                                    </Typography>
                                    <Button
                                        variant="contained"
                                        onClick={() => router.push('/auth/login')}
                                        sx={{
                                            py: 1.5,
                                            px: 4,
                                            borderRadius: 2,
                                            fontSize: '1rem',
                                            fontWeight: 600,
                                            textTransform: 'none',
                                            background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                                            boxShadow: '0 8px 20px rgba(40, 167, 69, 0.3)',
                                            '&:hover': {
                                                background: 'linear-gradient(135deg, #218838 0%, #1e7e34 100%)',
                                                boxShadow: '0 12px 30px rgba(40, 167, 69, 0.4)',
                                                transform: 'translateY(-1px)',
                                            },
                                        }}
                                    >
                                        Go to Sign In
                                    </Button>
                                </Box>
                            )}
                            
                            {!success && (
                                <Box textAlign="center" sx={{ mt: 2 }}>
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
                                        <ArrowBack fontSize="small" />
                                        Back to Sign In
                                    </Link>
                                </Box>
                            )}
                        </Paper>
                    </Box>
                </Container>
            </Box>
        </ResponsiveLayout>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <ResetPasswordContent />
        </Suspense>
    );
}