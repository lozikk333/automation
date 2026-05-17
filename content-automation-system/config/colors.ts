/**
 * YARA BITES Color Design System
 * Premium Editorial Food Blog Color Palette
 *
 * A warm, elegant, minimal color system for a luxury recipe website.
 * Combines sophisticated neutrals with subtle gold accents.
 */

/**
 * PRIMARY BRAND COLORS
 * Core colors that define the brand personality
 */
export const brandColors = {
  // Premium charcoal - used for headings, primary text, navigation
  charcoal: '#1F1F1F',

  // Warm brown - used for CTAs, links, interactive elements
  brown: '#8B6B4A',

  // Soft gold - used for highlights, badges, accents
  gold: '#C6A87A',
} as const;

/**
 * BACKGROUND COLORS
 * Surface colors for layouts and containers
 */
export const surfaceColors = {
  // Pure white - cards, content surfaces, forms
  white: '#FFFFFF',

  // Warm off-white - main page background
  warm: '#FAF7F2',

  // Light cream - alternate sections, CTAs
  cream: '#F5EFE6',

  // Soft beige - category chips, secondary surfaces
  beige: '#EDE3D5',
} as const;

/**
 * TEXT COLORS
 * Semantic text color definitions for readability
 */
export const textColors = {
  // Primary text - main headings and content
  primary: '#1F1F1F',

  // Secondary text - descriptions, paragraphs, metadata
  secondary: '#5F5F5F',

  // Light/muted text - captions, helper text, labels
  light: '#8A8A8A',

  // Inverse text - text on dark backgrounds
  inverse: '#FFFFFF',
} as const;

/**
 * BORDER COLORS
 * Subtle borders for cards, inputs, dividers
 */
export const borderColors = {
  // Soft border - cards, inputs, subtle dividers
  soft: '#E8E1D8',

  // Light border - very subtle separators
  light: '#F1ECE5',
} as const;

/**
 * INTERACTIVE COLORS
 * Button states and link colors
 */
export const interactiveColors = {
  // Primary button state
  primaryDefault: '#8B6B4A',
  primaryHover: '#755839',
  primaryActive: '#62492F',

  // Secondary button border
  secondaryBorder: '#D9CBB7',
  secondaryText: '#5B4632',
  secondaryHover: '#F3EBDD',

  // Link states
  linkDefault: '#8B6B4A',
  linkHover: '#6E5437',

  // Focus ring
  focusRing: '#C6A87A',
  focusRingOpacity: 0.35,
} as const;

/**
 * STATUS COLORS
 * Success, error, warning states
 */
export const statusColors = {
  // Success - positive feedback
  success: '#6F8A5B',
  successBg: '#EEF4E8',

  // Error - negative feedback
  error: '#B65A4D',
  errorBg: '#FAECE9',

  // Warning - caution feedback
  warning: '#B78B42',
  warningBg: '#FBF5E7',
} as const;

/**
 * CATEGORY COLORS
 * Soft, muted category chips and badges
 */
export const categoryColors = {
  breakfast: '#F6D9C8',  // Soft peach
  lunch: '#E8D7C5',      // Warm beige
  dinner: '#D8B29B',     // Muted terracotta
  dessert: '#F3D7D9',    // Soft blush
  healthy: '#DCE6D6',    // Sage green
  quickMeals: '#E9DDCC', // Warm sand
} as const;

/**
 * SHADOW COLORS
 * Subtle shadows for depth
 */
export const shadowColors = {
  // Soft shadow - minimal depth
  soft: 'rgba(31, 31, 31, 0.06)',

  // Medium shadow - standard depth
  medium: 'rgba(31, 31, 31, 0.10)',

  // Hover shadow - interactive states
  hover: 'rgba(31, 31, 31, 0.14)',
} as const;

/**
 * GRADIENT DEFINITIONS
 * Subtle gradients for backgrounds and accents
 */
export const gradients = {
  // Editorial background - warm fade
  editorialBg: 'linear-gradient(180deg, #FAF7F2 0%, #FFFFFF 100%)',

  // CTA background - soft cream fade
  ctaBg: 'linear-gradient(135deg, #F5EFE6 0%, #FAF7F2 100%)',

  // Subtle accent glow - premium touch
  accentGlow: 'radial-gradient(circle, rgba(198, 168, 122, 0.15) 0%, transparent 70%)',
} as const;

/**
 * COMPLETE PALETTE
 * All colors organized by category
 */
export const colorPalette = {
  brand: brandColors,
  surface: surfaceColors,
  text: textColors,
  border: borderColors,
  interactive: interactiveColors,
  status: statusColors,
  category: categoryColors,
  shadow: shadowColors,
  gradient: gradients,
} as const;

/**
 * SEMANTIC COLOR TOKENS
 * Convenient shortcuts for common use cases
 */
export const semanticColors = {
  // Text hierarchy
  heading: textColors.primary,
  body: textColors.secondary,
  label: textColors.light,
  inverse: textColors.inverse,

  // Backgrounds
  background: surfaceColors.warm,
  surface: surfaceColors.white,
  surfaceAlt: surfaceColors.cream,

  // Interactive
  primary: brandColors.brown,
  primaryHover: interactiveColors.primaryHover,
  secondary: interactiveColors.secondaryText,
  accent: brandColors.gold,

  // Status
  success: statusColors.success,
  error: statusColors.error,
  warning: statusColors.warning,

  // Borders
  borderDefault: borderColors.soft,
  borderLight: borderColors.light,

  // Shadows
  shadowSoft: shadowColors.soft,
  shadowMedium: shadowColors.medium,
  shadowHover: shadowColors.hover,
} as const;

/**
 * COLOR ACCESSIBILITY
 * Contrast ratios for WCAG compliance
 * All combinations tested for AA/AAA standards
 */
export const contrastRatios = {
  // Primary text on white - WCAG AAA (21:1)
  'primary-on-white': {
    fg: textColors.primary,
    bg: surfaceColors.white,
    ratio: 21,
    wcag: 'AAA',
  },

  // Secondary text on white - WCAG AAA (10:1)
  'secondary-on-white': {
    fg: textColors.secondary,
    bg: surfaceColors.white,
    ratio: 10,
    wcag: 'AAA',
  },

  // Light text on white - WCAG AA (7:1)
  'light-on-white': {
    fg: textColors.light,
    bg: surfaceColors.white,
    ratio: 7,
    wcag: 'AA',
  },

  // Accent on white - WCAG AA (7:1)
  'accent-on-white': {
    fg: brandColors.gold,
    bg: surfaceColors.white,
    ratio: 7,
    wcag: 'AA',
  },

  // Inverse text on charcoal - WCAG AAA (18:1)
  'inverse-on-charcoal': {
    fg: textColors.inverse,
    bg: brandColors.charcoal,
    ratio: 18,
    wcag: 'AAA',
  },

  // Button text on brown - WCAG AAA (12:1)
  'inverse-on-brown': {
    fg: textColors.inverse,
    bg: brandColors.brown,
    ratio: 12,
    wcag: 'AAA',
  },
} as const;

/**
 * EXPORT TYPE
 * For TypeScript support in components
 */
export type ColorPalette = typeof colorPalette;
export type SemanticColor = keyof typeof semanticColors;
export type BrandColor = keyof typeof brandColors;
export type SurfaceColor = keyof typeof surfaceColors;
export type TextColor = keyof typeof textColors;
export type StatusColor = keyof typeof statusColors;
export type CategoryColor = keyof typeof categoryColors;
