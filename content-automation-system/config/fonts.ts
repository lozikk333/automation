import { Playfair_Display, Inter } from 'next/font/google';

/**
 * YARA BITES Typography System
 * Premium Editorial Food Blog Font Configuration
 *
 * Font Pairing:
 * - Display: Playfair Display (serif) - luxury headlines & editorial moments
 * - UI: Inter (sans-serif) - body text, UI, navigation
 */

/**
 * Primary Display Font
 * Used for: hero headlines, section titles, article headings, feature callouts
 * Characteristics: elegant, luxurious, high contrast, sophisticated, editorial
 */
export const playfairDisplay = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  fallback: ['Georgia', 'serif'],
});

/**
 * Secondary UI Font
 * Used for: body text, buttons, navigation, metadata, descriptions, forms
 * Characteristics: modern, crisp, highly readable, minimal, clean
 */
export const inter = Inter({
  subsets: ['latin'],
  variable: '--font-ui',
  weight: ['400', '500', '600', '700', '800'],
  display: 'swap',
  fallback: ['Helvetica Neue', 'sans-serif'],
});

/**
 * Font Variable Classes for use in root layout
 * Example: <html className={`${playfairDisplay.variable} ${inter.variable}`}>
 */
export const fontVariables = `${playfairDisplay.variable} ${inter.variable}`;
