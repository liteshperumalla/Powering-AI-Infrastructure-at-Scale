'use client';

import React from 'react';
import { IconButton, Tooltip, useTheme as useMuiTheme } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import { useTheme } from '@/theme/ThemeContext';

interface ThemeToggleProps {
  size?: 'small' | 'medium' | 'large';
  showTooltip?: boolean;
  sx?: any;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  size = 'medium', 
  showTooltip = true,
  sx = {}
}) => {
  const { mode, toggleColorMode } = useTheme();
  const muiTheme = useMuiTheme();

  const isDark = mode === 'dark';
  const icon = isDark ? <Brightness4 /> : <Brightness7 />;
  const tooltipText = `Switch to ${isDark ? 'light' : 'dark'} mode`;

  const button = (
    <IconButton
      onClick={toggleColorMode}
      color="inherit"
      size={size}
      sx={{
        ml: 1,
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'rotate(180deg)',
          backgroundColor: isDark 
            ? 'rgba(255, 255, 255, 0.08)' 
            : 'rgba(0, 0, 0, 0.04)',
        },
        ...sx,
      }}
      aria-label={tooltipText}
    >
      {icon}
    </IconButton>
  );

  if (showTooltip) {
    return (
      <Tooltip title={tooltipText} arrow>
        {button}
      </Tooltip>
    );
  }

  return button;
};

export default ThemeToggle;