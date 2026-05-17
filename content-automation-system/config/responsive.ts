export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

export const responsiveClassNames = {
  container: "mx-auto w-full max-w-[1280px] px-4 sm:px-5 md:px-6 xl:px-8 2xl:px-12",
  textContainer: "mx-auto w-full max-w-[720px] px-4 sm:px-5 md:px-6",
  section: "py-14 sm:py-16 md:py-20 lg:py-24 xl:py-[120px]",
  heroSection: "py-14 sm:py-16 md:py-[90px] xl:py-[120px]",
  recipeGrid: "grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-3 xl:gap-8",
  categoryGrid: "grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-4 xl:gap-8",
  footerGrid: "grid grid-cols-1 gap-10 md:grid-cols-2 md:gap-12 xl:grid-cols-[1.25fr_0.75fr_0.9fr_1fr]",
  touchTarget: "min-h-11 min-w-11",
  primaryMobileCta: "min-h-12 w-full sm:w-auto",
  mobileOnly: "block lg:hidden",
  desktopOnly: "hidden lg:block",
} as const;

export const responsiveMotion = {
  desktopHover: { y: -6 },
  mobileTap: { scale: 0.98 },
  navDrawer: {
    closed: { opacity: 0, y: -12 },
    open: { opacity: 1, y: 0 },
  },
  fullScreenMenu: {
    closed: { opacity: 0 },
    open: { opacity: 1 },
  },
} as const;
