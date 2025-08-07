'use client';

import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    TextField,
    Button,
    Grid,
    Divider,
    Switch,
    FormControlLabel,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    Avatar,
    IconButton,
} from '@mui/material';
import {
    Settings as SettingsIcon,
    Person,
    Security,
    Notifications,
    Palette,
    Save,
    Edit,
} from '@mui/icons-material';
import Navigation from '@/components/Navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { updateProfile } from '@/store/slices/authSlice';

export default function SettingsPage() {
    const dispatch = useAppDispatch();
    const { user, loading } = useAppSelector(state => state.auth);
    
    const [profileData, setProfileData] = useState({
        fullName: user?.full_name || '',
        email: user?.email || '',
        company: '',
        role: user?.role || 'user',
    });
    
    const [preferences, setPreferences] = useState({
        theme: 'light',
        language: 'en',
        timezone: 'UTC',
        emailNotifications: true,
        pushNotifications: true,
        weeklyReports: true,
        securityAlerts: true,
    });
    
    const [securitySettings, setSecuritySettings] = useState({
        twoFactorEnabled: false,
        sessionTimeout: 30,
        autoLogout: true,
    });

    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

    useEffect(() => {
        if (user) {
            setProfileData({
                fullName: user.full_name || '',
                email: user.email || '',
                company: '',
                role: user.role || 'user',
            });
        }
    }, [user]);

    const handleProfileChange = (field: string, value: string) => {
        setProfileData(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handlePreferenceChange = (field: string, value: any) => {
        setPreferences(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleSecurityChange = (field: string, value: any) => {
        setSecuritySettings(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleSaveProfile = async () => {
        try {
            setSaveStatus('saving');
            await dispatch(updateProfile({
                full_name: profileData.fullName,
                company: profileData.company,
                preferences: preferences
            })).unwrap();
            setSaveStatus('success');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (error) {
            setSaveStatus('error');
            setTimeout(() => setSaveStatus('idle'), 3000);
        }
    };

    const getSaveButtonText = () => {
        switch (saveStatus) {
            case 'saving': return 'Saving...';
            case 'success': return 'Saved!';
            case 'error': return 'Error - Try Again';
            default: return 'Save Changes';
        }
    };

    const getSaveButtonColor = () => {
        switch (saveStatus) {
            case 'success': return 'success';
            case 'error': return 'error';
            default: return 'primary';
        }
    };

    return (
        <ProtectedRoute>
            <Navigation title="Settings">
                <Container maxWidth="lg">
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <SettingsIcon sx={{ fontSize: 40 }} />
                            Settings
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Manage your account preferences and security settings.
                        </Typography>
                    </Box>

                    {saveStatus === 'success' && (
                        <Alert severity="success" sx={{ mb: 3 }}>
                            Settings saved successfully!
                        </Alert>
                    )}

                    {saveStatus === 'error' && (
                        <Alert severity="error" sx={{ mb: 3 }}>
                            Failed to save settings. Please try again.
                        </Alert>
                    )}

                    <Grid container spacing={3}>
                        {/* Profile Settings */}
                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                        <Person color="primary" />
                                        <Typography variant="h6">Profile Information</Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                        <Avatar 
                                            sx={{ width: 60, height: 60 }}
                                            src="/api/placeholder/60/60"
                                        >
                                            {profileData.fullName.charAt(0).toUpperCase()}
                                        </Avatar>
                                        <Box>
                                            <Typography variant="h6">{profileData.fullName}</Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {profileData.email}
                                            </Typography>
                                        </Box>
                                        <IconButton size="small">
                                            <Edit />
                                        </IconButton>
                                    </Box>

                                    <Grid container spacing={2}>
                                        <Grid item xs={12}>
                                            <TextField
                                                fullWidth
                                                label="Full Name"
                                                value={profileData.fullName}
                                                onChange={(e) => handleProfileChange('fullName', e.target.value)}
                                                size="small"
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <TextField
                                                fullWidth
                                                label="Email"
                                                value={profileData.email}
                                                disabled
                                                size="small"
                                                helperText="Contact support to change your email"
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <TextField
                                                fullWidth
                                                label="Company"
                                                value={profileData.company}
                                                onChange={(e) => handleProfileChange('company', e.target.value)}
                                                size="small"
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <FormControl fullWidth size="small">
                                                <InputLabel>Role</InputLabel>
                                                <Select
                                                    value={profileData.role}
                                                    disabled
                                                    label="Role"
                                                >
                                                    <MenuItem value="user">User</MenuItem>
                                                    <MenuItem value="admin">Admin</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/* Preferences */}
                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                        <Palette color="primary" />
                                        <Typography variant="h6">Preferences</Typography>
                                    </Box>

                                    <Grid container spacing={2}>
                                        <Grid item xs={12}>
                                            <FormControl fullWidth size="small">
                                                <InputLabel>Theme</InputLabel>
                                                <Select
                                                    value={preferences.theme}
                                                    onChange={(e) => handlePreferenceChange('theme', e.target.value)}
                                                    label="Theme"
                                                >
                                                    <MenuItem value="light">Light</MenuItem>
                                                    <MenuItem value="dark">Dark</MenuItem>
                                                    <MenuItem value="auto">Auto</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        <Grid item xs={12}>
                                            <FormControl fullWidth size="small">
                                                <InputLabel>Language</InputLabel>
                                                <Select
                                                    value={preferences.language}
                                                    onChange={(e) => handlePreferenceChange('language', e.target.value)}
                                                    label="Language"
                                                >
                                                    <MenuItem value="en">English</MenuItem>
                                                    <MenuItem value="es">Spanish</MenuItem>
                                                    <MenuItem value="fr">French</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                        <Grid item xs={12}>
                                            <FormControl fullWidth size="small">
                                                <InputLabel>Timezone</InputLabel>
                                                <Select
                                                    value={preferences.timezone}
                                                    onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                                                    label="Timezone"
                                                >
                                                    <MenuItem value="UTC">UTC</MenuItem>
                                                    <MenuItem value="America/New_York">Eastern Time</MenuItem>
                                                    <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                                                    <MenuItem value="Europe/London">London</MenuItem>
                                                </Select>
                                            </FormControl>
                                        </Grid>
                                    </Grid>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/* Notifications */}
                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                        <Notifications color="primary" />
                                        <Typography variant="h6">Notifications</Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.emailNotifications}
                                                    onChange={(e) => handlePreferenceChange('emailNotifications', e.target.checked)}
                                                />
                                            }
                                            label="Email Notifications"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.pushNotifications}
                                                    onChange={(e) => handlePreferenceChange('pushNotifications', e.target.checked)}
                                                />
                                            }
                                            label="Push Notifications"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.weeklyReports}
                                                    onChange={(e) => handlePreferenceChange('weeklyReports', e.target.checked)}
                                                />
                                            }
                                            label="Weekly Reports"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.securityAlerts}
                                                    onChange={(e) => handlePreferenceChange('securityAlerts', e.target.checked)}
                                                />
                                            }
                                            label="Security Alerts"
                                        />
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/* Security */}
                        <Grid item xs={12} md={6}>
                            <Card>
                                <CardContent>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                                        <Security color="primary" />
                                        <Typography variant="h6">Security</Typography>
                                    </Box>

                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={securitySettings.twoFactorEnabled}
                                                    onChange={(e) => handleSecurityChange('twoFactorEnabled', e.target.checked)}
                                                />
                                            }
                                            label="Two-Factor Authentication"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={securitySettings.autoLogout}
                                                    onChange={(e) => handleSecurityChange('autoLogout', e.target.checked)}
                                                />
                                            }
                                            label="Auto Logout"
                                        />
                                        <FormControl size="small">
                                            <InputLabel>Session Timeout (minutes)</InputLabel>
                                            <Select
                                                value={securitySettings.sessionTimeout}
                                                onChange={(e) => handleSecurityChange('sessionTimeout', e.target.value)}
                                                label="Session Timeout (minutes)"
                                            >
                                                <MenuItem value={15}>15 minutes</MenuItem>
                                                <MenuItem value={30}>30 minutes</MenuItem>
                                                <MenuItem value={60}>1 hour</MenuItem>
                                                <MenuItem value={120}>2 hours</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>

                    <Divider sx={{ my: 4 }} />

                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                        <Button
                            variant="outlined"
                            onClick={() => {
                                // Reset to original values
                                if (user) {
                                    setProfileData({
                                        fullName: user.full_name || '',
                                        email: user.email || '',
                                        company: '',
                                        role: user.role || 'user',
                                    });
                                }
                            }}
                        >
                            Reset
                        </Button>
                        <Button
                            variant="contained"
                            startIcon={<Save />}
                            onClick={handleSaveProfile}
                            disabled={loading || saveStatus === 'saving'}
                            color={getSaveButtonColor() as any}
                        >
                            {getSaveButtonText()}
                        </Button>
                    </Box>
                </Container>
            </Navigation>
        </ProtectedRoute>
    );
}