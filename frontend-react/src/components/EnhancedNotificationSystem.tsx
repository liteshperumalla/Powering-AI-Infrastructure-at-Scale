'use client';

import React, { useState, useEffect } from 'react';
import { 
    IconButton, 
    Badge, 
    Menu, 
    MenuItem, 
    ListItemText, 
    Divider, 
    Box, 
    Typography,
    ListItemIcon
} from '@mui/material';
import { 
    Notifications as NotificationsIcon,
    NotificationsActive as NotificationsActiveIcon,
    Assessment,
    CloudQueue,
    Security,
    CheckCircle
} from '@mui/icons-material';

interface Notification {
    id: string;
    title: string;
    message: string;
    time: string;
    type: 'success' | 'info' | 'warning' | 'error';
    read: boolean;
}

const EnhancedNotificationSystem: React.FC = () => {
    const [isClient, setIsClient] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);

    // Fetch real notifications from backend
    const fetchNotifications = async () => {
        try {
            setLoading(true);
            // Try performance alerts first
            const performanceResponse = await fetch('/api/api/v1/performance/alerts');
            const performanceAlerts = performanceResponse.ok ? await performanceResponse.json() : [];
            
            // Try admin alerts
            const adminResponse = await fetch('/api/admin/alerts');
            const adminAlerts = adminResponse.ok ? await adminResponse.json() : [];
            
            // Try compliance alerts
            const complianceResponse = await fetch('/api/compliance/alerts');
            const complianceAlerts = complianceResponse.ok ? await complianceResponse.json() : [];

            // Transform alerts to notification format
            const allAlerts = [
                ...performanceAlerts.map((alert: any) => ({
                    id: alert.id || `perf-${Math.random()}`,
                    title: alert.title || alert.alert_name || 'Performance Alert',
                    message: alert.message || alert.description || 'System performance notification',
                    time: alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Just now',
                    type: alert.severity === 'critical' ? 'error' : 
                          alert.severity === 'warning' ? 'warning' : 'info',
                    read: alert.acknowledged || false
                })),
                ...adminAlerts.map((alert: any) => ({
                    id: alert.id || `admin-${Math.random()}`,
                    title: alert.title || 'Admin Alert',
                    message: alert.message || alert.description || 'System administration notification',
                    time: alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Just now',
                    type: alert.priority === 'high' ? 'error' : 
                          alert.priority === 'medium' ? 'warning' : 'info',
                    read: alert.read || false
                })),
                ...complianceAlerts.map((alert: any) => ({
                    id: alert.id || `comp-${Math.random()}`,
                    title: alert.title || 'Compliance Alert',
                    message: alert.message || alert.description || 'Compliance notification',
                    time: alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Just now',
                    type: alert.level === 'high' ? 'error' : 
                          alert.level === 'medium' ? 'warning' : 'success',
                    read: alert.resolved || false
                }))
            ];

            setNotifications(allAlerts.slice(0, 10)); // Limit to 10 most recent
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
            // Fallback: show empty array instead of hardcoded data
            setNotifications([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setIsClient(true);
        fetchNotifications();
        
        // Refresh notifications every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleNotificationClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    const handleNotificationRead = (notificationId: string) => {
        setNotifications(prev => 
            prev.map(notif => 
                notif.id === notificationId 
                    ? { ...notif, read: true }
                    : notif
            )
        );
    };

    const handleMarkAllRead = () => {
        setNotifications(prev => 
            prev.map(notif => ({ ...notif, read: true }))
        );
        handleClose();
    };

    const unreadCount = notifications.filter(notif => !notif.read).length;
    const isOpen = Boolean(anchorEl);

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'success': return <CheckCircle color="success" />;
            case 'info': return <CloudQueue color="info" />;
            case 'warning': return <Security color="warning" />;
            case 'error': return <Assessment color="error" />;
            default: return <NotificationsIcon />;
        }
    };

    if (!isClient) {
        // Return a simple version during SSR to match server rendering
        return (
            <IconButton 
                sx={{ 
                    color: 'text.primary',
                    '&:hover': {
                        backgroundColor: 'action.hover'
                    }
                }}
            >
                <NotificationsIcon />
            </IconButton>
        );
    }

    return (
        <>
            <IconButton 
                onClick={handleNotificationClick}
                sx={{ 
                    color: 'text.primary',
                    '&:hover': {
                        backgroundColor: 'action.hover'
                    }
                }}
            >
                <Badge badgeContent={unreadCount} color="error">
                    {unreadCount > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />}
                </Badge>
            </IconButton>

            <Menu
                anchorEl={anchorEl}
                open={isOpen}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                PaperProps={{
                    sx: { 
                        minWidth: 350, 
                        maxWidth: 400,
                        maxHeight: 500
                    }
                }}
            >
                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="h6" color="text.primary" fontWeight={600}>
                        Notifications {loading && '(Loading...)'}
                    </Typography>
                    {unreadCount > 0 && (
                        <Typography 
                            variant="caption" 
                            color="primary"
                            sx={{ cursor: 'pointer' }}
                            onClick={handleMarkAllRead}
                        >
                            Mark all as read
                        </Typography>
                    )}
                </Box>
                
                {loading ? (
                    <MenuItem>
                        <ListItemText 
                            primary="Loading notifications..."
                            secondary="Fetching latest alerts from system"
                            secondaryTypographyProps={{
                                component: 'span'
                            }}
                        />
                    </MenuItem>
                ) : notifications.length === 0 ? (
                    <MenuItem>
                        <ListItemText 
                            primary="No notifications"
                            secondary="You're all caught up!"
                            secondaryTypographyProps={{
                                component: 'span'
                            }}
                        />
                    </MenuItem>
                ) : (
                    notifications.map((notification) => (
                        <MenuItem
                            key={notification.id}
                            onClick={() => handleNotificationRead(notification.id)}
                            sx={{
                                backgroundColor: notification.read ? 'transparent' : 'action.hover',
                                '&:hover': {
                                    backgroundColor: 'action.selected'
                                }
                            }}
                        >
                            <ListItemIcon>
                                {getNotificationIcon(notification.type)}
                            </ListItemIcon>
                            <ListItemText 
                                primary={notification.title}
                                secondary={`${notification.message} • ${notification.time}`}
                                secondaryTypographyProps={{
                                    component: 'span',
                                    variant: 'body2',
                                    color: 'text.secondary'
                                }}
                            />
                            {!notification.read && (
                                <Box
                                    sx={{
                                        width: 8,
                                        height: 8,
                                        borderRadius: '50%',
                                        backgroundColor: 'primary.main',
                                        ml: 1
                                    }}
                                />
                            )}
                        </MenuItem>
                    ))
                )}
                
                <Divider />
                <MenuItem onClick={handleClose} sx={{ justifyContent: 'center' }}>
                    <ListItemText 
                        primary="View All Notifications" 
                        primaryTypographyProps={{
                            component: 'span',
                            color: 'primary',
                            fontWeight: 600,
                            textAlign: 'center'
                        }}
                    />
                </MenuItem>
            </Menu>
        </>
    );
};

export default EnhancedNotificationSystem;