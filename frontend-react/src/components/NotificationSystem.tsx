"use client";

import React, { useEffect, useState, useCallback } from 'react';
import {
    Alert,
    AlertTitle,
    Snackbar,
    Box,
    IconButton,
    Typography,
    Chip,
    Stack,
    Slide,
    Fade,
    Badge,
    Drawer,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Divider,
    Button,
    Tooltip
} from '@mui/material';
import {
    Close as CloseIcon,
    Notifications as NotificationsIcon,
    NotificationsActive as NotificationsActiveIcon,
    Info as InfoIcon,
    Warning as WarningIcon,
    Error as ErrorIcon,
    CheckCircle as SuccessIcon,
    Clear as ClearAllIcon,
    Settings as SettingsIcon
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState } from '../store';
import { addNotification, removeNotification, clearNotifications } from '../store/slices/uiSlice';

type NotificationType = 'success' | 'error' | 'warning' | 'info';
type SeverityType = 'critical' | 'high' | 'medium' | 'low';
type ActionColor = 'primary' | 'secondary';

// Use the store's notification type if it exists, otherwise define our own
type StoreNotification = Parameters<typeof addNotification>[0];

interface NotificationAction {
    label: string;
    onClick: () => void;
    color?: ActionColor;
}

interface Notification {
    id: string;
    type: NotificationType;
    title?: string;
    message: string;
    duration?: number;
    timestamp: number;
    persistent?: boolean;
    actions?: NotificationAction[];
    data?: Record<string, unknown>;
}

interface NotificationData {
    type?: NotificationType;
    title?: string;
    message: string;
    duration?: number;
    persistent?: boolean;
}

interface AlertData {
    severity: SeverityType;
    alert_type: string;
    message: string;
    persistent?: boolean;
}

interface WebSocketMessage {
    type: string;
    data: NotificationData | AlertData | Record<string, unknown>;
    timestamp: string;
    user_id?: string;
    session_id?: string;
}

interface NotificationSystemProps {
    websocket?: WebSocket | null; // Optional websocket connection
    maxNotifications?: number;
    defaultDuration?: number;
    position?: {
        vertical: 'top' | 'bottom';
        horizontal: 'left' | 'center' | 'right';
    };
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({
    websocket = null, // Default to null if not provided
    maxNotifications = 5,
    defaultDuration = 5000,
    position = { vertical: 'top', horizontal: 'right' }
}) => {
    const dispatch = useDispatch();
    const notifications = useSelector((state: RootState) => state.ui.notifications);
    const { isAuthenticated } = useSelector((state: RootState) => state.auth);

    // Don't render notification system if user is not authenticated
    if (!isAuthenticated) {
        return null;
    }

    const [drawerOpen, setDrawerOpen] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const [allNotifications, setAllNotifications] = useState<Notification[]>([]);

    // Helper function to check if data is NotificationData
    const isNotificationData = (data: unknown): data is NotificationData => {
        return data !== null && 
               data !== undefined && 
               typeof data === 'object' && 
               'message' in data && 
               typeof (data as Record<string, unknown>).message === 'string';
    };

    // Helper function to check if data is AlertData
    const isAlertData = (data: unknown): data is AlertData => {
        return data !== null && 
               data !== undefined && 
               typeof data === 'object' && 
               'severity' in data && 
               'alert_type' in data && 
               'message' in data &&
               typeof (data as Record<string, unknown>).severity === 'string' && 
               typeof (data as Record<string, unknown>).alert_type === 'string' && 
               typeof (data as Record<string, unknown>).message === 'string';
    };

    // WebSocket message handler
    const handleWebSocketMessage = useCallback((event: MessageEvent) => {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);

            if (message.type === 'notification' && isNotificationData(message.data)) {
                const notificationData = message.data;
                const notification: Omit<Notification, 'id' | 'timestamp'> = {
                    type: notificationData.type || 'info',
                    title: notificationData.title,
                    message: notificationData.message,
                    duration: notificationData.duration || defaultDuration,
                    persistent: notificationData.persistent || false,
                    data: message.data as unknown as Record<string, unknown>
                };

                dispatch(addNotification(notification));

                // Add to all notifications for history
                const fullNotification: Notification = {
                    ...notification,
                    id: Date.now().toString(),
                    timestamp: Date.now()
                };

                setAllNotifications(prev => [fullNotification, ...prev].slice(0, 100)); // Keep last 100
                setUnreadCount(prev => prev + 1);
            } else if (message.type === 'alert' && isAlertData(message.data)) {
                const alertData = message.data;
                // Handle performance alerts
                const alertNotification: Omit<Notification, 'id' | 'timestamp'> = {
                    type: alertData.severity === 'critical' ? 'error' :
                        alertData.severity === 'high' ? 'error' :
                            alertData.severity === 'medium' ? 'warning' : 'info',
                    title: `System Alert: ${alertData.alert_type}`,
                    message: alertData.message,
                    persistent: alertData.persistent ?? (alertData.severity === 'critical'),
                    data: message.data as unknown as Record<string, unknown>
                };

                dispatch(addNotification(alertNotification));

                const fullNotification: Notification = {
                    ...alertNotification,
                    id: Date.now().toString(),
                    timestamp: Date.now()
                };

                setAllNotifications(prev => [fullNotification, ...prev].slice(0, 100));
                setUnreadCount(prev => prev + 1);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }, [dispatch, defaultDuration]);

    // Setup WebSocket listener only if websocket is available and connected
    useEffect(() => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.addEventListener('message', handleWebSocketMessage);

            return () => {
                if (websocket.readyState === WebSocket.OPEN) {
                    websocket.removeEventListener('message', handleWebSocketMessage);
                }
            };
        }
    }, [websocket, handleWebSocketMessage]);

    // Method to manually add notifications for testing or manual updates
    const addManualNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
        const fullNotification: Notification = {
            ...notification,
            id: Date.now().toString(),
            timestamp: Date.now()
        };
        
        dispatch(addNotification(notification));
        setAllNotifications(prev => [fullNotification, ...prev].slice(0, 100));
        setUnreadCount(prev => prev + 1);
    };

    // Note: useImperativeHandle removed as it was causing errors
    // External components can use the Redux dispatch directly to add notifications

    // Auto-remove notifications after duration
    useEffect(() => {
        const timers: NodeJS.Timeout[] = [];

        notifications.forEach(notification => {
            if (notification.duration && notification.duration > 0 && !notification.persistent) {
                const timer = setTimeout(() => {
                    dispatch(removeNotification(notification.id));
                }, notification.duration);
                timers.push(timer);
            }
        });

        return () => {
            timers.forEach(timer => clearTimeout(timer));
        };
    }, [notifications, dispatch]);

    const handleClose = (notificationId: string) => {
        dispatch(removeNotification(notificationId));
    };

    const handleDrawerOpen = () => {
        setDrawerOpen(true);
        setUnreadCount(0); // Mark as read when opened
    };

    const handleDrawerClose = () => {
        setDrawerOpen(false);
    };

    const handleClearAll = () => {
        dispatch(clearNotifications());
        setAllNotifications([]);
        setUnreadCount(0);
    };

    const getNotificationIcon = (type: NotificationType) => {
        switch (type) {
            case 'success':
                return <SuccessIcon color="success" />;
            case 'error':
                return <ErrorIcon color="error" />;
            case 'warning':
                return <WarningIcon color="warning" />;
            case 'info':
            default:
                return <InfoIcon color="info" />;
        }
    };

    const getNotificationColor = (type: NotificationType): 'success' | 'error' | 'warning' | 'info' => {
        return type;
    };

    const formatTimestamp = (timestamp: number) => {
        const now = Date.now();
        const diff = now - timestamp;

        if (diff < 60000) { // Less than 1 minute
            return 'Just now';
        } else if (diff < 3600000) { // Less than 1 hour
            return `${Math.floor(diff / 60000)}m ago`;
        } else if (diff < 86400000) { // Less than 1 day
            return `${Math.floor(diff / 3600000)}h ago`;
        } else {
            return new Date(timestamp).toLocaleDateString();
        }
    };

    return (
        <>
            {/* Notification Bell Icon */}
            <Tooltip title="Notifications">
                <IconButton
                    color="inherit"
                    onClick={handleDrawerOpen}
                    sx={{ mr: 1 }}
                >
                    <Badge badgeContent={unreadCount} color="error">
                        {unreadCount > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />}
                    </Badge>
                </IconButton>
            </Tooltip>

            {/* Active Notifications (Snackbars) */}
            <Box
                sx={{
                    position: 'fixed',
                    [position.vertical]: 20,
                    [position.horizontal]: 20,
                    zIndex: (theme) => theme.zIndex.snackbar,
                    maxWidth: 400,
                    width: '100%'
                }}
            >
                <Stack spacing={1}>
                    {(notifications || []).slice(0, maxNotifications).map((notification) => (
                        <Slide
                            key={notification.id}
                            direction={position.horizontal === 'right' ? 'left' : 'right'}
                            in={true}
                            timeout={300}
                        >
                            <Alert
                                severity={getNotificationColor(notification.type)}
                                onClose={() => handleClose(notification.id)}
                                sx={{
                                    width: '100%',
                                    boxShadow: 3,
                                    '& .MuiAlert-message': {
                                        width: '100%'
                                    }
                                }}
                                action={
                                    <IconButton
                                        size="small"
                                        onClick={() => handleClose(notification.id)}
                                        color="inherit"
                                    >
                                        <CloseIcon fontSize="small" />
                                    </IconButton>
                                }
                            >
                                {notification.title && (
                                    <AlertTitle>{notification.title}</AlertTitle>
                                )}
                                <Typography variant="body2">
                                    {notification.message}
                                </Typography>

                                {/* Custom Actions */}
                                {notification.actions && (
                                    <Box sx={{ mt: 1 }}>
                                        <Stack direction="row" spacing={1}>
                                            {notification.actions.map((action, actionIndex) => (
                                                <Button
                                                    key={actionIndex}
                                                    size="small"
                                                    color={'color' in action ? (action as any).color || 'primary' : 'primary'}
                                                    onClick={action.onClick}
                                                >
                                                    {action.label}
                                                </Button>
                                            ))}
                                        </Stack>
                                    </Box>
                                )}
                            </Alert>
                        </Slide>
                    ))}
                </Stack>
            </Box>

            {/* Notification History Drawer */}
            <Drawer
                anchor="right"
                open={drawerOpen}
                onClose={handleDrawerClose}
                PaperProps={{
                    sx: { width: 400 }
                }}
            >
                <Box sx={{ p: 2 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="h6" color="text.primary">
                            Notifications
                        </Typography>
                        <Stack direction="row" spacing={1}>
                            <Tooltip title="Clear All">
                                <IconButton size="small" onClick={handleClearAll}>
                                    <ClearAllIcon />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Settings">
                                <IconButton size="small">
                                    <SettingsIcon />
                                </IconButton>
                            </Tooltip>
                            <IconButton size="small" onClick={handleDrawerClose}>
                                <CloseIcon />
                            </IconButton>
                        </Stack>
                    </Stack>
                </Box>

                <Divider />

                <List sx={{ flexGrow: 1, overflow: 'auto' }}>
                    {allNotifications.length === 0 ? (
                        <ListItem>
                            <ListItemText
                                primary="No notifications"
                                secondary="You're all caught up!"
                                sx={{ textAlign: 'center' }}
                            />
                        </ListItem>
                    ) : (
                        allNotifications.map((notification) => (
                            <React.Fragment key={notification.id}>
                                <ListItem alignItems="flex-start">
                                    <ListItemIcon sx={{ mt: 1 }}>
                                        {getNotificationIcon(notification.type)}
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={
                                            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                                                <Typography variant="subtitle2" component="div">
                                                    {notification.title || 'Notification'}
                                                </Typography>
                                                <Chip
                                                    label={formatTimestamp(notification.timestamp)}
                                                    size="small"
                                                    variant="outlined"
                                                    sx={{ ml: 1, fontSize: '0.7rem' }}
                                                />
                                            </Stack>
                                        }
                                        secondary={
                                            <Typography
                                                variant="body2"
                                                color="text.secondary"
                                                sx={{ mt: 0.5 }}
                                            >
                                                {notification.message}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                                <Divider variant="inset" component="li" />
                            </React.Fragment>
                        ))
                    )}
                </List>
            </Drawer>
        </>
    );
};

export default NotificationSystem;