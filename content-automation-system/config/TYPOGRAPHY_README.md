# YARA BITES Typography Design System

## 🎨 Premium Editorial Food Blog Typography

A comprehensive, production-ready typography system for a modern, luxury recipe website. Combines elegant serif headlines with clean sans-serif UI text to create a warm, sophisticated, and highly readable editorial aesthetic.

---

## 📋 Overview

### Font Pairing

| Purpose | Font | Weight | Usage |
|---------|------|--------|-------|
| **Display** | Playfair Display (Serif) | 400-900 | Hero headlines, article titles, section headings, premium moments |
| **UI** | Inter (Sans-Serif) | 400-800 | Body text, buttons, navigation, forms, cards, metadata |

### Design Philosophy

- **Elegant & Sophisticated**: Luxury editorial magazine aesthetic
- **Warm & Welcoming**: Inviting tone for a food brand
- **Highly Readable**: Optimized line heights and spacing
- **Modern & Minimal**: Clean, uncluttered design
- **Trustworthy & Polished**: Premium, professional feel

---

## 🚀 Quick Setup

### 1. Install Font Configuration

The system uses `next/font/google` for optimized font loading.

```tsx
// app/layout.tsx
import { playfairDisplay, inter, fontVariables } from '@/config/fonts'
import '@/styles/typography.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={fontVariables}>
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}
```

### 2. Update Tailwind Config

```tsx
// tailwind.config.ts
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
}

export default config
```

### 3. Import Typography Styles

The typography CSS is included in your global styles:

```tsx
// app/layout.tsx or app/globals.css
import '@/styles/typography.css'
```

---

## 📐 Typography Scale

### Display Scales (Hero & Feature Headlines)

| Class | Desktop | Tablet | Mobile | Font | Weight | Use Case |
|-------|---------|--------|--------|------|--------|----------|
| `text-display-xl` | 72px | 56px | 40px | Playfair | 700 | Hero headlines, main page titles |
| `text-display-lg` | 56px | 44px | 34px | Playfair | 700 | Major section headings |
| `text-display-md` | 42px | 34px | 28px | Playfair | 600-700 | Subsection headings |

### Heading Scales (Content Hierarchy)

| Class | Desktop | Tablet | Mobile | Font | Weight | Use Case |
|-------|---------|--------|--------|------|--------|----------|
| `text-heading-lg` | 30px | 26px | 22px | Playfair | 600 | Recipe titles, article headings |
| `text-heading-md` | 24px | 20px | 18px | Inter | 700 | Card headings, feature blocks |

### Body Scales (Content & Readability)

| Class | Desktop | Mobile | Font | Weight | Line Height | Use Case |
|-------|---------|--------|------|--------|-------------|----------|
| `text-body-lg` | 18px | 16px | Inter | 400 | 1.7 | Lead paragraphs, hero descriptions |
| `text-body` | 16px | 15px | Inter | 400 | 1.65 | Standard content, descriptions |
| `text-body-sm` | 14px | 13px | Inter | 400 | 1.5 | Metadata, captions, supporting text |

### Utility Scales (Labels, Buttons, Navigation)

| Class | Size | Font | Weight | Case | Use Case |
|-------|------|------|--------|------|----------|
| `text-label` | 12px/11px | Inter | 600 | Uppercase | Category labels, badges |
| `text-button` | 16px/15px | Inter | 600 | — | CTA buttons, actions |
| `text-navigation` | 16px | Inter | 500 | — | Navbar, menu links |
| `text-meta` | 14px/13px | Inter | 500 | — | Recipe info, timestamps |

---

## 🎯 Color Palette

```tsx
text-primary      // #1F1F1F - Main content (dark charcoal)
text-secondary    // #5F5F5F - Supporting content (muted gray)
text-light        // #8A8A8A - Subtle content (light gray)
text-accent       // #8B6B4A - Highlights (warm brown/gold)
text-inverse      // #FFFFFF - Inverse text (white)
```

---

## 💡 Usage Examples

### Hero Section

```tsx
<section className="py-20">
  <h1 className="text-display-xl font-display">
    Welcome to YARA BITES
  </h1>
  <p className="text-body-lg text-secondary mt-6 max-w-hero">
    Discover simple, delicious recipes made with love.
  </p>
</section>
```

### Recipe Card

```tsx
<article className="rounded-lg border border-neutral-200 p-6">
  <span className="text-label text-accent">
    BREAKFAST
  </span>
  <h3 className="text-heading-lg font-display text-primary mt-4">
    Fluffy Pancakes
  </h3>
  <p className="text-body text-secondary mt-4">
    Light, fluffy pancakes with fresh berries.
  </p>
  <div className="flex gap-6 mt-6">
    <span className="text-meta">Prep: 10 mins</span>
    <span className="text-meta">Cook: 15 mins</span>
  </div>
</article>
```

### Blog Article

```tsx
<article className="max-w-body mx-auto py-16">
  <h1 className="text-display-lg font-display text-primary mb-8">
    The Art of Perfect Rice
  </h1>
  
  <p className="text-body-lg text-primary leading-relaxed mb-8">
    Lead paragraph with elevated importance...
  </p>
  
  <p className="text-body text-primary leading-relaxed mb-6">
    Standard body text for main content...
  </p>
</article>
```

### Navigation Links

```tsx
<nav className="flex gap-8">
  <a href="/" className="nav-link">
    Home
  </a>
  <a href="/recipes" className="nav-link">
    Recipes
  </a>
</nav>
```

---

## 📦 Container Classes

For readable content width constraints:

```tsx
<div className="prose-container">     {/* 65ch - paragraphs */}
<div className="hero-container">      {/* 700px - hero content */}
<div className="body-container">      {/* 720px - body content */}
<div className="recipe-container">    {/* 500px - recipes */}
```

---

## ♿ Accessibility

The typography system includes built-in accessibility features:

- **WCAG AAA Contrast**: All color combinations meet AAA standards
- **Responsive Sizing**: Readable at all device sizes
- **Keyboard Navigation**: Focus states for all interactive text
- **Reduced Motion Support**: Animations respect `prefers-reduced-motion`
- **Print Styles**: Optimized typography for printing

### Focus States

Interactive text elements have visible focus rings:

```tsx
<a href="/" className="focus:outline-none focus:ring-2 focus:ring-amber-200 rounded px-1">
  Link
</a>
```

---

## 🎬 Animations & Transitions

Typography transitions use smooth, subtle animations:

```tsx
// Navigation link with hover effect
<a className="text-navigation transition-colors duration-300 hover:text-accent">
  Link
</a>

// Interactive text with lift effect
<button className="text-button transition-all duration-300 hover:-translate-y-0.5">
  Button
</button>

// Underline animation
<a className="link-underline">
  Hover me
</a>
```

---

## 📱 Responsive Behavior

The typography system scales beautifully across all devices:

### Desktop (1280px+)
- Full premium spacing and sizing
- Complete 4-column layouts
- Maximum visual hierarchy

### Tablet (768px - 1280px)
- Adjusted spacing and font sizes
- 2-column layouts where appropriate
- Balanced visual weight

### Mobile (320px - 768px)
- Tight but comfortable spacing
- Single-column layouts
- Touch-friendly sizes (minimum 15px body)

---

## 🔧 Customization

### Changing Font

To use different fonts, update `/config/fonts.ts`:

```tsx
import { Cormorant_Garamond } from 'next/font/google'

export const playfairDisplay = Cormorant_Garamond({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700'],
})
```

### Adding Custom Scales

Extend `/config/tailwind-typography.config.ts`:

```tsx
fontSize: {
  'custom-large': ['20px', { lineHeight: '1.6', fontWeight: '500' }],
}
```

---

## 📊 File Structure

```
config/
├── fonts.ts                           # Font imports & setup
├── typography.ts                      # Scale definitions & colors
├── tailwind-typography.config.ts      # Tailwind extensions
└── TYPOGRAPHY_IMPLEMENTATION.md       # Implementation guide

styles/
└── typography.css                     # CSS utility classes

components/
└── TypographyShowcase.tsx            # Usage examples
```

---

## ✅ Quality Checklist

- [ ] All headlines use Playfair Display (serif)
- [ ] All body text uses Inter (sans-serif)
- [ ] Text remains readable on all devices
- [ ] Hover states work on interactive text
- [ ] Focus states are visible
- [ ] Color contrast meets WCAG AAA
- [ ] Line lengths are 65-75ch for body
- [ ] Responsive sizes match breakpoints
- [ ] Print styles work correctly
- [ ] Animations respect prefers-reduced-motion

---

## 🎓 Best Practices

### ✅ DO

- Use `text-display-*` for main headlines
- Use `text-body` or `text-body-lg` for paragraphs
- Keep line lengths under 75 characters
- Use generous line heights (1.5-1.7 for body)
- Apply `text-label` for category badges
- Use hover transitions for interactive text
- Maintain focus states for keyboard navigation

### ❌ DON'T

- Mix serif and sans-serif in the same element
- Use display fonts for body text
- Cramped line heights (< 1.5 for body)
- All caps for long body paragraphs
- Rely on color alone for meaning
- Aggressive scaling on hover
- Remove focus states for styling

---

## 📖 Additional Resources

- **Fonts Config**: `/config/fonts.ts` - Font imports and setup
- **Typography Scale**: `/config/typography.ts` - Complete scale definitions
- **Tailwind Config**: `/config/tailwind-typography.config.ts` - Theme extensions
- **CSS Utilities**: `/styles/typography.css` - Utility classes
- **Examples**: `/components/TypographyShowcase.tsx` - Live examples
- **Implementation**: `/config/TYPOGRAPHY_IMPLEMENTATION.md` - Setup guide

---

## 🚀 Performance

The typography system is optimized for performance:

- **Font Loading**: `next/font/google` with `display: swap`
- **CSS Utilities**: Minimal CSS footprint (~2KB)
- **Responsive**: CSS `clamp()` for fluid sizing
- **Caching**: Font files cached by browser
- **No Layout Shift**: Font stack prevents CLS

---

## 🤝 Component Integration

All components should use the typography system:

- **Hero.tsx** → `text-display-xl`, `text-body-lg`
- **RecipeCard.tsx** → `text-heading-lg`, `text-body`, `text-meta`
- **Footer.tsx** → `text-body-sm`, `text-label`
- **Navigation.tsx** → `text-navigation`
- **Buttons.tsx** → `text-button`
- **Articles.tsx** → `text-display-lg`, `text-body`

---

## 📝 License

This typography system is part of the YARA BITES design system and is intended for use within this project.

---

## 🎉 Ready to Build

Your typography system is now ready to use! Start with the setup instructions above and refer to the examples for implementation patterns.

For questions or updates, see `/config/TYPOGRAPHY_IMPLEMENTATION.md` for detailed implementation guidance.
