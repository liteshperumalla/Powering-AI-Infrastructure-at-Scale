import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Box,
    Avatar,
    Typography,
    Chip,
    Alert,
    Divider,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    Person,
    Email,
    Business,
    Edit,
    Save,
    Cancel,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { updateProfile, logout } from '@/store/slices/authSlice';

interface UserProfileProps {
    open: boolean;
    onClose: () => void;
}

export default function UserProfile({ open, onClose }: UserProfileProps) {
    const dispatch = useAppDispatch();
    const { user, loading, error } = useAppSelector(state => state.auth);

    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        name: user?.name || '',
        company: user?.company || '',
        preferences: {
            emailNotifications: true,
            pushNotifications: false,
            weeklyReports: true,
            marketingEmails: false,
        },
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value,
        }));
    };

    const handlePreferenceChange = (preference: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            preferences: {
                ...prev.preferences,
                [preference]: e.target.checked,
            },
        }));
    };

    const handleSave = async () => {
        try {
            await dispatch(updateProfile({
                name: formData.name,
                company: formData.company,
                preferences: formData.preferences,
            })).unwrap();

            setIsEditing(false);
        } catch (error) {
            console.error('Failed to update profile:', error);
        }
    };

    const handleCancel = () => {
        // Reset form data
        setFormData({
            name: user?.name || '',
            company: user?.company || '',
            preferences: {
                emailNotifications: true,
                pushNotifications: false,
                weeklyReports: true,
                marketingEmails: false,
            },
        });
        setIsEditing(false);
    };

    const handleLogout = async () => {
        try {
            await dispatch(logout()).unwrap();
            onClose();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    if (!user) {
        return null;
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
                        <Person />
                    </Avatar>
                    <Box>
                        <Typography variant="h6">User Profile</Typography>
                        <Typography variant="body2" color="text.secondary">
                            Manage your account settings
                        </Typography>
                    </Box>
                </Box>
            </DialogTitle>

            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {/* Basic Information */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                        Basic Information
                    </Typography>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <TextField
                            label="Full Name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            disabled={!isEditing}
                            fullWidth
                            InputProps={{
                                startAdornment: <Person sx={{ mr: 1, color: 'text.secondary' }} />,
                            }}
                        />

                        <TextField
                            label="Email"
                            value={user.email}
                            disabled
                            fullWidth
                            InputProps={{
                                startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} />,
                            }}
                        />

                        <TextField
                            label="Company"
                            name="company"
                            value={formData.company}
                            onChange={handleChange}
                            disabled={!isEditing}
                            fullWidth
                            InputProps={{
                                startAdornment: <Business sx={{ mr: 1, color: 'text.secondary' }} />,
                            }}
                        />
                    </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Account Details */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                        Account Details
                    </Typography>

                    <List dense>
                        <ListItem>
                            <ListItemText
                                primary="Role"
                                secondary={user.role}
                            />
                            <ListItemSecondaryAction>
                                <Chip
                                    label={user.role}
                                    size="small"
                                    color="primary"
                                />
                            </ListItemSecondaryAction>
                        </ListItem>

                        <ListItem>
                            <ListItemText
                                primary="Member Since"
                                secondary={new Date(user.created_at).toLocaleDateString()}
                            />
                        </ListItem>

                        <ListItem>
                            <ListItemText
                                primary="Last Login"
                                secondary={new Date(user.last_login).toLocaleDateString()}
                            />
                        </ListItem>
                    </List>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Preferences */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                        Notification Preferences
                    </Typography>

                    <List dense>
                        <ListItem>
                            <ListItemText
                                primary="Email Notifications"
                                secondary="Receive notifications about assessments and reports"
                            />
                            <ListItemSecondaryAction>
                                <Switch
                                    checked={formData.preferences.emailNotifications}
                                    onChange={handlePreferenceChange('emailNotifications')}
                                    disabled={!isEditing}
                                />
                            </ListItemSecondaryAction>
                        </ListItem>

                        <ListItem>
                            <ListItemText
                                primary="Push Notifications"
                                secondary="Receive browser push notifications"
                            />
                            <ListItemSecondaryAction>
                                <Switch
                                    checked={formData.preferences.pushNotifications}
                                    onChange={handlePreferenceChange('pushNotifications')}
                                    disabled={!isEditing}
                                />
                            </ListItemSecondaryAction>
                        </ListItem>

                        <ListItem>
                            <ListItemText
                                primary="Weekly Reports"
                                secondary="Receive weekly summary reports"
                            />
                            <ListItemSecondaryAction>
                                <Switch
                                    checked={formData.preferences.weeklyReports}
                                    onChange={handlePreferenceChange('weeklyReports')}
                                    disabled={!isEditing}
                                />
                            </ListItemSecondaryAction>
                        </ListItem>

                        <ListItem>
                            <ListItemText
                                primary="Marketing Emails"
                                secondary="Receive product updates and marketing content"
                            />
                            <ListItemSecondaryAction>
                                <Switch
                                    checked={formData.preferences.marketingEmails}
                                    onChange={handlePreferenceChange('marketingEmails')}
                                    disabled={!isEditing}
                                />
                            </ListItemSecondaryAction>
                        </ListItem>
                    </List>
                </Box>
            </DialogContent>

            <DialogActions sx={{ px: 3, pb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <Button
                        onClick={handleLogout}
                        color="error"
                        variant="outlined"
                    >
                        Logout
                    </Button>

                    <Box sx={{ display: 'flex', gap: 1 }}>
                        {isEditing ? (
                            <>
                                <Button
                                    onClick={handleCancel}
                                    startIcon={<Cancel />}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleSave}
                                    variant="contained"
                                    startIcon={<Save />}
                                    disabled={loading}
                                >
                                    {loading ? 'Saving...' : 'Save'}
                                </Button>
                            </>
                        ) : (
                            <>
                                <Button onClick={onClose}>
                                    Close
                                </Button>
                                <Button
                                    onClick={() => setIsEditing(true)}
                                    variant="contained"
                                    startIcon={<Edit />}
                                >
                                    Edit Profile
                                </Button>
                            </>
                        )}
                    </Box>
                </Box>
            </DialogActions>
        </Dialog>
    );
}