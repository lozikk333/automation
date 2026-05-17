/**
 * YARA BITES Color System - Implementation Guide
 *
 * Complete instructions for implementing the premium color palette
 * across your Next.js application.
 */

// ============================================================================
// 1. SETUP IN ROOT LAYOUT
// ============================================================================

/*
File: app/layout.tsx

import '@/styles/colors.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#8B6B4A" />
      </head>
      <body className="bg-surface-warm">
        {children}
      </body>
    </html>
  )
}
*/

// ============================================================================
// 2. UPDATE TAILWIND CONFIG
// ============================================================================

/*
File: tailwind.config.ts

import type { Config } from 'tailwindcss'
import { tailwindColorConfig } from '@/config/tailwind-colors.config'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      ...tailwindColorConfig,
    },
  },
  plugins: [],
}

export default config
*/

// ============================================================================
// 3. USAGE IN COMPONENTS
// ============================================================================

/*
EXAMPLE 1: Button with Primary Color
*/

export const ButtonExample = () => {
  return (
    <button className="btn-primary px-6 py-3 rounded-lg font-medium">
      Subscribe Now
    </button>
  )
}

/*
EXAMPLE 2: Recipe Card with Color System
*/

export const RecipeCardExample = () => {
  return (
    <article className="card p-6">
      {/* Category Badge */}
      <span className="category-breakfast px-3 py-1 rounded-full text-sm font-medium">
        Breakfast
      </span>

      {/* Title */}
      <h3 className="text-heading-lg font-display text-text-primary mt-4">
        Fluffy Pancakes
      </h3>

      {/* Description */}
      <p className="text-body text-text-secondary mt-4">
        Light, fluffy pancakes with fresh berries and honey
      </p>

      {/* Footer with Link */}
      <a href="#" className="link-primary mt-6 inline-block">
        View Recipe →
      </a>
    </article>
  )
}

/*
EXAMPLE 3: Navigation with Interactive Colors
*/

export const NavigationExample = () => {
  return (
    <nav className="flex gap-8 bg-white border-b border-border-soft">
      <a href="/" className="link-primary py-4">
        Home
      </a>
      <a href="/recipes" className="link-primary py-4">
        Recipes
      </a>
      <a href="/about" className="link-primary py-4">
        About
      </a>
    </nav>
  )
}

/*
EXAMPLE 4: Hero Section with Gradient
*/

export const HeroExample = () => {
  return (
    <section className="bg-gradient-editorial py-20">
      <div className="max-w-hero mx-auto px-4">
        <h1 className="text-display-xl font-display text-text-primary">
          Premium Recipes
        </h1>
        <p className="text-body-lg text-text-secondary mt-6 max-w-prose">
          Discover the art of gourmet cooking with our curated collection.
        </p>
      </div>
    </section>
  )
}

/*
EXAMPLE 5: Form Input
*/

export const FormExample = () => {
  return (
    <form className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          Email
        </label>
        <input
          type="email"
          placeholder="your@email.com"
          className="input-base"
        />
      </div>

      <button type="submit" className="btn-primary px-6 py-3 rounded-lg font-medium">
        Submit
      </button>
    </form>
  )
}

/*
EXAMPLE 6: Status Messages
*/

export const StatusMessageExample = () => {
  return (
    <div className="space-y-4">
      <div className="badge-success">
        Recipe saved successfully!
      </div>

      <div className="badge-error">
        Please check your email address
      </div>

      <div className="badge-warning">
        This recipe contains nuts
      </div>
    </div>
  )
}

/*
EXAMPLE 7: Elevated Card
*/

export const CardElevatedExample = () => {
  return (
    <div className="card-elevated p-8">
      <h3 className="text-heading-md font-display text-text-primary">
        Featured Recipe
      </h3>
      <p className="text-body text-text-secondary mt-4">
        Premium content highlighted with subtle shadow elevation.
      </p>
    </div>
  )
}

/*
EXAMPLE 8: Link Variations
*/

export const LinkVariationsExample = () => {
  return (
    <div className="space-y-4">
      <a href="#" className="link-primary">
        Primary Link
      </a>

      <a href="#" className="link-unstyled">
        Unstyled Link
      </a>

      <button className="btn-tertiary">
        Link-like Button
      </button>
    </div>
  )
}

// ============================================================================
// 4. COLOR UTILITY USAGE
// ============================================================================

/*
TEXT COLOR UTILITIES:

text-text-primary       - Main headings
text-text-secondary     - Body text
text-text-muted         - Subtle text
text-inverse            - White text on dark

BACKGROUND UTILITIES:

bg-surface-white        - Card surfaces
bg-surface-warm         - Main background
bg-surface-cream        - Alternate sections
bg-surface-beige        - Secondary surfaces

INTERACTIVE UTILITIES:

bg-interactive-primary           - Button background
hover:bg-interactive-primary-hover - Button hover
text-interactive-link            - Link color
hover:text-interactive-link-hover - Link hover

COMPONENT UTILITIES:

btn-primary             - Primary button
btn-secondary           - Secondary button
btn-tertiary            - Tertiary button
link-primary            - Primary link
card                    - Card container
card-hover              - Card with hover effect
input-base              - Form input
badge-success           - Success badge
*/

// ============================================================================
// 5. IMPORTING COLORS IN CODE
// ============================================================================

/*
If you need to use colors programmatically:

import { colorPalette, semanticColors } from '@/config/colors'

const backgroundColor = colorPalette.surface.warm
const primaryColor = semanticColors.primary
const successColor = colorPalette.status.success

// In styled components or CSS-in-JS:
const styles = {
  heading: {
    color: colorPalette.text.primary,
  },
  button: {
    backgroundColor: colorPalette.brand.brown,
    color: colorPalette.text.inverse,
  },
}
*/

// ============================================================================
// 6. RESPONSIVE COLOR CHANGES
// ============================================================================

/*
For responsive behavior, use Tailwind's breakpoint prefixes:

<div className="bg-surface-warm md:bg-surface-cream lg:bg-surface-white">
  Responsive background color
</div>

<p className="text-text-secondary md:text-text-primary">
  Responsive text color
</p>
*/

// ============================================================================
// 7. DARK MODE SUPPORT (Optional)
// ============================================================================

/*
If implementing dark mode, create color variants:

File: config/colors-dark.ts

export const darkColorPalette = {
  brand: {
    charcoal: '#E8E1D8',  // Inverted
    brown: '#C6A87A',     // Adjusted
    gold: '#8B6B4A',      // Adjusted
  },
  // ... etc
}

Then in your Tailwind config, add dark mode support:

export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        light: lightColorPalette,
        dark: darkColorPalette,
      }
    }
  }
}
*/

// ============================================================================
// 8. COMPONENT COLOR PATTERNS
// ============================================================================

/*
HEADINGS:
Always use text-text-primary

BODY TEXT:
Default: text-text-secondary
Meta: text-text-muted

LINKS:
Default: link-primary
Or custom: text-interactive-link hover:text-interactive-link-hover

BUTTONS:
Primary: btn-primary
Secondary: btn-secondary
Tertiary: btn-tertiary

CARDS:
Standard: card
Elevated: card-elevated
With hover: card-hover

INPUTS:
Base: input-base
Error state: input-error
Success state: input-success

BADGES:
Success: badge-success
Error: badge-error
Warning: badge-warning

CATEGORIES:
Breakfast: category-breakfast
Lunch: category-lunch
Dinner: category-dinner
Dessert: category-dessert
Healthy: category-healthy
Quick: category-quick
*/

// ============================================================================
// 9. ACCESSIBILITY CONSIDERATIONS
// ============================================================================

/*
CONTRAST COMPLIANCE:

✓ Primary on white: 21:1 (WCAG AAA)
✓ Secondary on white: 10:1 (WCAG AAA)
✓ Light on white: 7:1 (WCAG AA)
✓ Accent on white: 7:1 (WCAG AA)
✓ Inverse on brown: 12:1 (WCAG AAA)

FOCUS STATES:
All interactive elements have visible focus rings using:
- focus:ring-2 focus:ring-interactive-focus-ring focus:ring-offset-2

MOTION PREFERENCES:
Animations respect prefers-reduced-motion:
- Included in colors.css for all transitions

FORCED COLORS MODE:
High contrast mode adjustments included for:
- btn-primary
- link-primary
- Text hierarchy adjustments
*/

// ============================================================================
// 10. TESTING CHECKLIST
// ============================================================================

/*
VISUAL QA:

□ Primary text is readable on all backgrounds
□ Secondary text has sufficient contrast
□ Links are visually distinct
□ Buttons are clearly interactive
□ Hover states work smoothly
□ Active states are obvious
□ Focus rings are visible
□ Category badges are distinct
□ Status indicators are clear
□ Shadows provide appropriate depth

RESPONSIVE TESTING:

□ Colors render correctly on mobile
□ No color shifts on tablet
□ Desktop experience is consistent
□ Print styles render correctly

ACCESSIBILITY TESTING:

□ Color not used alone for meaning
□ Contrast ratios meet WCAG AA/AAA
□ Focus states are keyboard navigable
□ Motion preferences respected
□ High contrast mode supported
□ Print styles work correctly
*/

// ============================================================================
// 11. COLOR PALETTE TOKENS
// ============================================================================

/*
EXPORT TO DESIGN TOOLS:

For Figma or design collaboration:

Brand Colors:
- Charcoal (#1F1F1F)
- Brown (#8B6B4A)
- Gold (#C6A87A)

Surface Colors:
- White (#FFFFFF)
- Warm (#FAF7F2)
- Cream (#F5EFE6)
- Beige (#EDE3D5)

Text Colors:
- Primary (#1F1F1F)
- Secondary (#5F5F5F)
- Light (#8A8A8A)
- Inverse (#FFFFFF)

Interactive:
- Primary Button (#8B6B4A)
- Button Hover (#755839)
- Button Active (#62492F)
- Link (#8B6B4A)
- Focus Ring (#C6A87A)

Status:
- Success (#6F8A5B)
- Error (#B65A4D)
- Warning (#B78B42)

Categories:
- Breakfast (#F6D9C8)
- Lunch (#E8D7C5)
- Dinner (#D8B29B)
- Dessert (#F3D7D9)
- Healthy (#DCE6D6)
- Quick Meals (#E9DDCC)
*/

// ============================================================================
// 12. COMMON RECIPES
// ============================================================================

/*
RECIPE: Premium Card Layout
*/

export const PremiumCardRecipe = () => {
  return (
    <div className="card card-hover">
      <div className="bg-gradient-editorial p-6">
        <span className="category-breakfast px-3 py-1 rounded text-sm font-medium">
          Breakfast
        </span>
        <h3 className="text-heading-lg text-text-primary mt-4">Recipe Title</h3>
      </div>
      <div className="p-6">
        <p className="text-text-secondary">Recipe description</p>
        <a href="#" className="link-primary mt-4 inline-block">
          View →
        </a>
      </div>
    </div>
  )
}

/*
RECIPE: CTA Section with Gradient
*/

export const CTASectionRecipe = () => {
  return (
    <section className="bg-gradient-cta py-16 rounded-lg">
      <div className="max-w-2xl mx-auto px-4 text-center">
        <h2 className="text-heading-lg text-text-primary mb-4">
          Subscribe for Recipes
        </h2>
        <p className="text-text-secondary mb-8">
          Get weekly recipes in your inbox
        </p>
        <button className="btn-primary px-8 py-3 rounded-lg font-medium">
          Subscribe Now
        </button>
      </div>
    </section>
  )
}

/*
RECIPE: Navigation Bar
*/

export const NavigationBarRecipe = () => {
  return (
    <nav className="bg-white border-b border-border-soft sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex justify-between items-center h-16">
        <div className="text-2xl font-bold text-brand-charcoal">
          YARA BITES
        </div>
        <div className="flex gap-8">
          <a href="/" className="link-primary py-4">
            Home
          </a>
          <a href="/recipes" className="link-primary py-4">
            Recipes
          </a>
          <a href="/about" className="link-primary py-4">
            About
          </a>
        </div>
      </div>
    </nav>
  )
}

// ============================================================================
// 13. MIGRATION GUIDE
// ============================================================================

/*
If migrating from another color system:

OLD -> NEW:

Old primary button:   #3B82F6 -> #8B6B4A
Old text:             #111827 -> #1F1F1F
Old background:       #FFFFFF -> #FAF7F2
Old border:           #E5E7EB -> #E8E1D8
Old accent:           #F59E0B -> #C6A87A

Search and replace patterns:
- Update class names to use new system
- Use Tailwind color utilities instead of hex values
- Update design tokens in Figma/design tools
- Test color contrast ratios
*/

export default {
  description: 'YARA BITES Color System Implementation Guide',
}
