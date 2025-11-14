'use client';

import React from 'react';
import { Breadcrumbs as MuiBreadcrumbs, Link, Typography, Box } from '@mui/material';
import { NavigateNext, Home } from '@mui/icons-material';
import { usePathname, useRouter } from 'next/navigation';

interface BreadcrumbItem {
    label: string;
    href?: string;
}

interface BreadcrumbsProps {
    customItems?: BreadcrumbItem[];
}

/**
 * Breadcrumb navigation component
 * Automatically generates breadcrumbs from current route or accepts custom items
 */
export default function Breadcrumbs({ customItems }: BreadcrumbsProps) {
    const pathname = usePathname();
    const router = useRouter();

    // Generate breadcrumb items from pathname
    const generateBreadcrumbs = (): BreadcrumbItem[] => {
        if (customItems) return customItems;

        const segments = pathname.split('/').filter(Boolean);
        const breadcrumbs: BreadcrumbItem[] = [
            { label: 'Home', href: '/dashboard' }
        ];

        // Map route segments to readable labels
        const labelMap: Record<string, string> = {
            'dashboard': 'Dashboard',
            'assessments': 'Assessments',
            'assessment': 'Assessment',
            'recommendations': 'Recommendations',
            'reports': 'Reports',
            'report': 'Report',
            'chat': 'AI Assistant',
            'settings': 'Settings',
            'profile': 'Profile',
            'auth': 'Authentication',
            'login': 'Login',
            'register': 'Register',
            'reset-password': 'Reset Password',
        };

        let currentPath = '';
        segments.forEach((segment, index) => {
            currentPath += `/${segment}`;

            // Skip UUID-like segments (assessment/report IDs)
            if (segment.match(/^[0-9a-f]{24}$/i)) {
                breadcrumbs.push({
                    label: 'Details',
                    href: index === segments.length - 1 ? undefined : currentPath
                });
            } else {
                breadcrumbs.push({
                    label: labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1),
                    href: index === segments.length - 1 ? undefined : currentPath
                });
            }
        });

        return breadcrumbs;
    };

    const breadcrumbs = generateBreadcrumbs();

    // Don't show breadcrumbs on home/login pages
    if (pathname === '/' || pathname === '/auth/login') {
        return null;
    }

    return (
        <Box sx={{ mb: 2, px: { xs: 2, sm: 3, md: 0 } }}>
            <MuiBreadcrumbs
                separator={<NavigateNext fontSize="small" />}
                aria-label="breadcrumb"
                sx={{
                    '& .MuiBreadcrumbs-separator': {
                        color: 'text.secondary'
                    }
                }}
            >
                {breadcrumbs.map((item, index) => {
                    const isLast = index === breadcrumbs.length - 1;
                    const isFirst = index === 0;

                    if (isLast) {
                        return (
                            <Typography
                                key={item.label}
                                color="text.primary"
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    fontWeight: 600
                                }}
                            >
                                {item.label}
                            </Typography>
                        );
                    }

                    return (
                        <Link
                            key={item.label}
                            color="inherit"
                            href={item.href}
                            onClick={(e) => {
                                if (item.href) {
                                    e.preventDefault();
                                    router.push(item.href);
                                }
                            }}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                textDecoration: 'none',
                                '&:hover': {
                                    textDecoration: 'underline',
                                    color: 'primary.main'
                                },
                                cursor: 'pointer'
                            }}
                        >
                            {isFirst && <Home fontSize="small" sx={{ mr: 0.5 }} />}
                            {item.label}
                        </Link>
                    );
                })}
            </MuiBreadcrumbs>
        </Box>
    );
}
