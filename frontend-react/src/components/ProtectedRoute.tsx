import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { getCurrentUser, setToken } from '@/store/slices/authSlice';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requireAuth?: boolean;
    redirectTo?: string;
    allowedRoles?: string[];
}

export default function ProtectedRoute({
    children,
    requireAuth = true,
    redirectTo = '/auth/login',
    allowedRoles = [],
}: ProtectedRouteProps) {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const { isAuthenticated, user, loading } = useAppSelector(state => state.auth);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        console.log('ProtectedRoute: initializeAuth effect', { isAuthenticated, user: !!user });
        const initializeAuth = async () => {
            // Check for stored token
            const storedToken = localStorage.getItem('auth_token');
            console.log('ProtectedRoute: storedToken exists:', !!storedToken);

            if (storedToken && !isAuthenticated) {
                // Set token and fetch user data
                dispatch(setToken(storedToken));
                try {
                    console.log('ProtectedRoute: calling getCurrentUser');
                    await dispatch(getCurrentUser()).unwrap();
                    console.log('ProtectedRoute: getCurrentUser success');
                } catch (error) {
                    console.error('ProtectedRoute: getCurrentUser failed:', error);
                    // Token is invalid, remove it
                    localStorage.removeItem('auth_token');
                    dispatch(setToken(null));
                }
            }

            setIsInitialized(true);
        };

        initializeAuth();
    }, [dispatch, isAuthenticated]);

    useEffect(() => {
        console.log('ProtectedRoute: redirect effect', {
            isInitialized,
            requireAuth,
            isAuthenticated,
            loading,
            shouldRedirect: isInitialized && requireAuth && !isAuthenticated && !loading
        });
        if (isInitialized && requireAuth && !isAuthenticated && !loading) {
            console.log('ProtectedRoute: redirecting to', redirectTo);
            router.push(redirectTo);
        }
    }, [isInitialized, requireAuth, isAuthenticated, loading, router, redirectTo]);

    // Check role-based access
    useEffect(() => {
        console.log('ProtectedRoute: role check effect');
        if (isAuthenticated && user && allowedRoles.length > 0) {
            if (!allowedRoles.includes(user.role)) {
                router.push('/unauthorized');
            }
        }
    }, [isAuthenticated, user?.role, allowedRoles.join(','), router]); // Use user.role and join allowedRoles to prevent array reference issues

    // Show loading while initializing or authenticating
    if (!isInitialized || (requireAuth && loading)) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '100vh',
                    gap: 2,
                }}
            >
                <CircularProgress size={40} />
                <Typography variant="body2" color="text.secondary">
                    Loading...
                </Typography>
            </Box>
        );
    }

    // If auth is required but user is not authenticated, don't render children
    if (requireAuth && !isAuthenticated) {
        return null;
    }

    // If role check fails, don't render children
    if (isAuthenticated && user && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
        return null;
    }

    return <>{children}</>;
}

// Higher-order component for easier usage
export function withAuth<P extends object>(
    Component: React.ComponentType<P>,
    options?: Omit<ProtectedRouteProps, 'children'>
) {
    return function AuthenticatedComponent(props: P) {
        return (
            <ProtectedRoute {...options}>
                <Component {...props} />
            </ProtectedRoute>
        );
    };
}

// Hook for checking authentication status
export function useAuth() {
    console.log('useAuth hook');
    const { isAuthenticated, user, loading, error } = useAppSelector(state => state.auth);
    const dispatch = useAppDispatch();

    const logout = () => {
        localStorage.removeItem('auth_token');
        dispatch(setToken(null));
    };

    return {
        isAuthenticated,
        user,
        loading,
        error,
        logout,
    };
}
