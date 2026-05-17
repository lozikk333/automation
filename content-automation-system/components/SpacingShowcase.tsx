'use client'

import React from 'react'

/**
 * YARA BITES Spacing System Showcase
 * Visual demonstration of all spacing patterns and utilities
 */

interface SpacingExampleProps {
  size: string
  value: string
}

function SpacingExample({ size, value }: SpacingExampleProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-4 mb-3">
        <code className="text-sm font-mono bg-gray-100 px-3 py-1 rounded">{size}</code>
        <span className="text-sm text-gray-600">{value}</span>
      </div>
      <div className="bg-warm rounded p-4 border border-gold">
        <div className="w-full bg-charcoal rounded" style={{ height: value }} />
      </div>
    </div>
  )
}

function ColorBox({
  label,
  className,
}: {
  label: string
  className: string
}) {
  return (
    <div className="text-center mb-4">
      <div className={`${className} rounded h-24 mb-2`} />
      <code className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
        {label}
      </code>
    </div>
  )
}

function GridExample({
  columns,
  gap,
}: {
  columns: number
  gap: string
}) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap,
      }}
    >
      {Array.from({ length: columns }).map((_, i) => (
        <div key={i} className="bg-warm rounded p-4 border border-gold aspect-square flex items-center justify-center text-sm font-medium text-charcoal">
          {i + 1}
        </div>
      ))}
    </div>
  )
}

export function SpacingShowcase() {
  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="section-hero bg-gradient-to-b from-warm to-white">
        <div className="container-max container-px">
          <div className="hero-max-width mx-auto text-center">
            <span className="text-label text-secondary">Design System</span>
            <h1 className="text-display-xl mt-4 md:mt-6">Spacing System</h1>
            <p className="text-body-lg text-secondary mt-6">
              Premium editorial layout rhythm based on an 8px grid
            </p>
          </div>
        </div>
      </section>

      {/* Spacing Scale */}
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Spacing Scale</h2>
          <p className="text-body-lg text-secondary mt-4">
            The fundamental spacing scale used throughout the system. All values derived from 8px base unit.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">
            <SpacingExample size="xs" value="4px" />
            <SpacingExample size="sm" value="8px" />
            <SpacingExample size="md" value="16px" />
            <SpacingExample size="lg" value="24px" />
            <SpacingExample size="xl" value="32px" />
            <SpacingExample size="2xl" value="48px" />
            <SpacingExample size="3xl" value="64px" />
            <SpacingExample size="4xl" value="80px" />
            <SpacingExample size="5xl" value="96px" />
            <SpacingExample size="6xl" value="120px" />
            <SpacingExample size="7xl" value="160px" />
          </div>
        </div>
      </section>

      {/* Section Spacing */}
      <section className="section-medium bg-warm">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Section Spacing</h2>
          <p className="text-body-lg text-secondary mt-4">
            Responsive section padding for different layout importance levels.
          </p>

          <div className="space-y-12 mt-12">
            {/* Hero Section Example */}
            <div>
              <h3 className="text-heading-lg mb-4">Hero Section (py-20 md:py-28 lg:py-32)</h3>
              <div className="bg-white rounded border-2 border-charcoal">
                <div className="py-20 md:py-28 lg:py-32 px-8 bg-warm border-2 border-gold text-center">
                  <p className="text-sm text-charcoal font-mono">Extra spacious top/bottom padding</p>
                </div>
              </div>
            </div>

            {/* Major Section Example */}
            <div>
              <h3 className="text-heading-lg mb-4">Major Section (py-24 md:py-32 lg:py-36)</h3>
              <div className="bg-white rounded border-2 border-charcoal">
                <div className="py-24 md:py-32 lg:py-36 px-8 bg-warm border-2 border-gold text-center">
                  <p className="text-sm text-charcoal font-mono">Large premium padding</p>
                </div>
              </div>
            </div>

            {/* Medium Section Example */}
            <div>
              <h3 className="text-heading-lg mb-4">Medium Section (py-16 md:py-20 lg:py-24)</h3>
              <div className="bg-white rounded border-2 border-charcoal">
                <div className="py-16 md:py-20 lg:py-24 px-8 bg-warm border-2 border-gold text-center">
                  <p className="text-sm text-charcoal font-mono">Standard section padding</p>
                </div>
              </div>
            </div>

            {/* Small Section Example */}
            <div>
              <h3 className="text-heading-lg mb-4">Small Section (py-12 md:py-16 lg:py-20)</h3>
              <div className="bg-white rounded border-2 border-charcoal">
                <div className="py-12 md:py-16 lg:py-20 px-8 bg-warm border-2 border-gold text-center">
                  <p className="text-sm text-charcoal font-mono">Compact section padding</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Container Widths */}
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Container Widths</h2>
          <p className="text-body-lg text-secondary mt-4">
            Predefined max-widths for different content types.
          </p>

          <div className="space-y-8 mt-12">
            {[
              { name: 'Content (max-w-7xl)', width: '1280px' },
              { name: 'Hero (max-w-2xl)', width: '800px' },
              { name: 'Text (max-w-3xl)', width: '720px' },
              { name: 'Form (max-w-2xl)', width: '600px' },
            ].map((container) => (
              <div key={container.name}>
                <p className="text-sm font-mono text-secondary mb-3">{container.name}</p>
                <div className="bg-gray-200 rounded p-4">
                  <div
                    className="bg-warm rounded border-2 border-charcoal mx-auto py-8 flex items-center justify-center text-charcoal font-mono"
                    style={{ maxWidth: container.width }}
                  >
                    {container.width}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Card Padding */}
      <section className="section-medium bg-warm">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Card Padding</h2>
          <p className="text-body-lg text-secondary mt-4">
            Padding options for different card types.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
            {[
              { name: 'Large (p-8)', padding: '32px' },
              { name: 'Medium (p-6)', padding: '24px' },
              { name: 'Small (p-4)', padding: '16px' },
            ].map((card) => (
              <div key={card.name} className="bg-white rounded border-2 border-charcoal overflow-hidden">
                <div
                  className="bg-warm border-b-2 border-charcoal flex items-center justify-center text-charcoal font-mono text-sm"
                  style={{ padding: card.padding, minHeight: '100px' }}
                >
                  {card.padding}
                </div>
                <div className="p-4 bg-white">
                  <p className="text-sm font-mono text-charcoal">{card.name}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Grid Gaps */}
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Grid Gaps</h2>
          <p className="text-body-lg text-secondary mt-4">
            Responsive gap values for different grid contexts.
          </p>

          <div className="space-y-12 mt-12">
            <div>
              <h3 className="text-heading-lg mb-6">Desktop (gap-8: 32px)</h3>
              <GridExample columns={3} gap="32px" />
            </div>
            <div>
              <h3 className="text-heading-lg mb-6">Tablet (gap-6: 24px)</h3>
              <GridExample columns={2} gap="24px" />
            </div>
            <div>
              <h3 className="text-heading-lg mb-6">Mobile (gap-4: 16px)</h3>
              <GridExample columns={1} gap="16px" />
            </div>
          </div>
        </div>
      </section>

      {/* Semantic Tokens */}
      <section className="section-medium bg-warm">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Semantic Spacing Tokens</h2>
          <p className="text-body-lg text-secondary mt-4">
            Named spacing values for different use cases and feelings.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
            {[
              { token: 'micro', value: '4px', use: 'Tight spacing' },
              { token: 'tight', value: '8px', use: 'Related elements' },
              { token: 'compact', value: '12px', use: 'Within components' },
              { token: 'default', value: '16px', use: 'Standard gap' },
              { token: 'comfortable', value: '24px', use: 'Breathing room' },
              { token: 'spacious', value: '32px', use: 'Premium gaps' },
              { token: 'luxury', value: '48px', use: 'Major sections' },
              { token: 'premium', value: '64px', use: 'Largest sections' },
            ].map((item) => (
              <div key={item.token} className="bg-white rounded p-4 border border-charcoal">
                <p className="font-mono font-bold text-charcoal">{item.token}</p>
                <p className="text-sm text-secondary mt-2">{item.value}</p>
                <p className="text-xs text-light mt-2">{item.use}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Component Examples */}
      <section className="section-medium">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Component Examples</h2>
          <p className="text-body-lg text-secondary mt-4">
            Real-world spacing applications in common components.
          </p>

          <div className="space-y-12 mt-12">
            {/* Recipe Card */}
            <div>
              <h3 className="text-heading-lg mb-6">Recipe Card</h3>
              <article className="bg-white rounded overflow-hidden shadow-lg border border-gold">
                <div className="bg-warm h-48 flex items-center justify-center text-charcoal font-mono">
                  Image
                </div>
                <div className="p-6">
                  <span className="text-label text-secondary">Breakfast</span>
                  <h4 className="text-heading-lg mt-4">Classic Pancakes</h4>
                  <p className="text-body text-secondary mt-3">
                    Fluffy and delicious pancakes perfect for Sunday morning.
                  </p>
                  <div className="text-meta text-light mt-4">15 min • Easy</div>
                  <a href="#" className="text-gold font-semibold block mt-5">
                    View Recipe →
                  </a>
                </div>
              </article>
            </div>

            {/* Form */}
            <div>
              <h3 className="text-heading-lg mb-6">Form Spacing</h3>
              <form className="max-w-md space-y-4 md:space-y-6">
                <div>
                  <label className="block mb-2 md:mb-3 font-medium text-charcoal">
                    Email Address
                  </label>
                  <input
                    type="email"
                    className="w-full h-12 md:h-14 px-4 border border-charcoal rounded bg-white"
                    placeholder="your@email.com"
                  />
                </div>
                <div>
                  <label className="block mb-2 md:mb-3 font-medium text-charcoal">
                    Full Name
                  </label>
                  <input
                    type="text"
                    className="w-full h-12 md:h-14 px-4 border border-charcoal rounded bg-white"
                    placeholder="Your name"
                  />
                </div>
                <button className="w-full bg-charcoal text-white px-8 py-4 rounded font-semibold mt-6">
                  Subscribe
                </button>
              </form>
            </div>

            {/* Two Column */}
            <div>
              <h3 className="text-heading-lg mb-6">Two Column Layout</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 lg:gap-16">
                <div className="bg-warm rounded p-8 border-2 border-charcoal text-center">
                  <p className="text-charcoal font-mono">Column 1</p>
                </div>
                <div className="bg-warm rounded p-8 border-2 border-charcoal text-center">
                  <p className="text-charcoal font-mono">Column 2</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mobile Rules */}
      <section className="section-medium bg-warm">
        <div className="container-max container-px">
          <h2 className="text-heading-xl">Mobile Rules</h2>
          <p className="text-body-lg text-secondary mt-4">
            Important spacing rules for mobile-first responsive design.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12">
            <div className="bg-white rounded p-6 border-2 border-charcoal">
              <h4 className="text-heading-lg mb-4">✓ DO</h4>
              <ul className="space-y-3 text-sm">
                <li>✓ Minimum 16px padding on mobile</li>
                <li>✓ Scale spacing responsively</li>
                <li>✓ Touch targets ≥ 44x44px</li>
                <li>✓ Mobile-first class ordering</li>
                <li>✓ Use semantic spacing tokens</li>
              </ul>
            </div>
            <div className="bg-white rounded p-6 border-2 border-charcoal">
              <h4 className="text-heading-lg mb-4">✗ DON'T</h4>
              <ul className="space-y-3 text-sm">
                <li>✗ Allow edges to touch screen</li>
                <li>✗ Use px-0 on mobile</li>
                <li>✗ Cramped layouts</li>
                <li>✗ Inconsistent scaling</li>
                <li>✗ Ignore touch targets</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section-major">
        <div className="container-max container-px">
          <div className="hero-max-width mx-auto text-center">
            <h2 className="text-heading-xl">Ready to use the spacing system?</h2>
            <p className="text-body-lg text-secondary mt-6">
              Check the implementation guide for setup instructions and component patterns.
            </p>
            <a
              href="/config/SPACING_IMPLEMENTATION.md"
              className="inline-block mt-8 px-8 py-4 bg-charcoal text-white rounded font-semibold"
            >
              View Implementation Guide
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default SpacingShowcase
