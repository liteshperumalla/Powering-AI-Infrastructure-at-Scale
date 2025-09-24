'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    CssBaseline,
    ThemeProvider,
    createTheme,
    useMediaQuery,
    Fab,
    Zoom,
    Snackbar,
    Alert,
    LinearProgress,
    Backdrop,
    CircularProgress,
} from '@mui/material';
import {
    KeyboardArrowUp,
    Wifi,
    WifiOff,
} from '@mui/icons-material';
import ModernNavbar from './ModernNavbar';
import EnhancedNotificationSystem from './EnhancedNotificationSystem';
import { useBackgroundSync } from '../services/backgroundSync';
import { useAppSelector } from '../store/hooks';

interface ResponsiveLayoutProps {
    children: React.ReactNode;
    title?: string;
    loading?: boolean;
    showProgress?: boolean;
    progressValue?: number;
    fullWidth?: boolean; // When true, no content padding is applied (for pages with their own containers)
}

export default function ResponsiveLayout({
    children,
    title,
    loading = false,
    showProgress = false,
    progressValue = 0,
    fullWidth = false
}: ResponsiveLayoutProps) {
    const [darkMode, setDarkMode] = useState(false);
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [online, setOnline] = useState(true);
    const [showOfflineAlert, setShowOfflineAlert] = useState(false);
    const [showConnectionRestored, setShowConnectionRestored] = useState(false);
    const [isHydrated, setIsHydrated] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [navbarReady, setNavbarReady] = useState(false);

    const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
    const { isOnline, isSyncing, queueLength } = useBackgroundSync();
    const { isAuthenticated, user } = useAppSelector(state => state.auth);

    // Initialize dark mode from user preference or system preference
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            setDarkMode(savedTheme === 'dark');
        } else {
            setDarkMode(prefersDarkMode);
        }
    }, [prefersDarkMode]);

    // Handle scroll to top button visibility
    useEffect(() => {
        if (typeof window === 'undefined') return;
        
        const handleScroll = () => {
            setShowScrollTop(window.pageYOffset > 300);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Handle mounting state
    useEffect(() => {
        setMounted(true);
        setIsHydrated(true);
        // Delay navbar loading slightly to improve perceived performance
        const timer = setTimeout(() => setNavbarReady(true), 50);
        return () => clearTimeout(timer);
    }, []);

    // Handle online/offline status
    useEffect(() => {
        if (!mounted) return;
        
        const handleOnline = () => {
            setOnline(true);
            setShowOfflineAlert(false);
            // Only show connection restored if we were previously offline
            if (!online) {
                setShowConnectionRestored(true);
                setTimeout(() => setShowConnectionRestored(false), 4000); // Hide after 4 seconds
            }
        };

        const handleOffline = () => {
            setOnline(false);
            setShowOfflineAlert(true);
            setShowConnectionRestored(false);
        };

        if (typeof window !== 'undefined') {
            window.addEventListener('online', handleOnline);
            window.addEventListener('offline', handleOffline);

            // Check initial status
            setOnline(navigator.onLine);
        }

        return () => {
            if (typeof window !== 'undefined') {
                window.removeEventListener('online', handleOnline);
                window.removeEventListener('offline', handleOffline);
            }
        };
    }, [mounted]);

    // Update document title
    useEffect(() => {
        if (title) {
            document.title = `${title} - Infra Mind`;
        } else {
            document.title = 'Infra Mind - AI Infrastructure Advisory Platform';
        }
    }, [title]);

    const theme = createTheme({
        palette: {
            mode: darkMode ? 'dark' : 'light',
            primary: {
                main: '#3b82f6',
                dark: '#1d4ed8',
                light: '#60a5fa',
            },
            secondary: {
                main: '#8b5cf6',
                dark: '#7c3aed',
                light: '#a78bfa',
            },
            background: {
                default: darkMode ? '#0f172a' : '#f8fafc',
                paper: darkMode ? '#1e293b' : '#ffffff',
            },
            success: {
                main: '#10b981',
            },
            warning: {
                main: '#f59e0b',
            },
            error: {
                main: '#ef4444',
            },
        },
        typography: {
            fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
            h1: {
                fontWeight: 700,
                fontSize: '2.5rem',
                lineHeight: 1.2,
            },
            h2: {
                fontWeight: 600,
                fontSize: '2rem',
                lineHeight: 1.3,
            },
            h3: {
                fontWeight: 600,
                fontSize: '1.5rem',
                lineHeight: 1.4,
            },
            h4: {
                fontWeight: 600,
                fontSize: '1.25rem',
                lineHeight: 1.4,
            },
            h5: {
                fontWeight: 600,
                fontSize: '1.125rem',
                lineHeight: 1.4,
            },
            h6: {
                fontWeight: 600,
                fontSize: '1rem',
                lineHeight: 1.4,
            },
            body1: {
                fontSize: '1rem',
                lineHeight: 1.6,
            },
            body2: {
                fontSize: '0.875rem',
                lineHeight: 1.6,
            },
        },
        shape: {
            borderRadius: 8,
        },
        components: {
            MuiButton: {
                styleOverrides: {
                    root: {
                        textTransform: 'none',
                        borderRadius: 8,
                        fontWeight: 500,
                        padding: '8px 16px',
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&:hover': {
                            transform: 'translateY(-1px)',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                        },
                    },
                },
            },
            MuiCard: {
                styleOverrides: {
                    root: {
                        borderRadius: 12,
                        boxShadow: darkMode 
                            ? '0 1px 3px rgba(0, 0, 0, 0.3)' 
                            : '0 1px 3px rgba(0, 0, 0, 0.1)',
                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: darkMode 
                                ? '0 4px 20px rgba(0, 0, 0, 0.4)' 
                                : '0 4px 20px rgba(0, 0, 0, 0.1)',
                        },
                    },
                },
            },
            MuiChip: {
                styleOverrides: {
                    root: {
                        borderRadius: 16,
                        fontWeight: 500,
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none',
                    },
                },
            },
        },
    });

    const handleThemeToggle = () => {
        const newDarkMode = !darkMode;
        setDarkMode(newDarkMode);
        localStorage.setItem('theme', newDarkMode ? 'dark' : 'light');
    };

    const scrollToTop = () => {
        if (typeof window !== 'undefined') {
            window.scrollTo({
                top: 0,
                behavior: 'smooth',
            });
        }
    };

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box 
                sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    minHeight: '100vh',
                    backgroundColor: 'background.default',
                }}
            >
                {/* Modern Navigation */}
                {navbarReady ? (
                    <ModernNavbar
                        onThemeToggle={handleThemeToggle}
                        isDarkMode={darkMode}
                        userName={user?.full_name || user?.first_name || "User"}
                        isAuthenticated={isAuthenticated}
                        syncStatus={{ isOnline, isSyncing, queueLength }}
                    />
                ) : (
                    <Box sx={{ height: 64, backgroundColor: 'background.paper', borderBottom: 1, borderColor: 'divider' }} />
                )}

                {/* Progress Bar */}
                {showProgress && (
                    <LinearProgress 
                        variant={progressValue > 0 ? "determinate" : "indeterminate"}
                        value={progressValue}
                        sx={{ 
                            height: 3,
                            backgroundColor: 'transparent',
                        }}
                    />
                )}

                {/* Main Content */}
                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        minHeight: 'calc(100vh - 64px)',
                        position: 'relative',
                    }}
                >
                    {/* Loading Backdrop */}
                    <Backdrop
                        sx={{ 
                            color: '#fff', 
                            zIndex: (theme) => theme.zIndex.drawer + 1,
                            backgroundColor: 'rgba(0, 0, 0, 0.4)',
                            backdropFilter: 'blur(4px)',
                        }}
                        open={loading}
                    >
                        <Box sx={{ textAlign: 'center' }}>
                            <CircularProgress color="inherit" size={60} />
                            <Box sx={{ mt: 2, color: 'white' }}>
                                Loading...
                            </Box>
                        </Box>
                    </Backdrop>

                    {/* Page Content */}
                    <Box
                        sx={{
                            flexGrow: 1,
                            ...(fullWidth ? {
                                // Full width pages - no padding, let pages manage their own layout
                                width: '100%',
                            } : {
                                // Content pages - add responsive padding and centering
                                px: { xs: 2, sm: 3, md: 4, lg: 5 }, // Responsive horizontal padding
                                py: { xs: 2, sm: 3 }, // Responsive vertical padding
                                maxWidth: '1400px', // Maximum content width
                                mx: 'auto', // Center content horizontally
                                width: '100%',
                            })
                        }}
                    >
                        {children}
                    </Box>
                </Box>

                {/* Scroll to Top Button */}
                <Zoom in={showScrollTop}>
                    <Fab
                        color="primary"
                        size="small"
                        onClick={scrollToTop}
                        sx={{
                            position: 'fixed',
                            bottom: 24,
                            right: 24,
                            zIndex: 1000,
                            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
                        }}
                    >
                        <KeyboardArrowUp />
                    </Fab>
                </Zoom>

                {/* Only render Snackbars after hydration to prevent SSR mismatches */}
                {mounted && isHydrated && (
                    <>
                        {/* Offline Alert */}
                        <Snackbar
                            open={showOfflineAlert}
                            autoHideDuration={6000}
                            onClose={() => setShowOfflineAlert(false)}
                            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                        >
                            <Alert
                                onClose={() => setShowOfflineAlert(false)}
                                severity="warning"
                                icon={<WifiOff />}
                                sx={{ width: '100%' }}
                            >
                                You are currently offline. Some features may not be available.
                            </Alert>
                        </Snackbar>

                        {/* Connection Restored Alert */}
                        <Snackbar
                            open={showConnectionRestored}
                            autoHideDuration={4000}
                            onClose={() => setShowConnectionRestored(false)}
                            anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                        >
                            <Alert
                                onClose={() => setShowConnectionRestored(false)}
                                severity="success"
                                icon={<Wifi />}
                                sx={{ width: '100%' }}
                            >
                                Connection restored!
                            </Alert>
                        </Snackbar>
                    </>
                )}
            </Box>
        </ThemeProvider>
    );
}