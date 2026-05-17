"use client";

import { ArrowRight } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

const categories = ["All", "Breakfast", "Lunch", "Dinner", "Dessert"];

const containerVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.08,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  },
};

export default function HeroSection() {
  const reduceMotion = useReducedMotion();
  const animationProps = reduceMotion
    ? {}
    : {
        initial: "hidden",
        whileInView: "show",
        viewport: { once: true, amount: 0.45 },
      };

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative isolate w-full overflow-hidden bg-gradient-to-b from-[#fffdf8] via-white to-[#fffaf2]"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-[8%] top-20 size-56 rounded-full bg-[#e7d7bd]/30 blur-3xl" />
        <div className="absolute bottom-8 right-[10%] size-64 rounded-full bg-[#98a46f]/15 blur-3xl" />
      </div>

      <motion.div
        variants={containerVariants}
        {...animationProps}
        className="mx-auto flex max-w-[1280px] flex-col items-center px-4 py-16 text-center sm:px-6 sm:py-[90px] lg:px-8 lg:py-[120px]"
      >
        <motion.p
          variants={itemVariants}
          className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500 sm:text-sm"
        >
          Welcome to YARA BITES
        </motion.p>

        <motion.h1
          id="hero-heading"
          variants={itemVariants}
          className="mt-4 max-w-5xl font-serif text-[38px] font-bold leading-[0.96] tracking-[-0.015em] text-stone-950 sm:text-5xl md:text-[56px] lg:text-[72px]"
        >
          Simple Recipes That Work
        </motion.h1>

        <motion.p
          variants={itemVariants}
          className="mt-6 max-w-[700px] text-base leading-8 text-stone-600 sm:text-lg lg:text-xl"
        >
          From speedy weeknight dinners to indulgent weekend bakes — every recipe tested, every time.
        </motion.p>

        <motion.div variants={itemVariants} className="mt-8">
          <motion.a
            href="/recipes"
            aria-label="Browse all recipes"
            whileHover={reduceMotion ? undefined : { y: -3 }}
            whileTap={reduceMotion ? undefined : { scale: 0.98 }}
            className="group inline-flex min-h-12 items-center gap-2 rounded-full bg-[#eadcc8] px-7 py-3.5 text-base font-semibold text-stone-950 shadow-[0_12px_28px_rgba(73,55,35,0.12)] outline-none transition duration-200 hover:bg-[#e1cfb6] hover:shadow-[0_18px_34px_rgba(73,55,35,0.18)] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
          >
            Browse Recipes
            <ArrowRight
              aria-hidden="true"
              size={18}
              className="transition-transform duration-200 group-hover:translate-x-1"
            />
          </motion.a>
        </motion.div>

        <motion.div
          variants={itemVariants}
          aria-label="Recipe category filters"
          className="mt-12 flex max-w-3xl flex-wrap items-center justify-center gap-3"
        >
          {categories.map((category, index) => {
            const isActive = index === 0;
            return (
              <motion.a
                key={category}
                href={category === "All" ? "/recipes" : `/category/${category.toLowerCase()}`}
                whileHover={reduceMotion ? undefined : { scale: 1.04 }}
                whileTap={reduceMotion ? undefined : { scale: 0.98 }}
                aria-current={isActive ? "page" : undefined}
                className={[
                  "rounded-full px-4 py-2 text-sm font-medium outline-none transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 sm:px-5",
                  isActive
                    ? "bg-stone-900 text-white shadow-sm"
                    : "bg-stone-100 text-stone-800 hover:bg-stone-200",
                ].join(" ")}
              >
                {category}
              </motion.a>
            );
          })}
        </motion.div>
      </motion.div>
    </section>
  );
}
