'use client';

import { createTheme, PaletteMode } from '@mui/material/styles';

// Base theme configuration
const getThemeConfig = (mode: PaletteMode) => {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? '#42a5f5' : '#1976d2',
        light: isDark ? '#64b5f6' : '#42a5f5',
        dark: isDark ? '#1976d2' : '#1565c0',
        contrastText: '#ffffff',
      },
      secondary: {
        main: isDark ? '#ff5983' : '#dc004e',
        light: isDark ? '#ff8a9b' : '#ff5983',
        dark: isDark ? '#e91e63' : '#9a0036',
        contrastText: '#ffffff',
      },
      error: {
        main: isDark ? '#ef5350' : '#f44336',
        light: isDark ? '#ff7961' : '#e57373',
        dark: isDark ? '#c62828' : '#d32f2f',
        contrastText: '#ffffff',
      },
      warning: {
        main: isDark ? '#ff9800' : '#ff9800',
        light: isDark ? '#ffb74d' : '#ffb74d',
        dark: isDark ? '#f57c00' : '#f57c00',
        contrastText: isDark ? '#000' : 'rgba(0, 0, 0, 0.87)',
      },
      info: {
        main: isDark ? '#29b6f6' : '#2196f3',
        light: isDark ? '#4fc3f7' : '#64b5f6',
        dark: isDark ? '#0288d1' : '#1976d2',
        contrastText: '#ffffff',
      },
      success: {
        main: isDark ? '#66bb6a' : '#4caf50',
        light: isDark ? '#81c784' : '#81c784',
        dark: isDark ? '#388e3c' : '#388e3c',
        contrastText: isDark ? '#000' : 'rgba(0, 0, 0, 0.87)',
      },
      grey: {
        50: isDark ? '#fafafa' : '#fafafa',
        100: isDark ? '#f5f5f5' : '#f5f5f5',
        200: isDark ? '#eeeeee' : '#eeeeee',
        300: isDark ? '#e0e0e0' : '#e0e0e0',
        400: isDark ? '#bdbdbd' : '#bdbdbd',
        500: isDark ? '#9e9e9e' : '#9e9e9e',
        600: isDark ? '#757575' : '#757575',
        700: isDark ? '#616161' : '#616161',
        800: isDark ? '#424242' : '#424242',
        900: isDark ? '#212121' : '#212121',
      },
      background: {
        default: isDark ? '#121212' : '#f5f5f5',
        paper: isDark ? '#1e1e1e' : '#ffffff',
      },
      text: {
        primary: isDark ? '#ffffff' : 'rgba(0, 0, 0, 0.87)',
        secondary: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
        disabled: isDark ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.38)',
      },
      divider: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
      action: {
        active: isDark ? 'rgba(255, 255, 255, 0.56)' : 'rgba(0, 0, 0, 0.54)',
        hover: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)',
        selected: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
        disabled: isDark ? 'rgba(255, 255, 255, 0.26)' : 'rgba(0, 0, 0, 0.26)',
        disabledBackground: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.12)',
      },
    },
    typography: {
      fontFamily: [
        '"Inter"',
        '"Roboto"',
        '"Helvetica"',
        '"Arial"',
        'sans-serif',
      ].join(','),
      h1: {
        fontSize: '2.125rem',
        fontWeight: 700,
        lineHeight: 1.235,
      },
      h2: {
        fontSize: '1.75rem',
        fontWeight: 600,
        lineHeight: 1.3,
      },
      h3: {
        fontSize: '1.5rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h4: {
        fontSize: '1.25rem',
        fontWeight: 600,
        lineHeight: 1.5,
      },
      h5: {
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.6,
      },
      h6: {
        fontSize: '0.875rem',
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
        lineHeight: 1.43,
        fontWeight: 400,
      },
      button: {
        fontSize: '0.875rem',
        fontWeight: 500,
        lineHeight: 1.75,
        textTransform: 'none' as const,
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.66,
        fontWeight: 400,
      },
    },
    shape: {
      borderRadius: 12,
    },
    spacing: 8,
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            padding: '8px 24px',
            fontWeight: 500,
            fontSize: '0.875rem',
            transition: 'all 0.2s ease-in-out',
          },
          contained: {
            boxShadow: isDark 
              ? '0 2px 8px rgba(0, 0, 0, 0.4)' 
              : '0 2px 4px rgba(0, 0, 0, 0.1)',
            '&:hover': {
              boxShadow: isDark 
                ? '0 4px 16px rgba(0, 0, 0, 0.5)' 
                : '0 4px 8px rgba(0, 0, 0, 0.15)',
              transform: 'translateY(-1px)',
            },
            '&:active': {
              transform: 'translateY(0px)',
            },
          },
          outlined: {
            borderWidth: '1.5px',
            '&:hover': {
              borderWidth: '1.5px',
              backgroundColor: isDark 
                ? 'rgba(255, 255, 255, 0.05)' 
                : 'rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            boxShadow: isDark
              ? '0 4px 20px rgba(0, 0, 0, 0.5)'
              : '0 2px 12px rgba(0, 0, 0, 0.08)',
            border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: isDark
                ? '0 8px 28px rgba(0, 0, 0, 0.6)'
                : '0 4px 20px rgba(0, 0, 0, 0.12)',
              transform: 'translateY(-2px)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundImage: isDark ? 'linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))' : 'none',
            border: isDark ? '1px solid rgba(255, 255, 255, 0.08)' : 'none',
          },
          elevation1: {
            boxShadow: isDark
              ? '0 1px 3px rgba(0, 0, 0, 0.4)'
              : '0 1px 3px rgba(0, 0, 0, 0.12)',
          },
          elevation2: {
            boxShadow: isDark
              ? '0 2px 6px rgba(0, 0, 0, 0.4)'
              : '0 2px 6px rgba(0, 0, 0, 0.12)',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: isDark
              ? '0 1px 3px rgba(0, 0, 0, 0.6)'
              : '0 1px 3px rgba(0, 0, 0, 0.12)',
            backgroundImage: isDark 
              ? 'linear-gradient(135deg, rgba(66, 165, 245, 0.1) 0%, rgba(25, 118, 210, 0.1) 100%)'
              : 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
            backdropFilter: 'blur(20px)',
            borderBottom: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.02)',
            transition: 'all 0.2s ease-in-out',
            boxShadow: 'none',
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'transparent',
              borderWidth: 0,
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'transparent',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: 'transparent',
            },
            '&.Mui-focused': {
              backgroundColor: isDark ? 'rgba(19, 20, 24, 0.98)' : '#ffffff',
              boxShadow: isDark
                ? '0 0 0 3px rgba(66, 165, 245, 0.35)'
                : '0 0 0 3px rgba(25, 118, 210, 0.2)',
            },
          },
        },
      },
      MuiInputLabel: {
        styleOverrides: {
          root: {
            fontWeight: 600,
            '&.MuiInputLabel-shrink': {
              transform: 'translate(14px, -8px) scale(0.9)',
              padding: '0 6px',
              borderRadius: '999px',
              backgroundColor: isDark ? 'rgba(15, 15, 15, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              color: isDark ? 'rgba(255, 255, 255, 0.85)' : 'rgba(22, 22, 22, 0.85)',
            },
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
          bar: {
            borderRadius: 4,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            fontWeight: 500,
            border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : 'none',
          },
          filled: {
            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : undefined,
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
              transform: 'scale(1.05)',
            },
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            margin: '4px 8px',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
              transform: 'translateX(4px)',
            },
            '&.Mui-selected': {
              backgroundColor: isDark ? 'rgba(66, 165, 245, 0.15)' : 'rgba(25, 118, 210, 0.08)',
              '&:hover': {
                backgroundColor: isDark ? 'rgba(66, 165, 245, 0.2)' : 'rgba(25, 118, 210, 0.12)',
              },
            },
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundImage: isDark 
              ? 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)'
              : 'none',
            borderRight: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : undefined,
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 16,
            border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
            boxShadow: isDark
              ? '0 8px 32px rgba(0, 0, 0, 0.6)'
              : '0 8px 32px rgba(0, 0, 0, 0.12)',
          },
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: 12,
            border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
            boxShadow: isDark
              ? '0 4px 20px rgba(0, 0, 0, 0.5)'
              : '0 4px 20px rgba(0, 0, 0, 0.15)',
            backdropFilter: 'blur(20px)',
            backgroundImage: isDark
              ? 'linear-gradient(rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.08))'
              : 'none',
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: isDark ? 'rgba(97, 97, 97, 0.95)' : 'rgba(97, 97, 97, 0.92)',
            backdropFilter: 'blur(6px)',
            borderRadius: 8,
            fontSize: '0.75rem',
          },
          arrow: {
            color: isDark ? 'rgba(97, 97, 97, 0.95)' : 'rgba(97, 97, 97, 0.92)',
          },
        },
      },
    },
  });
};

// Export individual themes
export const lightTheme = getThemeConfig('light');
export const darkTheme = getThemeConfig('dark');

// Export theme creator function
export const createAppTheme = (mode: PaletteMode) => getThemeConfig(mode);

export default { lightTheme, darkTheme, createAppTheme };
