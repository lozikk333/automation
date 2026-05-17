"use client";

import { ArrowRight, Heart, Mail } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import {
  buttonHover,
  buttonTap,
  cardHover,
  categoryChipHover,
  mobileTap,
  revealContainer,
  revealItem,
  socialIconHover,
} from "@/config/interactions";

const shadows = [
  { name: "Shadow XS", className: "shadow-soft-xs", usage: "Subtle dividers, pills, micro UI" },
  { name: "Shadow SM", className: "shadow-soft-sm", usage: "Buttons, chips, form inputs" },
  { name: "Shadow MD", className: "shadow-soft-md", usage: "Recipe cards, content panels" },
  { name: "Shadow LG", className: "shadow-soft-lg", usage: "Hero panels and elevated states" },
  { name: "Shadow Hover", className: "shadow-soft-hover", usage: "Premium interactive hover" },
];

const chips = ["Breakfast", "Dinner", "Dessert", "Quick Meals"];

export default function InteractionShowcase() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="w-full bg-[#fbf6ed] px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
      <motion.div
        initial={reduceMotion ? false : "hidden"}
        whileInView={reduceMotion ? undefined : "show"}
        viewport={{ once: true, amount: 0.2 }}
        variants={revealContainer}
        className="mx-auto max-w-[1280px]"
      >
        <motion.div variants={revealItem} className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#8b6b4a]">
            Interaction System
          </p>
          <h2 className="mt-4 font-serif text-[34px] font-bold leading-tight text-[#1f1f1f] sm:text-[44px]">
            Soft, tactile motion for a premium recipe experience
          </h2>
          <p className="mt-4 text-base leading-8 text-[#5f5f5f]">
            Subtle elevation, warm borders, calm motion, and accessible focus states for editorial recipe interfaces.
          </p>
        </motion.div>

        <motion.div variants={revealItem} className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-5">
          {shadows.map((shadow) => (
            <div
              key={shadow.name}
              className={`rounded-premium-lg border border-interaction-soft bg-white p-5 ${shadow.className}`}
            >
              <h3 className="font-serif text-xl font-bold text-[#1f1f1f]">{shadow.name}</h3>
              <p className="mt-3 text-sm leading-6 text-[#5f5f5f]">{shadow.usage}</p>
            </div>
          ))}
        </motion.div>

        <div className="mt-12 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
          <motion.div variants={revealItem} className="surface-premium p-6 sm:p-8">
            <h3 className="font-serif text-2xl font-bold text-[#1f1f1f]">Interactive Controls</h3>
            <div className="mt-6 flex flex-wrap gap-3">
              <motion.button
                type="button"
                whileHover={reduceMotion ? undefined : buttonHover}
                whileTap={reduceMotion ? undefined : buttonTap}
                className="button-premium px-6"
              >
                Browse Recipes
                <ArrowRight aria-hidden="true" size={18} />
              </motion.button>

              <motion.button
                type="button"
                whileHover={reduceMotion ? undefined : socialIconHover}
                whileTap={reduceMotion ? undefined : mobileTap}
                aria-label="Favorite recipe"
                className="social-icon-premium"
              >
                <Heart aria-hidden="true" size={18} />
              </motion.button>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {chips.map((chip) => (
                <motion.button
                  key={chip}
                  type="button"
                  whileHover={reduceMotion ? undefined : categoryChipHover}
                  whileTap={reduceMotion ? undefined : mobileTap}
                  className="chip-premium min-h-10 px-4 text-sm font-semibold text-[#5b4632]"
                >
                  {chip}
                </motion.button>
              ))}
            </div>

            <label className="mt-7 block text-sm font-semibold text-[#1f1f1f]" htmlFor="interaction-email">
              Newsletter email
            </label>
            <div className="relative mt-2">
              <Mail
                aria-hidden="true"
                size={18}
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#8a8a8a]"
              />
              <input
                id="interaction-email"
                type="email"
                placeholder="Your email"
                className="input-premium h-12 w-full pl-11 pr-4 text-sm text-[#1f1f1f] placeholder:text-[#8a8a8a]"
              />
            </div>
          </motion.div>

          <motion.article
            variants={revealItem}
            whileHover={reduceMotion ? undefined : cardHover}
            className="card-premium group"
          >
            <div className="aspect-[16/10] overflow-hidden bg-[#e9ddcc]">
              <div className="image-premium h-full w-full bg-[linear-gradient(135deg,#b65f3c,#f1d5a5_52%,#6f8a5b)]" />
            </div>
            <div className="p-6 sm:p-8">
              <span className="chip-premium inline-flex min-h-8 items-center px-3 text-xs font-semibold uppercase tracking-[0.14em] text-[#5b4632]">
                Seasonal
              </span>
              <h3 className="mt-5 font-serif text-3xl font-bold text-[#1f1f1f] transition-colors duration-smooth-fast ease-premium-out group-hover:text-[#8b6b4a]">
                Honey Roasted Carrot Salad
              </h3>
              <p className="mt-3 text-sm leading-7 text-[#5f5f5f]">
                A tactile card pattern with soft lift, image zoom, warm title accent, and calm elevation.
              </p>
            </div>
          </motion.article>
        </div>

        <motion.div variants={revealItem} className="mt-12 grid gap-4 md:grid-cols-3">
          <div className="rounded-premium-md border border-interaction-light bg-white p-5">
            <div className="skeleton-premium h-4 w-28 rounded-full" />
            <div className="skeleton-premium mt-4 h-8 w-3/4 rounded-premium-sm" />
            <div className="skeleton-premium mt-3 h-4 w-full rounded-premium-sm" />
          </div>
          <div className="rounded-premium-md border border-[#d99a91] bg-[#fff8f7] p-5 text-sm font-medium text-[#9d4d43]">
            Error state: soft red border and warm background tint.
          </div>
          <div className="rounded-premium-md border border-[#a9bd95] bg-[#fbfdf8] p-5 text-sm font-medium text-[#5f743e]">
            Success state: soft green border with quiet confirmation.
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}
