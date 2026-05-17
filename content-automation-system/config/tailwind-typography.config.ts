/**
 * YARA BITES Tailwind Typography Configuration
 * Add this to your tailwind.config.ts theme extensions
 *
 * Usage in tailwind.config.ts:
 * import { typographyConfig } from '@/config/tailwind-typography.config'
 *
 * export default {
 *   theme: {
 *     extend: {
 *       ...typographyConfig
 *     }
 *   }
 * }
 */

export const typographyConfig = {
  fontFamily: {
    display: 'var(--font-display)',
    ui: 'var(--font-ui)',
  },

  fontSize: {
    // Display Scale
    'display-xl': [
      '72px',
      {
        lineHeight: '1.1',
        letterSpacing: '-0.02em',
        fontWeight: '700',
      },
    ],
    'display-lg': [
      '56px',
      {
        lineHeight: '1.15',
        letterSpacing: '-0.015em',
        fontWeight: '700',
      },
    ],
    'display-md': [
      '42px',
      {
        lineHeight: '1.2',
        letterSpacing: '-0.01em',
        fontWeight: '700',
      },
    ],

    // Heading Scale
    'heading-lg': [
      '30px',
      {
        lineHeight: '1.25',
        letterSpacing: '-0.005em',
        fontWeight: '600',
      },
    ],
    'heading-md': [
      '24px',
      {
        lineHeight: '1.3',
        letterSpacing: '0em',
        fontWeight: '700',
      },
    ],

    // Body Scale
    'body-lg': [
      '18px',
      {
        lineHeight: '1.7',
        letterSpacing: '0em',
        fontWeight: '400',
      },
    ],
    body: [
      '16px',
      {
        lineHeight: '1.65',
        letterSpacing: '0em',
        fontWeight: '400',
      },
    ],
    'body-sm': [
      '14px',
      {
        lineHeight: '1.5',
        letterSpacing: '0em',
        fontWeight: '400',
      },
    ],

    // Utility Scale
    label: [
      '12px',
      {
        lineHeight: '1.4',
        letterSpacing: '0.14em',
        fontWeight: '600',
        textTransform: 'uppercase',
      },
    ],
    button: [
      '16px',
      {
        lineHeight: '1',
        letterSpacing: '0.01em',
        fontWeight: '600',
      },
    ],
    navigation: [
      '16px',
      {
        lineHeight: '1.4',
        letterSpacing: '0em',
        fontWeight: '500',
      },
    ],
    meta: [
      '14px',
      {
        lineHeight: '1.5',
        letterSpacing: '0em',
        fontWeight: '500',
      },
    ],
  },

  textColor: {
    primary: '#1F1F1F',
    secondary: '#5F5F5F',
    light: '#8A8A8A',
    accent: '#8B6B4A',
    inverse: '#FFFFFF',
  },

  maxWidth: {
    prose: '65ch',
    hero: '700px',
    body: '720px',
    recipe: '500px',
    card: '40ch',
  },
};

/**
 * Responsive typography utility classes
 * These utilities handle responsive font size changes
 */
export const responsiveTypographyUtilities = {
  'display-xl': {
    fontSize: 'clamp(40px, 8vw, 72px)',
    lineHeight: '1.1',
    letterSpacing: '-0.02em',
    fontWeight: '700',
  },
  'display-lg': {
    fontSize: 'clamp(34px, 6.5vw, 56px)',
    lineHeight: '1.15',
    letterSpacing: '-0.015em',
    fontWeight: '700',
  },
  'display-md': {
    fontSize: 'clamp(28px, 5vw, 42px)',
    lineHeight: '1.2',
    letterSpacing: '-0.01em',
    fontWeight: '700',
  },
  'heading-lg': {
    fontSize: 'clamp(22px, 3.5vw, 30px)',
    lineHeight: '1.25',
    letterSpacing: '-0.005em',
    fontWeight: '600',
  },
  'heading-md': {
    fontSize: 'clamp(18px, 2.5vw, 24px)',
    lineHeight: '1.3',
    letterSpacing: '0em',
    fontWeight: '700',
  },
  'body-lg': {
    fontSize: 'clamp(16px, 1.2vw, 18px)',
    lineHeight: '1.7',
    letterSpacing: '0em',
    fontWeight: '400',
  },
  body: {
    fontSize: 'clamp(15px, 1vw, 16px)',
    lineHeight: '1.65',
    letterSpacing: '0em',
    fontWeight: '400',
  },
  'body-sm': {
    fontSize: 'clamp(13px, 0.9vw, 14px)',
    lineHeight: '1.5',
    letterSpacing: '0em',
    fontWeight: '400',
  },
};
