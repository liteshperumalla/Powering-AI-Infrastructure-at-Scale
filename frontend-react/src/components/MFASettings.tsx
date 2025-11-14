'use client';

import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Button,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Chip,
    Switch,
    FormControlLabel,
    Divider,
    CircularProgress,
} from '@mui/material';
import {
    Security,
    Smartphone,
    VpnKey,
    Warning,
    CheckCircle,
    Settings,
    Add,
    Delete,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useAppSelector } from '@/store/hooks';

interface MFASettingsProps {
    onMFAToggle?: (enabled: boolean) => void;
}

export default function MFASettings({ onMFAToggle }: MFASettingsProps) {
    const router = useRouter();
    const { token, user } = useAppSelector(state => state.auth);
    
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [mfaSetupComplete, setMfaSetupComplete] = useState(false);
    const [loading, setLoading] = useState(true);
    const [disableDialogOpen, setDisableDialogOpen] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetchMFAStatus();
    }, []);

    const fetchMFAStatus = async () => {
        if (!token) return;
        
        setLoading(true);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                setMfaEnabled(data.mfa_enabled || false);
                setMfaSetupComplete(data.mfa_setup_complete || false);
            }
        } catch (error) {
            console.error('Failed to fetch MFA status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleEnableMFA = () => {
        router.push('/auth/mfa-setup');
    };

    const handleDisableMFA = async () => {
        if (!token) return;
        
        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/mfa/disable`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                setMfaEnabled(false);
                setMfaSetupComplete(false);
                setSuccess('MFA has been disabled successfully');
                setDisableDialogOpen(false);
                onMFAToggle?.(false);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to disable MFA');
            }
        } catch (error) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (loading && !mfaEnabled) {
        return (
            <Card>
                <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="center" p={4}>
                        <CircularProgress />
                    </Box>
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                        <Security sx={{ mr: 2, color: 'primary.main' }} />
                        <Typography variant="h6" color="text.primary" fontWeight="bold">
                            Multi-Factor Authentication
                        </Typography>
                    </Box>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Add an extra layer of security to your account with time-based one-time passwords (TOTP).
                    </Typography>

                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {success && (
                        <Alert severity="success" sx={{ mb: 2 }}>
                            {success}
                        </Alert>
                    )}

                    <Box sx={{ mb: 3 }}>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={mfaEnabled && mfaSetupComplete}
                                    disabled={loading}
                                    onChange={() => {
                                        if (mfaEnabled) {
                                            setDisableDialogOpen(true);
                                        } else {
                                            handleEnableMFA();
                                        }
                                    }}
                                />
                            }
                            label={
                                <Box>
                                    <Typography variant="body1" fontWeight="medium">
                                        Two-Factor Authentication
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {mfaEnabled && mfaSetupComplete 
                                            ? 'Your account is protected with 2FA'
                                            : 'Secure your account with an authenticator app'
                                        }
                                    </Typography>
                                </Box>
                            }
                        />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
                        Status
                    </Typography>

                    <List dense>
                        <ListItem>
                            <ListItemIcon>
                                {mfaEnabled && mfaSetupComplete ? (
                                    <CheckCircle color="success" />
                                ) : (
                                    <Warning color="warning" />
                                )}
                            </ListItemIcon>
                            <ListItemText
                                primary="Authentication Status"
                                secondary={
                                    mfaEnabled && mfaSetupComplete
                                        ? 'Two-factor authentication is enabled and active'
                                        : 'Two-factor authentication is disabled'
                                }
                            />
                            <Chip
                                label={mfaEnabled && mfaSetupComplete ? 'Enabled' : 'Disabled'}
                                color={mfaEnabled && mfaSetupComplete ? 'success' : 'default'}
                                size="small"
                            />
                        </ListItem>

                        {mfaEnabled && mfaSetupComplete && (
                            <ListItem>
                                <ListItemIcon>
                                    <Smartphone color="primary" />
                                </ListItemIcon>
                                <ListItemText
                                    primary="Authenticator App"
                                    secondary="Connected and ready to generate codes"
                                />
                                <Chip
                                    label="Active"
                                    color="primary"
                                    size="small"
                                />
                            </ListItem>
                        )}

                        {mfaEnabled && mfaSetupComplete && (
                            <ListItem>
                                <ListItemIcon>
                                    <VpnKey color="primary" />
                                </ListItemIcon>
                                <ListItemText
                                    primary="Backup Codes"
                                    secondary="Emergency codes for account recovery"
                                />
                                <Chip
                                    label="Available"
                                    color="primary"
                                    size="small"
                                />
                            </ListItem>
                        )}
                    </List>

                    <Divider sx={{ my: 2 }} />

                    <Box display="flex" gap={2} flexWrap="wrap">
                        {!mfaEnabled || !mfaSetupComplete ? (
                            <Button
                                variant="contained"
                                startIcon={<Add />}
                                onClick={handleEnableMFA}
                                disabled={loading}
                                sx={{
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                                    },
                                }}
                            >
                                Enable MFA
                            </Button>
                        ) : (
                            <>
                                <Button
                                    variant="outlined"
                                    startIcon={<Settings />}
                                    onClick={handleEnableMFA}
                                    disabled={loading}
                                >
                                    Reconfigure
                                </Button>
                                <Button
                                    variant="outlined"
                                    color="error"
                                    startIcon={<Delete />}
                                    onClick={() => setDisableDialogOpen(true)}
                                    disabled={loading}
                                >
                                    Disable MFA
                                </Button>
                            </>
                        )}
                    </Box>
                </CardContent>
            </Card>

            {/* Disable MFA Confirmation Dialog */}
            <Dialog
                open={disableDialogOpen}
                onClose={() => setDisableDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    <Box display="flex" alignItems="center">
                        <Warning sx={{ mr: 2, color: 'warning.main' }} />
                        Disable Two-Factor Authentication
                    </Box>
                </DialogTitle>
                <DialogContent>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                        Are you sure you want to disable two-factor authentication?
                    </Typography>
                    <Alert severity="warning">
                        <Typography variant="body2">
                            <strong>Warning:</strong> Disabling MFA will make your account less secure. 
                            You will only need your password to sign in, which could put your account at risk 
                            if your password is compromised.
                        </Typography>
                    </Alert>
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => setDisableDialogOpen(false)}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleDisableMFA}
                        color="error"
                        variant="contained"
                        disabled={loading}
                        startIcon={loading ? <CircularProgress size={16} /> : <Delete />}
                    >
                        {loading ? 'Disabling...' : 'Disable MFA'}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}