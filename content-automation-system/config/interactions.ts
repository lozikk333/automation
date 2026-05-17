import type { Variants } from "framer-motion";

export const premiumEase = [0.22, 1, 0.36, 1];

export const interactionTransition = {
  fast: { duration: 0.2, ease: premiumEase },
  default: { duration: 0.28, ease: premiumEase },
  slow: { duration: 0.35, ease: premiumEase },
  reveal: { duration: 0.62, ease: premiumEase },
};

export const revealContainer: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.08,
    },
  },
};

export const revealItem: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: interactionTransition.reveal,
  },
};

export const ctaRevealItem: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: premiumEase },
  },
};

export const buttonHover = {
  y: -2,
  transition: interactionTransition.fast,
};

export const buttonTap = {
  y: 1,
  scale: 0.99,
  transition: { duration: 0.1, ease: "easeOut" },
};

export const cardHover = {
  y: -6,
  transition: interactionTransition.default,
};

export const categoryChipHover = {
  scale: 1.02,
  transition: interactionTransition.fast,
};

export const socialIconHover = {
  y: -2,
  scale: 1.05,
  transition: interactionTransition.fast,
};

export const mobileTap = {
  scale: 0.98,
  transition: { duration: 0.1, ease: "easeOut" },
};

export const reducedMotionViewport = {
  once: true,
  amount: 0.2,
} as const;
