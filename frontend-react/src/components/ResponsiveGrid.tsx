'use client';

import React from 'react';
import {
    Grid,
    Box,
    useTheme,
    useMediaQuery,
    Container,
    Stack,
} from '@mui/material';

interface ResponsiveGridProps {
    children: React.ReactNode;
    spacing?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
    columns?: {
        xs?: number;
        sm?: number; 
        md?: number;
        lg?: number;
        xl?: number;
    };
    maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
    className?: string;
    container?: boolean;
    direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
    justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
    alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
    sx?: any;
}

export default function ResponsiveGrid({
    children,
    spacing = 3,
    columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 4 },
    maxWidth = 'xl',
    className,
    container = true,
    direction = 'row',
    justifyContent = 'flex-start',
    alignItems = 'stretch',
    sx,
}: ResponsiveGridProps) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
    const isTablet = useMediaQuery(theme.breakpoints.down('md'));

    // Handle responsive spacing
    const getSpacing = () => {
        if (typeof spacing === 'number') {
            return {
                xs: Math.max(1, spacing - 1),
                sm: spacing,
                md: spacing,
                lg: spacing,
                xl: spacing,
            };
        }
        return spacing;
    };

    const responsiveSpacing = getSpacing();

    // Calculate responsive columns for each child
    const getColumnConfig = (index: number, totalChildren: number) => {
        // For mobile: always single column unless specified
        const xsCols = columns.xs || 1;
        const smCols = columns.sm || 2;
        const mdCols = columns.md || 3;
        const lgCols = columns.lg || 4;
        const xlCols = columns.xl || 4;

        // Calculate grid sizes
        return {
            xs: 12 / xsCols,
            sm: 12 / smCols,
            md: 12 / mdCols,
            lg: 12 / lgCols,
            xl: 12 / xlCols,
        };
    };

    const content = (
        <Grid
            container
            spacing={responsiveSpacing}
            direction={direction}
            justifyContent={justifyContent}
            alignItems={alignItems}
            className={className}
            sx={{
                width: '100%',
                margin: 0,
                ...sx,
            }}
        >
            {React.Children.map(children, (child, index) => {
                if (!React.isValidElement(child)) return child;

                const columnConfig = getColumnConfig(index, React.Children.count(children));

                return (
                    <Grid
                        item
                        {...columnConfig}
                        key={child.key || index}
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            minHeight: isMobile ? 'auto' : '100%',
                        }}
                    >
                        <Box sx={{ 
                            flex: 1, 
                            display: 'flex', 
                            flexDirection: 'column',
                            height: '100%',
                        }}>
                            {child}
                        </Box>
                    </Grid>
                );
            })}
        </Grid>
    );

    if (container && maxWidth) {
        return (
            <Container 
                maxWidth={maxWidth}
                sx={{ 
                    px: { xs: 2, sm: 3, md: 4 },
                    py: { xs: 2, sm: 3 },
                }}
            >
                {content}
            </Container>
        );
    }

    if (container) {
        return (
            <Box sx={{ 
                px: { xs: 2, sm: 3, md: 4 },
                py: { xs: 2, sm: 3 },
            }}>
                {content}
            </Box>
        );
    }

    return content;
}

// Stack version for vertical layouts
interface ResponsiveStackProps {
    children: React.ReactNode;
    spacing?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
    direction?: 'column' | 'row' | 'column-reverse' | 'row-reverse';
    alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
    justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
    divider?: React.ReactElement;
    maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
    container?: boolean;
    sx?: any;
    className?: string;
}

export function ResponsiveStack({
    children,
    spacing = 2,
    direction = 'column',
    alignItems = 'stretch',
    justifyContent = 'flex-start',
    divider,
    maxWidth = 'xl',
    container = true,
    sx,
    className,
}: ResponsiveStackProps) {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    // Handle responsive spacing
    const getSpacing = () => {
        if (typeof spacing === 'number') {
            return {
                xs: Math.max(1, spacing - 1),
                sm: spacing,
                md: spacing,
                lg: spacing,
                xl: spacing,
            };
        }
        return spacing;
    };

    const responsiveSpacing = getSpacing();

    const content = (
        <Stack
            direction={isMobile && direction === 'row' ? 'column' : direction}
            spacing={responsiveSpacing}
            alignItems={alignItems}
            justifyContent={justifyContent}
            divider={divider}
            className={className}
            sx={{
                width: '100%',
                ...sx,
            }}
        >
            {children}
        </Stack>
    );

    if (container && maxWidth) {
        return (
            <Container 
                maxWidth={maxWidth}
                sx={{ 
                    px: { xs: 2, sm: 3, md: 4 },
                    py: { xs: 2, sm: 3 },
                }}
            >
                {content}
            </Container>
        );
    }

    if (container) {
        return (
            <Box sx={{ 
                px: { xs: 2, sm: 3, md: 4 },
                py: { xs: 2, sm: 3 },
            }}>
                {content}
            </Box>
        );
    }

    return content;
}

// Masonry-like grid for different sized cards
interface ResponsiveMasonryProps {
    children: React.ReactNode;
    columns?: {
        xs?: number;
        sm?: number; 
        md?: number;
        lg?: number;
        xl?: number;
    };
    spacing?: number;
    maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
    container?: boolean;
    sx?: any;
}

export function ResponsiveMasonry({
    children,
    columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 5 },
    spacing = 2,
    maxWidth = 'xl',
    container = true,
    sx,
}: ResponsiveMasonryProps) {
    const theme = useTheme();
    const childrenArray = React.Children.toArray(children);

    const content = (
        <Box
            sx={{
                columnCount: {
                    xs: columns.xs,
                    sm: columns.sm,
                    md: columns.md,
                    lg: columns.lg,
                    xl: columns.xl,
                },
                columnGap: spacing,
                ...sx,
            }}
        >
            {childrenArray.map((child, index) => (
                <Box
                    key={index}
                    sx={{
                        breakInside: 'avoid',
                        marginBottom: spacing,
                        display: 'inline-block',
                        width: '100%',
                    }}
                >
                    {child}
                </Box>
            ))}
        </Box>
    );

    if (container && maxWidth) {
        return (
            <Container 
                maxWidth={maxWidth}
                sx={{ 
                    px: { xs: 2, sm: 3, md: 4 },
                    py: { xs: 2, sm: 3 },
                }}
            >
                {content}
            </Container>
        );
    }

    if (container) {
        return (
            <Box sx={{ 
                px: { xs: 2, sm: 3, md: 4 },
                py: { xs: 2, sm: 3 },
            }}>
                {content}
            </Box>
        );
    }

    return content;
}