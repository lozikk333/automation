/**
 * YARA BITES Tailwind Interaction Configuration
 * Premium editorial recipe website shadows, borders, radii, and transitions.
 *
 * Add this to your tailwind.config.ts theme extensions:
 *
 * import { tailwindInteractionConfig } from "@/config/tailwind-interactions.config";
 *
 * export default {
 *   theme: {
 *     extend: {
 *       ...tailwindInteractionConfig,
 *     },
 *   },
 * };
 */

export const tailwindInteractionConfig = {
  boxShadow: {
    "soft-xs": "0 1px 2px rgba(31, 31, 31, 0.04)",
    "soft-sm": "0 4px 12px rgba(31, 31, 31, 0.06)",
    "soft-md": "0 10px 24px rgba(31, 31, 31, 0.08)",
    "soft-lg": "0 18px 40px rgba(31, 31, 31, 0.12)",
    "soft-hover": "0 20px 48px rgba(31, 31, 31, 0.14)",
  },

  borderColor: {
    "interaction-light": "#F1ECE5",
    "interaction-soft": "#E8E1D8",
    "interaction-emphasis": "#D9CBB7",
  },

  borderRadius: {
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    full: "9999px",
  },

  transitionDuration: {
    "smooth-fast": "200ms",
    "smooth-default": "280ms",
    "smooth-slow": "350ms",
  },

  transitionTimingFunction: {
    "premium-out": "cubic-bezier(0.22, 1, 0.36, 1)",
    "soft-out": "ease-out",
  },

  keyframes: {
    "soft-shimmer": {
      "0%": { backgroundPosition: "200% 0" },
      "100%": { backgroundPosition: "-200% 0" },
    },
  },

  animation: {
    "soft-shimmer": "soft-shimmer 1.9s ease-in-out infinite",
  },
};

export const interactionTokens = {
  shadows: {
    xs: "0 1px 2px rgba(31, 31, 31, 0.04)",
    sm: "0 4px 12px rgba(31, 31, 31, 0.06)",
    md: "0 10px 24px rgba(31, 31, 31, 0.08)",
    lg: "0 18px 40px rgba(31, 31, 31, 0.12)",
    hover: "0 20px 48px rgba(31, 31, 31, 0.14)",
  },
  borders: {
    light: "#F1ECE5",
    soft: "#E8E1D8",
    emphasis: "#D9CBB7",
  },
  radii: {
    small: "8px",
    medium: "16px",
    large: "24px",
    xl: "32px",
    full: "9999px",
  },
  focusRing: "0 0 0 4px rgba(198, 168, 122, 0.20)",
  easing: {
    premium: "cubic-bezier(0.22, 1, 0.36, 1)",
    soft: "ease-out",
  },
  duration: {
    fast: "200ms",
    default: "280ms",
    slow: "350ms",
  },
} as const;
