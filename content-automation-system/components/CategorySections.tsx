"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ChefHat, Sparkles } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import RecipeCard, { RecipeCardEmpty, RecipeCardSkeleton, type Recipe } from "./RecipeCard";

export type RecipeCategory = {
  id: string | number;
  name: string;
  slug: string;
  image: string;
  recipeCount: number;
  description?: string;
  featuredRecipes?: Recipe[];
};

type CategorySectionsProps = {
  categories?: RecipeCategory[];
  title?: string;
  description?: string;
  className?: string;
  loading?: boolean;
};

const defaultCategories: RecipeCategory[] = [
  {
    id: "breakfast",
    name: "Breakfast",
    slug: "breakfast",
    image: "/images/categories/breakfast.jpg",
    recipeCount: 24,
    description: "Bright, simple recipes for slow mornings, school days, and everything in between.",
    featuredRecipes: [
      {
        id: "pancakes",
        title: "Fluffy Homemade Pancakes",
        slug: "fluffy-homemade-pancakes",
        image: "/images/recipes/pancakes.jpg",
        category: "Breakfast",
        description: "Soft golden pancakes with a tender crumb and a cozy weekend feel.",
        prepTime: "25 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
      {
        id: "toast",
        title: "Berry French Toast Bake",
        slug: "berry-french-toast-bake",
        image: "/images/recipes/french-toast.jpg",
        category: "Breakfast",
        description: "A warm, fruit-filled breakfast bake made for sharing at the table.",
        prepTime: "40 mins",
        difficulty: "Easy",
        servings: "6 servings",
      },
      {
        id: "eggs",
        title: "Herby Breakfast Egg Skillet",
        slug: "herby-breakfast-egg-skillet",
        image: "/images/recipes/egg-skillet.jpg",
        category: "Breakfast",
        description: "A one-pan breakfast with soft eggs, vegetables, and fresh herbs.",
        prepTime: "20 mins",
        difficulty: "Easy",
        servings: "3 servings",
      },
    ],
  },
  {
    id: "lunch",
    name: "Lunch",
    slug: "lunch",
    image: "/images/categories/lunch.jpg",
    recipeCount: 31,
    description: "Fresh, satisfying lunches that feel thoughtful without taking over the day.",
    featuredRecipes: [
      {
        id: "chicken-wrap",
        title: "Crisp Chicken Salad Wraps",
        slug: "crisp-chicken-salad-wraps",
        image: "/images/recipes/chicken-wraps.jpg",
        category: "Lunch",
        description: "Crunchy, creamy, and packed with simple flavor for a quick midday meal.",
        prepTime: "20 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
      {
        id: "tomato-soup",
        title: "Roasted Tomato Basil Soup",
        slug: "roasted-tomato-basil-soup",
        image: "/images/recipes/tomato-soup.jpg",
        category: "Lunch",
        description: "Silky tomato soup with roasted sweetness and a fresh basil finish.",
        prepTime: "35 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
      {
        id: "grain-bowl",
        title: "Lemon Herb Grain Bowls",
        slug: "lemon-herb-grain-bowls",
        image: "/images/recipes/grain-bowl.jpg",
        category: "Lunch",
        description: "Colorful bowls with grains, crisp vegetables, and a bright lemon dressing.",
        prepTime: "30 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
    ],
  },
  {
    id: "dinner",
    name: "Dinner",
    slug: "dinner",
    image: "/images/categories/dinner.jpg",
    recipeCount: 42,
    description: "Comforting dinners with polished flavor and weeknight-friendly timing.",
    featuredRecipes: [
      {
        id: "garlic-chicken",
        title: "Creamy Garlic Chicken Pasta",
        slug: "creamy-garlic-chicken-pasta",
        image: "/images/recipes/garlic-chicken-pasta.jpg",
        category: "Dinner",
        description: "Tender chicken, silky sauce, and herbs in a dinner everyone asks for again.",
        prepTime: "35 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
      {
        id: "salmon",
        title: "Lemon Herb Roasted Salmon",
        slug: "lemon-herb-roasted-salmon",
        image: "/images/recipes/roasted-salmon.jpg",
        category: "Dinner",
        description: "A bright, flaky salmon dinner with a simple roasted finish.",
        prepTime: "28 mins",
        difficulty: "Easy",
        servings: "4 servings",
      },
      {
        id: "meatballs",
        title: "Skillet Chicken Meatballs",
        slug: "skillet-chicken-meatballs",
        image: "/images/recipes/chicken-meatballs.jpg",
        category: "Dinner",
        description: "Juicy chicken meatballs simmered in a rich, cozy tomato sauce.",
        prepTime: "45 mins",
        difficulty: "Medium",
        servings: "5 servings",
      },
    ],
  },
  {
    id: "dessert",
    name: "Dessert",
    slug: "dessert",
    image: "/images/categories/dessert.jpg",
    recipeCount: 29,
    description: "Sweet treats with bakery polish and approachable home-kitchen steps.",
    featuredRecipes: [
      {
        id: "lemon-bars",
        title: "Velvety Lemon Crumble Bars",
        slug: "velvety-lemon-crumble-bars",
        image: "/images/recipes/lemon-bars.jpg",
        category: "Dessert",
        description: "Buttery crumble bars with a sunny lemon center and soft finish.",
        prepTime: "50 mins",
        difficulty: "Easy",
        servings: "12 bars",
      },
      {
        id: "chocolate-cake",
        title: "Simple Chocolate Layer Cake",
        slug: "simple-chocolate-layer-cake",
        image: "/images/recipes/chocolate-cake.jpg",
        category: "Dessert",
        description: "A rich chocolate cake with a glossy finish and tender crumb.",
        prepTime: "1 hr",
        difficulty: "Medium",
        servings: "10 slices",
      },
      {
        id: "berry-crisp",
        title: "Warm Mixed Berry Crisp",
        slug: "warm-mixed-berry-crisp",
        image: "/images/recipes/berry-crisp.jpg",
        category: "Dessert",
        description: "Juicy berries baked under a golden oat crumble.",
        prepTime: "45 mins",
        difficulty: "Easy",
        servings: "6 servings",
      },
    ],
  },
  {
    id: "healthy",
    name: "Healthy Recipes",
    slug: "healthy-recipes",
    image: "/images/categories/healthy.jpg",
    recipeCount: 36,
    description: "Fresh, colorful meals built around balanced ingredients and full flavor.",
  },
  {
    id: "quick",
    name: "Quick Meals",
    slug: "quick-meals",
    image: "/images/categories/quick-meals.jpg",
    recipeCount: 33,
    description: "Fast recipes for busy days when dinner still needs to feel special.",
  },
  {
    id: "popular",
    name: "Popular Recipes",
    slug: "popular-recipes",
    image: "/images/categories/popular.jpg",
    recipeCount: 18,
    description: "Reader favorites, reliable classics, and highly loved everyday dishes.",
  },
  {
    id: "seasonal",
    name: "Seasonal Favorites",
    slug: "seasonal-favorites",
    image: "/images/categories/seasonal.jpg",
    recipeCount: 21,
    description: "Fresh ideas for the season, from cozy bakes to bright market meals.",
  },
];

const reveal = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

function categoryHref(slug: string) {
  return `/category/${slug}`;
}

export default function CategorySections({
  categories = defaultCategories,
  title = "Browse by Category",
  description = "Find the kind of recipe you need quickly, from easy breakfasts to polished dinners and sweet weekend bakes.",
  className = "",
  loading = false,
}: CategorySectionsProps) {
  const [activeCategory, setActiveCategory] = useState("all");
  const reduceMotion = useReducedMotion();

  const visibleCategories = useMemo(() => {
    if (activeCategory === "all") return categories;
    return categories.filter((category) => category.slug === activeCategory);
  }, [activeCategory, categories]);

  return (
    <section
      aria-labelledby="recipe-categories-heading"
      className={[
        "w-full bg-white px-4 py-14 sm:px-6 sm:py-20 lg:px-8 lg:py-[100px]",
        className,
      ].join(" ")}
    >
      <div className="mx-auto max-w-[1280px]">
        <motion.div
          initial={reduceMotion ? false : "hidden"}
          whileInView={reduceMotion ? undefined : "show"}
          viewport={{ once: true, amount: 0.2 }}
          variants={stagger}
          className="mb-10 grid gap-6 text-center lg:mb-14 lg:grid-cols-[1fr_auto] lg:items-end lg:text-left"
        >
          <div>
            <motion.p
              variants={reveal}
              className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500 sm:text-sm"
            >
              Category
            </motion.p>
            <motion.h2
              id="recipe-categories-heading"
              variants={reveal}
              className="mt-4 font-serif text-[32px] font-bold leading-tight tracking-normal text-stone-950 sm:text-[44px] lg:text-[56px]"
            >
              {title}
            </motion.h2>
            <motion.p
              variants={reveal}
              className="mx-auto mt-4 max-w-[640px] text-base leading-8 text-stone-600 lg:mx-0 lg:text-lg"
            >
              {description}
            </motion.p>
          </div>

          <motion.div variants={reveal}>
            <Link
              href="/recipes"
              className="group inline-flex items-center gap-2 text-sm font-semibold text-[#8b633f] outline-none transition hover:text-stone-950 focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
            >
              View All Recipes
              <ArrowRight
                aria-hidden="true"
                size={16}
                className="transition-transform duration-200 group-hover:translate-x-1"
              />
            </Link>
          </motion.div>
        </motion.div>

        <div
          aria-label="Recipe category filters"
          className="-mx-4 mb-10 flex snap-x gap-3 overflow-x-auto px-4 pb-2 sm:mx-0 sm:flex-wrap sm:justify-center sm:px-0 lg:mb-14 lg:justify-start"
        >
          <CategoryFilterButton
            active={activeCategory === "all"}
            label="All"
            onClick={() => setActiveCategory("all")}
          />
          {categories.map((category) => (
            <CategoryFilterButton
              key={category.id}
              active={activeCategory === category.slug}
              label={category.name}
              onClick={() => setActiveCategory(category.slug)}
            />
          ))}
        </div>

        {loading ? (
          <CategorySectionsSkeleton />
        ) : visibleCategories.length ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeCategory}
              initial={reduceMotion ? false : { opacity: 0, y: 10 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -10 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
              className="space-y-16 lg:space-y-24"
            >
              <CategoryCardGrid categories={visibleCategories} reduceMotion={reduceMotion} />

              {visibleCategories.map((category, index) => (
                <FeaturedCategorySection
                  key={category.id}
                  category={category}
                  reverse={index % 2 === 1}
                  reduceMotion={reduceMotion}
                />
              ))}
            </motion.div>
          </AnimatePresence>
        ) : (
          <RecipeCardEmpty message="No recipe categories found." />
        )}
      </div>
    </section>
  );
}

function CategoryFilterButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={[
        "snap-start whitespace-nowrap rounded-full px-5 py-3 text-sm font-semibold outline-none transition",
        "focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4",
        active
          ? "bg-stone-900 text-white shadow-[0_12px_24px_rgba(40,32,24,0.18)]"
          : "bg-[#f7f1e8] text-stone-800 hover:bg-[#efe4d2]",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

function CategoryCardGrid({
  categories,
  reduceMotion,
}: {
  categories: RecipeCategory[];
  reduceMotion: boolean | null;
}) {
  return (
    <motion.div
      initial={reduceMotion ? false : "hidden"}
      whileInView={reduceMotion ? undefined : "show"}
      viewport={{ once: true, amount: 0.18 }}
      variants={stagger}
      className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
    >
      {categories.map((category) => (
        <motion.article
          key={category.id}
          variants={reveal}
          whileHover={reduceMotion ? undefined : { y: -6 }}
          className="group overflow-hidden rounded-[24px] border border-stone-100 bg-white shadow-[0_14px_35px_rgba(39,33,25,0.06)] transition-shadow duration-300 hover:shadow-[0_24px_55px_rgba(39,33,25,0.12)]"
        >
          <Link
            href={categoryHref(category.slug)}
            aria-label={`Browse ${category.name} recipes`}
            className="block h-full outline-none focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
          >
            <div className="relative aspect-[4/5] overflow-hidden bg-stone-100">
              <Image
                src={category.image}
                alt={`${category.name} recipes`}
                fill
                sizes="(min-width: 1024px) 25vw, (min-width: 640px) 50vw, 100vw"
                className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.07]"
              />
              <div className="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-black/45 to-transparent" />
            </div>
            <div className="p-5 text-center">
              <h3 className="font-serif text-2xl font-bold leading-tight text-stone-950 transition-colors group-hover:text-[#8b633f]">
                {category.name}
              </h3>
              <p className="mt-1 text-sm font-medium text-stone-500">{category.recipeCount} Recipes</p>
            </div>
          </Link>
        </motion.article>
      ))}
    </motion.div>
  );
}

function FeaturedCategorySection({
  category,
  reverse,
  reduceMotion,
}: {
  category: RecipeCategory;
  reverse: boolean;
  reduceMotion: boolean | null;
}) {
  const recipes = category.featuredRecipes || [];

  return (
    <motion.section
      aria-labelledby={`category-${category.slug}-heading`}
      initial={reduceMotion ? false : "hidden"}
      whileInView={reduceMotion ? undefined : "show"}
      viewport={{ once: true, amount: 0.18 }}
      variants={stagger}
      className="border-t border-stone-100 pt-10 lg:pt-12"
    >
      <div
        className="grid gap-8 lg:grid-cols-[0.4fr_0.6fr] lg:items-stretch"
      >
        <motion.div
          variants={reveal}
          className={[
            "relative min-h-[430px] overflow-hidden rounded-[26px] bg-stone-100 shadow-[0_18px_45px_rgba(39,33,25,0.1)]",
            reverse ? "lg:order-2" : "",
          ].join(" ")}
        >
          <Image
            src={category.image}
            alt={`${category.name} category`}
            fill
            sizes="(min-width: 1024px) 480px, 100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-stone-950/65 via-stone-950/10 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-6 text-white sm:p-8">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-stone-900 shadow-sm backdrop-blur">
              <ChefHat aria-hidden="true" size={15} />
              {category.recipeCount} Recipes
            </span>
            <h3
              id={`category-${category.slug}-heading`}
              className="mt-5 max-w-sm font-serif text-[34px] font-bold leading-tight tracking-normal sm:text-[42px]"
            >
              {category.name}
            </h3>
            {category.description ? (
              <p className="mt-3 max-w-md text-sm leading-6 text-white/90 sm:text-base">{category.description}</p>
            ) : null}
            <Link
              href={categoryHref(category.slug)}
              className="group mt-6 inline-flex h-11 items-center justify-center gap-2 rounded-full bg-white px-5 text-sm font-semibold text-stone-950 outline-none transition hover:bg-[#f7f1e8] focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-4 focus-visible:ring-offset-stone-900"
            >
              Explore Category
              <ArrowRight
                aria-hidden="true"
                size={16}
                className="transition-transform duration-200 group-hover:translate-x-1"
              />
            </Link>
          </div>
        </motion.div>

        <motion.div variants={stagger} className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {recipes.length ? (
            recipes.slice(0, 3).map((recipe, index) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                priority={index === 0}
                showActions={false}
                className={index === 2 ? "md:hidden xl:block" : ""}
              />
            ))
          ) : (
            <div className="grid gap-4 md:col-span-2 xl:col-span-3">
              <div className="rounded-[24px] border border-dashed border-stone-200 bg-white p-8 text-center">
                <div className="mx-auto grid size-14 place-items-center rounded-full bg-[#f1e5d2] text-[#6f7c45]">
                  <Sparkles aria-hidden="true" size={22} />
                </div>
                <h4 className="mt-5 font-serif text-2xl font-bold text-stone-950">Recipes coming soon</h4>
                <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-stone-600">
                  Add featured recipes to this category to show polished preview cards here.
                </p>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </motion.section>
  );
}

export function CategorySectionsSkeleton() {
  return (
    <div aria-label="Loading recipe categories" aria-busy="true" className="space-y-10">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <article
            key={index}
            className="overflow-hidden rounded-[24px] border border-stone-100 bg-white shadow-[0_14px_35px_rgba(39,33,25,0.05)]"
          >
            <div className="aspect-[4/5] animate-pulse bg-stone-100" />
            <div className="space-y-3 p-5">
              <div className="mx-auto h-6 w-32 animate-pulse rounded bg-stone-100" />
              <div className="mx-auto h-4 w-20 animate-pulse rounded bg-stone-100" />
            </div>
          </article>
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-3">
        <RecipeCardSkeleton />
        <RecipeCardSkeleton />
        <RecipeCardSkeleton />
      </div>
    </div>
  );
}
