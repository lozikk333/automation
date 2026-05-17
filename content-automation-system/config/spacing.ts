/**
 * YARA BITES Spacing System
 * Premium Editorial Food Blog Layout Rhythm
 *
 * Based on 8px grid system for precise, premium spacing.
 * Creates luxurious whitespace and elegant visual rhythm.
 */

/**
 * SPACING SCALE
 * All spacing derived from 8px base unit
 */
export const spacingScale = {
  xs: '4px',    // 0.5 units - micro spacing
  sm: '8px',    // 1 unit - small gaps
  md: '16px',   // 2 units - standard spacing
  lg: '24px',   // 3 units - medium gaps
  xl: '32px',   // 4 units - large spacing
  '2xl': '48px', // 6 units - extra large
  '3xl': '64px', // 8 units - major spacing
  '4xl': '80px', // 10 units - large sections
  '5xl': '96px', // 12 units - major sections
  '6xl': '120px', // 15 units - premium sections
  '7xl': '160px', // 20 units - hero spacing
} as const;

/**
 * CONTAINER WIDTHS
 * Maximum content widths for different layout types
 */
export const containerWidths = {
  // Full responsive container
  full: '100%',

  // Max content width for general layout
  max: '1280px',

  // Narrow reading width for text content
  narrow: '720px',

  // Optimal text content width
  text: '680px',

  // Recipe card content
  card: {
    small: '320px',
    medium: '380px',
    large: '420px',
  },

  // Hero/feature sections
  hero: '800px',

  // Form sections
  form: '600px',
} as const;

/**
 * PAGE PADDING / HORIZONTAL GUTTERS
 * Responsive horizontal spacing for page containers
 */
export const pagePadding = {
  desktop: {
    standard: '32px',
    large: '48px',
  },
  tablet: '24px',
  mobile: '16px',
} as const;

/**
 * SECTION SPACING
 * Vertical spacing between major page sections
 */
export const sectionSpacing = {
  // Major section spacing (hero to categories, etc)
  major: {
    desktop: '120px',
    desktopMin: '96px',
    tablet: '96px',
    tabletMin: '72px',
    mobile: '64px',
    mobileMin: '48px',
  },

  // Medium section spacing
  medium: {
    desktop: '80px',
    tablet: '64px',
    mobile: '48px',
  },

  // Small section spacing
  small: {
    desktop: '48px',
    tablet: '40px',
    mobile: '32px',
  },
} as const;

/**
 * INTERNAL SECTION SPACING
 * Spacing within sections between header and content
 */
export const internalSectionSpacing = {
  // Section header to content (large title + description)
  headerToContent: {
    desktop: '56px',
    desktopMin: '40px',
    tablet: '40px',
    mobile: '32px',
  },

  // Small section header to content
  headerToContentSmall: {
    desktop: '32px',
    tablet: '24px',
    mobile: '20px',
  },

  // Title to subtitle/description
  titleToDescription: {
    desktop: '24px',
    tablet: '20px',
    mobile: '16px',
  },

  // Description to CTA
  descriptionToCTA: {
    desktop: '32px',
    tablet: '24px',
    mobile: '20px',
  },

  // CTA to secondary elements
  CTAToSecondary: {
    desktop: '40px',
    tablet: '32px',
    mobile: '24px',
  },
} as const;

/**
 * TYPOGRAPHY SPACING RHYTHM
 * Spacing around typography elements
 */
export const typographySpacing = {
  // Eyebrow/label to main title
  eyebrowToTitle: {
    desktop: '16px',
    mobile: '12px',
  },

  // Title to subtitle
  titleToSubtitle: {
    desktop: '24px',
    tablet: '20px',
    mobile: '16px',
  },

  // Paragraph to paragraph
  paragraphToNextParagraph: {
    desktop: '20px',
    tablet: '18px',
    mobile: '16px',
  },

  // Paragraph to button
  paragraphToButton: {
    desktop: '32px',
    tablet: '24px',
    mobile: '20px',
  },

  // Button to support text
  buttonToSupportText: {
    desktop: '16px',
    mobile: '12px',
  },

  // Long text block constraints
  maxTextWidth: '75ch', // ~65-75 characters
  optimalTextWidth: '65ch',
} as const;

/**
 * GRID SYSTEM
 * Column structure and gaps for layout grids
 */
export const gridSystem = {
  // Column counts
  columns: {
    desktop: 12,
    tablet: 8,
    mobile: 4,
  },

  // Grid gaps
  gap: {
    desktop: '32px',
    tablet: '24px',
    mobile: '16px',
  },

  // Card grid gaps
  cardGap: {
    desktop: '32px',
    tablet: '24px',
    mobile: '16px',
  },

  // Variant: compact grid
  compactGap: {
    desktop: '24px',
    tablet: '16px',
    mobile: '12px',
  },

  // Variant: spacious grid
  spaciousGap: {
    desktop: '40px',
    tablet: '32px',
    mobile: '24px',
  },
} as const;

/**
 * CARD SPACING
 * Padding and internal spacing for cards
 */
export const cardSpacing = {
  // Card padding sizes
  padding: {
    large: '32px',
    medium: '24px',
    small: '16px',
  },

  // Internal card spacing
  internal: {
    titleToDescription: '12px',
    descriptionToMeta: '16px',
    metaToCTA: '20px',
    ctaToSupport: '12px',
  },

  // Card to card gap in grid
  gap: {
    desktop: '32px',
    tablet: '24px',
    mobile: '16px',
  },
} as const;

/**
 * BUTTON SPACING
 * Button padding and group spacing
 */
export const buttonSpacing = {
  // Primary button padding
  primary: {
    vertical: '16px',
    horizontalDesktop: '32px',
    horizontalMobile: '24px',
  },

  // Small button padding
  small: {
    vertical: '12px',
    horizontal: '20px',
  },

  // Button group gaps
  groupGap: {
    desktop: '16px',
    tablet: '12px',
    mobile: '12px',
  },

  // Vertical button stack gap
  stackGap: {
    desktop: '12px',
    mobile: '10px',
  },
} as const;

/**
 * NAVBAR SPACING
 * Navigation bar and menu spacing
 */
export const navbarSpacing = {
  // Nav bar height
  height: {
    desktop: '80px',
    mobile: '68px',
  },

  // Logo to navigation items
  logoToNav: {
    desktop: '64px',
    tablet: '48px',
  },

  // Gap between nav items
  itemGap: {
    desktop: '36px',
    tablet: '28px',
    mobile: '20px',
  },

  // Mobile menu item spacing
  mobileItemSpacing: '20px',

  // Horizontal padding
  horizontalPadding: {
    desktop: '32px',
    tablet: '24px',
    mobile: '16px',
  },
} as const;

/**
 * FORM SPACING
 * Form elements and input spacing
 */
export const formSpacing = {
  // Input height
  inputHeight: {
    standard: '48px',
    large: '56px',
    small: '40px',
  },

  // Input padding
  inputPadding: {
    horizontal: '16px',
    vertical: '12px',
  },

  // Label to input
  labelToInput: '12px',

  // Input to input vertical
  inputToInput: '16px',

  // Input to button
  inputToButton: '20px',

  // Error/success message gap
  messageGap: {
    error: '8px',
    success: '12px',
  },

  // Form group spacing
  formGroupGap: {
    desktop: '24px',
    tablet: '20px',
    mobile: '16px',
  },
} as const;

/**
 * RECIPE CARD SPACING
 * Specific spacing for recipe cards
 */
export const recipeCardSpacing = {
  // Image to content padding
  imageToPadding: '0px', // Flush

  // Content padding
  contentPadding: '24px',

  // Category badge offset from edges
  categoryBadgeOffset: {
    top: '16px',
    left: '16px',
  },

  // Internal spacing
  titleToDescription: '12px',
  descriptionToMeta: '16px',
  metaToCTA: '20px',

  // Grid gaps
  gridGap: {
    desktop: '32px',
    tablet: '24px',
    mobile: '16px',
  },
} as const;

/**
 * AUTHOR SECTION SPACING
 * Spacing in author bio / byline sections
 */
export const authorSectionSpacing = {
  // Image column to text column
  imageToText: {
    desktop: '72px',
    tablet: '48px',
    mobile: '24px',
  },

  // Label to title
  labelToTitle: '16px',

  // Title to paragraph
  titleToParagraph: '24px',

  // Paragraph to paragraph
  paragraphSpacing: '16px',

  // Text to trust badges
  textToBadges: '28px',

  // Badges to CTA
  badgesToCTA: '32px',

  // CTA to social links
  CTAToSocial: '24px',
} as const;

/**
 * NEWSLETTER CTA SPACING
 * Newsletter subscription section spacing
 */
export const newsletterCTASpacing = {
  // Outer section padding
  outerPadding: {
    desktop: '80px',
    tablet: '64px',
    mobile: '48px',
  },

  // Inner card padding
  cardPadding: {
    desktop: '72px',
    tablet: '48px',
    mobile: '28px',
  },

  // Title to description
  titleToDescription: '20px',

  // Description to form
  descriptionToForm: '28px',

  // Form to trust text
  formToTrust: '16px',

  // Text column to image
  textToImage: {
    desktop: '64px',
    tablet: '48px',
  },
} as const;

/**
 * FOOTER SPACING
 * Footer section spacing
 */
export const footerSpacing = {
  // Top padding before footer
  topPadding: {
    desktop: '100px',
    tablet: '80px',
    mobile: '56px',
  },

  // Column gaps
  columnGap: {
    desktop: '48px',
    tablet: '32px',
    mobile: '24px',
  },

  // Link spacing
  linkSpacing: '16px',

  // Description to social icons
  descriptionToSocial: '24px',

  // Newsletter title to form
  newsletterTitleToForm: '20px',

  // Upper footer to lower bar
  upperToLower: '40px',

  // Lower bar padding
  lowerBarPadding: {
    desktop: '32px',
    tablet: '24px',
    mobile: '20px',
  },
} as const;

/**
 * MOBILE SPACING RULES
 * Responsive scaling factors for mobile
 */
export const mobileSpacingScale = {
  // Multiplier for reducing desktop spacing on mobile
  // Desktop 120px → Mobile 72px (0.6x)
  factor: 0.65,
  
  // Minimum touch target size
  minTouchTarget: '44px',

  // Reduce major section spacing proportionally
  scaledSpacing: {
    '120px': '72px',
    '96px': '64px',
    '80px': '56px',
    '64px': '48px',
    '48px': '32px',
    '40px': '28px',
    '32px': '24px',
    '24px': '16px',
    '16px': '12px',
  },
} as const;

/**
 * SEMANTIC SPACING TOKENS
 * Named spacing for common patterns
 */
export const semanticSpacing = {
  // Micro spacing (between closely related elements)
  micro: '4px',
  
  // Tight spacing (related elements)
  tight: '8px',
  
  // Compact spacing (within components)
  compact: '12px',
  
  // Default spacing (standard gap)
  default: '16px',
  
  // Comfortable spacing (breathing room)
  comfortable: '24px',
  
  // Spacious (premium gaps)
  spacious: '32px',
  
  // Luxury spacing (major sections)
  luxury: '48px',
  
  // Premium luxury (largest sections)
  premiumLuxury: '64px',
} as const;

/**
 * COMPLETE SPACING SYSTEM
 * All spacing organized by category
 */
export const spacingSystem = {
  scale: spacingScale,
  containers: containerWidths,
  padding: pagePadding,
  sections: sectionSpacing,
  internal: internalSectionSpacing,
  typography: typographySpacing,
  grid: gridSystem,
  cards: cardSpacing,
  buttons: buttonSpacing,
  navbar: navbarSpacing,
  forms: formSpacing,
  recipes: recipeCardSpacing,
  author: authorSectionSpacing,
  newsletter: newsletterCTASpacing,
  footer: footerSpacing,
  mobile: mobileSpacingScale,
  semantic: semanticSpacing,
} as const;

/**
 * EXPORT TYPES
 */
export type SpacingScale = keyof typeof spacingScale;
export type ContainerWidth = keyof typeof containerWidths;
export type SemanticSpacing = keyof typeof semanticSpacing;
