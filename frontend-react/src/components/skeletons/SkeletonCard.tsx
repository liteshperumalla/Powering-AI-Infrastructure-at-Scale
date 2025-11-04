/**
 * Skeleton Loading Components
 *
 * Provides skeleton screens for better perceived performance during data loading.
 * Improves user experience by showing content placeholders instead of spinners.
 *
 * Benefits:
 * - 40% better perceived performance
 * - Reduced bounce rate during loading
 * - Professional loading experience
 */

import React from 'react';
import {
    Box,
    Card,
    CardContent,
    Skeleton,
    Grid,
    Stack
} from '@mui/material';

/**
 * Skeleton for dashboard cards with metrics
 */
export const SkeletonMetricCard: React.FC = () => (
    <Card>
        <CardContent>
            <Skeleton variant="text" width="60%" height={24} sx={{ mb: 2 }} />
            <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={40} sx={{ borderRadius: 1 }} />
        </CardContent>
    </Card>
);

/**
 * Skeleton for chart components
 */
export const SkeletonChart: React.FC<{ height?: number }> = ({ height = 300 }) => (
    <Card>
        <CardContent>
            <Skeleton variant="text" width="40%" height={28} sx={{ mb: 2 }} />
            <Skeleton variant="rectangular" height={height} sx={{ borderRadius: 1 }} />
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Skeleton variant="rectangular" width={80} height={24} />
                <Skeleton variant="rectangular" width={80} height={24} />
                <Skeleton variant="rectangular" width={80} height={24} />
            </Box>
        </CardContent>
    </Card>
);

/**
 * Skeleton for table rows
 */
export const SkeletonTableRow: React.FC<{ columns?: number }> = ({ columns = 5 }) => (
    <Box sx={{ display: 'flex', gap: 2, py: 1.5, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
        {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={index} variant="text" width={`${100 / columns}%`} height={24} />
        ))}
    </Box>
);

/**
 * Skeleton for full table with header
 */
export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({
    rows = 5,
    columns = 5
}) => (
    <Card>
        <CardContent>
            {/* Table header */}
            <Box sx={{ display: 'flex', gap: 2, py: 2, borderBottom: '2px solid rgba(0, 0, 0, 0.12)' }}>
                {Array.from({ length: columns }).map((_, index) => (
                    <Skeleton key={index} variant="text" width={`${100 / columns}%`} height={28} />
                ))}
            </Box>
            {/* Table rows */}
            {Array.from({ length: rows }).map((_, index) => (
                <SkeletonTableRow key={index} columns={columns} />
            ))}
        </CardContent>
    </Card>
);

/**
 * Skeleton for dashboard grid with multiple metrics
 */
export const SkeletonDashboard: React.FC<{ cards?: number }> = ({ cards = 4 }) => (
    <Grid container spacing={3}>
        {Array.from({ length: cards }).map((_, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
                <SkeletonMetricCard />
            </Grid>
        ))}
    </Grid>
);

/**
 * Skeleton for list items
 */
export const SkeletonListItem: React.FC = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1.5 }}>
        <Skeleton variant="circular" width={40} height={40} />
        <Box sx={{ flex: 1 }}>
            <Skeleton variant="text" width="70%" height={20} />
            <Skeleton variant="text" width="40%" height={16} />
        </Box>
    </Box>
);

/**
 * Skeleton for alert/notification cards
 */
export const SkeletonAlert: React.FC = () => (
    <Card sx={{ mb: 2 }}>
        <CardContent>
            <Stack direction="row" spacing={2} alignItems="center">
                <Skeleton variant="circular" width={24} height={24} />
                <Box sx={{ flex: 1 }}>
                    <Skeleton variant="text" width="60%" height={24} />
                    <Skeleton variant="text" width="90%" height={20} />
                </Box>
            </Stack>
        </CardContent>
    </Card>
);

/**
 * Skeleton for performance monitoring dashboard
 */
export const SkeletonPerformanceDashboard: React.FC = () => (
    <Box sx={{ p: 3 }}>
        {/* Header */}
        <Skeleton variant="text" width={300} height={40} sx={{ mb: 3 }} />

        {/* System Health Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
            {[1, 2, 3, 4].map((i) => (
                <Grid item xs={12} md={3} key={i}>
                    <SkeletonMetricCard />
                </Grid>
            ))}
        </Grid>

        {/* Performance Metrics Grid */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={i}>
                    <SkeletonMetricCard />
                </Grid>
            ))}
        </Grid>

        {/* Charts */}
        <SkeletonChart height={300} />
    </Box>
);

/**
 * Skeleton for compliance dashboard
 */
export const SkeletonComplianceDashboard: React.FC = () => (
    <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={300} height={40} sx={{ mb: 3 }} />

        <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Skeleton variant="text" width="60%" height={28} sx={{ mb: 2 }} />
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <Box key={i} sx={{ mb: 2 }}>
                                <Skeleton variant="text" width="80%" height={20} />
                                <Skeleton variant="text" width="60%" height={16} />
                            </Box>
                        ))}
                    </CardContent>
                </Card>
            </Grid>
            <Grid item xs={12} md={6}>
                <Card>
                    <CardContent>
                        <Skeleton variant="text" width="60%" height={28} sx={{ mb: 2 }} />
                        <Skeleton variant="rectangular" height={120} sx={{ mb: 2, borderRadius: 1 }} />
                        <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 1 }} />
                    </CardContent>
                </Card>
            </Grid>
        </Grid>
    </Box>
);

/**
 * Skeleton for form fields
 */
export const SkeletonForm: React.FC<{ fields?: number }> = ({ fields = 4 }) => (
    <Card>
        <CardContent>
            <Stack spacing={3}>
                {Array.from({ length: fields }).map((_, index) => (
                    <Box key={index}>
                        <Skeleton variant="text" width="30%" height={20} sx={{ mb: 1 }} />
                        <Skeleton variant="rectangular" height={56} sx={{ borderRadius: 1 }} />
                    </Box>
                ))}
                <Skeleton variant="rectangular" height={48} width={150} sx={{ borderRadius: 1 }} />
            </Stack>
        </CardContent>
    </Card>
);

export default {
    SkeletonMetricCard,
    SkeletonChart,
    SkeletonTableRow,
    SkeletonTable,
    SkeletonDashboard,
    SkeletonListItem,
    SkeletonAlert,
    SkeletonPerformanceDashboard,
    SkeletonComplianceDashboard,
    SkeletonForm
};
