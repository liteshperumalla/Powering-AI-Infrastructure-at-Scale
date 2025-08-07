'use client';

import React from 'react';
import {
    Box,
    CircularProgress,
    Typography,
    Skeleton,
    Card,
    CardContent,
} from '@mui/material';

interface LoadingSpinnerProps {
    size?: number;
    message?: string;
    variant?: 'spinner' | 'skeleton' | 'card';
    fullPage?: boolean;
}

export default function LoadingSpinner({ 
    size = 40, 
    message = 'Loading...', 
    variant = 'spinner',
    fullPage = false 
}: LoadingSpinnerProps) {
    if (variant === 'skeleton') {
        return (
            <Box sx={{ p: 2 }}>
                <Skeleton variant="text" width="60%" height={32} />
                <Skeleton variant="text" width="40%" height={24} sx={{ mt: 1 }} />
                <Skeleton variant="rectangular" width="100%" height={200} sx={{ mt: 2 }} />
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Skeleton variant="rectangular" width={80} height={36} />
                    <Skeleton variant="rectangular" width={80} height={36} />
                </Box>
            </Box>
        );
    }

    if (variant === 'card') {
        return (
            <Card>
                <CardContent>
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            py: 4,
                        }}
                    >
                        <CircularProgress size={size} sx={{ mb: 2 }} />
                        <Typography variant="body1" color="text.secondary">
                            {message}
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    const content = (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
            }}
        >
            <CircularProgress size={size} />
            {message && (
                <Typography variant="body1" color="text.secondary">
                    {message}
                </Typography>
            )}
        </Box>
    );

    if (fullPage) {
        return (
            <Box
                sx={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                    zIndex: 9999,
                }}
            >
                {content}
            </Box>
        );
    }

    return content;
}

// Specific loading components for different scenarios
export function PageLoader({ message = 'Loading page...' }: { message?: string }) {
    return <LoadingSpinner fullPage message={message} size={60} />;
}

export function ComponentLoader({ message = 'Loading...' }: { message?: string }) {
    return <LoadingSpinner variant="card" message={message} />;
}

export function SkeletonLoader() {
    return <LoadingSpinner variant="skeleton" />;
}

// Loading states for specific components
export function DashboardSkeleton() {
    return (
        <Box sx={{ p: 3 }}>
            {/* Header skeleton */}
            <Skeleton variant="text" width="40%" height={40} sx={{ mb: 3 }} />
            
            {/* Cards skeleton */}
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3, mb: 4 }}>
                {[1, 2, 3].map((item) => (
                    <Card key={item}>
                        <CardContent>
                            <Skeleton variant="text" width="60%" height={24} />
                            <Skeleton variant="text" width="40%" height={20} sx={{ mt: 1 }} />
                            <Skeleton variant="rectangular" width="100%" height={120} sx={{ mt: 2 }} />
                        </CardContent>
                    </Card>
                ))}
            </Box>
            
            {/* Chart skeleton */}
            <Card>
                <CardContent>
                    <Skeleton variant="text" width="30%" height={32} sx={{ mb: 2 }} />
                    <Skeleton variant="rectangular" width="100%" height={300} />
                </CardContent>
            </Card>
        </Box>
    );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <Box sx={{ p: 2 }}>
            <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
            {Array.from({ length: rows }).map((_, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 2, mb: 1 }}>
                    <Skeleton variant="rectangular" width="20%" height={32} />
                    <Skeleton variant="rectangular" width="30%" height={32} />
                    <Skeleton variant="rectangular" width="25%" height={32} />
                    <Skeleton variant="rectangular" width="25%" height={32} />
                </Box>
            ))}
        </Box>
    );
}