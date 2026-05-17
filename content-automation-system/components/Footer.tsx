"use client";

import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowUp,
  CheckCircle2,
  Facebook,
  Instagram,
  Loader2,
  Mail,
  Music2,
  Pin,
  Youtube,
} from "lucide-react";
import { FormEvent, ReactNode, useEffect, useId, useState } from "react";

type FooterLinkItem = {
  label: string;
  href: string;
};

type SocialLink = {
  name: string;
  href: string;
  label: string;
  icon: ReactNode;
};

type FooterData = {
  brand: string;
  description: string;
  trustStatement?: string;
  socialLinks: SocialLink[];
  navigationLinks: FooterLinkItem[];
  categoryLinks: FooterLinkItem[];
  newsletterEnabled: boolean;
};

type FooterProps = {
  data?: FooterData;
};

export const footerData: FooterData = {
  brand: "YARA BITES",
  description:
    "Simple, delicious recipes made for everyday cooking, cozy gatherings, and sweet moments in the kitchen.",
  trustStatement: "Tested recipes. Real ingredients. Made with love.",
  socialLinks: [
    {
      name: "Instagram",
      href: "https://instagram.com",
      label: "Follow YARA BITES on Instagram",
      icon: <Instagram aria-hidden="true" size={18} strokeWidth={1.8} />,
    },
    {
      name: "Pinterest",
      href: "https://pinterest.com",
      label: "Follow YARA BITES on Pinterest",
      icon: <Pin aria-hidden="true" size={18} strokeWidth={1.8} />,
    },
    {
      name: "TikTok",
      href: "https://tiktok.com",
      label: "Follow YARA BITES on TikTok",
      icon: <Music2 aria-hidden="true" size={18} strokeWidth={1.8} />,
    },
    {
      name: "YouTube",
      href: "https://youtube.com",
      label: "Subscribe to YARA BITES on YouTube",
      icon: <Youtube aria-hidden="true" size={19} strokeWidth={1.8} />,
    },
    {
      name: "Facebook",
      href: "https://facebook.com",
      label: "Follow YARA BITES on Facebook",
      icon: <Facebook aria-hidden="true" size={18} strokeWidth={1.8} />,
    },
  ],
  navigationLinks: [
    { label: "Home", href: "/" },
    { label: "About", href: "/about" },
    { label: "Recipes", href: "/recipes" },
    { label: "Categories", href: "/categories" },
    { label: "Contact", href: "/contact" },
    { label: "FAQ", href: "/faq" },
  ],
  categoryLinks: [
    { label: "Breakfast", href: "/category/breakfast" },
    { label: "Lunch", href: "/category/lunch" },
    { label: "Dinner", href: "/category/dinner" },
    { label: "Dessert", href: "/category/dessert" },
    { label: "Healthy Recipes", href: "/category/healthy-recipes" },
    { label: "Quick Meals", href: "/category/quick-meals" },
    { label: "Seasonal Favorites", href: "/category/seasonal-favorites" },
  ],
  newsletterEnabled: true,
};

const policyLinks: FooterLinkItem[] = [
  { label: "Privacy Policy", href: "/privacy-policy" },
  { label: "Terms of Service", href: "/terms-of-service" },
  { label: "Cookie Policy", href: "/cookie-policy" },
];

const columnVariants = {
  hidden: { opacity: 0, y: 22 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.62, ease: [0.22, 1, 0.36, 1] },
  },
};

const gridVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.11,
      delayChildren: 0.08,
    },
  },
};

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function FooterColumn({
  title,
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <motion.div variants={columnVariants} className="flex flex-col items-center text-center md:items-start md:text-left">
      {title ? (
        <h3 className="mb-6 text-xs font-semibold uppercase tracking-[0.22em] text-stone-950">
          {title}
        </h3>
      ) : null}
      {children}
    </motion.div>
  );
}

function FooterNavLink({ href, label }: FooterLinkItem) {
  const reduceMotion = useReducedMotion();

  return (
    <li>
      <motion.div whileHover={reduceMotion ? undefined : { x: 4 }}>
        <Link
          href={href}
          className="inline-flex min-h-8 items-center rounded-sm text-[15px] font-medium text-stone-600 outline-none transition-colors duration-200 hover:text-[#7d5434] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 focus-visible:ring-offset-[#fbf6ed]"
        >
          {label}
        </Link>
      </motion.div>
    </li>
  );
}

function SocialIcons({ socialLinks }: { socialLinks: SocialLink[] }) {
  const reduceMotion = useReducedMotion();

  return (
    <div className="mt-7 flex flex-wrap justify-center gap-3 md:justify-start">
      {socialLinks.map((social) => (
        <motion.a
          key={social.name}
          href={social.href}
          aria-label={social.label}
          target="_blank"
          rel="noreferrer"
          whileHover={reduceMotion ? undefined : { y: -4, scale: 1.04 }}
          whileTap={reduceMotion ? undefined : { scale: 0.96 }}
          className="inline-flex size-11 items-center justify-center rounded-full border border-[#eadfce] bg-white/72 text-stone-700 shadow-[0_10px_24px_rgba(67,52,35,0.07)] outline-none transition duration-200 hover:border-[#d9c2a6] hover:bg-[#7d5434] hover:text-white hover:shadow-[0_16px_30px_rgba(67,52,35,0.14)] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 focus-visible:ring-offset-[#fbf6ed]"
        >
          {social.icon}
        </motion.a>
      ))}
    </div>
  );
}

function NewsletterMiniCta() {
  const reduceMotion = useReducedMotion();
  const emailId = useId();
  const feedbackId = useId();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("No spam. Just fresh recipes and useful kitchen notes.");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isValidEmail(email)) {
      setStatus("error");
      setMessage("Please enter a valid email address.");
      return;
    }

    setStatus("loading");
    setMessage("Adding you to the weekly list...");

    await new Promise((resolve) => setTimeout(resolve, 650));

    setStatus("success");
    setMessage("You're in. Fresh recipes are headed your way.");
    setEmail("");
  }

  return (
    <FooterColumn title="Get Weekly Recipes">
      <p className="max-w-[300px] text-[15px] leading-7 text-stone-600">
        Subscribe for fresh recipes, cooking inspiration, and kitchen tips.
      </p>

      <form onSubmit={onSubmit} noValidate className="mt-6 w-full max-w-[340px]">
        <label htmlFor={emailId} className="sr-only">
          Email address
        </label>
        <div className="space-y-3">
          <div className="relative">
            <Mail
              aria-hidden="true"
              size={18}
              className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-stone-400"
            />
            <input
              id={emailId}
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                if (status === "error") {
                  setStatus("idle");
                  setMessage("No spam. Just fresh recipes and useful kitchen notes.");
                }
              }}
              placeholder="Your email"
              aria-invalid={status === "error" ? "true" : "false"}
              aria-describedby={feedbackId}
              disabled={status === "loading"}
              className="h-[52px] w-full rounded-full border border-[#e5d8c8] bg-white pl-12 pr-5 text-[15px] text-stone-950 shadow-[0_10px_24px_rgba(67,52,35,0.05)] outline-none transition placeholder:text-stone-400 hover:border-[#d7c3ad] focus:border-[#7d5434] focus:shadow-[0_0_0_4px_rgba(125,84,52,0.12)] disabled:cursor-not-allowed disabled:opacity-70"
            />
          </div>

          <motion.button
            type="submit"
            disabled={status === "loading"}
            whileHover={reduceMotion || status === "loading" ? undefined : { y: -2 }}
            whileTap={reduceMotion || status === "loading" ? undefined : { scale: 0.98 }}
            className="inline-flex min-h-[52px] w-full items-center justify-center gap-2 rounded-full bg-stone-950 px-6 text-[15px] font-semibold text-white shadow-[0_16px_32px_rgba(40,32,24,0.2)] outline-none transition duration-200 hover:bg-[#7d5434] hover:shadow-[0_20px_38px_rgba(67,52,35,0.24)] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 focus-visible:ring-offset-[#fbf6ed] disabled:cursor-not-allowed disabled:opacity-75"
          >
            {status === "loading" ? (
              <>
                <Loader2 aria-hidden="true" size={17} className="animate-spin" />
                Subscribing
              </>
            ) : (
              "Subscribe"
            )}
          </motion.button>
        </div>

        <p
          id={feedbackId}
          role={status === "error" ? "alert" : status === "success" ? "status" : undefined}
          className={[
            "mt-3 inline-flex min-h-5 items-center justify-center gap-2 text-sm md:justify-start",
            status === "error"
              ? "font-medium text-red-700"
              : status === "success"
                ? "font-semibold text-[#617542]"
                : "text-stone-500",
          ].join(" ")}
        >
          {status === "success" ? <CheckCircle2 aria-hidden="true" size={16} /> : null}
          {message}
        </p>
      </form>
    </FooterColumn>
  );
}

function BackToTopButton() {
  const reduceMotion = useReducedMotion();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateVisibility = () => setIsVisible(window.scrollY > 520);

    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });
    return () => window.removeEventListener("scroll", updateVisibility);
  }, []);

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  }

  return (
    <AnimatePresence>
      {isVisible ? (
        <motion.button
          type="button"
          aria-label="Back to top"
          onClick={scrollToTop}
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 14, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 14, scale: 0.96 }}
          whileHover={reduceMotion ? undefined : { y: -3 }}
          whileTap={reduceMotion ? undefined : { scale: 0.96 }}
          className="fixed bottom-5 right-5 z-40 inline-flex size-12 items-center justify-center rounded-full border border-white/70 bg-stone-950 text-white shadow-[0_18px_40px_rgba(40,32,24,0.24)] outline-none transition hover:bg-[#7d5434] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 sm:bottom-8 sm:right-8"
        >
          <ArrowUp aria-hidden="true" size={19} />
        </motion.button>
      ) : null}
    </AnimatePresence>
  );
}

export function Footer({ data = footerData }: FooterProps) {
  const reduceMotion = useReducedMotion();
  const currentYear = new Date().getFullYear();
  const revealProps = reduceMotion
    ? {}
    : {
        initial: "hidden",
        whileInView: "show",
        viewport: { once: true, amount: 0.18 },
      };

  return (
    <footer className="relative w-full overflow-hidden border-t border-[#eadfce] bg-[#fbf6ed]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_12%,rgba(255,255,255,0.72),transparent_30%),linear-gradient(180deg,rgba(255,252,246,0.72),rgba(246,237,222,0.56))]"
      />

      <motion.div
        variants={gridVariants}
        {...revealProps}
        className="relative mx-auto grid max-w-[1280px] grid-cols-1 gap-12 px-4 pb-6 pt-14 sm:px-6 sm:pb-8 sm:pt-20 md:grid-cols-2 md:gap-x-12 md:gap-y-14 lg:grid-cols-[1.25fr_0.72fr_0.9fr_1fr] lg:gap-14 lg:px-8 lg:pb-10 lg:pt-[100px]"
      >
        <FooterColumn>
          <Link
            href="/"
            aria-label="YARA BITES homepage"
            className="font-serif text-[26px] font-black uppercase tracking-[0.08em] text-stone-950 outline-none transition-colors hover:text-[#7d5434] focus-visible:rounded-sm focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 focus-visible:ring-offset-[#fbf6ed]"
          >
            {data.brand}
          </Link>

          <p className="mt-5 max-w-[320px] text-[15px] leading-7 text-stone-600">
            {data.description}
          </p>

          {data.trustStatement ? (
            <p className="mt-4 text-sm font-medium text-[#7d5434]">{data.trustStatement}</p>
          ) : null}

          <SocialIcons socialLinks={data.socialLinks} />
        </FooterColumn>

        <FooterColumn title="Quick Links">
          <ul className="space-y-2.5">
            {data.navigationLinks.map((link) => (
              <FooterNavLink key={link.href} {...link} />
            ))}
          </ul>
        </FooterColumn>

        <FooterColumn title="Categories">
          <ul className="space-y-2.5">
            {data.categoryLinks.map((link) => (
              <FooterNavLink key={link.href} {...link} />
            ))}
          </ul>
        </FooterColumn>

        {data.newsletterEnabled ? <NewsletterMiniCta /> : null}
      </motion.div>

      <div className="relative mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={reduceMotion ? false : { scaleX: 0, opacity: 0 }}
          whileInView={{ scaleX: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
          className="h-px origin-center bg-gradient-to-r from-transparent via-[#dbcbb8] to-transparent"
        />

        <div className="flex flex-col items-center justify-between gap-5 py-6 text-center md:flex-row md:py-8 md:text-left">
          <p className="text-sm text-stone-500">
            © {currentYear} {data.brand}. All rights reserved.
          </p>

          <nav aria-label="Footer policy links">
            <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3 md:justify-end">
              {policyLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="rounded-sm text-sm font-medium text-stone-500 outline-none transition hover:text-stone-950 hover:underline hover:underline-offset-4 focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 focus-visible:ring-offset-[#fbf6ed]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      <BackToTopButton />
    </footer>
  );
}

export default Footer;
