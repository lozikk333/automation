/**
 * YARA BITES Tailwind Spacing Configuration
 * Add this to your tailwind.config.ts theme extensions
 *
 * Usage in tailwind.config.ts:
 * import { tailwindSpacingConfig } from '@/config/tailwind-spacing.config'
 *
 * export default {
 *   theme: {
 *     extend: {
 *       ...tailwindSpacingConfig
 *     }
 *   }
 * }
 */

export const tailwindSpacingConfig = {
  // SPACING SCALE
  spacing: {
    // Base scale (8px grid)
    0: '0px',
    1: '4px',    // xs
    2: '8px',    // sm
    3: '12px',
    4: '16px',   // md
    6: '24px',   // lg
    8: '32px',   // xl
    12: '48px',  // 2xl
    16: '64px',  // 3xl
    20: '80px',  // 4xl
    24: '96px',  // 5xl
    30: '120px', // 6xl
    40: '160px', // 7xl

    // Semantic names for convenience
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    '4xl': '80px',
    '5xl': '96px',
    '6xl': '120px',
    '7xl': '160px',

    // Semantic spacing tokens
    micro: '4px',
    tight: '8px',
    compact: '12px',
    default: '16px',
    comfortable: '24px',
    spacious: '32px',
    luxury: '48px',
    premiumLuxury: '64px',
  },

  // MAX WIDTH CONTAINER SIZES
  maxWidth: {
    // Default max-widths
    xs: '320px',
    sm: '380px',
    md: '420px',

    // Content widths
    prose: '65ch',
    text: '720px',
    narrow: '720px',
    hero: '800px',
    form: '600px',

    // Semantic names
    'card-small': '320px',
    'card-medium': '380px',
    'card-large': '420px',
    'content': '1280px',
    'content-narrow': '720px',

    // Full viewport
    full: '100%',
  },

  // PADDING
  padding: {
    // Responsive container padding
    'container-desktop': '32px',
    'container-desktop-lg': '48px',
    'container-tablet': '24px',
    'container-mobile': '16px',

    // Page section padding
    'section-desktop': '96px 32px',
    'section-tablet': '64px 24px',
    'section-mobile': '48px 16px',

    // Card padding
    'card-large': '32px',
    'card-medium': '24px',
    'card-small': '16px',
  },

  // GAP (for grids and flexbox)
  gap: {
    // Grid gaps
    'grid-desktop': '32px',
    'grid-tablet': '24px',
    'grid-mobile': '16px',

    // Compact grid
    'grid-compact-desktop': '24px',
    'grid-compact-tablet': '16px',
    'grid-compact-mobile': '12px',

    // Spacious grid
    'grid-spacious-desktop': '40px',
    'grid-spacious-tablet': '32px',
    'grid-spacious-mobile': '24px',

    // Card gaps
    'card-gap-desktop': '32px',
    'card-gap-tablet': '24px',
    'card-gap-mobile': '16px',

    // Navigation gaps
    'nav-gap-desktop': '36px',
    'nav-gap-tablet': '28px',
    'nav-gap-mobile': '20px',

    // Form gaps
    'form-gap-desktop': '24px',
    'form-gap-tablet': '20px',
    'form-gap-mobile': '16px',

    // Button group gaps
    'button-gap-desktop': '16px',
    'button-gap-mobile': '12px',

    // Semantic gaps
    'gap-micro': '4px',
    'gap-tight': '8px',
    'gap-compact': '12px',
    'gap-default': '16px',
    'gap-comfortable': '24px',
    'gap-spacious': '32px',
    'gap-luxury': '48px',
  },

  // MARGIN
  margin: {
    // Responsive section margins
    'section-desktop': '96px auto',
    'section-tablet': '64px auto',
    'section-mobile': '48px auto',

    // Semantic margins
    'micro': '4px',
    'tight': '8px',
    'compact': '12px',
    'default': '16px',
    'comfortable': '24px',
    'spacious': '32px',
    'luxury': '48px',
  },

  // WIDTH / HEIGHT helpers
  width: {
    'full': '100%',
    'screen': '100vw',
    'max-content': 'max-content',
    'min-content': 'min-content',
  },

  // CUSTOM SPACING PROPERTIES
  space: {
    // Section spacing
    'section-major': '96px',
    'section-major-min': '80px',
    'section-medium': '64px',
    'section-small': '48px',

    // Internal spacing
    'section-header': '40px',
    'section-header-small': '24px',

    // Component spacing
    'component-horizontal': '32px',
    'component-vertical': '24px',

    // Typography spacing
    'type-title-subtitle': '24px',
    'type-paragraph': '16px',
    'type-button': '32px',
  },

  // BORDER RADIUS (keeping for reference)
  borderRadius: {
    none: '0',
    sm: '2px',
    DEFAULT: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    full: '9999px',
  },
};

/**
 * RESPONSIVE SPACING UTILITIES
 * CSS variables for responsive behavior
 */
export const responsiveSpacingUtilities = {
  '--spacing-desktop-padding': '32px',
  '--spacing-tablet-padding': '24px',
  '--spacing-mobile-padding': '16px',

  '--spacing-section-major-desktop': '120px',
  '--spacing-section-major-tablet': '96px',
  '--spacing-section-major-mobile': '64px',

  '--spacing-section-medium-desktop': '80px',
  '--spacing-section-medium-tablet': '64px',
  '--spacing-section-medium-mobile': '48px',

  '--spacing-grid-gap-desktop': '32px',
  '--spacing-grid-gap-tablet': '24px',
  '--spacing-grid-gap-mobile': '16px',

  '--spacing-card-padding': '24px',
  '--spacing-button-padding-v': '16px',
  '--spacing-button-padding-h': '32px',
};

/**
 * BREAKPOINT-SPECIFIC SPACING
 */
export const breakpointSpacing = {
  // Mobile-first approach
  mobile: {
    padding: '16px',
    sectionGap: '48px',
    cardGap: '16px',
  },
  tablet: {
    padding: '24px',
    sectionGap: '72px',
    cardGap: '24px',
  },
  desktop: {
    padding: '32px',
    sectionGap: '96px',
    cardGap: '32px',
  },
  wide: {
    padding: '48px',
    sectionGap: '120px',
    cardGap: '40px',
  },
};

/**
 * COMPLETE TAILWIND SPACING CONFIG EXPORT
 * Import and use in tailwind.config.ts:
 * import { completeSpacingConfig } from '@/config/tailwind-spacing.config'
 * export default {
 *   theme: {
 *     extend: completeSpacingConfig
 *   }
 * }
 */
export const completeSpacingConfig = {
  ...tailwindSpacingConfig,
};

/**
 * SPACING ALIASES
 * Common spacing patterns
 */
export const spacingAliases = {
  // Container padding by screen
  containerPadding: {
    desktop: 'px-8', // 32px
    tablet: 'px-6',  // 24px
    mobile: 'px-4',  // 16px
  },

  // Section spacing
  sectionSpacing: {
    major: 'py-24',        // 96px
    majorMin: 'py-20',     // 80px
    medium: 'py-16',       // 64px
    small: 'py-12',        // 48px
  },

  // Card spacing
  cardPadding: {
    large: 'p-8',  // 32px
    medium: 'p-6', // 24px
    small: 'p-4',  // 16px
  },

  // Grid gaps
  gridGap: {
    desktop: 'gap-8',  // 32px
    tablet: 'gap-6',   // 24px
    mobile: 'gap-4',   // 16px
  },

  // Button spacing
  buttonPadding: {
    primary: 'px-8 py-4',    // 32px x 16px
    secondary: 'px-6 py-3',  // 24px x 12px
    small: 'px-4 py-2',      // 16px x 8px
  },

  // Form spacing
  formGap: {
    desktop: 'gap-6',  // 24px
    tablet: 'gap-5',   // 20px
    mobile: 'gap-4',   // 16px
  },

  // Typography spacing
  typographySpacing: {
    titleToDescription: 'mt-6',    // 24px
    paragraphGap: 'my-4',          // 16px
    buttonToText: 'mt-8',          // 32px
  },
};
