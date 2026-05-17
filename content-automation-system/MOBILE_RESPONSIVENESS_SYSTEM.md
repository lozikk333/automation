# YARA BITES Mobile Responsiveness System

This system defines mobile-first layout assumptions, responsive tokens, touch behavior, and testing rules for a premium modern recipe website. Mobile should feel designed, calm, readable, and tactile, not like a shrunken desktop.

## Breakpoints

Use Tailwind's mobile-first breakpoints:

- Mobile: default, `320px-639px`
- Small tablet: `sm`, `640px+`
- Tablet: `md`, `768px+`
- Large tablet: `lg`, `1024px+`
- Desktop: `xl`, `1280px+`
- Large desktop: `2xl`, `1536px+`

Progressively enhance upward. Prefer `grid-cols-1 md:grid-cols-2 xl:grid-cols-3` over desktop-first overrides.

## Installation

Import the CSS once in global styles:

```css
@import "@/styles/responsive.css";
```

Extend Tailwind:

```ts
import { tailwindResponsiveConfig } from "@/config/tailwind-responsive.config";

export default {
  theme: {
    screens: tailwindResponsiveConfig.screens,
    extend: {
      ...tailwindResponsiveConfig.extend,
    },
  },
};
```

Use behavior helpers:

```tsx
import { responsiveMotion } from "@/config/responsive";
import { useIsDesktop, useLockBodyScroll } from "@/hooks/useResponsive";
```

## Core Utilities

- `.container-responsive`: `1280px` max width with `16 / 20 / 24 / 32 / 48px` gutters.
- `.container-text-responsive`: readable text container up to `720px`.
- `.section-responsive`: section padding from `56px` mobile to `120px` desktop.
- `.hero-responsive`: hero padding from `56-72px` mobile to `120px` desktop.
- `.recipe-grid-responsive`: `1 / 2 / 3` columns.
- `.category-grid-responsive`: `1 / 2 / 4` columns.
- `.footer-grid-responsive`: `1 / 2 / 4` columns.
- `.touch-target`: minimum `44px`.
- `.touch-target-comfort`: recommended `52px`.
- `.mobile-scroll-row.hide-scrollbar`: swipeable category/chip rows.
- `.mobile-nav-shell`, `.mobile-nav-drawer`, `.mobile-nav-link`: sticky mobile navigation patterns.

## Layout Rules

Use `1280px` as the desktop max width. Keep prose between `680px` and `720px`. Full-width sections are appropriate for hero backgrounds, newsletter CTA bands, and footer backgrounds.

Maintain consistent gutters:

- Mobile: `16px`
- Small tablet: `20px`
- Tablet: `24px`
- Desktop: `32px`
- Large desktop: `48px`

## Typography Rules

- Hero headlines: `34-42px` mobile, `48-56px` tablet, `64-72px` desktop.
- Section titles: `28-36px` mobile, `38-46px` tablet, `48-56px` desktop.
- Card titles: `18px` mobile, `24px` desktop.
- Body: `15-16px` mobile, `16-18px` desktop.
- Labels: `11-12px` mobile, `12-14px` desktop.

Never ship unreadably small mobile type.

## Navigation Rules

Desktop uses horizontal navigation. Mobile uses a hamburger menu with either a full-screen overlay or slide-down drawer.

Mobile menu requirements:

- Sticky nav height: `64-68px`.
- Logo: `20-22px`.
- Links: `44px+` touch targets, ideally `52px`.
- Close button.
- Body scroll lock with `useLockBodyScroll`.
- Smooth open animation.
- No hover-only behavior.

## Component Rules

Hero:

- Mobile is single-column, centered, with natural pill wrapping.
- Desktop may become editorial split layout.
- CTA may be full-width on mobile.

Recipe cards:

- Full width on mobile.
- Preserve image aspect ratio.
- Clamp title to 2 lines and description to 2 lines.
- Metadata wraps naturally.
- Desktop hover can lift; mobile uses tap feedback.

Author section:

- Desktop split `45 / 55`.
- Tablet and mobile stack image then text.
- Mobile CTAs stack and trust badges can stack.

Newsletter:

- Desktop can be two-column.
- Mobile is single-column.
- Hide optional heavy imagery on mobile.
- Input and button are full width with `48-56px` height.

Footer:

- Desktop: 4 columns.
- Tablet: 2 columns.
- Mobile: centered single stack, stacked copyright and policy links.

## Interaction Rules

Use hover only for devices that support it:

```css
@media (hover: hover) and (pointer: fine) {
  .desktop-hover-lift:hover {
    transform: translateY(-6px);
  }
}
```

Touch devices use `.tap-feedback:active` or Framer Motion `whileTap={{ scale: 0.98 }}`.

## Performance Rules

Mobile must prioritize speed:

- Use `next/image`.
- Lazy load non-critical images.
- Keep animation transforms simple.
- Avoid heavy parallax and expensive background effects.
- Split optional showcase/heavy components.

## Accessibility Rules

- Touch targets are `44px+`.
- No horizontal scrolling.
- Semantic navigation.
- Proper form labels.
- Visible focus states.
- Body scroll lock for open mobile menus.
- Respect `prefers-reduced-motion`.

## Test Viewports

Validate at:

`320px`, `375px`, `390px`, `414px`, `640px`, `768px`, `1024px`, `1280px`, `1536px`.

Check no overflow, readable hierarchy, unbroken cards, smooth mobile nav, and fast rendering.
