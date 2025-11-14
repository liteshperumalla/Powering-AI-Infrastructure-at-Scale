'use client';

import { createTheme, alpha } from '@mui/material/styles';

// Type for theme mode
type PaletteMode = 'light' | 'dark';

/**
 * Enhanced Brand Theme for Infra-Mind
 *
 * Design Philosophy:
 * - AI-Forward: Gradient-rich, futuristic aesthetic
 * - Professional: Enterprise-grade visual language
 * - Modern: Glassmorphism, depth, micro-animations
 * - Accessible: WCAG 2.1 AA compliant color contrasts
 *
 * Brand Colors:
 * - Primary: Electric Blue (#0066FF) - Innovation, Intelligence
 * - Secondary: Cyber Purple (#7C3AED) - Premium, AI Technology
 * - Accent: Neon Cyan (#00D9FF) - Energy, Highlights
 * - Success: Emerald Green (#10B981) - Growth, Optimization
 * - Warning: Amber (#F59E0B) - Attention, Performance
 * - Error: Ruby Red (#EF4444) - Critical, Issues
 */

// Brand color palette
const brandColors = {
  // Primary - Electric Blue
  primary: {
    50: '#E6F0FF',
    100: '#CCE0FF',
    200: '#99C2FF',
    300: '#66A3FF',
    400: '#3385FF',
    500: '#0066FF', // Main
    600: '#0052CC',
    700: '#003D99',
    800: '#002966',
    900: '#001433',
  },
  // Secondary - Cyber Purple
  secondary: {
    50: '#F5F3FF',
    100: '#EDE9FE',
    200: '#DDD6FE',
    300: '#C4B5FD',
    400: '#A78BFA',
    500: '#7C3AED', // Main
    600: '#6D28D9',
    700: '#5B21B6',
    800: '#4C1D95',
    900: '#2E1065',
  },
  // Accent - Neon Cyan
  accent: {
    50: '#E6FBFF',
    100: '#CCF7FF',
    200: '#99EFFF',
    300: '#66E7FF',
    400: '#33DFFF',
    500: '#00D9FF', // Main
    600: '#00B8D9',
    700: '#0097B3',
    800: '#00768C',
    900: '#005566',
  },
  // Success - Emerald Green
  success: {
    50: '#ECFDF5',
    100: '#D1FAE5',
    200: '#A7F3D0',
    300: '#6EE7B7',
    400: '#34D399',
    500: '#10B981', // Main
    600: '#059669',
    700: '#047857',
    800: '#065F46',
    900: '#064E3B',
  },
  // Warning - Amber
  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B', // Main
    600: '#D97706',
    700: '#B45309',
    800: '#92400E',
    900: '#78350F',
  },
  // Error - Ruby Red
  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444', // Main
    600: '#DC2626',
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
  },
  // Neutrals
  neutral: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#0A0F1A',
  },
};

// Create enhanced theme with modern visual effects
export const createEnhancedTheme = (mode: PaletteMode) => {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: brandColors.primary[500],
        light: brandColors.primary[400],
        dark: brandColors.primary[600],
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: brandColors.secondary[500],
        light: brandColors.secondary[400],
        dark: brandColors.secondary[600],
        contrastText: '#FFFFFF',
      },
      error: {
        main: brandColors.error[500],
        light: brandColors.error[400],
        dark: brandColors.error[600],
        contrastText: '#FFFFFF',
      },
      warning: {
        main: brandColors.warning[500],
        light: brandColors.warning[400],
        dark: brandColors.warning[600],
        contrastText: isDark ? '#000000' : '#FFFFFF',
      },
      info: {
        main: brandColors.accent[500],
        light: brandColors.accent[400],
        dark: brandColors.accent[600],
        contrastText: '#000000',
      },
      success: {
        main: brandColors.success[500],
        light: brandColors.success[400],
        dark: brandColors.success[600],
        contrastText: '#FFFFFF',
      },
      background: {
        default: isDark ? brandColors.neutral[950] : brandColors.neutral[50],
        paper: isDark ? brandColors.neutral[900] : '#FFFFFF',
      },
      text: {
        primary: isDark ? '#FFFFFF' : brandColors.neutral[900],
        secondary: isDark ? brandColors.neutral[300] : brandColors.neutral[600],
        disabled: isDark ? brandColors.neutral[500] : brandColors.neutral[400],
      },
      divider: isDark ? alpha('#FFFFFF', 0.12) : alpha('#000000', 0.12),
      action: {
        active: isDark ? alpha('#FFFFFF', 0.56) : alpha('#000000', 0.54),
        hover: isDark ? alpha('#FFFFFF', 0.08) : alpha('#000000', 0.04),
        selected: isDark ? alpha(brandColors.primary[500], 0.16) : alpha(brandColors.primary[500], 0.08),
        disabled: isDark ? alpha('#FFFFFF', 0.26) : alpha('#000000', 0.26),
        disabledBackground: isDark ? alpha('#FFFFFF', 0.12) : alpha('#000000', 0.12),
      },
    },
    typography: {
      fontFamily: [
        '"Inter"',
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        '"Roboto"',
        '"Helvetica Neue"',
        'Arial',
        'sans-serif',
      ].join(','),
      h1: {
        fontSize: '3rem',
        fontWeight: 700,
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
      },
      h2: {
        fontSize: '2.25rem',
        fontWeight: 700,
        lineHeight: 1.3,
        letterSpacing: '-0.01em',
      },
      h3: {
        fontSize: '1.875rem',
        fontWeight: 600,
        lineHeight: 1.4,
        letterSpacing: '-0.01em',
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 600,
        lineHeight: 1.5,
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 600,
        lineHeight: 1.6,
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.6,
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.5,
        fontWeight: 400,
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.57,
        fontWeight: 400,
      },
      button: {
        fontSize: '0.875rem',
        fontWeight: 600,
        lineHeight: 1.75,
        textTransform: 'none' as const,
        letterSpacing: '0.02em',
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.66,
        fontWeight: 400,
      },
      overline: {
        fontSize: '0.75rem',
        lineHeight: 2.66,
        fontWeight: 600,
        textTransform: 'uppercase' as const,
        letterSpacing: '0.08em',
      },
    },
    shape: {
      borderRadius: 12,
    },
    spacing: 8,
    shadows: isDark ? [
      'none',
      '0px 2px 4px rgba(0, 0, 0, 0.5)',
      '0px 4px 8px rgba(0, 0, 0, 0.5)',
      '0px 8px 16px rgba(0, 0, 0, 0.5)',
      '0px 12px 24px rgba(0, 0, 0, 0.6)',
      '0px 16px 32px rgba(0, 0, 0, 0.6)',
      '0px 20px 40px rgba(0, 0, 0, 0.7)',
      '0px 24px 48px rgba(0, 0, 0, 0.7)',
      '0px 32px 64px rgba(0, 0, 0, 0.8)',
      '0px 40px 80px rgba(0, 0, 0, 0.8)',
      '0px 1px 3px rgba(0, 0, 0, 0.4)',
      '0px 1px 5px rgba(0, 0, 0, 0.4)',
      '0px 1px 8px rgba(0, 0, 0, 0.4)',
      '0px 2px 4px rgba(0, 0, 0, 0.4)',
      '0px 3px 5px rgba(0, 0, 0, 0.4)',
      '0px 3px 8px rgba(0, 0, 0, 0.5)',
      '0px 4px 10px rgba(0, 0, 0, 0.5)',
      '0px 5px 12px rgba(0, 0, 0, 0.5)',
      '0px 6px 16px rgba(0, 0, 0, 0.6)',
      '0px 7px 20px rgba(0, 0, 0, 0.6)',
      '0px 8px 24px rgba(0, 0, 0, 0.6)',
      '0px 9px 28px rgba(0, 0, 0, 0.7)',
      '0px 10px 32px rgba(0, 0, 0, 0.7)',
      '0px 12px 40px rgba(0, 0, 0, 0.7)',
      '0px 16px 48px rgba(0, 0, 0, 0.8)',
    ] : [
      'none',
      '0px 2px 4px rgba(0, 0, 0, 0.05)',
      '0px 4px 8px rgba(0, 0, 0, 0.08)',
      '0px 8px 16px rgba(0, 0, 0, 0.10)',
      '0px 12px 24px rgba(0, 0, 0, 0.12)',
      '0px 16px 32px rgba(0, 0, 0, 0.14)',
      '0px 20px 40px rgba(0, 0, 0, 0.16)',
      '0px 24px 48px rgba(0, 0, 0, 0.18)',
      '0px 32px 64px rgba(0, 0, 0, 0.20)',
      '0px 40px 80px rgba(0, 0, 0, 0.22)',
      '0px 1px 3px rgba(0, 0, 0, 0.08)',
      '0px 1px 5px rgba(0, 0, 0, 0.08)',
      '0px 1px 8px rgba(0, 0, 0, 0.08)',
      '0px 2px 4px rgba(0, 0, 0, 0.08)',
      '0px 3px 5px rgba(0, 0, 0, 0.08)',
      '0px 3px 8px rgba(0, 0, 0, 0.10)',
      '0px 4px 10px rgba(0, 0, 0, 0.10)',
      '0px 5px 12px rgba(0, 0, 0, 0.10)',
      '0px 6px 16px rgba(0, 0, 0, 0.12)',
      '0px 7px 20px rgba(0, 0, 0, 0.12)',
      '0px 8px 24px rgba(0, 0, 0, 0.12)',
      '0px 9px 28px rgba(0, 0, 0, 0.14)',
      '0px 10px 32px rgba(0, 0, 0, 0.14)',
      '0px 12px 40px rgba(0, 0, 0, 0.16)',
      '0px 16px 48px rgba(0, 0, 0, 0.18)',
    ],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            // Custom scrollbar
            '&::-webkit-scrollbar': {
              width: '8px',
              height: '8px',
            },
            '&::-webkit-scrollbar-track': {
              background: isDark ? brandColors.neutral[900] : brandColors.neutral[100],
            },
            '&::-webkit-scrollbar-thumb': {
              background: isDark ? brandColors.neutral[700] : brandColors.neutral[400],
              borderRadius: '4px',
              '&:hover': {
                background: isDark ? brandColors.neutral[600] : brandColors.neutral[500],
              },
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 10,
            padding: '10px 24px',
            fontWeight: 600,
            fontSize: '0.875rem',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
              transform: 'translateX(-100%)',
              transition: 'transform 0.6s',
            },
            '&:hover::before': {
              transform: 'translateX(100%)',
            },
          },
          contained: {
            background: `linear-gradient(135deg, ${brandColors.primary[500]} 0%, ${brandColors.primary[600]} 100%)`,
            boxShadow: `0 4px 14px 0 ${alpha(brandColors.primary[500], 0.4)}`,
            '&:hover': {
              background: `linear-gradient(135deg, ${brandColors.primary[600]} 0%, ${brandColors.primary[700]} 100%)`,
              boxShadow: `0 6px 20px ${alpha(brandColors.primary[500], 0.5)}`,
              transform: 'translateY(-2px)',
            },
            '&:active': {
              transform: 'translateY(0px)',
            },
          },
          containedSecondary: {
            background: `linear-gradient(135deg, ${brandColors.secondary[500]} 0%, ${brandColors.secondary[600]} 100%)`,
            boxShadow: `0 4px 14px 0 ${alpha(brandColors.secondary[500], 0.4)}`,
            '&:hover': {
              background: `linear-gradient(135deg, ${brandColors.secondary[600]} 0%, ${brandColors.secondary[700]} 100%)`,
              boxShadow: `0 6px 20px ${alpha(brandColors.secondary[500], 0.5)}`,
            },
          },
          outlined: {
            borderWidth: '2px',
            borderColor: isDark ? brandColors.primary[400] : brandColors.primary[500],
            color: isDark ? brandColors.primary[400] : brandColors.primary[600],
            '&:hover': {
              borderWidth: '2px',
              borderColor: isDark ? brandColors.primary[300] : brandColors.primary[600],
              backgroundColor: isDark
                ? alpha(brandColors.primary[500], 0.08)
                : alpha(brandColors.primary[500], 0.04),
            },
          },
          text: {
            '&:hover': {
              backgroundColor: isDark
                ? alpha(brandColors.primary[500], 0.08)
                : alpha(brandColors.primary[500], 0.04),
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            background: isDark
              ? `linear-gradient(135deg, ${alpha(brandColors.neutral[900], 0.9)} 0%, ${alpha(brandColors.neutral[800], 0.9)} 100%)`
              : '#FFFFFF',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isDark ? alpha('#FFFFFF', 0.1) : alpha('#000000', 0.06)}`,
            boxShadow: isDark
              ? `0 8px 32px ${alpha('#000000', 0.6)}, 0 0 0 1px ${alpha('#FFFFFF', 0.05)} inset`
              : `0 4px 20px ${alpha('#000000', 0.08)}, 0 0 0 1px ${alpha('#000000', 0.03)} inset`,
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              transform: 'translateY(-4px) scale(1.01)',
              boxShadow: isDark
                ? `0 12px 48px ${alpha('#000000', 0.7)}, 0 0 0 1px ${alpha('#FFFFFF', 0.08)} inset`
                : `0 8px 32px ${alpha('#000000', 0.12)}, 0 0 0 1px ${alpha(brandColors.primary[500], 0.1)} inset`,
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundImage: isDark
              ? `linear-gradient(${alpha('#FFFFFF', 0.05)}, ${alpha('#FFFFFF', 0.05)})`
              : 'none',
            backdropFilter: isDark ? 'blur(20px)' : undefined,
            border: isDark ? `1px solid ${alpha('#FFFFFF', 0.08)}` : 'none',
          },
          elevation1: {
            boxShadow: isDark
              ? `0 2px 8px ${alpha('#000000', 0.5)}`
              : `0 2px 8px ${alpha('#000000', 0.08)}`,
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: isDark
              ? `linear-gradient(135deg, ${alpha(brandColors.neutral[900], 0.8)} 0%, ${alpha(brandColors.neutral[800], 0.8)} 100%)`
              : `linear-gradient(135deg, ${brandColors.primary[500]} 0%, ${brandColors.primary[600]} 50%, ${brandColors.secondary[500]} 100%)`,
            backdropFilter: 'blur(20px) saturate(180%)',
            boxShadow: `0 4px 30px ${isDark ? alpha('#000000', 0.6) : alpha(brandColors.primary[500], 0.3)}`,
            borderBottom: `1px solid ${isDark ? alpha('#FFFFFF', 0.1) : 'transparent'}`,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 10,
              backgroundColor: isDark
                ? alpha(brandColors.neutral[800], 0.5)
                : alpha(brandColors.neutral[100], 0.5),
              backdropFilter: 'blur(10px)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              '& fieldset': {
                borderColor: isDark ? alpha('#FFFFFF', 0.1) : alpha('#000000', 0.12),
                borderWidth: '1.5px',
              },
              '&:hover': {
                backgroundColor: isDark
                  ? alpha(brandColors.neutral[700], 0.5)
                  : alpha(brandColors.neutral[200], 0.5),
                '& fieldset': {
                  borderColor: isDark ? alpha('#FFFFFF', 0.2) : alpha('#000000', 0.2),
                },
              },
              '&.Mui-focused': {
                backgroundColor: isDark
                  ? alpha(brandColors.neutral[700], 0.7)
                  : alpha(brandColors.neutral[100], 0.8),
                boxShadow: `0 0 0 4px ${alpha(brandColors.primary[500], 0.1)}`,
                '& fieldset': {
                  borderColor: brandColors.primary[500],
                  borderWidth: '2px',
                },
              },
            },
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            height: 6,
            borderRadius: 3,
            backgroundColor: isDark
              ? alpha(brandColors.neutral[700], 0.3)
              : alpha(brandColors.neutral[300], 0.3),
          },
          bar: {
            borderRadius: 3,
            background: `linear-gradient(90deg, ${brandColors.primary[500]} 0%, ${brandColors.accent[500]} 100%)`,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 20,
            fontWeight: 600,
            fontSize: '0.8125rem',
            backdropFilter: 'blur(10px)',
            border: `1px solid ${isDark ? alpha('#FFFFFF', 0.15) : 'transparent'}`,
          },
          filled: {
            backgroundColor: isDark
              ? alpha(brandColors.neutral[700], 0.6)
              : alpha(brandColors.neutral[200], 0.6),
          },
          colorPrimary: {
            background: `linear-gradient(135deg, ${alpha(brandColors.primary[500], 0.2)} 0%, ${alpha(brandColors.primary[600], 0.2)} 100%)`,
            color: isDark ? brandColors.primary[300] : brandColors.primary[700],
            border: `1px solid ${alpha(brandColors.primary[500], 0.3)}`,
          },
          colorSecondary: {
            background: `linear-gradient(135deg, ${alpha(brandColors.secondary[500], 0.2)} 0%, ${alpha(brandColors.secondary[600], 0.2)} 100%)`,
            color: isDark ? brandColors.secondary[300] : brandColors.secondary[700],
            border: `1px solid ${alpha(brandColors.secondary[500], 0.3)}`,
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              backgroundColor: isDark
                ? alpha(brandColors.primary[500], 0.15)
                : alpha(brandColors.primary[500], 0.08),
              transform: 'scale(1.08) rotate(5deg)',
            },
            '&:active': {
              transform: 'scale(0.95)',
            },
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            margin: '4px 8px',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              backgroundColor: isDark
                ? alpha(brandColors.primary[500], 0.12)
                : alpha(brandColors.primary[500], 0.06),
              transform: 'translateX(8px)',
              paddingLeft: '24px',
            },
            '&.Mui-selected': {
              background: `linear-gradient(90deg, ${alpha(brandColors.primary[500], 0.2)} 0%, ${alpha(brandColors.primary[600], 0.15)} 100%)`,
              borderLeft: `3px solid ${brandColors.primary[500]}`,
              '&:hover': {
                background: `linear-gradient(90deg, ${alpha(brandColors.primary[500], 0.25)} 0%, ${alpha(brandColors.primary[600], 0.2)} 100%)`,
              },
            },
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            background: isDark
              ? `linear-gradient(180deg, ${alpha(brandColors.neutral[900], 0.95)} 0%, ${alpha(brandColors.neutral[800], 0.95)} 100%)`
              : '#FFFFFF',
            backdropFilter: 'blur(20px)',
            borderRight: `1px solid ${isDark ? alpha('#FFFFFF', 0.1) : alpha('#000000', 0.08)}`,
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 20,
            border: isDark ? `1px solid ${alpha('#FFFFFF', 0.12)}` : 'none',
            boxShadow: isDark
              ? `0 24px 48px ${alpha('#000000', 0.8)}, 0 0 0 1px ${alpha('#FFFFFF', 0.05)} inset`
              : `0 24px 48px ${alpha('#000000', 0.15)}`,
            backdropFilter: 'blur(40px)',
            background: isDark
              ? `linear-gradient(135deg, ${alpha(brandColors.neutral[900], 0.95)} 0%, ${alpha(brandColors.neutral[800], 0.95)} 100%)`
              : '#FFFFFF',
          },
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: 12,
            border: isDark ? `1px solid ${alpha('#FFFFFF', 0.12)}` : 'none',
            boxShadow: isDark
              ? `0 8px 32px ${alpha('#000000', 0.6)}`
              : `0 8px 32px ${alpha('#000000', 0.12)}`,
            backdropFilter: 'blur(20px)',
            background: isDark
              ? `linear-gradient(${alpha(brandColors.neutral[800], 0.95)}, ${alpha(brandColors.neutral[800], 0.95)})`
              : alpha('#FFFFFF', 0.95),
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: isDark
              ? alpha(brandColors.neutral[700], 0.98)
              : alpha(brandColors.neutral[800], 0.95),
            backdropFilter: 'blur(10px)',
            borderRadius: 8,
            fontSize: '0.75rem',
            fontWeight: 500,
            padding: '8px 12px',
            boxShadow: `0 4px 20px ${alpha('#000000', 0.3)}`,
          },
          arrow: {
            color: isDark
              ? alpha(brandColors.neutral[700], 0.98)
              : alpha(brandColors.neutral[800], 0.95),
          },
        },
      },
      MuiBadge: {
        styleOverrides: {
          badge: {
            fontWeight: 700,
            fontSize: '0.7rem',
            minWidth: '20px',
            height: '20px',
            borderRadius: '10px',
            border: `2px solid ${isDark ? brandColors.neutral[900] : '#FFFFFF'}`,
            boxShadow: `0 2px 8px ${alpha('#000000', 0.2)}`,
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha('#FFFFFF', 0.1)}`,
          },
          filledSuccess: {
            background: `linear-gradient(135deg, ${brandColors.success[500]} 0%, ${brandColors.success[600]} 100%)`,
          },
          filledError: {
            background: `linear-gradient(135deg, ${brandColors.error[500]} 0%, ${brandColors.error[600]} 100%)`,
          },
          filledWarning: {
            background: `linear-gradient(135deg, ${brandColors.warning[500]} 0%, ${brandColors.warning[600]} 100%)`,
          },
          filledInfo: {
            background: `linear-gradient(135deg, ${brandColors.accent[500]} 0%, ${brandColors.accent[600]} 100%)`,
          },
        },
      },
    },
  });
};

// Export pre-configured themes
export const enhancedLightTheme = createEnhancedTheme('light');
export const enhancedDarkTheme = createEnhancedTheme('dark');

// Export brand colors for use in components
export { brandColors };

export default {
  enhancedLightTheme,
  enhancedDarkTheme,
  createEnhancedTheme,
  brandColors,
};
