'use client';

import React, { useState, useEffect } from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    IconButton,
    Drawer,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Box,
    Badge,
    Avatar,
    Menu,
    MenuItem,
    Divider,
    useMediaQuery,
    useTheme,
    Chip,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Dashboard,
    Assessment,
    Analytics,
    CloudQueue,
    Settings,
    AccountCircle,
    Notifications,
    DarkMode,
    LightMode,
    Close,
    Home,
    Chat,
    TrendingUp,
    Security,
    Speed,
    Approval,
    AccountTree,
    History,
    DeviceHub,
    Business,
    AttachMoney,
    Gavel,
    Lock,
    Report,
    MonitorHeart,
    Info,
    Science,
    Feedback,
    VerifiedUser,
} from '@mui/icons-material';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import EnhancedNotificationSystem from './EnhancedNotificationSystem';

interface NavItem {
    path: string;
    label: string;
    icon: React.ReactNode;
    badge?: number;
}

// Public navigation items (available without authentication)
const publicNavigationItems: NavItem[] = [
    // Home removed - logo now serves as home button
    // About moved to right side of navbar
];

// Private navigation items (require authentication)
const privateNavigationItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: <Dashboard /> },
    { path: '/assessments', label: 'Assessments', icon: <Assessment /> },
    { path: '/analytics', label: 'Advanced Analytics', icon: <Analytics /> },
    { path: '/recommendations', label: 'Recommendations', icon: <TrendingUp /> },
    { path: '/chat', label: 'AI Assistant', icon: <Chat /> },
    { path: '/performance', label: 'Performance', icon: <Speed /> },
    { path: '/security', label: 'Security', icon: <Security /> },
    { path: '/gitops', label: 'GitOps', icon: <DeviceHub /> },
    { path: '/experiments', label: 'A/B Testing', icon: <Science /> },
    { path: '/feedback', label: 'Feedback', icon: <Feedback /> },
    { path: '/quality', label: 'Quality Assurance', icon: <VerifiedUser /> },
    { path: '/approvals', label: 'Approvals', icon: <Approval /> },
    { path: '/impact-analysis', label: 'Impact Analysis', icon: <AccountTree /> },
    { path: '/rollback', label: 'Rollback', icon: <History /> },
    { path: '/executive-dashboard', label: 'Executive Dashboard', icon: <Business /> },
    { path: '/budget-forecasting', label: 'Budget Forecasting', icon: <AttachMoney /> },
    { path: '/vendor-lockin', label: 'Vendor Lock-in', icon: <Lock /> },
    { path: '/compliance', label: 'Compliance', icon: <Gavel /> },
    { path: '/reports', label: 'Reports', icon: <Report /> },
    { path: '/system-status', label: 'System Status', icon: <MonitorHeart /> },
    { path: '/settings', label: 'Settings', icon: <Settings /> },
];

interface ModernNavbarProps {
    onThemeToggle?: () => void;
    isDarkMode?: boolean;
    userName?: string;
    userAvatar?: string;
    isAuthenticated?: boolean;
    syncStatus?: {
        isOnline: boolean;
        isSyncing: boolean;
        queueLength: number;
    };
}

export default function ModernNavbar({ 
    onThemeToggle, 
    isDarkMode = false, 
    userName = 'User',
    userAvatar,
    isAuthenticated = false,
    syncStatus
}: ModernNavbarProps) {
    const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
    const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
    
    // Get appropriate navigation items based on authentication
    const getNavigationItems = () => {
        return isAuthenticated ? [...publicNavigationItems, ...privateNavigationItems] : publicNavigationItems;
    };
    
    const navigationItems = getNavigationItems();
    const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<null | HTMLElement>(null);
    const [notificationCount, setNotificationCount] = useState(3);
    
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const pathname = usePathname();
    const router = useRouter();

    // Close mobile drawer when route changes
    useEffect(() => {
        setMobileDrawerOpen(false);
    }, [pathname]);

    const handleMobileDrawerToggle = () => {
        setMobileDrawerOpen(!mobileDrawerOpen);
    };

    const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setUserMenuAnchor(event.currentTarget);
    };

    const handleUserMenuClose = () => {
        setUserMenuAnchor(null);
    };

    const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setNotificationMenuAnchor(event.currentTarget);
        setNotificationCount(0); // Clear count when opened
    };

    const handleNotificationMenuClose = () => {
        setNotificationMenuAnchor(null);
    };

    const isActiveRoute = (path: string) => {
        return pathname === path;
    };

    const mobileDrawer = (
        <Box sx={{ width: 280 }}>
            <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                p: 2,
                borderBottom: 1,
                borderColor: 'divider'
            }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Infra Mind
                </Typography>
                <IconButton 
                    onClick={handleMobileDrawerToggle}
                    aria-label="Close navigation menu"
                >
                    <Close />
                </IconButton>
            </Box>
            <List role="navigation" aria-label="Main navigation menu">
                {navigationItems.map((item) => (
                    <ListItem 
                        key={item.path}
                        component={Link}
                        href={item.path}
                        aria-current={isActiveRoute(item.path) ? 'page' : undefined}
                        aria-label={`Navigate to ${item.label}`}
                        sx={{
                            backgroundColor: isActiveRoute(item.path) 
                                ? theme.palette.primary.main + '20' 
                                : 'transparent',
                            color: isActiveRoute(item.path) 
                                ? theme.palette.primary.main 
                                : 'inherit',
                            borderRadius: 1,
                            mx: 1,
                            mb: 0.5,
                            '&:hover': {
                                backgroundColor: theme.palette.primary.main + '10',
                            }
                        }}
                    >
                        <ListItemIcon sx={{ 
                            color: isActiveRoute(item.path) 
                                ? theme.palette.primary.main 
                                : 'inherit',
                            minWidth: 40
                        }}>
                            {item.badge ? (
                                <Badge badgeContent={item.badge} color="secondary">
                                    {item.icon}
                                </Badge>
                            ) : item.icon}
                        </ListItemIcon>
                        <ListItemText 
                            primary={item.label}
                            primaryTypographyProps={{
                                fontWeight: isActiveRoute(item.path) ? 600 : 400
                            }}
                        />
                        {isActiveRoute(item.path) && (
                            <Chip size="small" label="Active" color="primary" />
                        )}
                    </ListItem>
                ))}
            </List>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ p: 2 }}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={isDarkMode}
                            onChange={onThemeToggle}
                            icon={<LightMode />}
                            checkedIcon={<DarkMode />}
                        />
                    }
                    label={isDarkMode ? "Dark Mode" : "Light Mode"}
                />
            </Box>
        </Box>
    );

    return (
        <>
            <AppBar 
                position="sticky" 
                elevation={1}
                sx={{ 
                    backgroundColor: theme.palette.background.paper,
                    borderBottom: 1,
                    borderColor: 'divider',
                    backdropFilter: 'blur(8px)',
                    backgroundColor: theme.palette.mode === 'dark' 
                        ? 'rgba(18, 18, 18, 0.8)' 
                        : 'rgba(255, 255, 255, 0.8)',
                }}
            >
                <Toolbar sx={{ justifyContent: 'space-between' }}>
                    {/* Left side - Logo and Navigation */}
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {isMobile && (
                            <IconButton
                                color="inherit"
                                aria-label="open drawer"
                                edge="start"
                                onClick={handleMobileDrawerToggle}
                                sx={{ mr: 1 }}
                            >
                                <MenuIcon />
                            </IconButton>
                        )}
                        
                        <Typography
                            variant="h6"
                            component={pathname === '/' ? 'div' : Link}
                            href={pathname === '/' ? undefined : '/'}
                            sx={{
                                fontWeight: 700,
                                color: theme.palette.primary.main,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 1,
                                textDecoration: 'none',
                                cursor: pathname === '/' ? 'default' : 'pointer',
                                '&:hover': {
                                    color: pathname === '/' ? theme.palette.primary.main : theme.palette.primary.dark,
                                }
                            }}
                        >
                            <CloudQueue />
                            Infra Mind
                        </Typography>

                        {/* Desktop Navigation */}
                        {!isMobile && (
                            <Box sx={{ ml: 4, display: 'flex', gap: 1 }}>
                                {navigationItems.slice(0, 6).map((item) => (
                                    <Button
                                        key={item.path}
                                        component={Link}
                                        href={item.path}
                                        startIcon={item.icon}
                                        variant={isActiveRoute(item.path) ? "contained" : "text"}
                                        size="small"
                                        sx={{
                                            minWidth: 'auto',
                                            textTransform: 'none',
                                            fontWeight: isActiveRoute(item.path) ? 600 : 400,
                                            px: 2,
                                            py: 0.5,
                                            borderRadius: 2,
                                            '& .MuiButton-startIcon': {
                                                marginLeft: 0,
                                                marginRight: 1,
                                            }
                                        }}
                                    >
                                        {item.badge ? (
                                            <Badge badgeContent={item.badge} color="secondary">
                                                <span>{item.label}</span>
                                            </Badge>
                                        ) : item.label}
                                    </Button>
                                ))}
                            </Box>
                        )}
                    </Box>

                    {/* Right side - Theme, Notifications, Profile */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {/* Theme Toggle - Always visible */}
                        <IconButton 
                            onClick={onThemeToggle} 
                            sx={{ 
                                color: 'text.primary',
                                '&:hover': {
                                    backgroundColor: 'action.hover'
                                }
                            }}
                        >
                            {isDarkMode ? <LightMode /> : <DarkMode />}
                        </IconButton>

                        {/* Sync Status Indicator - Only for authenticated users and when needed */}
                        {syncStatus && isAuthenticated && (
                            syncStatus.isSyncing || !syncStatus.isOnline || syncStatus.queueLength > 0
                        ) && (
                            <Chip
                                icon={syncStatus.isOnline ? <TrendingUp /> : <Close />}
                                label={
                                    syncStatus.isSyncing ? 'Syncing...' : 
                                    !syncStatus.isOnline ? 'Offline' :
                                    `${syncStatus.queueLength} pending`
                                }
                                size="small"
                                color={
                                    syncStatus.isSyncing ? 'primary' :
                                    !syncStatus.isOnline ? 'error' :
                                    'warning'
                                }
                                variant="outlined"
                                sx={{ display: { xs: 'none', sm: 'flex' } }}
                            />
                        )}

                        {isAuthenticated ? (
                            <>
                                {/* Enhanced Notifications */}
                                <EnhancedNotificationSystem />

                                {/* User Profile */}
                                <IconButton
                                    onClick={handleUserMenuOpen}
                                    aria-label={`User menu for ${userName}`}
                                    aria-haspopup="true"
                                    aria-expanded={Boolean(userMenuAnchor)}
                                    sx={{ p: 0.5 }}
                                >
                                    <Avatar 
                                        src={userAvatar}
                                        alt={`${userName} profile picture`}
                                        sx={{ width: 32, height: 32 }}
                                    >
                                        {userName[0]?.toUpperCase()}
                                    </Avatar>
                                </IconButton>
                            </>
                        ) : (
                            <>
                                {/* About Button */}
                                <Button
                                    component={Link}
                                    href="/about"
                                    variant="text"
                                    sx={{ 
                                        textTransform: 'none',
                                        color: 'text.primary',
                                        '&:hover': {
                                            backgroundColor: 'action.hover'
                                        }
                                    }}
                                >
                                    About
                                </Button>
                                
                                {/* Sign In Button */}
                                <Button
                                    component={Link}
                                    href="/auth/login"
                                    variant="contained"
                                    sx={{ 
                                        textTransform: 'none',
                                        borderRadius: 2,
                                        px: 3
                                    }}
                                >
                                    Sign In
                                </Button>
                            </>
                        )}
                    </Box>
                </Toolbar>
            </AppBar>

            {/* Mobile Drawer */}
            <Drawer
                variant="temporary"
                anchor="left"
                open={mobileDrawerOpen}
                onClose={handleMobileDrawerToggle}
                ModalProps={{
                    keepMounted: true, // Better open performance on mobile
                }}
                sx={{
                    '& .MuiDrawer-paper': {
                        boxSizing: 'border-box',
                        width: 280,
                    },
                }}
            >
                {mobileDrawer}
            </Drawer>

            {/* User Menu - Only show for authenticated users */}
            {isAuthenticated && (
                <Menu
                anchorEl={userMenuAnchor}
                open={Boolean(userMenuAnchor)}
                onClose={handleUserMenuClose}
                role="menu"
                aria-label="User account menu"
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                PaperProps={{
                    sx: { minWidth: 200 }
                }}
            >
                <MenuItem 
                    onClick={() => {
                        handleUserMenuClose();
                        router.push('/profile');
                    }}
                    role="menuitem"
                    aria-label="Go to user profile"
                >
                    <ListItemIcon>
                        <AccountCircle />
                    </ListItemIcon>
                    <ListItemText primary="Profile" />
                </MenuItem>
                <MenuItem 
                    onClick={() => {
                        handleUserMenuClose();
                        router.push('/settings');
                    }}
                    role="menuitem"
                    aria-label="Go to settings"
                >
                    <ListItemIcon>
                        <Settings />
                    </ListItemIcon>
                    <ListItemText primary="Settings" />
                </MenuItem>
                <Divider />
                <MenuItem 
                    onClick={() => {
                        handleUserMenuClose();
                        // Add sign out logic here
                        router.push('/auth/login');
                    }}
                    role="menuitem"
                    aria-label="Sign out of account"
                >
                    <ListItemText primary="Sign Out" />
                </MenuItem>
            </Menu>
            )}

            {/* Notification Menu */}
            <Menu
                anchorEl={notificationMenuAnchor}
                open={Boolean(notificationMenuAnchor)}
                onClose={handleNotificationMenuClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                PaperProps={{
                    sx: { minWidth: 300, maxWidth: 400 }
                }}
            >
                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="h6" fontWeight={600}>
                        Notifications
                    </Typography>
                </Box>
                <MenuItem>
                    <ListItemText 
                        primary="Assessment Complete"
                        secondary="Novatech assessment finished processing"
                    />
                </MenuItem>
                <MenuItem>
                    <ListItemText 
                        primary="New Recommendations"
                        secondary="3 new optimization recommendations available"
                    />
                </MenuItem>
                <MenuItem>
                    <ListItemText 
                        primary="System Update"
                        secondary="AI models have been updated with latest features"
                    />
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleNotificationMenuClose}>
                    <ListItemText 
                        primary="View All Notifications" 
                        sx={{ textAlign: 'center' }}
                    />
                </MenuItem>
            </Menu>
        </>
    );
}