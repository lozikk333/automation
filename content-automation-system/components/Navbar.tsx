"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

type NavItem = {
  label: string;
  href: string;
};

const navItems: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Breakfast", href: "/category/breakfast" },
  { label: "Lunch", href: "/category/lunch" },
  { label: "Dinner", href: "/category/dinner" },
  { label: "Dessert", href: "/category/dessert" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Navbar() {
  const pathname = usePathname();
  const reduceMotion = useReducedMotion();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  const mobileMenuId = "mobile-recipe-navigation";

  return (
    <header
      className={[
        "sticky top-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur",
        "transition-[height,box-shadow,background-color] duration-200 ease-out",
        isScrolled ? "shadow-[0_10px_30px_rgba(31,41,55,0.08)]" : "shadow-none",
      ].join(" ")}
    >
      <nav
        aria-label="Primary navigation"
        className={[
          "mx-auto flex max-w-[1280px] items-center justify-between",
          "px-4 sm:px-6 lg:px-8",
          "transition-[height] duration-200 ease-out",
          isScrolled ? "h-[60px] lg:h-[72px]" : "h-[68px] lg:h-20",
        ].join(" ")}
      >
        <Link
          href="/"
          aria-label="Yara Bites homepage"
          className="font-serif text-[22px] font-black uppercase tracking-[0.08em] text-stone-900 outline-none transition-colors hover:text-stone-700 focus-visible rounded-sm focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 lg:text-[28px]"
        >
          YARA BITES
        </Link>

        <div className="hidden items-center gap-8 lg:flex">
          {navItems.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className="group relative py-2 text-[15px] font-medium text-stone-700 outline-none transition-colors duration-200 hover:text-stone-950 focus-visible rounded-sm focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
              >
                {item.label}
                <span
                  className={[
                    "absolute inset-x-0 -bottom-1 h-px origin-left bg-stone-900 transition-transform duration-200",
                    active ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100",
                  ].join(" ")}
                />
              </Link>
            );
          })}
        </div>

        <div className="hidden items-center lg:flex">
          <Link
            href="/recipes"
            className="rounded-full bg-[#efe4d2] px-5 py-2.5 text-sm font-semibold text-stone-900 shadow-sm outline-none transition duration-200 hover:-translate-y-0.5 hover:bg-[#e8d8bf] hover:shadow-md focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
          >
            Browse Recipes
          </Link>
        </div>

        <button
          type="button"
          aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={isOpen}
          aria-controls={mobileMenuId}
          onClick={() => setIsOpen((value) => !value)}
          className="inline-flex size-11 items-center justify-center rounded-full text-stone-900 outline-none transition hover:bg-stone-100 focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 lg:hidden"
        >
          {isOpen ? <X aria-hidden="true" size={22} /> : <Menu aria-hidden="true" size={22} />}
        </button>
      </nav>

      <AnimatePresence initial={false}>
        {isOpen ? (
          <motion.div
            id={mobileMenuId}
            key="mobile-menu"
            initial={reduceMotion ? false : { height: 0, opacity: 0 }}
            animate={reduceMotion ? { opacity: 1 } : { height: "auto", opacity: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden border-t border-gray-100 bg-white shadow-[0_18px_35px_rgba(31,41,55,0.08)] lg:hidden"
          >
            <div className="mx-auto max-w-[1280px] px-4 py-3 sm:px-6">
              {navItems.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={[
                      "flex min-h-12 items-center border-b border-gray-100 text-base font-medium outline-none transition-colors last:border-b-0 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-stone-900",
                      active ? "text-stone-950" : "text-stone-700 hover:text-stone-950",
                    ].join(" ")}
                  >
                    <span className="relative">
                      {item.label}
                      {active ? <span className="absolute -bottom-1 left-0 h-px w-full bg-stone-900" /> : null}
                    </span>
                  </Link>
                );
              })}
              <Link
                href="/recipes"
                className="mt-4 flex min-h-12 items-center justify-center rounded-full bg-[#efe4d2] px-5 text-base font-semibold text-stone-900 shadow-sm outline-none transition hover:bg-[#e8d8bf] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-2"
              >
                Browse Recipes
              </Link>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </header>
  );
}
