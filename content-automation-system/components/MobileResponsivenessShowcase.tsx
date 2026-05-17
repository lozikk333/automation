"use client";

import Image from "next/image";
import Link from "next/link";
import { Menu, Search, X } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import { responsiveMotion } from "@/config/responsive";
import { useIsDesktop, useLockBodyScroll } from "@/hooks/useResponsive";

const navItems = ["Home", "Breakfast", "Dinner", "Dessert", "About"];
const categories = ["Breakfast", "Lunch", "Dinner", "Dessert", "Healthy", "Quick Meals"];

export default function MobileResponsivenessShowcase() {
  const reduceMotion = useReducedMotion();
  const isDesktop = useIsDesktop();
  const [menuOpen, setMenuOpen] = useState(false);

  useLockBodyScroll(menuOpen);

  return (
    <section className="no-horizontal-overflow bg-[#fbf6ed]">
      <header className="mobile-nav-shell">
        <div className="container-responsive flex min-h-[68px] items-center justify-between lg:min-h-[80px]">
          <Link
            href="/"
            className="font-serif text-[21px] font-black uppercase tracking-[0.08em] text-[#1f1f1f] lg:text-[28px]"
          >
            YARA BITES
          </Link>

          <nav aria-label="Desktop showcase navigation" className="hidden items-center gap-8 lg:flex">
            {navItems.map((item) => (
              <Link key={item} href="/" className="nav-link-premium text-[15px] font-medium">
                {item}
              </Link>
            ))}
          </nav>

          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((value) => !value)}
            className="touch-target grid place-items-center rounded-full bg-white text-[#1f1f1f] shadow-soft-xs lg:hidden"
          >
            {menuOpen ? <X aria-hidden="true" size={22} /> : <Menu aria-hidden="true" size={22} />}
          </button>
        </div>
      </header>

      <AnimatePresence>
        {menuOpen ? (
          <motion.div
            className="mobile-nav-drawer"
            initial={reduceMotion ? false : "closed"}
            animate="open"
            exit="closed"
            variants={responsiveMotion.fullScreenMenu}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="flex min-h-[52px] items-center justify-between">
              <span className="font-serif text-[21px] font-black uppercase tracking-[0.08em] text-[#1f1f1f]">
                YARA BITES
              </span>
              <button
                type="button"
                aria-label="Close menu"
                onClick={() => setMenuOpen(false)}
                className="touch-target grid place-items-center rounded-full bg-white shadow-soft-xs"
              >
                <X aria-hidden="true" size={22} />
              </button>
            </div>

            <nav aria-label="Mobile showcase navigation" className="mt-8">
              {navItems.map((item) => (
                <Link key={item} href="/" onClick={() => setMenuOpen(false)} className="mobile-nav-link">
                  {item}
                </Link>
              ))}
            </nav>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="container-responsive hero-responsive">
        <div className="hero-layout-responsive">
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 24 }}
            whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.25 }}
            transition={{ duration: 0.62, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="text-label-mobile font-semibold uppercase text-[#8b6b4a] xl:text-label-desktop">
              Mobile-first recipe system
            </p>
            <h1 className="text-hero-responsive mt-4 font-serif font-bold text-[#1f1f1f]">
              Designed for calm, readable cooking on every screen
            </h1>
            <p className="text-body-responsive mx-auto mt-5 max-w-[620px] text-[#5f5f5f] lg:mx-0 xl:text-body-desktop">
              Containers, grids, typography, navigation, forms, and touch states scale from compact phones to large editorial desktops.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center lg:justify-start">
              <Link href="/recipes" className="button-premium mobile-full px-7 sm:w-auto">
                Browse Recipes
              </Link>
              <Link
                href="/categories"
                className="touch-target-comfort inline-flex w-full items-center justify-center rounded-full border border-interaction-soft bg-white px-7 text-sm font-semibold text-[#1f1f1f] shadow-soft-xs sm:w-auto"
              >
                View Categories
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 24 }}
            whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
            whileHover={!reduceMotion && isDesktop ? responsiveMotion.desktopHover : undefined}
            whileTap={!reduceMotion && !isDesktop ? responsiveMotion.mobileTap : undefined}
            viewport={{ once: true, amount: 0.25 }}
            transition={{ duration: 0.62, ease: [0.22, 1, 0.36, 1] }}
            className="card-premium desktop-hover-lift tap-feedback"
          >
            <div className="relative aspect-[4/3] overflow-hidden bg-[#e9ddcc]">
              <Image
                src="/assets/img/bang-bang-chicken-bowl-healthy.jpg"
                alt="Colorful healthy chicken bowl"
                fill
                sizes="(min-width: 1024px) 520px, 100vw"
                className="image-premium object-cover"
              />
            </div>
            <div className="p-5 sm:p-6">
              <h2 className="text-card-responsive line-clamp-2 font-serif font-bold text-[#1f1f1f] xl:text-card-desktop">
                Full-width mobile cards preserve image ratio and readable hierarchy
              </h2>
              <p className="mt-3 line-clamp-2 text-sm leading-6 text-[#5f5f5f]">
                Metadata wraps, text clamps, and tap feedback replaces hover on touch devices.
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="container-responsive pb-16 lg:pb-24">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-section-responsive font-serif font-bold text-[#1f1f1f]">Responsive Patterns</h2>
          <button
            type="button"
            aria-label="Search recipes"
            className="touch-target grid shrink-0 place-items-center rounded-full bg-white text-[#1f1f1f] shadow-soft-xs"
          >
            <Search aria-hidden="true" size={19} />
          </button>
        </div>

        <div className="mobile-scroll-row hide-scrollbar mt-6 sm:hidden">
          {categories.map((category) => (
            <button key={category} type="button" className="chip-premium touch-target px-4 text-sm font-semibold">
              {category}
            </button>
          ))}
        </div>

        <div className="category-grid-responsive mt-6 hidden sm:grid">
          {categories.slice(0, 4).map((category) => (
            <article key={category} className="rounded-premium-lg border border-interaction-soft bg-white p-5 shadow-soft-sm">
              <h3 className="font-serif text-xl font-bold text-[#1f1f1f]">{category}</h3>
              <p className="mt-2 text-sm leading-6 text-[#5f5f5f]">1-2 columns on small screens, 4 on desktop.</p>
            </article>
          ))}
        </div>

        <div className="recipe-grid-responsive mt-8">
          {[1, 2, 3].map((item) => (
            <article key={item} className="card-premium desktop-hover-lift tap-feedback">
              <div className="aspect-[4/3] bg-[#e9ddcc]" />
              <div className="p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#8b6b4a]">Recipe Card</p>
                <h3 className="text-card-responsive mt-3 line-clamp-2 font-serif font-bold text-[#1f1f1f] xl:text-card-desktop">
                  One column mobile, two tablet, three desktop
                </h3>
                <p className="mt-3 line-clamp-2 text-sm leading-6 text-[#5f5f5f]">
                  Consistent gutters and stable cards prevent cramped layouts and horizontal overflow.
                </p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
