/**
 * YARA BITES Tailwind Color Configuration
 * Add this to your tailwind.config.ts theme extensions
 *
 * Usage in tailwind.config.ts:
 * import { tailwindColorConfig } from '@/config/tailwind-colors.config'
 *
 * export default {
 *   theme: {
 *     extend: {
 *       ...tailwindColorConfig
 *     }
 *   }
 * }
 */

export const tailwindColorConfig = {
  colors: {
    // Brand colors
    brand: {
      charcoal: '#1F1F1F',
      brown: '#8B6B4A',
      gold: '#C6A87A',
    },

    // Surface colors
    surface: {
      white: '#FFFFFF',
      warm: '#FAF7F2',
      cream: '#F5EFE6',
      beige: '#EDE3D5',
    },

    // Text colors
    text: {
      primary: '#1F1F1F',
      secondary: '#5F5F5F',
      muted: '#8A8A8A',
      inverse: '#FFFFFF',
    },

    // Border colors
    border: {
      soft: '#E8E1D8',
      light: '#F1ECE5',
      DEFAULT: '#E8E1D8',
    },

    // Interactive colors
    interactive: {
      primary: '#8B6B4A',
      'primary-hover': '#755839',
      'primary-active': '#62492F',
      'secondary-border': '#D9CBB7',
      'secondary-text': '#5B4632',
      'secondary-hover': '#F3EBDD',
      'link': '#8B6B4A',
      'link-hover': '#6E5437',
      'focus-ring': '#C6A87A',
    },

    // Status colors
    status: {
      success: '#6F8A5B',
      'success-bg': '#EEF4E8',
      error: '#B65A4D',
      'error-bg': '#FAECE9',
      warning: '#B78B42',
      'warning-bg': '#FBF5E7',
    },

    // Category colors
    category: {
      breakfast: '#F6D9C8',
      lunch: '#E8D7C5',
      dinner: '#D8B29B',
      dessert: '#F3D7D9',
      healthy: '#DCE6D6',
      'quick-meals': '#E9DDCC',
    },

    // Semantic colors
    semantic: {
      heading: '#1F1F1F',
      body: '#5F5F5F',
      label: '#8A8A8A',
      background: '#FAF7F2',
      primary: '#8B6B4A',
      'primary-hover': '#755839',
      accent: '#C6A87A',
    },

    // Transparent variants
    transparent: 'transparent',
    current: 'currentColor',

    // Neutral grays (for generic components)
    neutral: {
      50: '#FAFAF9',
      100: '#F5F5F4',
      200: '#E7E5E4',
      300: '#D6D3D1',
      400: '#A8A29E',
      500: '#78716B',
      600: '#57534E',
      700: '#44403C',
      800: '#292423',
      900: '#1C1917',
    },

    // Override default colors
    black: '#1F1F1F',
    white: '#FFFFFF',
    red: '#B65A4D',
    green: '#6F8A5B',
    yellow: '#B78B42',
    gray: {
      50: '#FAF7F2',
      100: '#F5EFE6',
      200: '#EDE3D5',
      300: '#E8E1D8',
      400: '#D9CBB7',
      500: '#8A8A8A',
      600: '#5F5F5F',
      700: '#1F1F1F',
      800: '#1F1F1F',
      900: '#1F1F1F',
    },

    // Named color tokens for common uses
    primary: {
      DEFAULT: '#8B6B4A',
      hover: '#755839',
      active: '#62492F',
      light: '#F3EBDD',
    },

    secondary: {
      DEFAULT: '#5B4632',
      hover: '#F3EBDD',
      border: '#D9CBB7',
    },

    accent: {
      DEFAULT: '#C6A87A',
      light: 'rgba(198, 168, 122, 0.15)',
    },

    success: {
      DEFAULT: '#6F8A5B',
      light: '#EEF4E8',
    },

    error: {
      DEFAULT: '#B65A4D',
      light: '#FAECE9',
    },

    warning: {
      DEFAULT: '#B78B42',
      light: '#FBF5E7',
    },
  },

  backgroundColor: {
    primary: '#1F1F1F',
    secondary: '#5F5F5F',
    brand: '#8B6B4A',
    accent: '#C6A87A',
    surface: '#FFFFFF',
    'surface-warm': '#FAF7F2',
    'surface-cream': '#F5EFE6',
    'surface-beige': '#EDE3D5',
  },

  textColor: {
    primary: '#1F1F1F',
    secondary: '#5F5F5F',
    muted: '#8A8A8A',
    inverse: '#FFFFFF',
    brand: '#8B6B4A',
    accent: '#C6A87A',
    error: '#B65A4D',
    success: '#6F8A5B',
    warning: '#B78B42',
  },

  borderColor: {
    primary: '#E8E1D8',
    light: '#F1ECE5',
    brand: '#8B6B4A',
  },

  ringColor: {
    brand: '#C6A87A',
    'brand-light': 'rgba(198, 168, 122, 0.35)',
  },

  divideColor: {
    primary: '#E8E1D8',
    light: '#F1ECE5',
  },

  placeholderColor: {
    primary: '#8A8A8A',
    secondary: '#D9CBB7',
  },
};

/**
 * BOX SHADOW CONFIGURATION
 * Add to your tailwind shadow extensions
 */
export const shadowConfig = {
  shadow: {
    'soft': '0 1px 2px rgba(31, 31, 31, 0.06)',
    'medium': '0 4px 6px rgba(31, 31, 31, 0.10)',
    'hover': '0 10px 15px rgba(31, 31, 31, 0.14)',
    'lg': '0 20px 25px rgba(31, 31, 31, 0.15)',
    'xl': '0 25px 50px rgba(31, 31, 31, 0.15)',
    'elevation-1': '0 2px 4px rgba(31, 31, 31, 0.08)',
    'elevation-2': '0 4px 8px rgba(31, 31, 31, 0.10)',
    'elevation-3': '0 8px 16px rgba(31, 31, 31, 0.12)',
  },
};

/**
 * GRADIENT CONFIGURATION
 * Add to your tailwind gradient extensions
 */
export const gradientConfig = {
  backgroundImage: {
    'editorial': 'linear-gradient(180deg, #FAF7F2 0%, #FFFFFF 100%)',
    'cta': 'linear-gradient(135deg, #F5EFE6 0%, #FAF7F2 100%)',
    'accent-glow': 'radial-gradient(circle, rgba(198, 168, 122, 0.15) 0%, transparent 70%)',
    'warm-fade': 'linear-gradient(to bottom, rgba(250, 247, 242, 0.5), transparent)',
    'cream-fade': 'linear-gradient(135deg, rgba(245, 239, 230, 0.3), rgba(250, 247, 242, 0.3))',
  },
};

/**
 * OPACITY CONFIGURATION
 * Common opacity values for interactive states
 */
export const opacityConfig = {
  opacity: {
    0: '0',
    5: '0.05',
    10: '0.1',
    15: '0.15',
    20: '0.2',
    25: '0.25',
    30: '0.3',
    35: '0.35',
    40: '0.4',
    50: '0.5',
    60: '0.6',
    70: '0.7',
    75: '0.75',
    80: '0.8',
    90: '0.9',
    95: '0.95',
    100: '1',
  },
};

/**
 * COMPLETE TAILWIND CONFIG EXPORT
 * Import and use in tailwind.config.ts:
 * import { completeColorConfig } from '@/config/tailwind-colors.config'
 * export default {
 *   theme: {
 *     extend: completeColorConfig
 *   }
 * }
 */
export const completeColorConfig = {
  ...tailwindColorConfig,
  ...shadowConfig,
  ...gradientConfig,
  ...opacityConfig,
};
