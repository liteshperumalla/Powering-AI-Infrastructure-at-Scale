'use client';

import React from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeContextProvider, useTheme } from '@/theme/ThemeContext';
import { createAppTheme } from '@/theme/themes';

interface ThemeProviderProps {
    children: React.ReactNode;
}

function MuiThemeWrapper({ children }: { children: React.ReactNode }) {
    const { mode } = useTheme();
    const theme = createAppTheme(mode);

    return (
        <MuiThemeProvider theme={theme}>
            <CssBaseline enableColorScheme />
            {children}
        </MuiThemeProvider>
    );
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
    return (
        <AppRouterCacheProvider options={{ enableCssLayer: true }}>
            <ThemeContextProvider>
                <MuiThemeWrapper>
                    {children}
                </MuiThemeWrapper>
            </ThemeContextProvider>
        </AppRouterCacheProvider>
    );
}