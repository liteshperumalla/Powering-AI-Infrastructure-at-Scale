'use client';

import React, { useState, useEffect } from 'react';
import {
    Container,
    Paper,
    Typography,
    Box,
    Button,
    TextField,
    Alert,
    Step,
    Stepper,
    StepLabel,
    StepContent,
    Chip,
    Grid,
    Card,
    CardContent,
    InputAdornment,
    CircularProgress,
} from '@mui/material';
import { 
    Security, 
    QrCode, 
    Smartphone, 
    VerifiedUser,
    ContentCopy,
    Download,
    CheckCircle
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useAppSelector } from '@/store/hooks';
import ResponsiveLayout from '@/components/ResponsiveLayout';

interface MFASetupData {
    secret: string;
    qr_code_url: string;
    backup_codes: string[];
}

export default function MFASetupPage() {
    const router = useRouter();
    const { token, isAuthenticated } = useAppSelector(state => state.auth);
    
    const [activeStep, setActiveStep] = useState(0);
    const [mfaData, setMfaData] = useState<MFASetupData | null>(null);
    const [verificationCode, setVerificationCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            router.push('/auth/login');
            return;
        }
        initializeMFA();
    }, [isAuthenticated, router]);

    const initializeMFA = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/mfa/setup`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                setMfaData(data);
                setActiveStep(1);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to initialize MFA setup');
            }
        } catch (error) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const verifyMFA = async () => {
        if (!verificationCode || verificationCode.length !== 6) {
            setError('Please enter a valid 6-digit code');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/mfa/verify`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: verificationCode }),
            });

            if (response.ok) {
                setSuccess(true);
                setActiveStep(3);
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

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const downloadBackupCodes = () => {
        if (!mfaData) return;
        
        const content = `Infra Mind MFA Backup Codes\n\nIMPORTANT: Store these codes securely. Each code can only be used once.\n\n${mfaData.backup_codes.join('\n')}\n\nGenerated: ${new Date().toLocaleString()}`;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'infra-mind-backup-codes.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const steps = [
        'Initialize Setup',
        'Scan QR Code',
        'Verify Setup',
        'Save Backup Codes'
    ];

    return (
        <ResponsiveLayout title="MFA Setup">
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
                                    <Security sx={{ color: 'white', fontSize: '2rem' }} />
                                )}
                            </Box>
                            
                            <Typography 
                                component="h1" 
                                variant="h4" color="text.primary" 
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
                                {success ? 'MFA Enabled!' : 'Setup Multi-Factor Authentication'}
                            </Typography>
                            
                            <Typography 
                                variant="body1" 
                                color="text.secondary" 
                                sx={{
                                    textAlign: 'center',
                                    mb: 4,
                                    maxWidth: 600,
                                }}
                            >
                                {success 
                                    ? 'Your account is now protected with two-factor authentication.'
                                    : 'Add an extra layer of security to your account with time-based one-time passwords (TOTP).'
                                }
                            </Typography>

                            {error && (
                                <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
                                    {error}
                                </Alert>
                            )}

                            <Box sx={{ width: '100%' }}>
                                <Stepper activeStep={activeStep} orientation="vertical">
                                    <Step>
                                        <StepLabel>Initialize MFA Setup</StepLabel>
                                        <StepContent>
                                            <Typography variant="body2" sx={{ mb: 2 }}>
                                                Setting up multi-factor authentication for your account...
                                            </Typography>
                                            {loading && activeStep === 0 && (
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                    <CircularProgress size={20} />
                                                    <Typography variant="body2">Generating MFA secret...</Typography>
                                                </Box>
                                            )}
                                        </StepContent>
                                    </Step>

                                    <Step>
                                        <StepLabel>Scan QR Code with Authenticator App</StepLabel>
                                        <StepContent>
                                            {mfaData && (
                                                <Grid container spacing={3}>
                                                    <Grid item xs={12} md={6}>
                                                        <Card>
                                                            <CardContent sx={{ textAlign: 'center' }}>
                                                                <QrCode sx={{ fontSize: 40, mb: 2, color: 'primary.main' }} />
                                                                <Typography variant="h6" color="text.primary" gutterBottom>
                                                                    Scan QR Code
                                                                </Typography>
                                                                <Box sx={{ p: 2, mb: 2 }}>
                                                                    <img 
                                                                        src={mfaData.qr_code_url} 
                                                                        alt="MFA QR Code"
                                                                        style={{ 
                                                                            maxWidth: '100%', 
                                                                            height: 'auto',
                                                                            border: '1px solid #ddd',
                                                                            borderRadius: '8px'
                                                                        }}
                                                                    />
                                                                </Box>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Use Google Authenticator, Authy, or any TOTP app
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                    
                                                    <Grid item xs={12} md={6}>
                                                        <Card>
                                                            <CardContent>
                                                                <Smartphone sx={{ fontSize: 40, mb: 2, color: 'primary.main' }} />
                                                                <Typography variant="h6" color="text.primary" gutterBottom>
                                                                    Manual Setup
                                                                </Typography>
                                                                <Typography variant="body2" sx={{ mb: 2 }}>
                                                                    If you can't scan the QR code, enter this secret manually:
                                                                </Typography>
                                                                <Box
                                                                    sx={{
                                                                        p: 2,
                                                                        backgroundColor: 'grey.100',
                                                                        borderRadius: 1,
                                                                        fontFamily: 'monospace',
                                                                        fontSize: '0.9rem',
                                                                        wordBreak: 'break-all',
                                                                        position: 'relative',
                                                                    }}
                                                                >
                                                                    {mfaData.secret}
                                                                    <Button
                                                                        size="small"
                                                                        onClick={() => copyToClipboard(mfaData.secret)}
                                                                        sx={{ position: 'absolute', top: 8, right: 8 }}
                                                                    >
                                                                        <ContentCopy fontSize="small" />
                                                                    </Button>
                                                                </Box>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                </Grid>
                                            )}
                                            
                                            <Box sx={{ mt: 3 }}>
                                                <Button
                                                    variant="contained"
                                                    onClick={() => setActiveStep(2)}
                                                    sx={{
                                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                    }}
                                                >
                                                    Continue to Verification
                                                </Button>
                                            </Box>
                                        </StepContent>
                                    </Step>

                                    <Step>
                                        <StepLabel>Verify Your Setup</StepLabel>
                                        <StepContent>
                                            <Typography variant="body2" sx={{ mb: 3 }}>
                                                Enter the 6-digit code from your authenticator app to verify the setup:
                                            </Typography>
                                            
                                            <TextField
                                                fullWidth
                                                label="Verification Code"
                                                value={verificationCode}
                                                onChange={(e) => {
                                                    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                                                    setVerificationCode(value);
                                                    setError('');
                                                }}
                                                placeholder="123456"
                                                InputProps={{
                                                    startAdornment: (
                                                        <InputAdornment position="start">
                                                            <VerifiedUser />
                                                        </InputAdornment>
                                                    ),
                                                }}
                                                sx={{ mb: 2 }}
                                            />
                                            
                                            <Button
                                                variant="contained"
                                                onClick={verifyMFA}
                                                disabled={loading || verificationCode.length !== 6}
                                                sx={{
                                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                    mr: 1,
                                                }}
                                            >
                                                {loading ? 'Verifying...' : 'Verify & Enable MFA'}
                                            </Button>
                                            
                                            <Button
                                                onClick={() => setActiveStep(1)}
                                                disabled={loading}
                                            >
                                                Back
                                            </Button>
                                        </StepContent>
                                    </Step>

                                    <Step>
                                        <StepLabel>Save Backup Codes</StepLabel>
                                        <StepContent>
                                            <Alert severity="warning" sx={{ mb: 3 }}>
                                                <Typography variant="body2" fontWeight="bold">
                                                    Important: Save these backup codes!
                                                </Typography>
                                                <Typography variant="body2">
                                                    These codes can be used to access your account if you lose your authenticator device. 
                                                    Each code can only be used once.
                                                </Typography>
                                            </Alert>
                                            
                                            {mfaData && (
                                                <Grid container spacing={1} sx={{ mb: 3 }}>
                                                    {mfaData.backup_codes.map((code, index) => (
                                                        <Grid item xs={6} sm={4} key={index}>
                                                            <Chip
                                                                label={code}
                                                                variant="outlined"
                                                                sx={{ 
                                                                    fontFamily: 'monospace',
                                                                    fontSize: '0.9rem',
                                                                    width: '100%'
                                                                }}
                                                            />
                                                        </Grid>
                                                    ))}
                                                </Grid>
                                            )}
                                            
                                            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                                                <Button
                                                    variant="outlined"
                                                    startIcon={<Download />}
                                                    onClick={downloadBackupCodes}
                                                >
                                                    Download Codes
                                                </Button>
                                                
                                                <Button
                                                    variant="outlined"
                                                    startIcon={<ContentCopy />}
                                                    onClick={() => mfaData && copyToClipboard(mfaData.backup_codes.join('\n'))}
                                                >
                                                    Copy All
                                                </Button>
                                            </Box>
                                            
                                            <Button
                                                variant="contained"
                                                onClick={() => router.push('/dashboard')}
                                                sx={{
                                                    background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
                                                }}
                                            >
                                                Complete Setup
                                            </Button>
                                        </StepContent>
                                    </Step>
                                </Stepper>
                            </Box>
                        </Paper>
                    </Box>
                </Container>
            </Box>
        </ResponsiveLayout>
    );
}