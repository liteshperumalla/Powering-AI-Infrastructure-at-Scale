'use client';

import React from 'react';
import { useAppSelector } from '@/store/hooks';
import { Alert, Box, Button } from '@mui/material';
import { Home as HomeIcon } from '@mui/icons-material';
import { useRouter } from 'next/navigation';

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: string[];
  fallbackMessage?: string;
  redirectTo?: string;
}

const RoleProtectedRoute: React.FC<RoleProtectedRouteProps> = ({
  children,
  allowedRoles,
  fallbackMessage = "You don't have permission to access this feature.",
  redirectTo = '/dashboard'
}) => {
  const router = useRouter();
  const { user, isAuthenticated } = useAppSelector(state => state.auth);

  // If not authenticated, show authentication required message
  if (!isAuthenticated) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          Authentication required to access this feature.
        </Alert>
        <Button
          variant="contained"
          startIcon={<HomeIcon />}
          onClick={() => router.push('/auth/login')}
        >
          Go to Login
        </Button>
      </Box>
    );
  }

  // If user doesn't exist or doesn't have required role
  const userRole = user?.role || 'user';
  const hasPermission = allowedRoles.includes(userRole) || allowedRoles.includes('*');

  if (!hasPermission) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {fallbackMessage}
          <br />
          <strong>Your role:</strong> {userRole}
          <br />
          <strong>Required roles:</strong> {allowedRoles.join(', ')}
        </Alert>
        <Button
          variant="contained"
          startIcon={<HomeIcon />}
          onClick={() => router.push(redirectTo)}
        >
          Go to Dashboard
        </Button>
      </Box>
    );
  }

  // User has permission, render children
  return <>{children}</>;
};

export default RoleProtectedRoute;