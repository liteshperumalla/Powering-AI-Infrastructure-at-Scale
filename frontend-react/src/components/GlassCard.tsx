'use client';

import React from 'react';
import { Card, CardProps, alpha, useTheme } from '@mui/material';
import { fadeInUp, hoverEffects } from '@/utils/animations';

interface GlassCardProps extends CardProps {
  /**
   * Blur intensity (default: 20px)
   */
  blur?: number;

  /**
   * Background opacity (default: 0.1)
   */
  opacity?: number;

  /**
   * Enable hover effect (default: true)
   */
  hoverable?: boolean;

  /**
   * Glow color (uses primary color if not specified)
   */
  glowColor?: string;

  /**
   * Animation on mount (default: true)
   */
  animated?: boolean;
}

/**
 * GlassCard Component - Glassmorphism design card
 *
 * Features:
 * - Frosted glass effect with backdrop blur
 * - Gradient border
 * - Hover animations
 * - Entrance animation
 * - Dark mode support
 *
 * @example
 * <GlassCard blur={30} opacity={0.15} hoverable>
 *   <CardContent>Your content here</CardContent>
 * </GlassCard>
 */
export default function GlassCard({
  blur = 20,
  opacity = 0.1,
  hoverable = true,
  glowColor,
  animated = true,
  children,
  sx,
  ...props
}: GlassCardProps) {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  // Use provided glow color or theme primary
  const resolvedGlowColor = glowColor || theme.palette.primary.main;

  return (
    <Card
      sx={{
        position: 'relative',
        overflow: 'hidden',

        // Glassmorphism effect
        background: isDark
          ? alpha(theme.palette.background.paper, opacity + 0.05)
          : alpha('#FFFFFF', opacity + 0.8),
        backdropFilter: `blur(${blur}px) saturate(180%)`,
        WebkitBackdropFilter: `blur(${blur}px) saturate(180%)`,

        // Gradient border
        border: `1px solid ${isDark ? alpha('#FFFFFF', 0.12) : alpha('#000000', 0.08)}`,
        borderRadius: '16px',

        // Shadow
        boxShadow: isDark
          ? `0 8px 32px ${alpha('#000000', 0.4)}, inset 0 0 0 1px ${alpha('#FFFFFF', 0.05)}`
          : `0 4px 20px ${alpha('#000000', 0.08)}, inset 0 0 0 1px ${alpha('#FFFFFF', 0.5)}`,

        // Entrance animation
        ...(animated && {
          animation: `${fadeInUp} 0.6s cubic-bezier(0.4, 0, 0.2, 1) backwards`,
        }),

        // Hover effects
        ...(hoverable && {
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          cursor: 'pointer',
          '&:hover': {
            transform: 'translateY(-8px) scale(1.02)',
            boxShadow: isDark
              ? `0 16px 48px ${alpha('#000000', 0.6)},
                 0 0 0 1px ${alpha(resolvedGlowColor, 0.3)} inset,
                 0 0 30px ${alpha(resolvedGlowColor, 0.2)}`
              : `0 12px 40px ${alpha('#000000', 0.12)},
                 0 0 0 1px ${alpha(resolvedGlowColor, 0.2)} inset,
                 0 0 30px ${alpha(resolvedGlowColor, 0.15)}`,
            border: `1px solid ${alpha(resolvedGlowColor, 0.3)}`,
          },
          '&:active': {
            transform: 'translateY(-4px) scale(0.99)',
          },
        }),

        // Gradient overlay on hover
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          borderRadius: '16px',
          padding: '1px',
          background: `linear-gradient(135deg, ${alpha(resolvedGlowColor, 0.4)} 0%, transparent 50%, ${alpha(
            resolvedGlowColor,
            0.4
          )} 100%)`,
          WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
          WebkitMaskComposite: 'xor',
          maskComposite: 'exclude',
          opacity: 0,
          transition: 'opacity 0.4s ease',
          pointerEvents: 'none',
        },
        ...(hoverable && {
          '&:hover::before': {
            opacity: 1,
          },
        }),

        // Shine effect on hover
        '&::after': {
          content: '""',
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: `radial-gradient(circle, ${alpha('#FFFFFF', 0.1)} 0%, transparent 60%)`,
          transform: 'translate(-100%, -100%)',
          transition: 'transform 0.6s ease',
          pointerEvents: 'none',
        },
        ...(hoverable && {
          '&:hover::after': {
            transform: 'translate(0%, 0%)',
          },
        }),

        // Custom sx overrides
        ...sx,
      }}
      {...props}
    >
      {children}
    </Card>
  );
}
