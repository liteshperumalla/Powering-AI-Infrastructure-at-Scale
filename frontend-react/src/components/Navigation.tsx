'use client';

import React, { useState, useEffect } from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    IconButton,
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Menu,
    MenuItem,
    Box,
    useTheme,
    useMediaQuery,
    Avatar,
    Chip,
} from '@mui/material';
import {
    Dashboard,
    Assessment,
    CloudQueue,
    Security,
    Analytics,
    Settings,
    AccountCircle,
    Menu as MenuIcon,
    Logout,
    Person,
    Chat as ChatIcon,
    MonitorHeart,
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { logout } from '@/store/slices/authSlice';
import UserProfile from './UserProfile';
import NotificationSystem from './NotificationSystem';

const navigationItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Assessment', icon: <Assessment />, path: '/assessment' },
    { text: 'AI Assistant', icon: <ChatIcon />, path: '/chat' },
    { text: 'Cloud Services', icon: <CloudQueue />, path: '/cloud-services' },
    { text: 'Compliance', icon: <Security />, path: '/compliance' },
    { text: 'Reports', icon: <Analytics />, path: '/reports' },
    { text: 'System Status', icon: <MonitorHeart />, path: '/system-status' },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
];

interface NavigationProps {
    title?: string;
    children?: React.ReactNode;
}

export default function Navigation({ title = 'Dashboard', children }: NavigationProps) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const router = useRouter();
    const pathname = usePathname();
    const dispatch = useAppDispatch();
    const { user, isAuthenticated } = useAppSelector(state => state.auth);

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [profileOpen, setProfileOpen] = useState(false);

    const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleLogout = async () => {
        handleMenuClose();
        try {
            await dispatch(logout()).unwrap();
            router.push('/auth/login');
        } catch (error) {
            console.error('Logout failed:', error);
            // Force logout even if API call fails
            localStorage.removeItem('auth_token');
            router.push('/auth/login');
        }
    };

    const handleProfileClick = () => {
        handleMenuClose();
        setProfileOpen(true);
    };


    const drawer = (
        <Box sx={{ width: 250 }}>
            <Toolbar>
                <Typography variant="h6" noWrap component="div" color="primary" fontWeight="bold">
                    Infra Mind
                </Typography>
            </Toolbar>
            <List>
                {navigationItems.map((item) => (
                    <ListItem
                        key={item.text}
                        component="button"
                        onClick={() => {
                            router.push(item.path);
                            if (isMobile) {
                                setMobileOpen(false);
                            }
                        }}
                        sx={{
                            width: '100%',
                            textAlign: 'left',
                            border: 'none',
                            background: pathname === item.path ? 'action.selected' : 'none',
                            cursor: 'pointer',
                            '&:hover': {
                                backgroundColor: 'action.hover',
                            },
                            borderRadius: 1,
                            mx: 1,
                            mb: 0.5,
                        }}
                    >
                        <ListItemIcon sx={{ color: pathname === item.path ? 'primary.main' : 'inherit' }}>
                            {item.icon}
                        </ListItemIcon>
                        <ListItemText
                            primary={item.text}
                            sx={{
                                color: pathname === item.path ? 'primary.main' : 'inherit',
                                fontWeight: pathname === item.path ? 'bold' : 'normal'
                            }}
                        />
                    </ListItem>
                ))}
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex' }}>
            {/* Navigation */}
            <AppBar
                position="fixed"
                sx={{
                    width: { sm: '100%', md: `calc(100% - 250px)` },
                    ml: { md: `250px` },
                    zIndex: (theme) => theme.zIndex.drawer + 1,
                    transition: (theme) => theme.transitions.create(['margin', 'width'], {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2, display: { md: 'none' } }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                        {title}
                    </Typography>

                    {isAuthenticated && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 1 }}>
                            {/* Notification System Bell - positioned in toolbar */}
                            <Box sx={{ mr: 1 }}>
                                <NotificationSystem />
                            </Box>
                            
                            {user && (
                                <>
                                    <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                                        <Typography variant="body2">{user.full_name}</Typography>
                                        <Chip
                                            label={user.role}
                                            size="small"
                                            color="secondary"
                                            sx={{ height: 16, fontSize: '0.7rem' }}
                                        />
                                    </Box>
                                    <Avatar
                                        sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}
                                        onClick={handleProfileMenuOpen}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <Person fontSize="small" />
                                    </Avatar>
                                </>
                            )}
                        </Box>
                    )}
                </Toolbar>
            </AppBar>

            {/* Sidebar */}
            <Box
                component="nav"
                sx={{ width: { md: 250 }, flexShrink: { md: 0 } }}
            >
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true,
                    }}
                    sx={{
                        display: { xs: 'block', md: 'none' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 250 },
                        zIndex: (theme) => theme.zIndex.drawer,
                    }}
                >
                    {drawer}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', md: 'block' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 250 },
                        zIndex: (theme) => theme.zIndex.drawer,
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>

            {/* Profile Menu */}
            {/* Profile Menu */}
            {isAuthenticated && (
                <Menu
                    anchorEl={anchorEl}
                    anchorOrigin={{
                        vertical: 'bottom',
                        horizontal: 'right',
                    }}
                    keepMounted
                    transformOrigin={{
                        vertical: 'top',
                        horizontal: 'right',
                    }}
                    open={Boolean(anchorEl)}
                    onClose={handleMenuClose}
                    sx={{
                        zIndex: (theme) => theme.zIndex.modal,
                    }}
                >
                    <MenuItem onClick={handleProfileClick}>
                        <AccountCircle sx={{ mr: 1 }} />
                        Profile
                    </MenuItem>
                    <MenuItem onClick={() => {
                        handleMenuClose();
                        router.push('/settings');
                    }}>
                        <Settings sx={{ mr: 1 }} />
                        Settings
                    </MenuItem>
                    <MenuItem onClick={handleLogout}>
                        <Logout sx={{ mr: 1 }} />
                        Logout
                    </MenuItem>
                </Menu>
            )}

            {/* User Profile Dialog */}
            <UserProfile
                open={profileOpen}
                onClose={() => setProfileOpen(false)}
            />


            {/* Main Content */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: { xs: 2, sm: 3 },
                    pt: { xs: 1, sm: 3 },
                    width: { 
                        xs: '100%', 
                        sm: '100%', 
                        md: `calc(100% - 250px)` 
                    },
                    minHeight: '100vh',
                    position: 'relative',
                    overflow: 'auto',
                    transition: (theme) => theme.transitions.create(['margin', 'width'], {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                <Toolbar />
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                    {children}
                </Box>
            </Box>
        </Box>
    );
}