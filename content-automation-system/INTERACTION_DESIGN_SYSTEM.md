# YARA BITES Interaction Design System

Premium interactions should feel soft, warm, tactile, and editorial. Use calm elevation, gentle movement, quiet borders, and visible focus states. Avoid neon effects, hard outlines, oversized movement, and bouncy easing.

## Install

Import the CSS once in your global stylesheet:

```css
@import "@/styles/interactions.css";
```

Extend Tailwind with:

```ts
import { tailwindInteractionConfig } from "@/config/tailwind-interactions.config";

export default {
  theme: {
    extend: {
      ...tailwindInteractionConfig,
    },
  },
};
```

Use Framer Motion helpers from:

```ts
import { revealContainer, revealItem, buttonHover, buttonTap, cardHover } from "@/config/interactions";
```

## Tokens

Shadows:

- `shadow-soft-xs`: `0 1px 2px rgba(31,31,31,0.04)`
- `shadow-soft-sm`: `0 4px 12px rgba(31,31,31,0.06)`
- `shadow-soft-md`: `0 10px 24px rgba(31,31,31,0.08)`
- `shadow-soft-lg`: `0 18px 40px rgba(31,31,31,0.12)`
- `shadow-soft-hover`: `0 20px 48px rgba(31,31,31,0.14)`

Borders:

- `border-interaction-light`: `#F1ECE5`
- `border-interaction-soft`: `#E8E1D8`
- `border-interaction-emphasis`: `#D9CBB7`

Radius:

- `rounded-premium-sm`: `8px`
- `rounded-premium-md`: `16px`
- `rounded-premium-lg`: `24px`
- `rounded-premium-xl`: `32px`
- `rounded-full`: `9999px`

Transitions:

- `transition-smooth-fast`: `200ms cubic-bezier(0.22,1,0.36,1)`
- `transition-smooth-default`: `280ms cubic-bezier(0.22,1,0.36,1)`
- `transition-smooth-slow`: `350ms cubic-bezier(0.22,1,0.36,1)`

## Component Patterns

Buttons:

- Use `.button-premium`.
- Hover lifts `translateY(-2px)`, darkens subtly, and moves icons `2px`.
- Active state presses down with reduced shadow.

Cards:

- Use `.card-premium`.
- Hover lifts `translateY(-6px)`, moves from `shadow-soft-md` to hover depth, and softly emphasizes the border.
- Put images inside `.image-premium` for a gentle `scale(1.06)` hover zoom.

Navigation:

- Use `.nav-link-premium`.
- Hover color shifts, lifts `-1px`, and reveals a scaled underline.

Social Icons:

- Use `.social-icon-premium`.
- Hover lifts `-2px`, scales `1.05`, and uses warm tinting.

Chips:

- Use `.chip-premium`.
- Hover scales `1.02`, raises from `shadow-soft-xs` to `shadow-soft-sm`, and warms the background.

Inputs:

- Use `.input-premium`.
- Focus uses `0 0 0 4px rgba(198,168,122,0.20)` plus soft elevation.
- Use `aria-invalid="true"` or `.input-error` for error states.
- Use `.input-success` for success states.

Loading:

- Use `.skeleton-premium` for a slow neutral shimmer.

## Motion Rules

Reveal sections with `revealContainer` and `revealItem`:

```tsx
<motion.section initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }} variants={revealContainer}>
  <motion.div variants={revealItem}>Content</motion.div>
</motion.section>
```

Respect reduced motion:

```tsx
const reduceMotion = useReducedMotion();

<motion.button
  whileHover={reduceMotion ? undefined : buttonHover}
  whileTap={reduceMotion ? undefined : buttonTap}
/>
```

Mobile and touch interactions should use subtle tap feedback like `scale(0.98)` instead of relying on hover.
