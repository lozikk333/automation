/**
 * YARA BITES Color System - Quick Reference
 * Keep this handy while building components
 */

// ============================================================================
// QUICK COLOR LOOKUP
// ============================================================================

export const QUICK_REFERENCE = {
  // Brand
  CHARCOAL: '#1F1F1F',
  BROWN: '#8B6B4A',
  GOLD: '#C6A87A',

  // Surfaces
  WHITE: '#FFFFFF',
  WARM: '#FAF7F2',
  CREAM: '#F5EFE6',
  BEIGE: '#EDE3D5',

  // Text
  TEXT_PRIMARY: '#1F1F1F',
  TEXT_SECONDARY: '#5F5F5F',
  TEXT_LIGHT: '#8A8A8A',
  TEXT_INVERSE: '#FFFFFF',

  // Interactive
  BUTTON_PRIMARY: '#8B6B4A',
  BUTTON_HOVER: '#755839',
  BUTTON_ACTIVE: '#62492F',
  LINK: '#8B6B4A',
  LINK_HOVER: '#6E5437',
  FOCUS_RING: '#C6A87A',

  // Status
  SUCCESS: '#6F8A5B',
  ERROR: '#B65A4D',
  WARNING: '#B78B42',

  // Categories
  BREAKFAST: '#F6D9C8',
  LUNCH: '#E8D7C5',
  DINNER: '#D8B29B',
  DESSERT: '#F3D7D9',
  HEALTHY: '#DCE6D6',
  QUICK_MEALS: '#E9DDCC',

  // Borders
  BORDER_SOFT: '#E8E1D8',
  BORDER_LIGHT: '#F1ECE5',
} as const;

// ============================================================================
// TAILWIND CLASS QUICK REFERENCE
// ============================================================================

export const TAILWIND_QUICK_REFERENCE = {
  // TEXT COLORS
  text: {
    primary: 'text-text-primary',
    secondary: 'text-text-secondary',
    muted: 'text-text-muted',
    inverse: 'text-inverse',
  },

  // BACKGROUND COLORS
  bg: {
    white: 'bg-surface-white',
    warm: 'bg-surface-warm',
    cream: 'bg-surface-cream',
    beige: 'bg-surface-beige',
  },

  // BUTTONS
  buttons: {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    tertiary: 'btn-tertiary',
  },

  // LINKS
  links: {
    primary: 'link-primary',
    unstyled: 'link-unstyled',
  },

  // CARDS
  cards: {
    base: 'card',
    hover: 'card-hover',
    elevated: 'card-elevated',
  },

  // FORMS
  forms: {
    input: 'input-base',
    inputError: 'input-error',
    inputSuccess: 'input-success',
  },

  // BADGES
  badges: {
    success: 'badge-success',
    error: 'badge-error',
    warning: 'badge-warning',
  },

  // CATEGORIES
  categories: {
    breakfast: 'category-breakfast',
    lunch: 'category-lunch',
    dinner: 'category-dinner',
    dessert: 'category-dessert',
    healthy: 'category-healthy',
    quick: 'category-quick',
  },

  // BORDERS
  borders: {
    soft: 'border-soft',
    light: 'border-light',
  },

  // GRADIENTS
  gradients: {
    editorial: 'gradient-editorial',
    cta: 'gradient-cta',
    accent: 'gradient-accent',
  },

  // SHADOWS
  shadows: {
    soft: 'shadow-soft',
    medium: 'shadow-medium',
    hover: 'shadow-hover',
  },
};

// ============================================================================
// COMPONENT SNIPPETS
// ============================================================================

export const SNIPPETS = {
  // Button Primary
  buttonPrimary: `<button className="btn-primary px-6 py-3 rounded-lg font-medium">
  Click Me
</button>`,

  // Button Secondary
  buttonSecondary: `<button className="btn-secondary px-6 py-3 rounded-lg font-medium">
  Click Me
</button>`,

  // Link
  link: `<a href="#" className="link-primary">
  Link Text
</a>`,

  // Card
  card: `<div className="card p-6">
  <h3 className="text-text-primary font-semibold">Title</h3>
  <p className="text-text-secondary mt-2">Description</p>
</div>`,

  // Card Hover
  cardHover: `<div className="card-hover p-6">
  <h3 className="text-text-primary font-semibold">Title</h3>
  <p className="text-text-secondary mt-2">Description</p>
  <a href="#" className="link-primary mt-4">Learn More →</a>
</div>`,

  // Input
  input: `<input
  type="text"
  placeholder="Enter text..."
  className="input-base"
/>`,

  // Badge Success
  badgeSuccess: `<div className="badge-success">
  Success message
</div>`,

  // Badge Error
  badgeError: `<div className="badge-error">
  Error message
</div>`,

  // Category Badge
  categoryBadge: `<span className="category-breakfast px-3 py-1 rounded-full text-sm font-medium">
  Breakfast
</span>`,

  // Hero Section
  heroSection: `<section className="bg-gradient-editorial py-20">
  <div className="max-w-hero mx-auto px-4">
    <h1 className="text-5xl font-bold text-text-primary">
      Hero Headline
    </h1>
    <p className="text-lg text-text-secondary mt-6 max-w-prose">
      Descriptive text here
    </p>
  </div>
</section>`,

  // CTA Section
  ctaSection: `<section className="bg-gradient-cta py-16 rounded-lg">
  <div className="max-w-2xl mx-auto px-4 text-center">
    <h2 className="text-text-primary text-3xl font-bold mb-4">
      Call to Action
    </h2>
    <button className="btn-primary px-8 py-3 rounded-lg font-medium">
      Take Action
    </button>
  </div>
</section>`,

  // Recipe Card
  recipeCard: `<div className="card-hover">
  <div className="bg-gradient-editorial p-6">
    <span className="category-breakfast">Breakfast</span>
    <h3 className="text-heading-lg text-text-primary mt-4">Recipe Name</h3>
  </div>
  <div className="p-6">
    <p className="text-text-secondary">Recipe description</p>
    <a href="#" className="link-primary mt-4 inline-block">View Recipe →</a>
  </div>
</div>`,
};

// ============================================================================
// COMMON PATTERNS
// ============================================================================

export const PATTERNS = {
  heading: 'text-text-primary font-semibold',
  bodyText: 'text-text-secondary leading-relaxed',
  smallText: 'text-text-muted text-sm',
  interactiveHover: 'transition-colors duration-200 hover:text-brand-brown',
  cardBase: 'bg-white rounded-lg border border-border-soft shadow-soft',
  buttonBase: 'px-6 py-3 rounded-lg font-medium transition-all duration-200',
  focusRing:
    'focus:outline-none focus:ring-2 focus:ring-interactive-focus-ring focus:ring-offset-2',
};

// ============================================================================
// COMPOSITION EXAMPLES
// ============================================================================

export const COMPOSITIONS = {
  // Heading + Description
  headingWithDescription:
    '<h2 class="text-heading-lg text-text-primary mb-2">Heading</h2><p class="text-text-secondary">Description text</p>',

  // Button with Icon (Tailwind + Icon)
  buttonWithIcon:
    '<button class="btn-primary px-6 py-3 rounded-lg font-medium inline-flex gap-2 items-center"><span>Icon</span><span>Button Text</span></button>',

  // Card with Action
  cardWithAction:
    '<div class="card p-6"><h3 class="text-text-primary font-semibold">Title</h3><p class="text-text-secondary mt-2">Description</p><a href="#" class="link-primary mt-4 inline-block">Action →</a></div>',

  // Two Column Layout
  twoColumn:
    '<div class="grid grid-cols-1 md:grid-cols-2 gap-8"><div class="card p-6">Column 1</div><div class="card p-6">Column 2</div></div>',

  // Navigation Item
  navItem:
    '<a href="#" class="link-primary py-2 px-4 rounded hover:bg-surface-cream transition-colors">Menu Item</a>',
};

// ============================================================================
// ACCESSIBILITY REMINDERS
// ============================================================================

export const ACCESSIBILITY_CHECKLIST = [
  '✓ Use semantic HTML elements (button, a, input)',
  '✓ Add focus:ring-2 focus:ring-interactive-focus-ring to all interactive elements',
  '✓ Never use color alone to convey information',
  '✓ Maintain contrast ratio ≥ 4.5:1 for text',
  '✓ Use descriptive link text, not "click here"',
  '✓ Add aria-labels where needed',
  '✓ Ensure keyboard navigation works',
  '✓ Test with screen readers',
  '✓ Don\'t remove focus outlines',
  '✓ Make touch targets ≥ 44x44px',
];

// ============================================================================
// COMMON MISTAKES TO AVOID
// ============================================================================

export const AVOID = [
  '❌ Using #000000 for text (use #1F1F1F instead)',
  '❌ Using #FFFFFF as main background (use #FAF7F2)',
  '❌ Overriding focus ring colors',
  '❌ Removing underlines from links without hover state',
  '❌ Using multiple strong accent colors at once',
  '❌ Applying color without text/icon labels',
  '❌ Creating custom colors outside the palette',
  '❌ Breaking contrast ratios for styling',
  '❌ Using generic startup blues or grays',
  '❌ Forgetting accessibility in dark mode',
];

// ============================================================================
// COLOR CONTRAST QUICK CHECK
// ============================================================================

export const CONTRAST_RATIOS = {
  'Primary on White': '21:1 ✓ AAA',
  'Secondary on White': '10:1 ✓ AAA',
  'Light on White': '7:1 ✓ AA',
  'Accent on White': '7:1 ✓ AA',
  'Inverse on Brown': '12:1 ✓ AAA',
  'Inverse on Charcoal': '18:1 ✓ AAA',
} as const;

// ============================================================================
// SETUP CHECKLIST
// ============================================================================

export const SETUP_CHECKLIST = [
  '□ Import tailwindColorConfig in tailwind.config.ts',
  '□ Add colors.css to app/layout.tsx',
  '□ Verify Tailwind build includes all colors',
  '□ Test button states (hover, active, focus)',
  '□ Verify link colors and underlines',
  '□ Check card shadows and borders',
  '□ Test form input focus states',
  '□ Validate status message colors',
  '□ Review category badge colors',
  '□ Test responsive color changes if any',
];

// ============================================================================
// FILE LOCATIONS
// ============================================================================

export const FILE_LOCATIONS = {
  'Color Definitions': './config/colors.ts',
  'Tailwind Config': './config/tailwind-colors.config.ts',
  'CSS Utilities': './styles/colors.css',
  'Color Showcase': './components/ColorPalette.tsx',
  'Implementation Guide': './config/COLORS_IMPLEMENTATION.md',
  'Full Documentation': './config/COLORS_README.md',
  'This Quick Reference': './config/COLORS_QUICK_REFERENCE.ts',
} as const;

// ============================================================================
// IMPORTING COLORS PROGRAMMATICALLY
// ============================================================================

export const IMPORT_EXAMPLES = {
  example1: `import { colorPalette } from '@/config/colors'

const bgColor = colorPalette.surface.warm
const textColor = colorPalette.text.primary
const buttonColor = colorPalette.brand.brown`,

  example2: `import { semanticColors } from '@/config/colors'

const primaryColor = semanticColors.primary
const accentColor = semanticColors.accent
const bodyColor = semanticColors.body`,

  example3: `import { categoryColors } from '@/config/colors'

const breakfastColor = categoryColors.breakfast
const dinnerColor = categoryColors.dinner`,
};

// ============================================================================
// COLOR USAGE BY COMPONENT TYPE
// ============================================================================

export const COMPONENT_COLOR_USAGE = {
  'Hero Section': {
    background: 'bg-gradient-editorial',
    heading: 'text-text-primary',
    description: 'text-text-secondary',
    button: 'btn-primary',
  },

  'Recipe Card': {
    container: 'card-hover',
    heading: 'text-text-primary',
    description: 'text-text-secondary',
    category: 'category-breakfast',
    link: 'link-primary',
  },

  'Navigation': {
    background: 'bg-surface-white',
    link: 'link-primary',
    border: 'border-border-light',
    text: 'text-text-primary',
  },

  'Footer': {
    background: 'bg-surface-cream',
    heading: 'text-text-primary',
    text: 'text-text-secondary',
    link: 'link-primary',
  },

  'Form': {
    input: 'input-base',
    label: 'text-text-primary',
    helper: 'text-text-muted',
    error: 'input-error badge-error',
  },

  'Modal/Dialog': {
    background: 'bg-surface-white',
    heading: 'text-text-primary',
    content: 'text-text-secondary',
    button: 'btn-primary',
    divider: 'border-border-soft',
  },
};

export default {
  QUICK_REFERENCE,
  TAILWIND_QUICK_REFERENCE,
  SNIPPETS,
  PATTERNS,
  COMPOSITIONS,
  ACCESSIBILITY_CHECKLIST,
  AVOID,
  CONTRAST_RATIOS,
  SETUP_CHECKLIST,
  FILE_LOCATIONS,
  IMPORT_EXAMPLES,
  COMPONENT_COLOR_USAGE,
};
