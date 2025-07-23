'use client';

import React, { useState } from 'react';
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
    Notifications,
    Logout,
} from '@mui/icons-material';
import { useRouter, usePathname } from 'next/navigation';

const navigationItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Assessment', icon: <Assessment />, path: '/assessment' },
    { text: 'Cloud Services', icon: <CloudQueue />, path: '/cloud-services' },
    { text: 'Compliance', icon: <Security />, path: '/compliance' },
    { text: 'Reports', icon: <Analytics />, path: '/reports' },
    { text: 'Visualization Demo', icon: <Analytics />, path: '/visualization-demo' },
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

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [mobileOpen, setMobileOpen] = useState(false);

    const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleLogout = () => {
        handleMenuClose();
        // Clear any stored auth tokens here
        router.push('/');
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
                    width: { md: `calc(100% - 250px)` },
                    ml: { md: `250px` },
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
                    <IconButton color="inherit" sx={{ mr: 1 }}>
                        <Notifications />
                    </IconButton>
                    <IconButton
                        size="large"
                        edge="end"
                        aria-label="account of current user"
                        aria-haspopup="true"
                        onClick={handleProfileMenuOpen}
                        color="inherit"
                    >
                        <AccountCircle />
                    </IconButton>
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
                    }}
                >
                    {drawer}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', md: 'block' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 250 },
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>

            {/* Profile Menu */}
            <Menu
                anchorEl={anchorEl}
                anchorOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={handleMenuClose}>
                    <AccountCircle sx={{ mr: 1 }} />
                    Profile
                </MenuItem>
                <MenuItem onClick={handleMenuClose}>
                    <Settings sx={{ mr: 1 }} />
                    Settings
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                    <Logout sx={{ mr: 1 }} />
                    Logout
                </MenuItem>
            </Menu>

            {/* Main Content */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: { md: `calc(100% - 250px)` },
                }}
            >
                <Toolbar />
                {children}
            </Box>
        </Box>
    );
}