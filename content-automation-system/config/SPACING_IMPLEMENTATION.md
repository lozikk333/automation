# SPACING SYSTEM IMPLEMENTATION GUIDE

## Complete Setup Instructions

This guide walks you through integrating the YARA BITES spacing system into your Next.js project.

---

## Step 1: Configure Tailwind CSS

### Update `tailwind.config.ts`

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'
import { completeSpacingConfig } from '@/config/tailwind-spacing.config'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // Merge spacing config with other extensions
      ...completeSpacingConfig,
      
      // Your other theme extensions
      colors: {
        // your colors
      },
      fontFamily: {
        // your fonts
      },
    },
  },
  plugins: [],
}

export default config
```

---

## Step 2: Import CSS Utilities

### Add to Global Styles

**Option A: In `app/layout.tsx`**

```typescript
// app/layout.tsx
import '@/styles/spacing.css'
import '@/styles/typography.css'
import '@/styles/colors.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>{children}</body>
    </html>
  )
}
```

**Option B: In `styles/globals.css`**

```css
/* styles/globals.css */
@import '@/styles/spacing.css';
@import '@/styles/typography.css';
@import '@/styles/colors.css';

/* Your global styles */
```

---

## Step 3: Verify Configuration

### Test Spacing Classes

Create a test component to verify everything works:

```tsx
// app/test-spacing.tsx
export default function TestSpacing() {
  return (
    <div className="section-major">
      <div className="container-max container-px">
        <h1 className="text-4xl">Spacing System Test</h1>
        <p className="mt-6">This uses section-major spacing</p>
        
        <div className="recipe-grid mt-12">
          <div className="card-p-medium bg-gray-100 rounded">
            <h3 className="text-heading-lg">Card 1</h3>
            <p className="mt-3 text-body">Content here</p>
          </div>
          <div className="card-p-medium bg-gray-100 rounded">
            <h3 className="text-heading-lg">Card 2</h3>
            <p className="mt-3 text-body">Content here</p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### Run Development Server

```bash
npm run dev
# or
yarn dev
```

Visit `http://localhost:3000/test-spacing` and verify spacing displays correctly.

---

## Step 4: Apply to Page Layouts

### Hero Section Template

```tsx
// components/HeroSection.tsx
export function HeroSection() {
  return (
    <section className="section-hero">
      <div className="container-max container-px">
        <div className="hero-max-width mx-auto text-center">
          <span className="text-label text-secondary">New Recipe</span>
          <h1 className="text-display-xl mt-4 md:mt-6">
            Perfect Holiday Desserts
          </h1>
          <p className="text-body-lg text-secondary mt-6">
            Master the art of elegant desserts with our collection
            of sophisticated recipes.
          </p>
          <button className="btn-primary mt-8">
            Browse Recipes
          </button>
        </div>
      </div>
    </section>
  )
}
```

### Recipe Grid Template

```tsx
// components/RecipeGrid.tsx
import { RecipeCard } from '@/components/RecipeCard'

interface Recipe {
  id: string
  title: string
  category: string
  image: string
  // ... other fields
}

export function RecipeGrid({ recipes }: { recipes: Recipe[] }) {
  return (
    <section className="section-medium">
      <div className="container-max container-px">
        <h2 className="text-heading-xl">Featured Recipes</h2>
        
        <div className="recipe-grid mt-12 md:mt-16 lg:mt-20">
          {recipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      </div>
    </section>
  )
}
```

### Form Template

```tsx
// components/SubscribeForm.tsx
export function SubscribeForm() {
  return (
    <form className="form-spacing max-w-md">
      <div className="form-group-spacing">
        <label htmlFor="email" className="form-label-spacing block">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          className="form-input-spacing w-full px-4 border border-gray-300 rounded"
          placeholder="your@email.com"
        />
      </div>

      <div className="form-group-spacing">
        <label htmlFor="name" className="form-label-spacing block">
          Full Name
        </label>
        <input
          id="name"
          type="text"
          className="form-input-spacing w-full px-4 border border-gray-300 rounded"
          placeholder="Your name"
        />
      </div>

      <button className="btn-primary w-full mt-6">
        Subscribe
      </button>
    </form>
  )
}
```

### Two Column Layout Template

```tsx
// components/ContentLayout.tsx
export function ContentLayout({ 
  image, 
  content, 
  imagePosition = 'left'
}: ContentLayoutProps) {
  const gridClass = imagePosition === 'left' 
    ? 'grid-cols-1 lg:grid-cols-2'
    : 'grid-cols-1 lg:grid-cols-2'

  return (
    <section className="section-medium">
      <div className="container-max container-px">
        <div className={`grid ${gridClass} two-column-spacing`}>
          <div>{image}</div>
          <div className="flex flex-col justify-center">
            {content}
          </div>
        </div>
      </div>
    </section>
  )
}
```

---

## Step 5: Mobile-Specific Spacing

### Mobile Padding Rule

Always ensure mobile elements have at least 16px padding:

```tsx
// CORRECT - has mobile padding
<div className="px-4 md:px-6 lg:px-8">
  Content
</div>

// INCORRECT - no mobile padding
<div className="px-0 md:px-6 lg:px-8">
  Content
</div>
```

### Touch Target Sizing

Ensure interactive elements meet 44px minimum:

```tsx
// Button with proper sizing
<button className="px-6 py-3 md:px-8 md:py-4">
  {/* min 44x44px on mobile */}
  Tap me
</button>

// Link area with proper sizing
<a href="#" className="h-12 px-4 flex items-center">
  Link
</a>
```

### Mobile-First Approach

Always define mobile-first, then add responsive modifiers:

```tsx
// CORRECT - mobile first
<div className="py-6 md:py-8 lg:py-10">
  Mobile: 24px, Tablet: 32px, Desktop: 40px
</div>

// INCORRECT - desktop first
<div className="py-10 md:py-8 lg:py-6">
  Confusing hierarchy
</div>
```

---

## Step 6: Responsive Grid Patterns

### Recipe Grid (3-column on desktop)

```tsx
<div className="recipe-grid gap-8">
  {/* grid-cols-1 md:grid-cols-2 lg:grid-cols-3 */}
  {recipes.map(recipe => <RecipeCard key={recipe.id} {...recipe} />)}
</div>
```

### Blog Grid (2-column on desktop)

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-8">
  {articles.map(article => <ArticleCard key={article.id} {...article} />)}
</div>
```

### Feature Grid (4-column on large desktop)

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 grid-gap-standard">
  {items.map(item => <Item key={item.id} {...item} />)}
</div>
```

---

## Step 7: Section Spacing Rules

### Rule: Scale spacing for importance

- **Hero sections**: `section-hero` or `section-major`
- **Main content**: `section-medium`
- **Supplementary**: `section-small`
- **Nested sections**: Scale down one level

### Example Page Structure

```tsx
export default function RecipeDetail() {
  return (
    <>
      {/* Hero - largest spacing */}
      <HeroSection />
      
      {/* Main content - medium spacing */}
      <section className="section-medium">
        <div className="container-max container-px">
          <RecipeContent />
        </div>
      </section>

      {/* Related content - medium spacing */}
      <section className="section-medium bg-warm">
        <div className="container-max container-px">
          <RelatedRecipes />
        </div>
      </section>

      {/* Newsletter - medium spacing */}
      <section className="section-medium">
        <div className="container-max container-px">
          <NewsletterSignup />
        </div>
      </section>

      {/* Footer - custom spacing */}
      <Footer />
    </>
  )
}
```

---

## Step 8: Component-Specific Spacing

### Card Padding Selection

```tsx
// Large cards (featured content)
<article className="card-p-large">
  Featured recipe here
</article>

// Medium cards (standard recipe cards)
<article className="card-p-medium">
  Standard recipe here
</article>

// Small cards (compact layouts)
<article className="card-p-small">
  Compact recipe here
</article>
```

### Internal Card Spacing

```tsx
<article className="card-p-medium">
  <span className="category">Breakfast</span>
  
  <h3 className="card-spacing-title">
    Recipe Title
  </h3>
  
  <p className="text-secondary card-spacing-description">
    Description text
  </p>
  
  <div className="card-spacing-meta">
    15 min • Easy
  </div>
  
  <a href="#" className="card-spacing-cta link-primary">
    View Recipe →
  </a>
</article>
```

---

## Step 9: Accessibility Considerations

### Reduced Motion Support

```tsx
// Maintains spacing but removes animations
<div className="section-major">
  {/* Spacing respected with prefers-reduced-motion */}
</div>
```

### High Contrast Mode

```tsx
// Section dividers adapt in high contrast mode
<div className="section-divider">
  Content
</div>
```

### Print Styles

```tsx
// Spacing reduces for print output
<div className="no-print">Hidden on print</div>
```

---

## Step 10: Common Spacing Patterns

### Pattern 1: Hero with CTA

```tsx
<section className="section-hero">
  <div className="container-max container-px">
    <div className="hero-max-width mx-auto">
      <h1 className="text-display-xl">Title</h1>
      <p className="text-body-lg mt-6">Description</p>
      <button className="btn-primary mt-8">CTA</button>
    </div>
  </div>
</section>
```

### Pattern 2: Three-Column Content

```tsx
<section className="section-medium">
  <div className="container-max container-px">
    <h2 className="text-heading-xl mb-12">Heading</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div>{/* Column 1 */}</div>
      <div>{/* Column 2 */}</div>
      <div>{/* Column 3 */}</div>
    </div>
  </div>
</section>
```

### Pattern 3: Feature with Sidebar

```tsx
<section className="section-medium">
  <div className="container-max container-px">
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
      <div className="lg:col-span-2">
        {/* Main content */}
      </div>
      <div>
        {/* Sidebar */}
      </div>
    </div>
  </div>
</section>
```

### Pattern 4: Form with Help Text

```tsx
<form className="form-spacing max-w-md">
  <div className="form-group-spacing">
    <label className="form-label-spacing">Email</label>
    <input className="form-input-spacing w-full" />
    <p className="text-secondary text-sm mt-2">
      We'll never share your email
    </p>
  </div>
  <button className="btn-primary w-full">Submit</button>
</form>
```

---

## Troubleshooting

### Spacing Not Applying

1. **Verify Tailwind config**: Check `tailwind.config.ts` imports
2. **Check CSS import**: Ensure `spacing.css` is imported
3. **Clear cache**: Run `npm run dev` or delete `.next` folder
4. **Inspect element**: Use browser DevTools to verify classes

### Mobile Padding Issues

1. **Use `container-px`**: Apply to all page-level containers
2. **Never use `px-0` on mobile**: Minimum `px-4`
3. **Test on device**: Check actual mobile devices, not just browser

### Grid Not Responsive

1. **Mobile-first order**: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
2. **Gap responsive too**: `gap-4 md:gap-6 lg:gap-8`
3. **Container responsive**: Use `container-max` with `container-px`

---

## Best Practices

✅ **DO:**
- Use semantic spacing tokens (`section-major`, `card-p-medium`)
- Scale all spacing responsively
- Group related elements with smaller gaps
- Maintain at least 16px mobile padding
- Test on real mobile devices

❌ **DON'T:**
- Mix arbitrary and defined spacing
- Use `px-0` or `py-0` on mobile containers
- Over-space related elements
- Ignore mobile touch targets
- Skip responsive modifiers

---

## Performance Tips

- Spacing system uses Tailwind utilities (no runtime overhead)
- CSS is static and builds into main bundle
- No additional HTTP requests
- Responsive classes compile at build time

---

## Migration Guide

If migrating from existing spacing:

1. **Audit current spacing**: Document all current spacings
2. **Create mapping**: Map to nearest spacing scale value
3. **Update components gradually**: Use new classes incrementally
4. **Test responsive**: Verify mobile, tablet, desktop
5. **Remove old CSS**: Clean up hardcoded spacing

---

## Testing Checklist

- [ ] Spacing classes render correctly
- [ ] Mobile padding ≥ 16px everywhere
- [ ] Touch targets ≥ 44x44px
- [ ] Responsive spacing works (mobile/tablet/desktop)
- [ ] Cards display with proper padding
- [ ] Forms have proper gaps
- [ ] Navigation spacing correct
- [ ] Footer spacing correct
- [ ] Print styles work
- [ ] No console errors

---

**Version**: 1.0  
**Last Updated**: May 10, 2026
