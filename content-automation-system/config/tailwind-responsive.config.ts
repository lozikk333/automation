/**
 * YARA BITES Tailwind Responsive Configuration
 * Mobile-first layout tokens for a premium editorial recipe website.
 *
 * Add this to your tailwind.config.ts:
 *
 * import { tailwindResponsiveConfig } from "@/config/tailwind-responsive.config";
 *
 * export default {
 *   theme: {
 *     screens: tailwindResponsiveConfig.screens,
 *     extend: {
 *       ...tailwindResponsiveConfig.extend,
 *     },
 *   },
 * };
 */

export const tailwindResponsiveConfig = {
  screens: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },

  extend: {
    maxWidth: {
      "yb-content": "1280px",
      "yb-text": "720px",
      "yb-readable": "680px",
      "yb-form": "600px",
    },

    spacing: {
      "gutter-mobile": "16px",
      "gutter-sm": "20px",
      "gutter-tablet": "24px",
      "gutter-desktop": "32px",
      "gutter-wide": "48px",

      "hero-mobile": "64px",
      "hero-tablet": "90px",
      "hero-desktop": "120px",

      "nav-mobile": "68px",
      "nav-desktop": "80px",

      "touch-min": "44px",
      "touch-comfort": "52px",
    },

    fontSize: {
      "hero-mobile": ["clamp(34px, 10vw, 42px)", { lineHeight: "1.02" }],
      "hero-tablet": ["clamp(48px, 7vw, 56px)", { lineHeight: "1" }],
      "hero-desktop": ["clamp(64px, 5.8vw, 72px)", { lineHeight: "0.98" }],

      "section-mobile": ["clamp(28px, 8vw, 36px)", { lineHeight: "1.08" }],
      "section-tablet": ["clamp(38px, 5vw, 46px)", { lineHeight: "1.04" }],
      "section-desktop": ["clamp(48px, 4.5vw, 56px)", { lineHeight: "1" }],

      "card-mobile": ["18px", { lineHeight: "1.2" }],
      "card-desktop": ["24px", { lineHeight: "1.18" }],
      "body-mobile": ["15px", { lineHeight: "1.65" }],
      "body-desktop": ["18px", { lineHeight: "1.7" }],
      "label-mobile": ["11px", { lineHeight: "1.4", letterSpacing: "0.14em" }],
      "label-desktop": ["14px", { lineHeight: "1.4", letterSpacing: "0.14em" }],
    },

    gridTemplateColumns: {
      "recipe-mobile": "minmax(0, 1fr)",
      "recipe-tablet": "repeat(2, minmax(0, 1fr))",
      "recipe-desktop": "repeat(3, minmax(0, 1fr))",
      "category-mobile": "repeat(2, minmax(0, 1fr))",
      "category-tablet": "repeat(2, minmax(0, 1fr))",
      "category-desktop": "repeat(4, minmax(0, 1fr))",
      "footer-desktop": "1.25fr 0.75fr 0.9fr 1fr",
    },
  },
};

export const responsiveTokens = {
  breakpoints: {
    mobile: "320px-639px",
    sm: "640px+",
    md: "768px+",
    lg: "1024px+",
    xl: "1280px+",
    "2xl": "1536px+",
  },
  containerPadding: {
    mobile: "16px",
    sm: "20px",
    md: "24px",
    xl: "32px",
    "2xl": "48px",
  },
  maxWidth: {
    page: "1280px",
    text: "680px-720px",
    form: "600px",
  },
  touchTarget: {
    minimum: "44px",
    recommended: "48px-56px",
  },
  navHeight: {
    mobile: "64px-68px",
    desktop: "80px",
  },
  gridGap: {
    mobile: "16px",
    tablet: "24px",
    desktop: "32px",
  },
} as const;
