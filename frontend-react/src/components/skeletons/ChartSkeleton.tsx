import React from 'react';
import { Card, CardContent, Box, Skeleton } from '@mui/material';

interface ChartSkeletonProps {
    height?: number;
    title?: boolean;
}

/**
 * Skeleton loader for chart components
 * Provides visual feedback while charts are loading
 */
export default function ChartSkeleton({ height = 300, title = true }: ChartSkeletonProps) {
    return (
        <Card>
            <CardContent>
                {title && (
                    <Box sx={{ mb: 2 }}>
                        <Skeleton variant="text" width="40%" height={32} sx={{ mb: 0.5 }} />
                        <Skeleton variant="text" width="60%" height={20} />
                    </Box>
                )}
                <Skeleton
                    variant="rectangular"
                    width="100%"
                    height={height}
                    sx={{ borderRadius: 1 }}
                />
                <Box sx={{ display: 'flex', justifyContent: 'space-around', mt: 2 }}>
                    <Skeleton variant="text" width={80} height={20} />
                    <Skeleton variant="text" width={80} height={20} />
                    <Skeleton variant="text" width={80} height={20} />
                </Box>
            </CardContent>
        </Card>
    );
}
