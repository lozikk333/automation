/**
 * YARA BITES Typography System - Component Examples
 * Live examples of proper typography usage across the website
 */

'use client'

import React from 'react'

/**
 * HERO SECTION EXAMPLE
 * Demonstrates display typography and responsive sizing
 */
export const HeroSectionExample = () => {
  return (
    <section className="py-20 lg:py-28">
      <div className="max-w-hero mx-auto px-4">
        {/* Main Headline */}
        <h1 className="text-display-xl font-display font-bold text-primary">
          Discover Culinary Magic
        </h1>

        {/* Subtitle */}
        <p className="text-body-lg text-secondary mt-8 max-w-prose">
          Simple, delicious recipes made for everyday cooking, cozy gatherings,
          and sweet moments in the kitchen.
        </p>

        {/* CTA Button */}
        <button className="mt-10 px-8 py-4 bg-amber-900 text-white text-button font-medium rounded-lg hover:bg-amber-950 transition-colors duration-300">
          Explore Recipes
        </button>
      </div>
    </section>
  )
}

/**
 * RECIPE CARD EXAMPLE
 * Shows proper hierarchy and typography in cards
 */
export const RecipeCardExample = () => {
  return (
    <article className="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow duration-300">
      {/* Card Image Placeholder */}
      <div className="w-full h-48 bg-gradient-to-br from-amber-100 to-orange-100" />

      {/* Card Content */}
      <div className="p-6">
        {/* Category Badge */}
        <span className="inline-block text-label text-accent tracking-wider font-semibold uppercase">
          Breakfast
        </span>

        {/* Recipe Title */}
        <h3 className="text-heading-lg font-display font-semibold text-primary mt-4 line-clamp-2">
          Classic French Toast with Vanilla Custard
        </h3>

        {/* Description */}
        <p className="text-body text-secondary mt-4">
          Golden-brown French toast dipped in a silky vanilla custard, topped with
          fresh berries and a drizzle of maple syrup.
        </p>

        {/* Recipe Meta */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-neutral-100">
          <div>
            <p className="text-meta text-light font-medium">Prep Time</p>
            <p className="text-body-sm text-primary font-semibold mt-1">10 mins</p>
          </div>
          <div>
            <p className="text-meta text-light font-medium">Cook Time</p>
            <p className="text-body-sm text-primary font-semibold mt-1">15 mins</p>
          </div>
          <div>
            <p className="text-meta text-light font-medium">Servings</p>
            <p className="text-body-sm text-primary font-semibold mt-1">4 servings</p>
          </div>
        </div>
      </div>
    </article>
  )
}

/**
 * BLOG ARTICLE EXAMPLE
 * Full article with proper typography hierarchy
 */
export const BlogArticleExample = () => {
  return (
    <article className="max-w-body mx-auto px-4 py-16">
      {/* Article Header */}
      <header className="mb-12">
        {/* Category */}
        <span className="text-label text-accent uppercase tracking-wider font-semibold">
          Cooking Tips
        </span>

        {/* Title */}
        <h1 className="text-display-lg font-display font-bold text-primary mt-4">
          The Perfect Cup of Coffee: A Guide to Brewing
        </h1>

        {/* Article Meta */}
        <div className="flex flex-wrap gap-6 mt-8 pt-8 border-t border-neutral-200">
          <div>
            <p className="text-meta text-light">By Sarah Johnson</p>
          </div>
          <div>
            <p className="text-meta text-light">May 10, 2026</p>
          </div>
          <div>
            <p className="text-meta text-light">8 min read</p>
          </div>
        </div>
      </header>

      {/* Lead Paragraph */}
      <p className="text-body-lg text-primary leading-relaxed mb-8 italic">
        Coffee is more than just a morning beverage—it's a ritual, a moment of
        peace before the day begins. But what makes a truly exceptional cup of coffee?
      </p>

      {/* Body Content */}
      <div className="space-y-6">
        <p className="text-body text-primary leading-relaxed">
          The journey from bean to cup is a delicate process that involves numerous
          variables, each one affecting the final flavor profile. Water temperature,
          grind size, brewing time, and the coffee bean itself all play crucial roles
          in creating the perfect cup.
        </p>

        {/* Subheading */}
        <h2 className="text-heading-lg font-display font-semibold text-primary mt-12 mb-6">
          Understanding Water Temperature
        </h2>

        <p className="text-body text-primary leading-relaxed">
          The water temperature is arguably one of the most critical factors in coffee
          brewing. Ideally, water should be heated to between 195°F and 205°F (90-96°C).
          This temperature range ensures optimal extraction of the coffee's oils and
          flavors without burning the grounds.
        </p>

        {/* Subsection */}
        <h3 className="text-heading-md font-ui font-semibold text-primary mt-10 mb-4">
          Too Hot: Risk of Over-Extraction
        </h3>

        <p className="text-body text-primary leading-relaxed">
          Water that's too hot can over-extract the coffee, pulling out bitter compounds
          that create an unpleasant, harsh flavor. This is one of the most common mistakes
          home brewers make.
        </p>
      </div>

      {/* Call-to-Action */}
      <div className="mt-16 p-8 bg-neutral-50 rounded-lg border border-neutral-200">
        <h3 className="text-heading-md font-ui font-semibold text-primary">
          Never Miss a Recipe
        </h3>
        <p className="text-body text-secondary mt-3">
          Subscribe to our newsletter for weekly recipes, cooking tips, and
          culinary inspiration delivered to your inbox.
        </p>
        <button className="mt-6 px-6 py-3 bg-amber-900 text-white text-button font-semibold rounded-lg hover:bg-amber-950 transition-colors duration-300">
          Subscribe Now
        </button>
      </div>
    </article>
  )
}

/**
 * RECIPE GRID EXAMPLE
 * Multiple cards with consistent typography
 */
export const RecipeGridExample = () => {
  const recipes = [
    { title: 'Creamy Pasta Carbonara', category: 'Dinner', time: '20 mins' },
    { title: 'Chocolate Chip Cookies', category: 'Dessert', time: '25 mins' },
    { title: 'Buddha Bowl with Tahini Dressing', category: 'Lunch', time: '15 mins' },
  ]

  return (
    <section className="py-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Section Title */}
        <h2 className="text-display-lg font-display font-bold text-primary mb-4">
          Trending Recipes
        </h2>

        {/* Subtitle */}
        <p className="text-body-lg text-secondary mb-12 max-w-prose">
          Discover our most loved recipes, curated for taste and simplicity.
        </p>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {recipes.map((recipe) => (
            <div
              key={recipe.title}
              className="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-lg transition-all duration-300"
            >
              <div className="w-full h-40 bg-gradient-to-br from-amber-50 to-orange-50" />
              <div className="p-6">
                <span className="text-label text-accent uppercase font-semibold">
                  {recipe.category}
                </span>
                <h3 className="text-heading-md font-ui font-bold text-primary mt-3">
                  {recipe.title}
                </h3>
                <p className="text-meta text-light mt-3">{recipe.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/**
 * FOOTER EXAMPLE
 * Proper typography usage in footer
 */
export const FooterExample = () => {
  return (
    <footer className="bg-neutral-900 text-white border-t border-neutral-200">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Column */}
          <div>
            <h3 className="text-heading-md font-display font-bold text-white mb-4">
              YARA BITES
            </h3>
            <p className="text-body-sm text-gray-300">
              Simple, delicious recipes made with love.
            </p>
          </div>

          {/* Navigation Column */}
          <div>
            <h4 className="text-label text-white uppercase tracking-wider font-semibold mb-6">
              Quick Links
            </h4>
            <ul className="space-y-3">
              {['Home', 'Recipes', 'About', 'Contact'].map((link) => (
                <li key={link}>
                  <a href="#" className="text-body-sm text-gray-400 hover:text-white transition-colors">
                    {link}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Categories Column */}
          <div>
            <h4 className="text-label text-white uppercase tracking-wider font-semibold mb-6">
              Categories
            </h4>
            <ul className="space-y-3">
              {['Breakfast', 'Lunch', 'Dinner', 'Dessert'].map((cat) => (
                <li key={cat}>
                  <a href="#" className="text-body-sm text-gray-400 hover:text-white transition-colors">
                    {cat}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter Column */}
          <div>
            <h4 className="text-label text-white uppercase tracking-wider font-semibold mb-4">
              Newsletter
            </h4>
            <p className="text-body-sm text-gray-400 mb-4">
              Subscribe for weekly recipes.
            </p>
            <input
              type="email"
              placeholder="Your email"
              className="w-full px-4 py-2 rounded bg-neutral-800 text-white text-body-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-600"
            />
          </div>
        </div>

        {/* Footer Bottom */}
        <div className="pt-8 border-t border-neutral-800 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <p className="text-body-sm text-gray-500">
            © 2026 YARA BITES. All rights reserved.
          </p>
          <div className="flex gap-6">
            {['Privacy', 'Terms', 'Cookies'].map((link) => (
              <a
                key={link}
                href="#"
                className="text-body-sm text-gray-500 hover:text-white transition-colors"
              >
                {link}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}

/**
 * TYPOGRAPHY SHOWCASE
 * All typography scales demonstrated
 */
export const TypographyShowcase = () => {
  return (
    <section className="max-w-4xl mx-auto px-4 py-20">
      <h1 className="text-display-xl font-display font-bold text-primary mb-12">
        Typography System
      </h1>

      {/* Display Scales */}
      <div className="mb-16">
        <h2 className="text-heading-md font-ui font-bold text-secondary mb-8">
          Display Scales
        </h2>

        <div className="space-y-8">
          <div>
            <span className="text-label text-accent">Display XL • 72px</span>
            <h3 className="text-display-xl font-display font-bold text-primary mt-4">
              The Art of Premium Typography
            </h3>
          </div>

          <div>
            <span className="text-label text-accent">Display Large • 56px</span>
            <h3 className="text-display-lg font-display font-bold text-primary mt-4">
              Creating Elegant Editorial Moments
            </h3>
          </div>

          <div>
            <span className="text-label text-accent">Display Medium • 42px</span>
            <h3 className="text-display-md font-display font-bold text-primary mt-4">
              Building Visual Hierarchy
            </h3>
          </div>
        </div>
      </div>

      {/* Heading Scales */}
      <div className="mb-16">
        <h2 className="text-heading-md font-ui font-bold text-secondary mb-8">
          Heading Scales
        </h2>

        <div className="space-y-6">
          <div>
            <span className="text-label text-accent">Heading Large • 30px</span>
            <h3 className="text-heading-lg font-display font-semibold text-primary mt-4">
              Perfect Recipe Titles
            </h3>
          </div>

          <div>
            <span className="text-label text-accent">Heading Medium • 24px</span>
            <h3 className="text-heading-md font-ui font-bold text-primary mt-4">
              Card Headings and Features
            </h3>
          </div>
        </div>
      </div>

      {/* Body Scales */}
      <div className="mb-16">
        <h2 className="text-heading-md font-ui font-bold text-secondary mb-8">
          Body Scales
        </h2>

        <div className="space-y-6">
          <div>
            <span className="text-label text-accent">Body Large • 18px</span>
            <p className="text-body-lg text-primary mt-4">
              This is body large text, perfect for lead paragraphs and author introductions.
              It maintains excellent readability with proper line height and generous spacing.
            </p>
          </div>

          <div>
            <span className="text-label text-accent">Body Default • 16px</span>
            <p className="text-body text-primary mt-4">
              This is the default body text size, used for standard content throughout the website.
              It strikes the perfect balance between readability and density.
            </p>
          </div>

          <div>
            <span className="text-label text-accent">Body Small • 14px</span>
            <p className="text-body-sm text-secondary mt-4">
              This is small body text, ideal for metadata, captions, and supporting information.
            </p>
          </div>
        </div>
      </div>

      {/* Utility Scales */}
      <div>
        <h2 className="text-heading-md font-ui font-bold text-secondary mb-8">
          Utility Scales
        </h2>

        <div className="space-y-6">
          <div>
            <span className="text-label text-accent">Label / Micro • 12px</span>
            <p className="text-label text-accent mt-4">BREAKFAST</p>
          </div>

          <div>
            <span className="text-label text-accent">Button • 16px</span>
            <button className="text-button font-semibold bg-amber-900 text-white px-6 py-3 rounded mt-4 hover:bg-amber-950 transition-colors">
              Subscribe Now
            </button>
          </div>

          <div>
            <span className="text-label text-accent">Navigation • 16px</span>
            <nav className="flex gap-6 mt-4">
              <a href="#" className="text-navigation text-primary hover:text-accent transition-colors">
                Home
              </a>
              <a href="#" className="text-navigation text-primary hover:text-accent transition-colors">
                Recipes
              </a>
              <a href="#" className="text-navigation text-primary hover:text-accent transition-colors">
                About
              </a>
            </nav>
          </div>

          <div>
            <span className="text-label text-accent">Meta / Recipe Info • 14px</span>
            <p className="text-meta text-light mt-4">Prep time: 20 minutes • Serves: 4 people</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default TypographyShowcase
