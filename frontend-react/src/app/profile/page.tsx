'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Paper,
    Typography,
    Avatar,
    Button,
    TextField,
    Grid,
    Divider,
    Chip,
    Card,
    CardContent,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    AccountCircle,
    Email,
    Business,
    LocationOn,
    Phone,
    Edit,
    Save,
    Cancel,
    Security,
    Notifications,
    Language,
    Palette,
    Work,
} from '@mui/icons-material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { updateProfile } from '@/store/slices/authSlice';

interface UserProfile {
    name: string;
    email: string;
    company: string;
    location: string;
    phone: string;
    avatar?: string;
    role: string;
    joinDate: string;
}

export default function ProfilePage() {
    const dispatch = useAppDispatch();
    const { user, loading } = useAppSelector(state => state.auth);
    const [isEditing, setIsEditing] = useState(false);

    const [profile, setProfile] = useState<UserProfile>({
        name: user?.full_name || '',
        email: user?.email || '',
        company: user?.company_name || '',
        location: '',
        phone: '',
        role: user?.job_title || user?.role || '',
        joinDate: user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : ''
    });

    const [editedProfile, setEditedProfile] = useState<UserProfile>(profile);

    // Update profile when user data changes
    useEffect(() => {
        if (user) {
            const updatedProfile = {
                name: user.full_name || '',
                email: user.email || '',
                company: user.company_name || '',
                location: '',
                phone: '',
                role: user.job_title || user.role || '',
                joinDate: user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : ''
            };
            setProfile(updatedProfile);
            setEditedProfile(updatedProfile);
        }
    }, [user]);
    
    const [preferences, setPreferences] = useState({
        emailNotifications: true,
        pushNotifications: true,
        darkMode: false,
        language: 'English'
    });

    const handleEdit = () => {
        setEditedProfile(profile);
        setIsEditing(true);
    };

    const handleSave = async () => {
        try {
            await dispatch(updateProfile({
                full_name: editedProfile.name,
                company: editedProfile.company,
                job_title: editedProfile.role,
            })).unwrap();
            setProfile(editedProfile);
            setIsEditing(false);
        } catch (error) {
            console.error('Failed to update profile:', error);
            // You might want to show an error message to the user
        }
    };

    const handleCancel = () => {
        setEditedProfile(profile);
        setIsEditing(false);
    };

    const handleInputChange = (field: keyof UserProfile) => (event: React.ChangeEvent<HTMLInputElement>) => {
        setEditedProfile({
            ...editedProfile,
            [field]: event.target.value
        });
    };

    const handlePreferenceChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
        setPreferences({
            ...preferences,
            [field]: event.target.checked
        });
    };

    return (
        <ProtectedRoute>
            <ResponsiveLayout title="User Profile">
                <Container maxWidth="lg" sx={{ py: 4 }}>
                    <Grid container spacing={4}>
                        {/* Profile Card */}
                        <Grid item xs={12} md={4}>
                            <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
                                <Avatar
                                    src={profile.avatar}
                                    sx={{ 
                                        width: 120, 
                                        height: 120, 
                                        mx: 'auto', 
                                        mb: 2,
                                        fontSize: '3rem'
                                    }}
                                >
                                    {profile.name.split(' ').map(n => n[0]).join('')}
                                </Avatar>
                                
                                <Typography variant="h5" color="text.primary" gutterBottom fontWeight={600}>
                                    {profile.name}
                                </Typography>
                                
                                <Chip
                                    label={profile.role || 'User'}
                                    color="primary"
                                    variant="outlined"
                                    sx={{ mb: 2 }}
                                />
                                
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    Member since {profile.joinDate}
                                </Typography>

                                <Box sx={{ mt: 3 }}>
                                    {!isEditing ? (
                                        <Button
                                            variant="contained"
                                            startIcon={<Edit />}
                                            onClick={handleEdit}
                                            fullWidth
                                        >
                                            Edit Profile
                                        </Button>
                                    ) : (
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <Button
                                                variant="contained"
                                                startIcon={<Save />}
                                                onClick={handleSave}
                                                fullWidth
                                            >
                                                Save
                                            </Button>
                                            <Button
                                                variant="outlined"
                                                startIcon={<Cancel />}
                                                onClick={handleCancel}
                                                fullWidth
                                            >
                                                Cancel
                                            </Button>
                                        </Box>
                                    )}
                                </Box>
                            </Paper>
                        </Grid>

                        {/* Profile Details */}
                        <Grid item xs={12} md={8}>
                            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                                <Typography variant="h6" color="text.primary" gutterBottom fontWeight={600}>
                                    Profile Information
                                </Typography>
                                <Divider sx={{ mb: 3 }} />

                                <Grid container spacing={3}>
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Full Name"
                                            value={isEditing ? editedProfile.name : profile.name}
                                            onChange={handleInputChange('name')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <AccountCircle sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Email"
                                            value={isEditing ? editedProfile.email : profile.email}
                                            onChange={handleInputChange('email')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <Email sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Company"
                                            value={isEditing ? editedProfile.company : profile.company}
                                            onChange={handleInputChange('company')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <Business sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>

                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Job Title / Profession"
                                            value={isEditing ? editedProfile.role : profile.role}
                                            onChange={handleInputChange('role')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <Work sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>

                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Location"
                                            value={isEditing ? editedProfile.location : profile.location}
                                            onChange={handleInputChange('location')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <LocationOn sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Phone"
                                            value={isEditing ? editedProfile.phone : profile.phone}
                                            onChange={handleInputChange('phone')}
                                            disabled={!isEditing}
                                            InputProps={{
                                                startAdornment: <Phone sx={{ mr: 1, color: 'action.active' }} />
                                            }}
                                        />
                                    </Grid>
                                </Grid>
                            </Paper>

                            {/* Preferences Card */}
                            <Paper elevation={2} sx={{ p: 3 }}>
                                <Typography variant="h6" color="text.primary" gutterBottom fontWeight={600}>
                                    Preferences & Settings
                                </Typography>
                                <Divider sx={{ mb: 3 }} />

                                <List>
                                    <ListItem>
                                        <ListItemIcon>
                                            <Email />
                                        </ListItemIcon>
                                        <ListItemText 
                                            primary="Email Notifications" 
                                            secondary="Receive email updates about assessments and reports"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.emailNotifications}
                                                    onChange={handlePreferenceChange('emailNotifications')}
                                                />
                                            }
                                            label=""
                                        />
                                    </ListItem>
                                    
                                    <ListItem>
                                        <ListItemIcon>
                                            <Notifications />
                                        </ListItemIcon>
                                        <ListItemText 
                                            primary="Push Notifications" 
                                            secondary="Get real-time notifications in your browser"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.pushNotifications}
                                                    onChange={handlePreferenceChange('pushNotifications')}
                                                />
                                            }
                                            label=""
                                        />
                                    </ListItem>
                                    
                                    <ListItem>
                                        <ListItemIcon>
                                            <Palette />
                                        </ListItemIcon>
                                        <ListItemText 
                                            primary="Dark Mode" 
                                            secondary="Use dark theme for better viewing experience"
                                        />
                                        <FormControlLabel
                                            control={
                                                <Switch 
                                                    checked={preferences.darkMode}
                                                    onChange={handlePreferenceChange('darkMode')}
                                                />
                                            }
                                            label=""
                                        />
                                    </ListItem>
                                    
                                    <ListItem>
                                        <ListItemIcon>
                                            <Language />
                                        </ListItemIcon>
                                        <ListItemText 
                                            primary="Language" 
                                            secondary="Currently set to English"
                                        />
                                        <Chip label="English" size="small" />
                                    </ListItem>
                                </List>
                            </Paper>
                        </Grid>
                    </Grid>
                </Container>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}