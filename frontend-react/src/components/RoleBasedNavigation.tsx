'use client';

import React from 'react';
import { useAppSelector } from '@/store/hooks';
import { useRouter } from 'next/navigation';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Chip,
  Box,
  Typography
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  Recommend as RecommendIcon,
  Chat as ChatIcon,
  Cloud as CloudIcon,
  Analytics as AnalyticsIcon,
  Description as ReportIcon,
  Settings as SettingsIcon,
  Person as ProfileIcon,
  Feedback as FeedbackIcon,
  // Admin features
  AdminPanelSettings as AdminIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  VerifiedUser as ComplianceIcon,
  Science as ExperimentIcon,
  HighQuality as QualityIcon,
  Business as ExecutiveIcon,
  Approval as ApprovalIcon,
  AccountBalance as BudgetIcon,
  Code as GitOpsIcon,
  Assessment as ImpactIcon,
  Undo as RollbackIcon,
  CompareArrows as VendorIcon,
  MonitorHeart as SystemStatusIcon
} from '@mui/icons-material';

interface NavigationItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  roles: string[];
  category: 'user' | 'admin' | 'both';
}

const navigationItems: NavigationItem[] = [
  // User Features
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon />, roles: ['*'], category: 'user' },
  { path: '/assessments', label: 'Assessments', icon: <AssessmentIcon />, roles: ['*'], category: 'user' },
  { path: '/recommendations', label: 'Recommendations', icon: <RecommendIcon />, roles: ['*'], category: 'user' },
  { path: '/chat', label: 'AI Assistant', icon: <ChatIcon />, roles: ['*'], category: 'user' },
  { path: '/cloud-services', label: 'Cloud Services', icon: <CloudIcon />, roles: ['*'], category: 'user' },
  { path: '/analytics', label: 'Analytics', icon: <AnalyticsIcon />, roles: ['*'], category: 'user' },
  { path: '/reports', label: 'Reports', icon: <ReportIcon />, roles: ['*'], category: 'user' },
  { path: '/feedback', label: 'Feedback', icon: <FeedbackIcon />, roles: ['*'], category: 'user' },
  { path: '/profile', label: 'Profile', icon: <ProfileIcon />, roles: ['*'], category: 'user' },
  { path: '/settings', label: 'Settings', icon: <SettingsIcon />, roles: ['*'], category: 'user' },

  // Admin Features
  { path: '/system-status', label: 'System Status', icon: <SystemStatusIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/security', label: 'Security', icon: <SecurityIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/performance', label: 'Performance', icon: <PerformanceIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/compliance', label: 'Compliance', icon: <ComplianceIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/experiments', label: 'Experiments', icon: <ExperimentIcon />, roles: ['admin'], category: 'admin' },
  { path: '/quality', label: 'Quality', icon: <QualityIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/executive-dashboard', label: 'Executive Dashboard', icon: <ExecutiveIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/approvals', label: 'Approvals', icon: <ApprovalIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/budget-forecasting', label: 'Budget Forecasting', icon: <BudgetIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/gitops', label: 'GitOps', icon: <GitOpsIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/impact-analysis', label: 'Impact Analysis', icon: <ImpactIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/rollback', label: 'Rollback', icon: <RollbackIcon />, roles: ['admin', 'manager'], category: 'admin' },
  { path: '/vendor-lockin', label: 'Vendor Lock-in', icon: <VendorIcon />, roles: ['admin', 'manager'], category: 'admin' },
];

interface RoleBasedNavigationProps {
  onItemClick?: () => void;
}

const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({ onItemClick }) => {
  const { user, isAuthenticated } = useAppSelector(state => state.auth);
  const currentAssessment = useAppSelector(state => state.assessment.currentAssessment);
  const router = useRouter();
  const userRole = user?.role || 'user';

  const hasAccess = (item: NavigationItem): boolean => {
    if (!isAuthenticated) return item.roles.includes('*') && item.category === 'user';
    return item.roles.includes('*') || item.roles.includes(userRole);
  };

  // Feature pages that need assessment ID
  const featurePages = [
    '/performance',
    '/compliance',
    '/experiments',
    '/quality',
    '/approvals',
    '/budget-forecasting',
    '/executive-dashboard',
    '/rollback',
    '/vendor-lockin'
  ];

  const handleNavigation = (path: string) => {
    if (onItemClick) onItemClick();

    // If it's a feature page and we have a current assessment, add the assessment ID
    if (featurePages.includes(path) && currentAssessment?.id) {
      router.push(`${path}?assessment_id=${currentAssessment.id}`);
    } else {
      router.push(path);
    }
  };

  const userItems = navigationItems.filter(item =>
    item.category === 'user' && hasAccess(item)
  );

  const adminItems = navigationItems.filter(item =>
    item.category === 'admin' && hasAccess(item)
  );

  const renderNavigationSection = (items: NavigationItem[], title: string, chipColor: 'primary' | 'secondary' = 'primary') => {
    if (items.length === 0) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
        </Box>
        <List dense>
          {items.map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 1,
                  mx: 1,
                  '&:hover': {
                    bgcolor: 'action.hover',
                  }
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: 500
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    );
  };

  return (
    <Box>
      {/* User Role Indicator */}
      {isAuthenticated && (
        <Box sx={{ px: 2, py: 1, mb: 2 }}>
          <Chip
            icon={<AdminIcon />}
            label={`Role: ${userRole.charAt(0).toUpperCase() + userRole.slice(1)}`}
            color={userRole === 'admin' ? 'error' : userRole === 'manager' ? 'warning' : 'default'}
            variant="outlined"
            size="small"
          />
        </Box>
      )}

      {/* User Features */}
      {renderNavigationSection(userItems, 'User Features', 'primary')}

      {/* Admin Features */}
      {adminItems.length > 0 && (
        <>
          <Divider sx={{ my: 1 }} />
          {renderNavigationSection(adminItems, 'Admin Features', 'secondary')}
        </>
      )}

      {/* No access message for unauthenticated users */}
      {!isAuthenticated && (
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            💡 Log in to access all features
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default RoleBasedNavigation;