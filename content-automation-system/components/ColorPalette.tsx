'use client'

import React from 'react'
import { colorPalette, semanticColors, categoryColors } from '@/config/colors'

/**
 * COLOR PALETTE SHOWCASE
 * Visual representation of the complete YARA BITES color system
 */

const ColorSwatch = ({
  name,
  hex,
  description,
}: {
  name: string
  hex: string
  description?: string
}) => {
  return (
    <div className="flex flex-col gap-3">
      <div
        className="w-full h-24 rounded-lg border border-border-soft shadow-soft transition-transform duration-300 hover:shadow-hover hover:scale-105 cursor-pointer"
        style={{ backgroundColor: hex }}
        title={hex}
      />
      <div>
        <h4 className="text-sm font-semibold text-text-primary">{name}</h4>
        <p className="text-xs text-text-muted font-mono mt-1">{hex}</p>
        {description && <p className="text-xs text-text-muted mt-2">{description}</p>}
      </div>
    </div>
  )
}

/**
 * BRAND COLORS SECTION
 */
export const BrandColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Brand Colors</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <ColorSwatch
          name="Brand Charcoal"
          hex={colorPalette.brand.charcoal}
          description="Primary text, headings, navigation"
        />
        <ColorSwatch
          name="Brand Brown"
          hex={colorPalette.brand.brown}
          description="Primary CTAs, links, highlights"
        />
        <ColorSwatch
          name="Soft Gold"
          hex={colorPalette.brand.gold}
          description="Badges, accents, decorative elements"
        />
      </div>
    </section>
  )
}

/**
 * SURFACE COLORS SECTION
 */
export const SurfaceColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Surface Colors</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <ColorSwatch
          name="Pure White"
          hex={colorPalette.surface.white}
          description="Cards, surfaces, forms"
        />
        <ColorSwatch
          name="Warm Off-White"
          hex={colorPalette.surface.warm}
          description="Main page background"
        />
        <ColorSwatch
          name="Light Cream"
          hex={colorPalette.surface.cream}
          description="Alternate sections, CTAs"
        />
        <ColorSwatch
          name="Soft Beige"
          hex={colorPalette.surface.beige}
          description="Category chips, secondary surfaces"
        />
      </div>
    </section>
  )
}

/**
 * TEXT COLORS SECTION
 */
export const TextColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Text Colors</h2>
      <div className="space-y-6">
        <div className="p-6 bg-white rounded-lg border border-border-soft">
          <p className="text-text-primary text-lg font-semibold">
            Primary Text • {colorPalette.text.primary}
          </p>
          <p className="text-sm text-text-muted mt-2">Used for main headings and important content</p>
        </div>

        <div className="p-6 bg-white rounded-lg border border-border-soft">
          <p className="text-text-secondary text-lg">
            Secondary Text • {colorPalette.text.secondary}
          </p>
          <p className="text-sm text-text-muted mt-2">
            Used for body text, descriptions, and supporting content
          </p>
        </div>

        <div className="p-6 bg-white rounded-lg border border-border-soft">
          <p className="text-text-muted text-lg">
            Light Text • {colorPalette.text.light}
          </p>
          <p className="text-sm text-text-muted mt-2">Used for captions, labels, and helper text</p>
        </div>

        <div className="p-6 bg-brand-charcoal rounded-lg border border-border-soft">
          <p className="text-white text-lg">
            Inverse Text • {colorPalette.text.inverse}
          </p>
          <p className="text-sm text-white/80 mt-2">Used for text on dark backgrounds</p>
        </div>
      </div>
    </section>
  )
}

/**
 * INTERACTIVE COLORS SECTION
 */
export const InteractiveColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Interactive Colors</h2>

      {/* Buttons */}
      <div className="mb-12">
        <h3 className="text-xl font-semibold text-text-primary mb-6">Buttons</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <button className="btn-primary px-6 py-3 rounded-lg font-medium">
              Primary Button
            </button>
            <p className="text-sm text-text-muted mt-3">
              Default: {colorPalette.interactive.primaryDefault}
            </p>
            <p className="text-sm text-text-muted">
              Hover: {colorPalette.interactive.primaryHover}
            </p>
          </div>

          <div>
            <button className="btn-secondary px-6 py-3 rounded-lg font-medium">
              Secondary Button
            </button>
            <p className="text-sm text-text-muted mt-3">
              Border: {colorPalette.interactive.secondaryBorder}
            </p>
            <p className="text-sm text-text-muted">
              Text: {colorPalette.interactive.secondaryText}
            </p>
          </div>

          <div>
            <button className="btn-tertiary px-6 py-3 rounded-lg font-medium">
              Tertiary Button
            </button>
            <p className="text-sm text-text-muted mt-3">Text only link style button</p>
          </div>
        </div>
      </div>

      {/* Links */}
      <div>
        <h3 className="text-xl font-semibold text-text-primary mb-6">Links</h3>
        <div className="space-y-4">
          <div>
            <a href="#" className="link-primary">
              Default Link • {colorPalette.interactive.linkDefault}
            </a>
            <p className="text-sm text-text-muted mt-2">Hover: {colorPalette.interactive.linkHover}</p>
          </div>

          <div>
            <p className="text-sm text-text-muted">
              Focus Ring: {colorPalette.interactive.focusRing} @ {colorPalette.interactive.focusRingOpacity * 100}%
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

/**
 * STATUS COLORS SECTION
 */
export const StatusColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Status Colors</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Success */}
        <div className="p-6 rounded-lg border border-border-soft" style={{ backgroundColor: colorPalette.status.successBg }}>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-full"
              style={{ backgroundColor: colorPalette.status.success }}
            />
            <h4 className="font-semibold" style={{ color: colorPalette.status.success }}>
              Success
            </h4>
          </div>
          <p className="text-sm text-text-primary">
            Color: {colorPalette.status.success}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            Background: {colorPalette.status.successBg}
          </p>
        </div>

        {/* Error */}
        <div className="p-6 rounded-lg border border-border-soft" style={{ backgroundColor: colorPalette.status.errorBg }}>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-full"
              style={{ backgroundColor: colorPalette.status.error }}
            />
            <h4 className="font-semibold" style={{ color: colorPalette.status.error }}>
              Error
            </h4>
          </div>
          <p className="text-sm text-text-primary">
            Color: {colorPalette.status.error}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            Background: {colorPalette.status.errorBg}
          </p>
        </div>

        {/* Warning */}
        <div className="p-6 rounded-lg border border-border-soft" style={{ backgroundColor: colorPalette.status.warningBg }}>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-full"
              style={{ backgroundColor: colorPalette.status.warning }}
            />
            <h4 className="font-semibold" style={{ color: colorPalette.status.warning }}>
              Warning
            </h4>
          </div>
          <p className="text-sm text-text-primary">
            Color: {colorPalette.status.warning}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            Background: {colorPalette.status.warningBg}
          </p>
        </div>
      </div>
    </section>
  )
}

/**
 * CATEGORY COLORS SECTION
 */
export const CategoryColorsSection = () => {
  const categories = [
    { name: 'Breakfast', key: 'breakfast' },
    { name: 'Lunch', key: 'lunch' },
    { name: 'Dinner', key: 'dinner' },
    { name: 'Dessert', key: 'dessert' },
    { name: 'Healthy', key: 'healthy' },
    { name: 'Quick Meals', key: 'quickMeals' },
  ]

  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Category Colors</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        {categories.map((cat) => (
          <div key={cat.key}>
            <div
              className="h-32 rounded-lg border border-border-soft shadow-soft hover:shadow-hover transition-all"
              style={{
                backgroundColor: categoryColors[cat.key as keyof typeof categoryColors],
              }}
            />
            <h4 className="mt-3 font-semibold text-text-primary">{cat.name}</h4>
            <p className="text-xs text-text-muted font-mono mt-1">
              {categoryColors[cat.key as keyof typeof categoryColors]}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}

/**
 * BORDER COLORS SECTION
 */
export const BorderColorsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Border Colors</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          className="p-8 rounded-lg"
          style={{ borderWidth: '2px', borderColor: colorPalette.border.soft }}
        >
          <h4 className="font-semibold text-text-primary mb-2">Soft Border</h4>
          <p className="text-sm text-text-muted">{colorPalette.border.soft}</p>
          <p className="text-xs text-text-muted mt-2">Cards, inputs, standard dividers</p>
        </div>

        <div
          className="p-8 rounded-lg"
          style={{ borderWidth: '2px', borderColor: colorPalette.border.light }}
        >
          <h4 className="font-semibold text-text-primary mb-2">Light Border</h4>
          <p className="text-sm text-text-muted">{colorPalette.border.light}</p>
          <p className="text-xs text-text-muted mt-2">Subtle separators, minimal contrast</p>
        </div>
      </div>
    </section>
  )
}

/**
 * GRADIENT SECTION
 */
export const GradientsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Gradients</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div
          className="h-40 rounded-lg border border-border-soft shadow-soft"
          style={{
            backgroundImage: colorPalette.gradient.editorialBg,
          }}
        >
          <div className="p-4 h-full flex flex-col justify-end">
            <h4 className="font-semibold text-text-primary">Editorial</h4>
            <p className="text-xs text-text-muted mt-1">Main background gradient</p>
          </div>
        </div>

        <div
          className="h-40 rounded-lg border border-border-soft shadow-soft"
          style={{
            backgroundImage: colorPalette.gradient.ctaBg,
          }}
        >
          <div className="p-4 h-full flex flex-col justify-end">
            <h4 className="font-semibold text-text-primary">CTA</h4>
            <p className="text-xs text-text-muted mt-1">Call-to-action gradient</p>
          </div>
        </div>

        <div
          className="h-40 rounded-lg border border-border-soft shadow-soft bg-surface-white"
          style={{
            backgroundImage: colorPalette.gradient.accentGlow,
          }}
        >
          <div className="p-4 h-full flex flex-col justify-end">
            <h4 className="font-semibold text-text-primary">Accent Glow</h4>
            <p className="text-xs text-text-muted mt-1">Subtle accent overlay</p>
          </div>
        </div>
      </div>
    </section>
  )
}

/**
 * SHADOW SECTION
 */
export const ShadowsSection = () => {
  return (
    <section className="py-16">
      <h2 className="text-3xl font-bold text-text-primary mb-8">Shadows</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div
          className="h-32 rounded-lg bg-white"
          style={{ boxShadow: colorPalette.shadow.soft }}
        >
          <div className="p-4">
            <h4 className="font-semibold text-text-primary">Soft</h4>
            <p className="text-xs text-text-muted mt-2">{colorPalette.shadow.soft}</p>
          </div>
        </div>

        <div
          className="h-32 rounded-lg bg-white"
          style={{ boxShadow: colorPalette.shadow.medium }}
        >
          <div className="p-4">
            <h4 className="font-semibold text-text-primary">Medium</h4>
            <p className="text-xs text-text-muted mt-2">{colorPalette.shadow.medium}</p>
          </div>
        </div>

        <div
          className="h-32 rounded-lg bg-white"
          style={{ boxShadow: colorPalette.shadow.hover }}
        >
          <div className="p-4">
            <h4 className="font-semibold text-text-primary">Hover</h4>
            <p className="text-xs text-text-muted mt-2">{colorPalette.shadow.hover}</p>
          </div>
        </div>
      </div>
    </section>
  )
}

/**
 * COMPLETE COLOR PALETTE SHOWCASE
 */
export const ColorPaletteShowcase = () => {
  return (
    <div className="bg-surface-warm min-h-screen py-16">
      <div className="max-w-7xl mx-auto px-4">
        <header className="mb-20">
          <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-4">
            YARA BITES Color System
          </h1>
          <p className="text-lg text-text-secondary max-w-prose">
            A premium, warm, elegant color palette designed for editorial recipe publications.
            Built with luxury lifestyle brands in mind.
          </p>
        </header>

        <div className="space-y-20">
          <BrandColorsSection />
          <SurfaceColorsSection />
          <TextColorsSection />
          <InteractiveColorsSection />
          <StatusColorsSection />
          <CategoryColorsSection />
          <BorderColorsSection />
          <GradientsSection />
          <ShadowsSection />
        </div>

        {/* Color Grid Export */}
        <section className="py-16 mt-20 pt-20 border-t border-border-soft">
          <h2 className="text-3xl font-bold text-text-primary mb-8">Quick Reference</h2>
          <div className="bg-white rounded-lg p-8 border border-border-soft">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-soft">
                  <th className="text-left py-3 font-semibold text-text-primary">Color Name</th>
                  <th className="text-left py-3 font-semibold text-text-primary">Hex Value</th>
                  <th className="text-left py-3 font-semibold text-text-primary">Usage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-soft">
                <tr>
                  <td className="py-3 text-text-primary font-medium">Brand Charcoal</td>
                  <td className="py-3 font-mono text-text-secondary">#1F1F1F</td>
                  <td className="py-3 text-text-muted">Primary text, headings</td>
                </tr>
                <tr>
                  <td className="py-3 text-text-primary font-medium">Brand Brown</td>
                  <td className="py-3 font-mono text-text-secondary">#8B6B4A</td>
                  <td className="py-3 text-text-muted">CTAs, links, highlights</td>
                </tr>
                <tr>
                  <td className="py-3 text-text-primary font-medium">Soft Gold</td>
                  <td className="py-3 font-mono text-text-secondary">#C6A87A</td>
                  <td className="py-3 text-text-muted">Accents, badges, focus</td>
                </tr>
                <tr>
                  <td className="py-3 text-text-primary font-medium">Warm Off-White</td>
                  <td className="py-3 font-mono text-text-secondary">#FAF7F2</td>
                  <td className="py-3 text-text-muted">Main background</td>
                </tr>
                <tr>
                  <td className="py-3 text-text-primary font-medium">Soft Border</td>
                  <td className="py-3 font-mono text-text-secondary">#E8E1D8</td>
                  <td className="py-3 text-text-muted">Card borders, inputs</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}

export default ColorPaletteShowcase
