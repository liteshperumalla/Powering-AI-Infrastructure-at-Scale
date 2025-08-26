import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
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
    ListItemIcon,
} from '@mui/material';
import {
    Person,
    Email,
    Business,
    Settings,
    AdminPanelSettings,
    CalendarToday,
    Schedule,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { logout } from '@/store/slices/authSlice';
import { useRouter } from 'next/navigation';

interface UserProfileProps {
    open: boolean;
    onClose: () => void;
}

export default function UserProfile({ open, onClose }: UserProfileProps) {
    const dispatch = useAppDispatch();
    const router = useRouter();
    const { user, error } = useAppSelector(state => state.auth);

    const handleLogout = async () => {
        try {
            await dispatch(logout()).unwrap();
            onClose();
            router.push('/auth/login');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    const handleGoToSettings = () => {
        onClose();
        router.push('/settings');
    };

    if (!user) {
        return null;
    }

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
                        {user.full_name?.charAt(0).toUpperCase() || 'U'}
                    </Avatar>
                    <Box>
                        <Typography variant="h6">{user.full_name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                            {user.email}
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

                {/* Account Summary */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Person color="primary" />
                        Account Information
                    </Typography>

                    <List dense>
                        <ListItem>
                            <ListItemIcon>
                                <Email color="action" />
                            </ListItemIcon>
                            <ListItemText
                                primary="Email Address"
                                secondary={user.email}
                            />
                        </ListItem>

                        <ListItem>
                            <ListItemIcon>
                                <AdminPanelSettings color="action" />
                            </ListItemIcon>
                            <ListItemText
                                primary="Role"
                                secondary={user.role}
                            />
                            <Box sx={{ ml: 1 }}>
                                <Chip
                                    label={user.role}
                                    size="small"
                                    color="primary"
                                    variant="outlined"
                                />
                            </Box>
                        </ListItem>

                        <ListItem>
                            <ListItemIcon>
                                <CalendarToday color="action" />
                            </ListItemIcon>
                            <ListItemText
                                primary="Member Since"
                                secondary={new Date(user.created_at).toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })}
                            />
                        </ListItem>

                        <ListItem>
                            <ListItemIcon>
                                <Schedule color="action" />
                            </ListItemIcon>
                            <ListItemText
                                primary="Last Login"
                                secondary={new Date(user.last_login).toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            />
                        </ListItem>
                    </List>
                </Box>

                <Alert severity="info" sx={{ mb: 2 }}>
                    To update your profile information, notification preferences, or other settings, 
                    please visit the Settings page.
                </Alert>
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
                        <Button onClick={onClose}>
                            Close
                        </Button>
                        <Button
                            onClick={handleGoToSettings}
                            variant="contained"
                            startIcon={<Settings />}
                        >
                            Go to Settings
                        </Button>
                    </Box>
                </Box>
            </DialogActions>
        </Dialog>
    );
}
