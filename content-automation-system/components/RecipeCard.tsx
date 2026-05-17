"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Bookmark, Clock3, Flame, Heart, UsersRound } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

export type Recipe = {
  id: string | number;
  title: string;
  slug: string;
  image: string;
  category: string;
  description: string;
  prepTime: string;
  difficulty: string;
  servings: string;
};

type RecipeCardProps = {
  recipe: Recipe;
  href?: string;
  priority?: boolean;
  showActions?: boolean;
  className?: string;
};

function recipeHref(recipe: Recipe, href?: string) {
  return href || `/recipes/${recipe.slug}`;
}

export default function RecipeCard({
  recipe,
  href,
  priority = false,
  showActions = true,
  className = "",
}: RecipeCardProps) {
  const reduceMotion = useReducedMotion();
  const targetHref = recipeHref(recipe, href);

  return (
    <motion.article
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={reduceMotion ? undefined : { y: -6 }}
      className={[
        "group relative w-full overflow-hidden rounded-[22px] border border-[#f1f1f1] bg-white",
        "shadow-[0_14px_35px_rgba(39,33,25,0.07)] transition-shadow duration-300",
        "hover:shadow-[0_24px_55px_rgba(39,33,25,0.13)]",
        className,
      ].join(" ")}
    >
      <Link
        href={targetHref}
        aria-label={`View recipe: ${recipe.title}`}
        className="block h-full outline-none focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
      >
        <div className="relative aspect-[4/3] overflow-hidden bg-stone-100">
          <Image
            src={recipe.image}
            alt={recipe.title}
            fill
            priority={priority}
            sizes="(min-width: 1280px) 380px, (min-width: 768px) 50vw, 100vw"
            className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.07]"
          />
          <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/30 to-transparent" />

          <span className="absolute left-4 top-4 rounded-full bg-[#f1e5d2]/90 px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-900 shadow-sm backdrop-blur">
            {recipe.category}
          </span>
        </div>

        <div className="p-4 sm:p-5 lg:p-6">
          <h3 className="line-clamp-2 font-serif text-[18px] font-bold leading-tight text-stone-950 transition-colors duration-200 group-hover:text-[#8b633f] sm:text-xl lg:text-2xl">
            {recipe.title}
          </h3>

          <p className="mt-3 line-clamp-3 text-sm leading-6 text-stone-600 sm:text-[15px]">
            {recipe.description}
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-medium text-stone-500 sm:text-sm">
            <span className="inline-flex items-center gap-1.5">
              <Clock3 aria-hidden="true" size={15} />
              {recipe.prepTime}
            </span>
            <span className="h-1 w-1 rounded-full bg-stone-300" aria-hidden="true" />
            <span className="inline-flex items-center gap-1.5">
              <Flame aria-hidden="true" size={15} />
              {recipe.difficulty}
            </span>
            <span className="h-1 w-1 rounded-full bg-stone-300" aria-hidden="true" />
            <span className="inline-flex items-center gap-1.5">
              <UsersRound aria-hidden="true" size={15} />
              {recipe.servings}
            </span>
          </div>

          <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[#8b633f]">
            View Recipe
            <ArrowRight
              aria-hidden="true"
              size={16}
              className="transition-transform duration-200 group-hover:translate-x-1"
            />
          </span>
        </div>
      </Link>

      {showActions ? (
        <div className="absolute right-4 top-4 z-10 flex gap-2">
          <button
            type="button"
            aria-label={`Save ${recipe.title}`}
            className="grid size-9 place-items-center rounded-full bg-white/85 text-stone-800 shadow-sm backdrop-blur transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900"
          >
            <Bookmark aria-hidden="true" size={17} />
          </button>
          <button
            type="button"
            aria-label={`Favorite ${recipe.title}`}
            className="grid size-9 place-items-center rounded-full bg-white/85 text-stone-800 shadow-sm backdrop-blur transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900"
          >
            <Heart aria-hidden="true" size={17} />
          </button>
        </div>
      ) : null}
    </motion.article>
  );
}

export function RecipeCardSkeleton({ className = "" }: { className?: string }) {
  return (
    <article
      aria-label="Loading recipe"
      aria-busy="true"
      className={[
        "w-full overflow-hidden rounded-[22px] border border-[#f1f1f1] bg-white shadow-[0_14px_35px_rgba(39,33,25,0.06)]",
        className,
      ].join(" ")}
    >
      <div className="aspect-[4/3] animate-pulse bg-stone-100" />
      <div className="space-y-4 p-4 sm:p-5 lg:p-6">
        <div className="h-5 w-28 animate-pulse rounded-full bg-stone-100" />
        <div className="space-y-2">
          <div className="h-6 w-4/5 animate-pulse rounded bg-stone-100" />
          <div className="h-6 w-3/5 animate-pulse rounded bg-stone-100" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full animate-pulse rounded bg-stone-100" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-stone-100" />
        </div>
        <div className="flex gap-3">
          <div className="h-4 w-16 animate-pulse rounded bg-stone-100" />
          <div className="h-4 w-16 animate-pulse rounded bg-stone-100" />
          <div className="h-4 w-20 animate-pulse rounded bg-stone-100" />
        </div>
      </div>
    </article>
  );
}

export function RecipeCardEmpty({ message = "No recipes found." }: { message?: string }) {
  return (
    <article className="grid min-h-[340px] w-full place-items-center rounded-[22px] border border-dashed border-stone-200 bg-white p-8 text-center shadow-[0_14px_35px_rgba(39,33,25,0.04)]">
      <div>
        <div className="mx-auto mb-5 grid size-14 place-items-center rounded-full bg-[#f1e5d2] text-stone-900">
          <Clock3 aria-hidden="true" size={22} />
        </div>
        <h3 className="font-serif text-2xl font-bold text-stone-950">Nothing cooking yet</h3>
        <p className="mt-2 max-w-sm text-sm leading-6 text-stone-600">{message}</p>
      </div>
    </article>
  );
}
