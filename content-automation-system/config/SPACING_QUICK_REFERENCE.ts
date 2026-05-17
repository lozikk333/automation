/**
 * YARA BITES Spacing System - Quick Reference
 * Developer cheat sheet and copy-paste snippets
 */

export const SPACING_QUICK_REFERENCE = {
  // Spacing scale
  SCALE: {
    xs: '4px',     // 0.5 units
    sm: '8px',     // 1 unit
    md: '16px',    // 2 units
    lg: '24px',    // 3 units
    xl: '32px',    // 4 units
    '2xl': '48px', // 6 units
    '3xl': '64px', // 8 units
    '4xl': '80px', // 10 units
    '5xl': '96px', // 12 units
    '6xl': '120px', // 15 units
    '7xl': '160px', // 20 units
  },

  // Container widths
  CONTAINERS: {
    max: '1280px',
    narrow: '720px',
    text: '720px',
    hero: '800px',
    form: '600px',
    'card-small': '320px',
    'card-medium': '380px',
    'card-large': '420px',
  },

  // Section spacing
  SECTIONS: {
    heroDesktop: '80px',
    heroTablet: '112px',
    heroMobile: '128px',
    majorDesktop: '120px',
    majorTablet: '96px',
    majorMobile: '64px',
    mediumDesktop: '80px',
    mediumTablet: '64px',
    mediumMobile: '48px',
    smallDesktop: '48px',
    smallTablet: '40px',
    smallMobile: '32px',
  },

  // Card padding
  CARDS: {
    largePadding: '32px',
    mediumPadding: '24px',
    smallPadding: '16px',
    gridGapDesktop: '32px',
    gridGapTablet: '24px',
    gridGapMobile: '16px',
  },

  // Mobile rules
  MOBILE: {
    minPadding: '16px',
    minTouchTarget: '44px',
    scalingFactor: 0.65, // Desktop to mobile multiplier
  },
};

/**
 * TAILWIND CLASS QUICK REFERENCE
 * Copy-paste ready class names
 */
export const TAILWIND_QUICK_REFERENCE = {
  SECTION_SPACING: {
    hero: 'py-20 md:py-28 lg:py-32',
    major: 'py-24 md:py-32 lg:py-36',
    medium: 'py-16 md:py-20 lg:py-24',
    small: 'py-12 md:py-16 lg:py-20',
  },

  CONTAINER: {
    max: 'max-w-7xl mx-auto',
    narrow: 'max-w-2xl mx-auto',
    text: 'max-w-3xl mx-auto',
    prose: 'max-w-prose mx-auto',
    withPadding: 'max-w-7xl mx-auto px-4 md:px-6 lg:px-8',
  },

  GRIDS: {
    recipe: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 lg:gap-8',
    blog: 'grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 lg:gap-8',
    features: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 lg:gap-8',
    twoColumn: 'grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 lg:gap-16',
  },

  CARDS: {
    padLarge: 'p-6 md:p-8',
    padMedium: 'p-5 md:p-6',
    padSmall: 'p-4 md:p-5',
  },

  BUTTONS: {
    primary: 'px-8 py-4 md:px-8 md:py-4',
    secondary: 'px-6 py-3 md:px-6 md:py-3',
    small: 'px-4 py-2 md:px-4 md:py-2',
  },

  FORMS: {
    spacing: 'space-y-4 md:space-y-6',
    inputHeight: 'h-12 md:h-14',
    labelSpacing: 'mb-2 md:mb-3',
  },
};

/**
 * COMPONENT SPACING SNIPPETS
 * Ready to copy-paste into components
 */
export const SNIPPETS = {
  heroSection: `
    <section className="py-20 md:py-28 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl">Headline</h1>
          <p className="mt-6 text-lg">Description</p>
          <button className="mt-8">CTA</button>
        </div>
      </div>
    </section>
  `,

  recipeGrid: `
    <section className="py-16 md:py-20 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <h2 className="text-4xl mb-8">Recipes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 lg:gap-8">
          {recipes.map(recipe => (
            <article key={recipe.id} className="p-5 md:p-6">
              {/* Card content */}
            </article>
          ))}
        </div>
      </div>
    </section>
  `,

  formSpacing: `
    <form className="space-y-4 md:space-y-6 max-w-md">
      <div>
        <label className="mb-2 md:mb-3 block">Email</label>
        <input className="h-12 md:h-14 w-full px-4" />
      </div>
      <button>Submit</button>
    </form>
  `,

  twoColumnLayout: `
    <section className="py-16 md:py-20 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 lg:gap-16">
          <div>{/* Column 1 */}</div>
          <div>{/* Column 2 */}</div>
        </div>
      </div>
    </section>
  `,

  cardWithInternalSpacing: `
    <article className="p-5 md:p-6">
      <span className="text-label">Category</span>
      <h3 className="mt-4 text-2xl font-bold">Title</h3>
      <p className="mt-3 text-gray-600">Description</p>
      <div className="mt-4 text-sm">Meta info</div>
      <a href="#" className="mt-5 block text-blue-600">Learn more →</a>
    </article>
  `,
};

/**
 * COMMON PATTERNS
 * Frequently used spacing combinations
 */
export const PATTERNS = {
  // Header to content spacing
  SECTION_STRUCTURE: {
    title: 'text-heading-xl',
    titleToContent: 'mt-8 md:mt-12', // After title
    contentGap: 'space-y-6 md:space-y-8', // Between content items
  },

  // Responsive padding
  PAGE_PADDING: {
    mobile: 'px-4',
    tablet: 'md:px-6',
    desktop: 'lg:px-8',
    all: 'px-4 md:px-6 lg:px-8',
  },

  // Responsive margins
  RESPONSIVE_MARGINS: {
    topSmall: 'mt-4 md:mt-6',
    topMedium: 'mt-6 md:mt-8',
    topLarge: 'mt-8 md:mt-12',
    topXLarge: 'mt-12 md:mt-16',
  },

  // Responsive gaps
  RESPONSIVE_GAPS: {
    compact: 'gap-3 md:gap-4 lg:gap-6',
    standard: 'gap-4 md:gap-6 lg:gap-8',
    spacious: 'gap-6 md:gap-8 lg:gap-12',
    luxury: 'gap-8 md:gap-12 lg:gap-16',
  },

  // Touch targets
  TOUCH_TARGET: {
    default: 'h-11 px-4', // 44x44px minimum
    large: 'h-12 px-6', // 48x48px
    small: 'h-10 px-3', // 40x40px (use sparingly)
  },
};

/**
 * COMPONENT SPACING USAGE
 * How to space each component type
 */
export const COMPONENT_SPACING_USAGE = {
  HERO_SECTION: {
    topPadding: 'py-20 md:py-28 lg:py-32',
    contentGap: 'gap-6 md:gap-8',
    titleToParagraph: 'mt-6',
    paragraphToButton: 'mt-8',
  },

  RECIPE_CARD: {
    padding: 'p-5 md:p-6',
    titleToDesc: 'mt-3',
    descToMeta: 'mt-4',
    metaToCTA: 'mt-5',
  },

  FORM_INPUT: {
    height: 'h-12 md:h-14',
    labelToInput: 'mb-2 md:mb-3',
    inputToInput: 'mt-4 md:mt-6', // via space-y class
    buttonMargin: 'mt-6 md:mt-8',
  },

  ARTICLE_CARD: {
    imageHeight: 'h-48 md:h-64 lg:h-80',
    padding: 'p-6 md:p-8',
    categoryToTitle: 'mt-4',
    titleToExcerpt: 'mt-4',
    excerptToMeta: 'mt-6',
    metaToCTA: 'mt-6',
  },

  SECTION: {
    topPadding: 'py-16 md:py-20 lg:py-24',
    titleToContent: 'mt-8 md:mt-12',
    contentGap: 'space-y-6 md:space-y-8',
    gridGap: 'gap-4 md:gap-6 lg:gap-8',
  },

  NAVIGATION: {
    height: 'h-16 md:h-20',
    itemGap: 'gap-8 md:gap-9 lg:gap-10',
    horizontalPadding: 'px-4 md:px-6 lg:px-8',
  },

  FOOTER: {
    topPadding: 'pt-20 md:pt-24 lg:pt-32',
    columnGap: 'gap-8 md:gap-12 lg:gap-12',
    linkGap: 'gap-3 md:gap-4',
  },

  NEWSLETTER_CTA: {
    outerPadding: 'py-16 md:py-20 lg:py-24',
    cardPadding: 'p-8 md:p-12 lg:p-16',
    titleToDesc: 'mt-6',
    descToForm: 'mt-8 md:mt-10',
    formToTrust: 'mt-6',
  },

  AUTHOR_SECTION: {
    imageToText: 'gap-8 md:gap-12 lg:gap-16',
    contentGap: 'space-y-4 md:space-y-6',
    labelToTitle: 'mt-4',
    textToSocial: 'mt-6',
  },
};

/**
 * SETUP CHECKLIST
 * Verify spacing system is properly configured
 */
export const SETUP_CHECKLIST = [
  '[ ] tailwind.config.ts imports completeSpacingConfig',
  '[ ] spacing.css is imported in layout.tsx or globals.css',
  '[ ] Container elements use container-px class',
  '[ ] Section spacing follows section-major/medium/small pattern',
  '[ ] Grid gaps are responsive (gap-4 md:gap-6 lg:gap-8)',
  '[ ] Mobile padding >= 16px everywhere',
  '[ ] Touch targets >= 44x44px',
  '[ ] Typography spacing follows hierarchy',
  '[ ] Cards use card-p-* padding classes',
  '[ ] Forms use form-spacing class',
  '[ ] Responsive classes tested on mobile/tablet/desktop',
  '[ ] No hardcoded spacing values in components',
  '[ ] Color and typography systems integrated',
];

/**
 * DEBUGGING TIPS
 * Common issues and solutions
 */
export const DEBUGGING = {
  'Spacing not showing': [
    'Check tailwind.config.ts has spacing config imported',
    'Verify spacing.css is imported in layout or globals',
    'Clear .next folder and rebuild',
    'Check class names are spelled correctly',
  ],

  'Mobile padding missing': [
    'Use container-px on all page-level containers',
    'Never use px-0 on mobile',
    'Always start with mobile-first classes',
    'Test on real mobile device',
  ],

  'Responsive spacing broken': [
    'Check class order: mobile md: lg: 2xl:',
    'Verify breakpoint modifiers are supported',
    'Test in production build (not just dev)',
    'Check for CSS specificity conflicts',
  ],

  'Grid not responsive': [
    'Add gap classes: gap-4 md:gap-6 lg:gap-8',
    'Ensure grid-cols-N classes are responsive',
    'Check container is responsive too',
    'Verify width is 100% on mobile',
  ],

  'Cards look cramped': [
    'Increase card padding from small to medium',
    'Add more gap between grid items',
    'Check internal element spacing',
    'Consider reducing text content density',
  ],
};

/**
 * QUICK COPY-PASTE SECTION TEMPLATE
 */
export const SECTION_TEMPLATE = {
  basic: {
    className: 'section-medium',
    structure: `
      <section className="section-medium">
        <div className="container-max container-px">
          {/* Content here */}
        </div>
      </section>
    `,
  },

  withTitle: {
    className: 'section-medium',
    structure: `
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Section Title</h2>
          <div className="mt-8 md:mt-12">
            {/* Content here */}
          </div>
        </div>
      </section>
    `,
  },

  withGrid: {
    className: 'section-medium',
    structure: `
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Section Title</h2>
          <div className="recipe-grid mt-8 md:mt-12">
            {items.map(item => (
              <article key={item.id} className="card-p-medium">
                {/* Card content */}
              </article>
            ))}
          </div>
        </div>
      </section>
    `,
  },

  withTwoColumns: {
    className: 'section-medium',
    structure: `
      <section className="section-medium">
        <div className="container-max container-px">
          <div className="grid grid-cols-1 lg:grid-cols-2 two-column-spacing">
            <div>{/* Column 1 */}</div>
            <div>{/* Column 2 */}</div>
          </div>
        </div>
      </section>
    `,
  },
};

/**
 * MOBILE SCALING REFERENCE
 * Desktop to mobile multiplier: 0.65x
 */
export const MOBILE_SCALING = {
  fromDesktop: (desktopValue: number) => {
    const factor = 0.65
    return Math.round(desktopValue * factor)
  },

  examples: {
    '120px → 78px': '120 * 0.65 = 78',
    '96px → 62px': '96 * 0.65 = 62',
    '80px → 52px': '80 * 0.65 = 52',
    '64px → 42px': '64 * 0.65 = 42',
    '48px → 31px': '48 * 0.65 = 31',
    '32px → 21px': '32 * 0.65 = 21',
  },
};

export default {
  SPACING_QUICK_REFERENCE,
  TAILWIND_QUICK_REFERENCE,
  SNIPPETS,
  PATTERNS,
  COMPONENT_SPACING_USAGE,
  SETUP_CHECKLIST,
  DEBUGGING,
  SECTION_TEMPLATE,
  MOBILE_SCALING,
};
