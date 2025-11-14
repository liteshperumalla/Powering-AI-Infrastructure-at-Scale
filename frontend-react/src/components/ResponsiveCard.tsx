'use client';

import React from 'react';
import {
    Card,
    CardContent,
    CardActions,
    Box,
    Typography,
    Chip,
    IconButton,
    LinearProgress,
    Skeleton,
    useTheme,
    useMediaQuery,
    Avatar,
    Divider,
    Collapse,
    Tooltip,
} from '@mui/material';
import {
    MoreVert,
    TrendingUp,
    TrendingDown,
    Schedule,
    CheckCircle,
    Error,
    Warning,
    ExpandMore,
    ExpandLess,
} from '@mui/icons-material';

interface ResponsiveCardProps {
    title: string;
    subtitle?: string;
    description?: string;
    status?: 'success' | 'warning' | 'error' | 'pending' | 'in_progress' | 'completed';
    progress?: number;
    loading?: boolean;
    actions?: React.ReactNode;
    children?: React.ReactNode;
    onClick?: () => void;
    expandable?: boolean;
    avatar?: string | React.ReactNode;
    tags?: string[];
    metrics?: Array<{
        label: string;
        value: string | number;
        trend?: 'up' | 'down' | 'neutral';
        color?: string;
    }>;
    compact?: boolean;
    elevation?: number;
    className?: string;
}

const getStatusConfig = (status: string) => {
    const configs = {
        success: { color: 'success', icon: CheckCircle, label: 'Completed' },
        warning: { color: 'warning', icon: Warning, label: 'Warning' },
        error: { color: 'error', icon: Error, label: 'Error' },
        pending: { color: 'default', icon: Schedule, label: 'Pending' },
        in_progress: { color: 'primary', icon: Schedule, label: 'In Progress' },
        completed: { color: 'success', icon: CheckCircle, label: 'Completed' },
    };
    return configs[status as keyof typeof configs] || configs.pending;
};

export default function ResponsiveCard({
    title,
    subtitle,
    description,
    status,
    progress,
    loading = false,
    actions,
    children,
    onClick,
    expandable = false,
    avatar,
    tags = [],
    metrics = [],
    compact = false,
    elevation = 1,
    className,
}: ResponsiveCardProps) {
    const [expanded, setExpanded] = React.useState(false);
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const isTablet = useMediaQuery(theme.breakpoints.down('md'));

    const statusConfig = status ? getStatusConfig(status) : null;
    const StatusIcon = statusConfig?.icon;

    const handleExpandClick = () => {
        setExpanded(!expanded);
    };

    if (loading) {
        return (
            <Card 
                elevation={elevation}
                className={className}
                sx={{
                    height: compact ? 'auto' : { xs: 'auto', sm: 280, md: 320 },
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <CardContent sx={{ flex: 1, p: { xs: 2, sm: 3 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
                        <Box sx={{ flex: 1 }}>
                            <Skeleton variant="text" width="60%" height={28} />
                            <Skeleton variant="text" width="40%" height={20} />
                        </Box>
                    </Box>
                    <Skeleton variant="text" width="100%" />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="text" width="60%" />
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                        <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 12 }} />
                        <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 12 }} />
                    </Box>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card
            elevation={elevation}
            className={className}
            sx={{
                cursor: onClick ? 'pointer' : 'default',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                height: compact ? 'auto' : { xs: 'auto', sm: 'fit-content' },
                display: 'flex',
                flexDirection: 'column',
                '&:hover': onClick ? {
                    transform: 'translateY(-2px)',
                    boxShadow: theme.shadows[4],
                } : {},
                ...(isMobile && {
                    borderRadius: 2,
                    margin: 1,
                }),
            }}
            onClick={onClick}
        >
            <CardContent sx={{ 
                flex: 1, 
                p: { xs: 2, sm: 3 },
                pb: actions || expandable ? 1 : undefined,
            }}>
                {/* Header */}
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'flex-start', 
                    justifyContent: 'space-between',
                    mb: 2,
                    gap: 2,
                }}>
                    <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center',
                        flex: 1,
                        minWidth: 0, // Allow text truncation
                    }}>
                        {avatar && (
                            <Box sx={{ mr: 2, flexShrink: 0 }}>
                                {typeof avatar === 'string' ? (
                                    <Avatar src={avatar} alt="User avatar" sx={{ width: 40, height: 40 }} />
                                ) : (
                                    avatar
                                )}
                            </Box>
                        )}
                        
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                            <Typography 
                                variant={isMobile ? "h6" : "h5"} 
                                component="h2"
                                sx={{ 
                                    fontWeight: 600,
                                    mb: subtitle ? 0.5 : 0,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    display: '-webkit-box',
                                    WebkitLineClamp: isMobile ? 2 : 1,
                                    WebkitBoxOrient: 'vertical',
                                }}
                            >
                                {title}
                            </Typography>
                            
                            {subtitle && (
                                <Typography 
                                    variant="body2" 
                                    color="text.secondary"
                                    sx={{
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: isMobile ? 'normal' : 'nowrap',
                                    }}
                                >
                                    {subtitle}
                                </Typography>
                            )}
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                        {status && statusConfig && (
                            <Tooltip title={statusConfig.label}>
                                <Chip
                                    icon={<StatusIcon />}
                                    label={isMobile ? '' : statusConfig.label}
                                    color={statusConfig.color as any}
                                    size={isMobile ? "small" : "medium"}
                                    sx={{ 
                                        minWidth: isMobile ? 32 : 'auto',
                                        '& .MuiChip-label': {
                                            display: isMobile ? 'none' : 'block',
                                        }
                                    }}
                                />
                            </Tooltip>
                        )}
                        
                        <IconButton size="small" sx={{ opacity: 0.7 }}>
                            <MoreVert />
                        </IconButton>
                    </Box>
                </Box>

                {/* Progress */}
                {typeof progress === 'number' && (
                    <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                                Progress
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                {Math.round(progress)}%
                            </Typography>
                        </Box>
                        <LinearProgress 
                            variant="determinate" 
                            value={progress}
                            sx={{ 
                                height: 8,
                                borderRadius: 4,
                                backgroundColor: theme.palette.grey[200],
                            }}
                        />
                    </Box>
                )}

                {/* Description */}
                {description && (
                    <Typography 
                        variant="body2" 
                        color="text.secondary"
                        sx={{ 
                            mb: 2,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: isMobile ? 3 : 2,
                            WebkitBoxOrient: 'vertical',
                            lineHeight: 1.5,
                        }}
                    >
                        {description}
                    </Typography>
                )}

                {/* Metrics */}
                {metrics.length > 0 && (
                    <Box sx={{ 
                        display: 'grid',
                        gridTemplateColumns: {
                            xs: 'repeat(2, 1fr)',
                            sm: `repeat(${Math.min(metrics.length, 3)}, 1fr)`,
                        },
                        gap: 2,
                        mb: 2,
                    }}>
                        {metrics.slice(0, isMobile ? 4 : 6).map((metric, index) => (
                            <Box key={index} sx={{ textAlign: 'center' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                                    <Typography variant="h6" color="text.primary" component="div" sx={{ fontWeight: 600 }}>
                                        {metric.value}
                                    </Typography>
                                    {metric.trend && (
                                        <Box sx={{ color: metric.trend === 'up' ? 'success.main' : 'error.main' }}>
                                            {metric.trend === 'up' ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                                        </Box>
                                    )}
                                </Box>
                                <Typography variant="caption" color="text.secondary">
                                    {metric.label}
                                </Typography>
                            </Box>
                        ))}
                    </Box>
                )}

                {/* Tags */}
                {tags.length > 0 && (
                    <Box sx={{ 
                        display: 'flex', 
                        flexWrap: 'wrap', 
                        gap: 1,
                        mb: expandable || children ? 2 : 0,
                    }}>
                        {tags.slice(0, isMobile ? 3 : 5).map((tag, index) => (
                            <Chip
                                key={index}
                                label={tag}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.75rem' }}
                            />
                        ))}
                        {tags.length > (isMobile ? 3 : 5) && (
                            <Chip
                                label={`+${tags.length - (isMobile ? 3 : 5)}`}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.75rem' }}
                            />
                        )}
                    </Box>
                )}

                {/* Expandable Content */}
                {expandable && (
                    <Collapse in={expanded} timeout="auto" unmountOnExit>
                        <Divider sx={{ mb: 2 }} />
                        {children}
                    </Collapse>
                )}

                {/* Static Children */}
                {!expandable && children && (
                    <>
                        <Divider sx={{ mb: 2 }} />
                        {children}
                    </>
                )}
            </CardContent>

            {/* Actions */}
            {(actions || expandable) && (
                <CardActions sx={{ 
                    px: { xs: 2, sm: 3 }, 
                    pb: { xs: 2, sm: 3 },
                    pt: 0,
                    justifyContent: 'space-between',
                }}>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        {actions}
                    </Box>
                    
                    {expandable && (
                        <IconButton
                            onClick={handleExpandClick}
                            aria-expanded={expanded}
                            aria-label="show more"
                            size={isMobile ? "small" : "medium"}
                        >
                            {expanded ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                    )}
                </CardActions>
            )}
        </Card>
    );
}