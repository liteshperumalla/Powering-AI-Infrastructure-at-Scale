# Infra-Mind Brand Design Guide

**Version:** 1.0
**Last Updated:** November 12, 2025
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Brand Overview](#brand-overview)
2. [Logo & Identity](#logo--identity)
3. [Color Palette](#color-palette)
4. [Typography](#typography)
5. [Visual Design System](#visual-design-system)
6. [Component Styles](#component-styles)
7. [Animations & Micro-Interactions](#animations--micro-interactions)
8. [Usage Guidelines](#usage-guidelines)
9. [Implementation Guide](#implementation-guide)

---

## 1. Brand Overview

### Brand Identity

**Infra-Mind** is an AI-powered infrastructure assessment platform that combines enterprise-grade reliability with cutting-edge artificial intelligence.

### Design Philosophy

Our brand visual language reflects:

- **🤖 AI-Forward:** Futuristic, gradient-rich aesthetics that signal advanced technology
- **💼 Professional:** Enterprise-grade visual language that builds trust
- **✨ Modern:** Contemporary design with glassmorphism, depth, and micro-animations
- **♿ Accessible:** WCAG 2.1 AA compliant with excellent contrast ratios

### Brand Personality

| Attribute | Description |
|-----------|-------------|
| **Intelligent** | Showcases AI capabilities through smart, adaptive interfaces |
| **Trustworthy** | Clean, professional design inspires confidence |
| **Innovative** | Modern visual effects demonstrate cutting-edge technology |
| **Powerful** | Bold colors and gradients convey capability and scale |

---

## 2. Logo & Identity

### Logo Concept

The Infra-Mind logo combines two powerful metaphors:

1. **Hexagon:** Represents infrastructure, stability, and interconnected systems
2. **Neural Network:** Symbolizes AI intelligence with connected nodes

### Logo Variants

#### Primary Logo (Full Horizontal)
- **File:** `infra-mind-logo.svg` (Light mode)
- **File:** `infra-mind-logo-dark.svg` (Dark mode)
- **Dimensions:** 180×48px
- **Usage:** Headers, marketing materials, documentation

#### Icon Only
- **File:** `infra-mind-icon.svg`
- **Dimensions:** 48×48px
- **Usage:** Favicon, app icons, social media profiles

### Logo Anatomy

```
┌─────────┬──────────────────────┐
│  ICON   │   INFRA + MIND       │  ← Wordmark
│ Hexagon │   AI-POWERED         │  ← Tagline
│ + Nodes │   INFRASTRUCTURE     │
└─────────┴──────────────────────┘
```

### Logo Clear Space

Maintain a minimum clear space equal to the height of the "I" in "Infra" on all sides.

```
    [X]
[X] LOGO [X]
    [X]
```

### Logo Don'ts

❌ Do not rotate the logo
❌ Do not apply filters or effects
❌ Do not change colors outside brand palette
❌ Do not stretch or distort
❌ Do not place on busy backgrounds without backdrop
❌ Do not use old logo variants

---

## 3. Color Palette

### Primary Colors

#### Electric Blue
The cornerstone of our brand, representing innovation and intelligence.

```
Primary 50:  #E6F0FF  (230, 240, 255)
Primary 100: #CCE0FF  (204, 224, 255)
Primary 200: #99C2FF  (153, 194, 255)
Primary 300: #66A3FF  (102, 163, 255)
Primary 400: #3385FF  (51, 133, 255)
Primary 500: #0066FF  (0, 102, 255)    ← Main
Primary 600: #0052CC  (0, 82, 204)
Primary 700: #003D99  (0, 61, 153)
Primary 800: #002966  (0, 41, 102)
Primary 900: #001433  (0, 20, 51)
```

**Usage:** Primary CTAs, links, interactive elements, brand moments

**Accessibility:**
- Primary 500 on white: 4.59:1 (AA)
- Primary 600 on white: 6.35:1 (AAA)
- Primary 400 on dark: 8.12:1 (AAA)

#### Cyber Purple
Premium secondary color representing AI technology.

```
Secondary 50:  #F5F3FF  (245, 243, 255)
Secondary 100: #EDE9FE  (237, 233, 254)
Secondary 200: #DDD6FE  (221, 214, 254)
Secondary 300: #C4B5FD  (196, 181, 253)
Secondary 400: #A78BFA  (167, 139, 250)
Secondary 500: #7C3AED  (124, 58, 237)   ← Main
Secondary 600: #6D28D9  (109, 40, 217)
Secondary 700: #5B21B6  (91, 33, 182)
Secondary 800: #4C1D95  (76, 29, 149)
Secondary 900: #2E1065  (46, 16, 101)
```

**Usage:** Secondary CTAs, accents, premium features, gradients

### Accent Colors

#### Neon Cyan
Energy and highlight color for emphasis.

```
Accent 500: #00D9FF  (0, 217, 255)
```

**Usage:** Highlights, progress indicators, success states, energy moments

### Semantic Colors

#### Success - Emerald Green
```
Success 500: #10B981  (16, 185, 129)
```
**Usage:** Success messages, completion states, positive metrics

#### Warning - Amber
```
Warning 500: #F59E0B  (245, 158, 11)
```
**Usage:** Warnings, attention states, performance alerts

#### Error - Ruby Red
```
Error 500: #EF4444  (239, 68, 68)
```
**Usage:** Error messages, critical states, destructive actions

### Neutral Colors

```
Neutral 50:  #F9FAFB  (249, 250, 251)
Neutral 100: #F3F4F6  (243, 244, 246)
Neutral 200: #E5E7EB  (229, 231, 235)
Neutral 300: #D1D5DB  (209, 213, 219)
Neutral 400: #9CA3AF  (156, 163, 175)
Neutral 500: #6B7280  (107, 114, 128)
Neutral 600: #4B5563  (75, 85, 99)
Neutral 700: #374151  (55, 65, 81)
Neutral 800: #1F2937  (31, 41, 55)
Neutral 900: #111827  (17, 24, 39)
Neutral 950: #0A0F1A  (10, 15, 26)
```

**Usage:** Text, backgrounds, borders, shadows

### Gradient Combinations

#### Primary Gradient (Default)
```css
linear-gradient(135deg, #0066FF 0%, #0052CC 100%)
```

#### Hero Gradient
```css
linear-gradient(135deg, #0066FF 0%, #7C3AED 50%, #00D9FF 100%)
```

#### Secondary Gradient
```css
linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)
```

#### Accent Gradient
```css
linear-gradient(90deg, #0066FF 0%, #00D9FF 100%)
```

#### AppBar Gradient (Light Mode)
```css
linear-gradient(135deg, #0066FF 0%, #0052CC 50%, #7C3AED 100%)
```

---

## 4. Typography

### Font Family

**Primary:** Inter
**Fallbacks:** -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif

### Why Inter?

- Excellent screen readability
- Professional, modern aesthetic
- Comprehensive character set
- Open source and web-optimized
- Variable font support for performance

### Type Scale

| Element | Size | Weight | Line Height | Letter Spacing | Use Case |
|---------|------|--------|-------------|----------------|----------|
| H1 | 3rem (48px) | 700 Bold | 1.2 | -0.02em | Hero headlines |
| H2 | 2.25rem (36px) | 700 Bold | 1.3 | -0.01em | Section titles |
| H3 | 1.875rem (30px) | 600 Semibold | 1.4 | -0.01em | Subsections |
| H4 | 1.5rem (24px) | 600 Semibold | 1.5 | 0 | Cards, modules |
| H5 | 1.25rem (20px) | 600 Semibold | 1.6 | 0 | Tertiary headers |
| H6 | 1rem (16px) | 600 Semibold | 1.6 | 0 | Small headers |
| Body 1 | 1rem (16px) | 400 Regular | 1.5 | 0 | Primary body text |
| Body 2 | 0.875rem (14px) | 400 Regular | 1.57 | 0 | Secondary text |
| Button | 0.875rem (14px) | 600 Semibold | 1.75 | 0.02em | Buttons, CTAs |
| Caption | 0.75rem (12px) | 400 Regular | 1.66 | 0 | Metadata, labels |
| Overline | 0.75rem (12px) | 600 Semibold | 2.66 | 0.08em | Category labels |

### Text Colors

#### Light Mode
- Primary: `#111827` (Neutral 900)
- Secondary: `#4B5563` (Neutral 600)
- Disabled: `#9CA3AF` (Neutral 400)

#### Dark Mode
- Primary: `#FFFFFF`
- Secondary: `#D1D5DB` (Neutral 300)
- Disabled: `#6B7280` (Neutral 500)

### Gradient Text

For special emphasis (hero headlines, CTAs):

```css
background: linear-gradient(135deg, #0066FF 0%, #7C3AED 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

---

## 5. Visual Design System

### Shadows

#### Light Mode
```css
/* Elevation 1 (Cards, low elevation) */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

/* Elevation 2 (Elevated cards, menus) */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

/* Elevation 3 (Modals, dialogs) */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);

/* Elevation 4 (Floating action buttons) */
box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16);
```

#### Dark Mode
```css
/* Elevation 1 */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);

/* Elevation 2 */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);

/* Elevation 3 */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);

/* Elevation 4 */
box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7);
```

### Border Radius

| Element | Radius | Usage |
|---------|--------|-------|
| Buttons | 10px | Interactive elements |
| Cards | 16px | Content containers |
| Inputs | 10px | Form fields |
| Chips | 20px | Tags, status badges |
| Dialogs | 20px | Modal windows |
| Tooltips | 8px | Floating hints |

### Spacing

Based on 8px grid system:

```
4px  = 0.5 unit
8px  = 1 unit
12px = 1.5 units
16px = 2 units
24px = 3 units
32px = 4 units
48px = 6 units
64px = 8 units
96px = 12 units
```

---

## 6. Component Styles

### Buttons

#### Primary Button
```css
/* Gradient background */
background: linear-gradient(135deg, #0066FF 0%, #0052CC 100%);
color: #FFFFFF;
padding: 10px 24px;
border-radius: 10px;
font-weight: 600;
box-shadow: 0 4px 14px rgba(0, 102, 255, 0.4);

/* Hover */
background: linear-gradient(135deg, #0052CC 0%, #003D99 100%);
transform: translateY(-2px);
box-shadow: 0 6px 20px rgba(0, 102, 255, 0.5);

/* Active */
transform: translateY(0px);
```

#### Secondary Button
```css
border: 2px solid #0066FF;
color: #0066FF;
background: transparent;

/* Hover */
background: rgba(0, 102, 255, 0.04);
```

#### Text Button
```css
color: #0066FF;
background: transparent;

/* Hover */
background: rgba(0, 102, 255, 0.04);
```

### Cards

#### Glass Card
```css
background: rgba(255, 255, 255, 0.9);  /* Light mode */
background: rgba(17, 24, 39, 0.95);    /* Dark mode */
backdrop-filter: blur(20px) saturate(180%);
border: 1px solid rgba(255, 255, 255, 0.12);  /* Dark mode */
border-radius: 16px;
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),    /* Dark mode */
            inset 0 0 0 1px rgba(255, 255, 255, 0.05);

/* Hover */
transform: translateY(-8px) scale(1.02);
box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);   /* Dark mode */
border: 1px solid rgba(0, 102, 255, 0.3);
```

### Inputs

#### Text Field
```css
background: rgba(156, 163, 175, 0.5);  /* Light mode */
background: rgba(31, 41, 55, 0.5);     /* Dark mode */
backdrop-filter: blur(10px);
border: 1.5px solid rgba(255, 255, 255, 0.1);
border-radius: 10px;

/* Focus */
border: 2px solid #0066FF;
box-shadow: 0 0 0 4px rgba(0, 102, 255, 0.1);
background: rgba(31, 41, 55, 0.7);     /* Dark mode */
```

### Progress Indicators

#### Linear Progress
```css
height: 6px;
border-radius: 3px;
background: rgba(107, 114, 128, 0.3);

/* Bar */
background: linear-gradient(90deg, #0066FF 0%, #00D9FF 100%);
border-radius: 3px;
```

### Chips

#### Status Chip
```css
border-radius: 20px;
padding: 6px 12px;
font-weight: 600;
font-size: 0.8125rem;
backdrop-filter: blur(10px);

/* Success */
background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
color: #10B981;
border: 1px solid rgba(16, 185, 129, 0.3);

/* Error */
background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
color: #EF4444;
border: 1px solid rgba(239, 68, 68, 0.3);

/* Warning */
background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%);
color: #F59E0B;
border: 1px solid rgba(245, 158, 11, 0.3);
```

---

## 7. Animations & Micro-Interactions

### Animation Principles

1. **Purposeful:** Every animation serves a functional purpose
2. **Performant:** GPU-accelerated, smooth 60fps
3. **Subtle:** Enhance UX without distraction
4. **Consistent:** Same timing across similar interactions

### Timing Functions

```css
/* Fast - Micro-interactions */
cubic-bezier(0.4, 0, 0.2, 1)  /* 150ms */

/* Standard - Most UI elements */
cubic-bezier(0.4, 0, 0.2, 1)  /* 300ms */

/* Slow - Page-level changes */
cubic-bezier(0.4, 0, 0.2, 1)  /* 500ms */

/* Elastic - Emphasis */
cubic-bezier(0.68, -0.55, 0.265, 1.55)  /* 500ms */
```

### Entrance Animations

#### Fade In Up
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) backwards;
```

#### Scale In
```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Hover States

#### Lift
```css
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

&:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}
```

#### Scale
```css
transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);

&:hover {
  transform: scale(1.05);
}
```

#### Glow
```css
transition: box-shadow 0.3s ease;

&:hover {
  box-shadow: 0 0 20px rgba(0, 102, 255, 0.4);
}
```

### Loading States

#### Shimmer (Skeleton)
```css
@keyframes shimmer {
  0% {
    background-position: -100% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

background: linear-gradient(90deg, #E5E7EB 0%, #F3F4F6 50%, #E5E7EB 100%);
background-size: 200% 100%;
animation: shimmer 1.5s ease-in-out infinite;
```

#### Pulse
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

animation: pulse 2s ease-in-out infinite;
```

---

## 8. Usage Guidelines

### Do's ✅

- **Use gradients strategically** on CTAs and hero sections
- **Maintain consistent spacing** using 8px grid system
- **Apply glassmorphism** to cards and overlays for depth
- **Use animations subtly** to enhance, not distract
- **Follow accessibility standards** (WCAG 2.1 AA minimum)
- **Test in both light and dark modes**
- **Use semantic colors appropriately** (success, error, warning)

### Don'ts ❌

- **Don't overuse gradients** - reserve for emphasis
- **Don't create custom colors** outside the palette
- **Don't animate everything** - only meaningful interactions
- **Don't use low-contrast colors** for text
- **Don't ignore dark mode** - design for both
- **Don't mix different animation timings** for similar interactions
- **Don't use Comic Sans** (please, just don't)

### Accessibility Checklist

- [ ] Color contrast ratio ≥ 4.5:1 for normal text
- [ ] Color contrast ratio ≥ 3:1 for large text (18pt+)
- [ ] All interactive elements have focus states
- [ ] Animations respect `prefers-reduced-motion`
- [ ] Text is readable at 200% zoom
- [ ] Icons have ARIA labels or text alternatives
- [ ] Touch targets are minimum 44×44px

---

## 9. Implementation Guide

### Setup Enhanced Theme

```tsx
// src/app/layout.tsx
import { createEnhancedTheme } from '@/theme/enhanced-theme';
import { ThemeProvider } from '@mui/material/styles';

const theme = createEnhancedTheme('light');

export default function RootLayout({ children }) {
  return (
    <ThemeProvider theme={theme}>
      {children}
    </ThemeProvider>
  );
}
```

### Using Brand Colors

```tsx
import { brandColors } from '@/theme/enhanced-theme';

// In component
<Box sx={{
  color: brandColors.primary[500],
  backgroundColor: brandColors.neutral[50],
}} />
```

### Using Animations

```tsx
import { fadeInUp, hoverEffects } from '@/utils/animations';

<Box sx={{
  animation: `${fadeInUp} 0.6s ease-out`,
  ...hoverEffects.lift,
}} />
```

### Using GlassCard

```tsx
import GlassCard from '@/components/GlassCard';

<GlassCard blur={30} opacity={0.15} hoverable>
  <CardContent>
    Your content here
  </CardContent>
</GlassCard>
```

### Creating Gradient Text

```tsx
import { gradientText } from '@/utils/animations';

<Typography sx={gradientText('linear-gradient(135deg, #0066FF 0%, #7C3AED 100%)')}>
  Gradient Headline
</Typography>
```

### Implementing Dark Mode

```tsx
import { enhancedDarkTheme } from '@/theme/enhanced-theme';

const theme = mode === 'dark' ? enhancedDarkTheme : enhancedLightTheme;
```

---

## Appendix A: File Structure

```
frontend-react/
├── public/
│   ├── infra-mind-logo.svg         # Primary logo (light)
│   ├── infra-mind-logo-dark.svg    # Primary logo (dark)
│   └── infra-mind-icon.svg         # Icon only
├── src/
│   ├── theme/
│   │   ├── enhanced-theme.ts       # Enhanced Material-UI theme
│   │   ├── themes.ts               # Original themes (legacy)
│   │   └── theme.ts                # Theme exports
│   ├── utils/
│   │   └── animations.ts           # Animation utilities
│   └── components/
│       ├── GlassCard.tsx           # Glassmorphism card
│       ├── Breadcrumbs.tsx         # Navigation breadcrumbs
│       └── skeletons/
│           ├── AssessmentCardSkeleton.tsx
│           └── ChartSkeleton.tsx
```

---

## Appendix B: Quick Reference

### Color Codes
- Primary: `#0066FF`
- Secondary: `#7C3AED`
- Accent: `#00D9FF`
- Success: `#10B981`
- Warning: `#F59E0B`
- Error: `#EF4444`

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

### Border Radius
- Small: 8px
- Medium: 12px
- Large: 16px
- XL: 20px

### Animation Durations
- Fast: 150ms
- Standard: 300ms
- Slow: 500ms

---

## Changelog

### Version 1.0 (November 12, 2025)
- ✅ Initial brand design guide
- ✅ Logo design and variants
- ✅ Enhanced color palette
- ✅ Typography system
- ✅ Component library
- ✅ Animation utilities
- ✅ Implementation guide

---

**Maintained by:** Design Team
**Contact:** design@infra-mind.com
**Last Review:** November 12, 2025
**Next Review:** December 12, 2025

---

*"Design is not just what it looks like and feels like. Design is how it works." - Steve Jobs*
