/**
 * YARA BITES Typography Scale
 * Premium Editorial Food Blog Typography System
 *
 * This file defines the complete typography scale with:
 * - Font sizes (desktop, tablet, mobile)
 * - Font weights
 * - Line heights
 * - Letter spacing
 * - Usage guidelines
 */

export const typographyScale = {
  /**
   * DISPLAY XL
   * Usage: Hero headline, main page titles
   * Characteristics: Bold, luxurious, high impact
   */
  displayXL: {
    desktop: {
      fontSize: '72px',
      lineHeight: '1.1',
      letterSpacing: '-0.02em',
      fontWeight: '700',
    },
    tablet: {
      fontSize: '56px',
      lineHeight: '1.1',
      letterSpacing: '-0.02em',
      fontWeight: '700',
    },
    mobile: {
      fontSize: '40px',
      lineHeight: '1.1',
      letterSpacing: '-0.02em',
      fontWeight: '700',
    },
    usage: 'Hero headline, main page titles',
    fontFamily: 'var(--font-display)',
  },

  /**
   * DISPLAY LARGE
   * Usage: Major section headings, feature headlines
   * Characteristics: Elegant, sophisticated
   */
  displayLarge: {
    desktop: {
      fontSize: '56px',
      lineHeight: '1.15',
      letterSpacing: '-0.015em',
      fontWeight: '700',
    },
    tablet: {
      fontSize: '44px',
      lineHeight: '1.15',
      letterSpacing: '-0.015em',
      fontWeight: '700',
    },
    mobile: {
      fontSize: '34px',
      lineHeight: '1.15',
      letterSpacing: '-0.015em',
      fontWeight: '700',
    },
    usage: 'Major section headings, feature headlines',
    fontFamily: 'var(--font-display)',
  },

  /**
   * DISPLAY MEDIUM
   * Usage: Subsection headings, feature blocks
   * Characteristics: Strong editorial presence
   */
  displayMedium: {
    desktop: {
      fontSize: '42px',
      lineHeight: '1.2',
      letterSpacing: '-0.01em',
      fontWeight: '700',
    },
    tablet: {
      fontSize: '34px',
      lineHeight: '1.2',
      letterSpacing: '-0.01em',
      fontWeight: '600',
    },
    mobile: {
      fontSize: '28px',
      lineHeight: '1.2',
      letterSpacing: '-0.01em',
      fontWeight: '600',
    },
    usage: 'Subsection headings, feature blocks',
    fontFamily: 'var(--font-display)',
  },

  /**
   * HEADING LARGE
   * Usage: Recipe titles, article headings, card titles
   * Characteristics: Premium recipe focus
   */
  headingLarge: {
    desktop: {
      fontSize: '30px',
      lineHeight: '1.25',
      letterSpacing: '-0.005em',
      fontWeight: '600',
    },
    tablet: {
      fontSize: '26px',
      lineHeight: '1.25',
      letterSpacing: '-0.005em',
      fontWeight: '600',
    },
    mobile: {
      fontSize: '22px',
      lineHeight: '1.25',
      letterSpacing: '-0.005em',
      fontWeight: '600',
    },
    usage: 'Recipe titles, article headings, card titles',
    fontFamily: 'var(--font-display)',
  },

  /**
   * HEADING MEDIUM
   * Usage: Card headings, feature blocks, subsection titles
   * Characteristics: Clean, modern hierarchy
   */
  headingMedium: {
    desktop: {
      fontSize: '24px',
      lineHeight: '1.3',
      letterSpacing: '0em',
      fontWeight: '700',
    },
    tablet: {
      fontSize: '20px',
      lineHeight: '1.3',
      letterSpacing: '0em',
      fontWeight: '700',
    },
    mobile: {
      fontSize: '18px',
      lineHeight: '1.3',
      letterSpacing: '0em',
      fontWeight: '700',
    },
    usage: 'Card headings, feature blocks, subsection titles',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * BODY LARGE
   * Usage: Lead paragraphs, hero descriptions, author intro text
   * Characteristics: Premium, elevated, warm
   */
  bodyLarge: {
    desktop: {
      fontSize: '18px',
      lineHeight: '1.7',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    tablet: {
      fontSize: '17px',
      lineHeight: '1.7',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    mobile: {
      fontSize: '16px',
      lineHeight: '1.7',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    usage: 'Lead paragraphs, hero descriptions, author intro',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * BODY DEFAULT
   * Usage: Standard content, recipe descriptions, newsletter text
   * Characteristics: Highly readable, comfortable
   */
  bodyDefault: {
    desktop: {
      fontSize: '16px',
      lineHeight: '1.65',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    tablet: {
      fontSize: '16px',
      lineHeight: '1.65',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    mobile: {
      fontSize: '15px',
      lineHeight: '1.65',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    usage: 'Standard content, recipe descriptions, newsletter text',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * BODY SMALL
   * Usage: Metadata, supporting text, captions, timestamps
   * Characteristics: Subtle, readable
   */
  bodySmall: {
    desktop: {
      fontSize: '14px',
      lineHeight: '1.5',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    mobile: {
      fontSize: '13px',
      lineHeight: '1.5',
      letterSpacing: '0em',
      fontWeight: '400',
    },
    usage: 'Metadata, supporting text, captions',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * LABEL / MICRO TEXT
   * Usage: Category labels, eyebrow text, section tags, badges
   * Characteristics: Uppercase, tracked, subtle
   */
  label: {
    desktop: {
      fontSize: '12px',
      lineHeight: '1.4',
      letterSpacing: '0.14em',
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    mobile: {
      fontSize: '11px',
      lineHeight: '1.4',
      letterSpacing: '0.14em',
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    usage: 'Category labels, eyebrow text, badges',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * BUTTON TEXT
   * Usage: CTA buttons, navigation actions
   * Characteristics: Bold, actionable
   */
  button: {
    desktop: {
      fontSize: '16px',
      lineHeight: '1',
      letterSpacing: '0.01em',
      fontWeight: '600',
    },
    mobile: {
      fontSize: '15px',
      lineHeight: '1',
      letterSpacing: '0.01em',
      fontWeight: '600',
    },
    usage: 'CTA buttons, navigation actions',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * NAVIGATION TEXT
   * Usage: Navbar menu items, footer links
   * Characteristics: Modern, navigable
   */
  navigation: {
    desktop: {
      fontSize: '16px',
      lineHeight: '1.4',
      letterSpacing: '0em',
      fontWeight: '500',
    },
    usage: 'Navbar menu items, footer links',
    fontFamily: 'var(--font-ui)',
  },

  /**
   * RECIPE META TEXT
   * Usage: Prep time, servings, difficulty, recipe metadata
   * Characteristics: Subtle, informative
   */
  recipeMeta: {
    desktop: {
      fontSize: '14px',
      lineHeight: '1.5',
      letterSpacing: '0em',
      fontWeight: '500',
    },
    mobile: {
      fontSize: '13px',
      lineHeight: '1.5',
      letterSpacing: '0em',
      fontWeight: '500',
    },
    usage: 'Prep time, servings, difficulty',
    fontFamily: 'var(--font-ui)',
  },
};

/**
 * Color Palette for Typography
 * Premium, warm, editorial aesthetic
 */
export const typographyColors = {
  // Primary text - main content
  primary: '#1F1F1F', // Dark charcoal
  
  // Secondary text - supporting content
  secondary: '#5F5F5F', // Muted dark gray
  
  // Light/tertiary text - subtle content
  light: '#8A8A8A', // Light gray
  
  // Accent text - highlighted content
  accent: '#8B6B4A', // Warm brown / muted gold
  
  // Inverse text - on dark backgrounds
  inverse: '#FFFFFF', // White
};

/**
 * Maximum line lengths for optimal readability
 */
export const readabilityConstraints = {
  paragraph: '65ch', // Standard paragraph max width
  hero: '700px', // Hero content max width
  body: '720px', // Body content max width
  recipe: '500px', // Recipe descriptions max width
  card: '40ch', // Card title max width
};

/**
 * Typography utility factory
 * Creates responsive typography classes
 */
export function getTypographyClass(scale: keyof typeof typographyScale) {
  const config = typographyScale[scale];
  return {
    className: `font-${scale}`,
    fontFamily: config.fontFamily,
    ...config.desktop,
  };
}
