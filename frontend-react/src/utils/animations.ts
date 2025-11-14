/**
 * Animation Utilities for Infra-Mind
 *
 * Modern CSS animations and transitions using Material-UI and vanilla CSS
 * Focus on performant, GPU-accelerated animations
 */

import { keyframes } from '@mui/system';

// ===== ENTRANCE ANIMATIONS =====

export const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

export const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const fadeInDown = keyframes`
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const fadeInLeft = keyframes`
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

export const fadeInRight = keyframes`
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
`;

export const scaleIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

export const bounceIn = keyframes`
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
`;

// ===== CONTINUOUS ANIMATIONS =====

export const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
`;

export const shimmer = keyframes`
  0% {
    background-position: -100% 0;
  }
  100% {
    background-position: 200% 0;
  }
`;

export const float = keyframes`
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
`;

export const rotate = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

export const glow = keyframes`
  0%, 100% {
    box-shadow: 0 0 10px rgba(0, 102, 255, 0.3),
                0 0 20px rgba(0, 102, 255, 0.2),
                0 0 30px rgba(0, 102, 255, 0.1);
  }
  50% {
    box-shadow: 0 0 20px rgba(0, 102, 255, 0.5),
                0 0 40px rgba(0, 102, 255, 0.3),
                0 0 60px rgba(0, 102, 255, 0.2);
  }
`;

export const gradientShift = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

// ===== LOADING ANIMATIONS =====

export const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

export const bounce = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
`;

export const wave = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  25% {
    transform: translateY(-10px);
  }
  75% {
    transform: translateY(10px);
  }
`;

// ===== ATTENTION SEEKERS =====

export const shake = keyframes`
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-5px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(5px);
  }
`;

export const wobble = keyframes`
  0%, 100% {
    transform: translateX(0) rotate(0deg);
  }
  15% {
    transform: translateX(-10px) rotate(-5deg);
  }
  30% {
    transform: translateX(10px) rotate(3deg);
  }
  45% {
    transform: translateX(-10px) rotate(-3deg);
  }
  60% {
    transform: translateX(10px) rotate(2deg);
  }
  75% {
    transform: translateX(-5px) rotate(-1deg);
  }
`;

export const heartbeat = keyframes`
  0%, 100% {
    transform: scale(1);
  }
  10%, 30% {
    transform: scale(1.1);
  }
  20%, 40% {
    transform: scale(1);
  }
`;

// ===== UTILITY FUNCTIONS =====

/**
 * Get animation CSS string for sx prop
 * @param animation - Keyframe animation
 * @param duration - Duration in seconds (default: 0.3)
 * @param timing - Timing function (default: 'ease-in-out')
 * @param delay - Delay in seconds (default: 0)
 * @param count - Iteration count (default: 1, or 'infinite')
 */
export const getAnimation = (
  animation: any,
  duration: number = 0.3,
  timing: string = 'ease-in-out',
  delay: number = 0,
  count: number | 'infinite' = 1
) => `${animation} ${duration}s ${timing} ${delay}s ${count}`;

/**
 * Transition presets for common use cases
 */
export const transitions = {
  // Fast transitions for micro-interactions
  fast: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',

  // Standard transitions for most UI elements
  standard: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',

  // Slow transitions for page-level changes
  slow: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',

  // Smooth elastic bounce
  elastic: 'all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',

  // Sharp in/out for emphasis
  sharp: 'all 0.2s cubic-bezier(0.4, 0, 0.6, 1)',

  // Smooth ease
  smooth: 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
};

/**
 * Hover effects as sx prop objects
 */
export const hoverEffects = {
  lift: {
    transition: transitions.standard,
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
    },
  },

  scale: {
    transition: transitions.standard,
    '&:hover': {
      transform: 'scale(1.05)',
    },
  },

  glow: {
    transition: transitions.standard,
    '&:hover': {
      boxShadow: '0 0 20px rgba(0, 102, 255, 0.4)',
    },
  },

  shine: {
    position: 'relative',
    overflow: 'hidden',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: '-100%',
      width: '100%',
      height: '100%',
      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
      transition: transitions.standard,
    },
    '&:hover::before': {
      left: '100%',
    },
  },

  tilt: {
    transition: transitions.smooth,
    '&:hover': {
      transform: 'perspective(1000px) rotateX(5deg) rotateY(5deg)',
    },
  },
};

/**
 * Stagger delay calculator for list animations
 * @param index - Item index
 * @param baseDelay - Base delay in seconds (default: 0.1)
 */
export const staggerDelay = (index: number, baseDelay: number = 0.1) => index * baseDelay;

/**
 * CSS for glassmorphism effect
 */
export const glassmorphism = (opacity: number = 0.1) => ({
  background: `rgba(255, 255, 255, ${opacity})`,
  backdropFilter: 'blur(20px) saturate(180%)',
  WebkitBackdropFilter: 'blur(20px) saturate(180%)',
  border: '1px solid rgba(255, 255, 255, 0.18)',
});

/**
 * CSS for gradient text
 */
export const gradientText = (gradient: string = 'linear-gradient(135deg, #0066FF 0%, #7C3AED 100%)') => ({
  background: gradient,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
});

export default {
  fadeIn,
  fadeInUp,
  fadeInDown,
  fadeInLeft,
  fadeInRight,
  scaleIn,
  bounceIn,
  pulse,
  shimmer,
  float,
  rotate,
  glow,
  gradientShift,
  spin,
  bounce,
  wave,
  shake,
  wobble,
  heartbeat,
  getAnimation,
  transitions,
  hoverEffects,
  staggerDelay,
  glassmorphism,
  gradientText,
};
