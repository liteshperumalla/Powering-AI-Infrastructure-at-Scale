import React from 'react';
import { Card, CardContent, Box, Skeleton } from '@mui/material';

interface AssessmentCardSkeletonProps {
    count?: number;
}

/**
 * Skeleton loader for assessment cards
 * Provides visual feedback during data loading
 */
export default function AssessmentCardSkeleton({ count = 3 }: AssessmentCardSkeletonProps) {
    return (
        <>
            {Array.from({ length: count }).map((_, index) => (
                <Card key={index} sx={{ height: '100%' }}>
                    <CardContent sx={{ p: 2.5 }}>
                        {/* Header with checkbox and status */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flex: 1 }}>
                                <Skeleton variant="rectangular" width={20} height={20} />
                                <Box sx={{ flex: 1 }}>
                                    <Skeleton variant="text" width="70%" height={32} sx={{ mb: 0.5 }} />
                                    <Skeleton variant="text" width="90%" height={20} />
                                </Box>
                            </Box>
                            <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 12 }} />
                        </Box>

                        {/* Progress bar */}
                        <Box sx={{ mb: 2, mt: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Skeleton variant="text" width={100} height={16} />
                                <Skeleton variant="text" width={80} height={16} />
                            </Box>
                            <Skeleton variant="rectangular" width="100%" height={6} sx={{ borderRadius: 1 }} />
                        </Box>

                        {/* Chips and date */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Skeleton variant="rectangular" width={120} height={24} sx={{ borderRadius: 12 }} />
                                <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 12 }} />
                            </Box>
                            <Skeleton variant="text" width={100} height={16} />
                        </Box>

                        {/* Action buttons */}
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                            <Skeleton variant="rectangular" width={100} height={36} sx={{ borderRadius: 1 }} />
                            <Skeleton variant="rectangular" width={100} height={36} sx={{ borderRadius: 1 }} />
                        </Box>
                    </CardContent>
                </Card>
            ))}
        </>
    );
}
