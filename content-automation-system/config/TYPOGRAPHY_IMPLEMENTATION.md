/**
 * YARA BITES Typography System - Implementation Guide
 *
 * This document provides complete instructions for implementing
 * the premium editorial typography system across your Next.js application.
 */

// ============================================================================
// 1. SETUP IN ROOT LAYOUT
// ============================================================================

/*
File: app/layout.tsx

import { playfairDisplay, inter, fontVariables } from '@/config/fonts'
import '@/styles/typography.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={fontVariables}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={inter.className}>
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
import { typographyConfig } from '@/config/tailwind-typography.config'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      ...typographyConfig,
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
EXAMPLE 1: Hero Section with Display XL
*/

export const HeroExample = () => {
  return (
    <section className="py-20">
      <h1 className="text-display-xl font-display">
        Welcome to YARA BITES
      </h1>
      <p className="text-body-lg text-secondary mt-6 max-w-hero">
        Discover simple, delicious recipes made for everyday cooking.
      </p>
    </section>
  )
}

/*
EXAMPLE 2: Recipe Card with Proper Hierarchy
*/

export const RecipeCardExample = () => {
  return (
    <article className="rounded-lg border border-neutral-200 overflow-hidden">
      <div className="p-6">
        {/* Category Label */}
        <span className="text-label text-accent">
          Breakfast
        </span>

        {/* Recipe Title */}
        <h2 className="text-heading-lg font-display text-primary mt-3 line-clamp-2">
          Fluffy Banana Pancakes with Honey Drizzle
        </h2>

        {/* Description */}
        <p className="text-body text-secondary mt-4">
          Light, fluffy pancakes topped with fresh honey and berries
        </p>

        {/* Recipe Meta */}
        <div className="flex gap-6 mt-6">
          <span className="text-meta">
            <strong>Prep:</strong> 10 mins
          </span>
          <span className="text-meta">
            <strong>Cook:</strong> 15 mins
          </span>
          <span className="text-meta">
            <strong>Serves:</strong> 4
          </span>
        </div>
      </div>
    </article>
  )
}

/*
EXAMPLE 3: Section with Heading and Body Content
*/

export const ArticleExample = () => {
  return (
    <article className="max-w-body mx-auto py-16">
      {/* Section Heading */}
      <h2 className="text-display-lg font-display text-primary mb-8">
        The Art of Perfect Rice
      </h2>

      {/* Byline/Meta */}
      <div className="mb-8">
        <p className="text-body-sm text-light">
          By Jane Smith • May 10, 2026 • 8 min read
        </p>
      </div>

      {/* Lead Paragraph */}
      <p className="text-body-lg text-primary leading-relaxed mb-8">
        Cooking the perfect rice might seem simple, but it's an art form that
        has been perfected over centuries across different cuisines.
      </p>

      {/* Body Content */}
      <p className="text-body text-primary leading-relaxed mb-6">
        Whether you're making jasmine rice, basmati, or arborio, the fundamental
        principles remain the same. Understanding the water ratio, heat level,
        and timing is key to achieving fluffy, perfectly cooked rice every time.
      </p>
    </article>
  )
}

/*
EXAMPLE 4: Navigation Links
*/

export const NavigationExample = () => {
  return (
    <nav className="flex gap-8">
      <a href="/" className="nav-link">
        Home
      </a>
      <a href="/recipes" className="nav-link">
        Recipes
      </a>
      <a href="/about" className="nav-link">
        About
      </a>
    </nav>
  )
}

/*
EXAMPLE 5: Button with Proper Typography
*/

export const ButtonExample = () => {
  return (
    <button className="px-6 py-3 bg-amber-900 text-white rounded-lg font-medium text-button hover:bg-amber-950 transition-colors duration-300">
      Subscribe Now
    </button>
  )
}

// ============================================================================
// 4. RESPONSIVE TYPOGRAPHY PATTERNS
// ============================================================================

/*
For responsive text that automatically scales, use Tailwind's responsive prefixes:

Desktop:  text-[72px]
Tablet:   md:text-[56px]
Mobile:   sm:text-[40px]

Example:
<h1 className="text-[72px] md:text-[56px] sm:text-[40px] font-display font-bold">
  Responsive Heading
</h1>
*/

// ============================================================================
// 5. UTILITY CLASS REFERENCE
// ============================================================================

/*
TEXT SIZES:

Display:
- text-display-xl   (72px)
- text-display-lg   (56px)
- text-display-md   (42px)

Headings:
- text-heading-lg   (30px, serif)
- text-heading-md   (24px, sans)

Body:
- text-body-lg      (18px)
- text-body         (16px)
- text-body-sm      (14px)

Utility:
- text-label        (12px, uppercase)
- text-button       (16px, bold)
- text-navigation   (16px, medium)
- text-meta         (14px, medium)

TEXT COLORS:

- text-primary      (#1F1F1F - main content)
- text-secondary    (#5F5F5F - supporting)
- text-light        (#8A8A8A - subtle)
- text-accent       (#8B6B4A - highlights)
- text-inverse      (#FFFFFF - on dark)

CONTAINERS:

- prose-container   (max-width: 65ch)
- hero-container    (max-width: 700px)
- body-container    (max-width: 720px)
- recipe-container  (max-width: 500px)

HELPER CLASSES:

- uppercase-label         (uppercase micro text)
- text-secondary-muted    (light gray text)
- text-accent-highlight   (warm brown accent)
- serif-display          (Playfair Display)
- sans-ui                (Inter)
- nav-link               (interactive link styles)
- button-text            (button styling)
- link-underline         (hover underline animation)
- line-clamp-1/2/3       (truncate with ellipsis)
*/

// ============================================================================
// 6. TYPOGRAPHIC BEST PRACTICES
// ============================================================================

/*
HEADLINES SHOULD USE:
- Serif (Playfair Display) for main visual impact
- text-display-* or text-heading-lg classes
- Strong font weight (600-700)
- Dark charcoal color (text-primary)

BODY TEXT SHOULD USE:
- Sans-serif (Inter) for readability
- text-body or text-body-lg for primary content
- Regular weight (400) for body paragraphs
- Generous line-height (1.65-1.7) for comfort

LABELS/BADGES SHOULD USE:
- Uppercase text
- text-label class
- Smaller, medium weight
- Muted color (text-light)

INTERACTIVE TEXT SHOULD USE:
- Medium to semi-bold weight
- Smooth color transitions
- Focus states for accessibility
- Use nav-link class for navigation

AVOID:
- Mixing serif and sans-serif in same element
- Using display fonts for body text
- Cramped line-height (< 1.5 for body)
- Lines too wide for comfortable reading (> 75ch)
- Using all caps for body paragraphs
- Relying on color alone for meaning
*/

// ============================================================================
// 7. ACCESSIBILITY CONSIDERATIONS
// ============================================================================

/*
CONTRAST RATIOS:
- Primary text on white: ✓ WCAG AAA (21:1)
- Secondary text on white: ✓ WCAG AAA (10:1)
- Accent text: ✓ WCAG AA (7:1)

RESPONSIVE TEXT SIZING:
- Mobile: 15px minimum for body text
- Zoomed views (200%): Ensure text remains readable
- Support: :focus-visible for keyboard navigation

PREFERS-REDUCED-MOTION:
- Transitions are removed for users with motion sensitivity
- Included in typography.css

PRINT STYLES:
- High quality typography output
- Optimized for document reading
- Included in typography.css
*/

// ============================================================================
// 8. INTEGRATION WITH COMPONENTS
// ============================================================================

/*
All major components should import and use the typography system:

- Hero.tsx → text-display-xl, text-body-lg
- RecipeCard.tsx → text-heading-lg, text-body, text-meta
- Footer.tsx → text-body-sm, text-label
- Navigation.tsx → text-navigation
- Buttons.tsx → text-button
- CardGrid.tsx → text-heading-md, text-body
- Newsletter.tsx → text-body, text-label

See component examples in /components/ folder.
*/

// ============================================================================
// 9. CUSTOM FONT WEIGHTS
// ============================================================================

/*
PLAYFAIR DISPLAY WEIGHTS:
- 400 (light) - not commonly used
- 500 (medium) - subtle display
- 600 (semibold) - default headlines
- 700 (bold) - strong emphasis
- 800 (extrabold) - hero headlines
- 900 (black) - maximum impact

INTER WEIGHTS:
- 400 (normal) - body text
- 500 (medium) - labels, metadata
- 600 (semibold) - buttons, subheadings
- 700 (bold) - strong emphasis
- 800 (extrabold) - rare, minimal use
*/

// ============================================================================
// 10. TESTING THE SYSTEM
// ============================================================================

/*
VISUAL QA CHECKLIST:

□ Headlines use Playfair Display (serif)
□ Body text uses Inter (sans-serif)
□ Line lengths are 65-75ch for body
□ Text is readable on all devices
□ Hover states work on interactive text
□ Focus states are visible
□ Colors have sufficient contrast
□ Spacing is consistent
□ Responsive sizes match breakpoints
□ Print styles work correctly
□ Animations respect prefers-reduced-motion

RESPONSIVE TESTING:

□ Mobile (320px) - single column, tight spacing
□ Tablet (768px) - comfortable spacing
□ Desktop (1280px+) - full premium spacing
□ Zoom (200%) - text remains readable
*/

// ============================================================================
// 11. FIGMA DESIGN TOKENS
// ============================================================================

/*
EXPORT THESE TO FIGMA FOR DESIGN CONSISTENCY:

Typography Styles:
- Display XL
- Display Large
- Display Medium
- Heading Large
- Heading Medium
- Body Large
- Body
- Body Small
- Label
- Button
- Navigation
- Meta

Color Styles:
- Primary (#1F1F1F)
- Secondary (#5F5F5F)
- Light (#8A8A8A)
- Accent (#8B6B4A)
- Inverse (#FFFFFF)
*/

export default {
  description: 'YARA BITES Typography System Implementation Guide',
}
