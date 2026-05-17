"use client";

import Image from "next/image";
import Link from "next/link";
import { Check, Instagram, Play, Send, Youtube } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

export type AuthorSocialLink = {
  label: "Instagram" | "Pinterest" | "YouTube" | "TikTok" | string;
  href: string;
};

export type Author = {
  name: string;
  title: string;
  bio: string;
  image: string;
  socialLinks?: AuthorSocialLink[];
  trustHighlights?: string[];
};

type AuthorSectionProps = {
  author?: Author;
  className?: string;
};

const defaultAuthor: Author = {
  name: "Yara",
  title: "Hi, I’m Yara — sharing simple recipes made with love.",
  bio:
    "I believe cooking should feel joyful, approachable, and full of flavor. Here you'll find easy recipes for everyday meals, sweet treats, and dishes worth sharing.\n\nFrom quick weeknight dinners to cozy weekend baking, every recipe is tested in my kitchen and designed to make home cooking easier and more enjoyable.",
  image: "/images/author-yara.jpg",
  socialLinks: [
    { label: "Instagram", href: "https://instagram.com" },
    { label: "Pinterest", href: "https://pinterest.com" },
    { label: "YouTube", href: "https://youtube.com" },
    { label: "TikTok", href: "https://tiktok.com" },
  ],
  trustHighlights: ["Tested recipes", "Beginner friendly", "Family approved", "Quick everyday meals"],
};

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

function socialIcon(label: string) {
  const key = label.toLowerCase();
  if (key.includes("instagram")) return Instagram;
  if (key.includes("pinterest")) return Send;
  if (key.includes("youtube")) return Youtube;
  if (key.includes("tiktok")) return Play;
  return Send;
}

export default function AuthorSection({ author = defaultAuthor, className = "" }: AuthorSectionProps) {
  const reduceMotion = useReducedMotion();
  const paragraphs = author.bio.split(/\n{2,}/).map((paragraph) => paragraph.trim()).filter(Boolean);
  const highlights = author.trustHighlights?.length ? author.trustHighlights : defaultAuthor.trustHighlights || [];

  return (
    <section
      aria-labelledby="author-heading"
      className={[
        "relative isolate w-full overflow-hidden bg-[#fffdf8] px-4 py-14 sm:px-6 sm:py-20 lg:px-8 lg:py-[100px]",
        className,
      ].join(" ")}
    >
      <motion.div
        initial={reduceMotion ? false : "hidden"}
        whileInView={reduceMotion ? undefined : "show"}
        viewport={{ once: true, amount: 0.25 }}
        variants={containerVariants}
        className="mx-auto grid max-w-[1280px] items-center gap-12 lg:grid-cols-[0.45fr_0.55fr] lg:gap-16"
      >
        <motion.div variants={itemVariants} className="relative mx-auto w-full max-w-[520px]">
          <div className="absolute -bottom-5 -right-5 hidden h-full w-full rounded-[32px] bg-[#efe4d2] sm:block" />
          <motion.div
            whileHover={reduceMotion ? undefined : { scale: 1.015 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="relative aspect-[4/5] overflow-hidden rounded-[28px] bg-stone-100 shadow-[0_28px_70px_rgba(47,38,27,0.16)] sm:rounded-[32px] lg:min-h-[620px]"
          >
            <Image
              src={author.image}
              alt={`${author.name}, recipe author`}
              fill
              sizes="(min-width: 1024px) 500px, 100vw"
              className="object-cover"
            />
          </motion.div>

          <motion.div
            aria-hidden="true"
            animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -left-3 bottom-8 rounded-2xl bg-white px-5 py-4 shadow-[0_18px_40px_rgba(47,38,27,0.14)] sm:-left-8"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Kitchen Notes</p>
            <p className="mt-1 font-serif text-xl font-bold text-stone-950">with {author.name}</p>
          </motion.div>
        </motion.div>

        <div className="text-center lg:text-left">
          <motion.p
            variants={itemVariants}
            className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500 sm:text-sm"
          >
            About the author
          </motion.p>

          <motion.h2
            id="author-heading"
            variants={itemVariants}
            className="mx-auto mt-4 max-w-[680px] font-serif text-[34px] font-bold leading-[1.02] tracking-normal text-stone-950 sm:text-[46px] lg:mx-0 lg:text-[60px]"
          >
            {author.title}
          </motion.h2>

          <motion.div variants={itemVariants} className="mx-auto mt-6 max-w-[620px] space-y-4 lg:mx-0">
            {paragraphs.map((paragraph) => (
              <p key={paragraph} className="text-base leading-8 text-stone-600 lg:text-lg">
                {paragraph}
              </p>
            ))}
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="mx-auto mt-7 grid max-w-[620px] gap-3 text-left sm:grid-cols-2 lg:mx-0"
          >
            {highlights.map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-full bg-white px-4 py-3 shadow-sm ring-1 ring-stone-100">
                <span className="grid size-7 shrink-0 place-items-center rounded-full bg-[#f1e5d2] text-[#6f7c45]">
                  <Check aria-hidden="true" size={16} strokeWidth={2.4} />
                </span>
                <span className="text-sm font-semibold text-stone-700">{item}</span>
              </div>
            ))}
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start"
          >
            <motion.div whileHover={reduceMotion ? undefined : { y: -2 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
              <Link
                href="/about"
                className="inline-flex h-12 items-center justify-center rounded-full bg-stone-900 px-7 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(40,32,24,0.22)] outline-none transition hover:bg-stone-800 hover:shadow-[0_18px_36px_rgba(40,32,24,0.28)] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
              >
                Read My Story
              </Link>
            </motion.div>

            <motion.div whileHover={reduceMotion ? undefined : { y: -2 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
              <Link
                href="/recipes"
                className="inline-flex h-12 items-center justify-center rounded-full border border-stone-300 bg-white px-7 text-sm font-semibold text-stone-900 outline-none transition hover:bg-stone-50 focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
              >
                Browse Recipes
              </Link>
            </motion.div>
          </motion.div>

          {author.socialLinks?.length ? (
            <motion.div
              variants={itemVariants}
              aria-label={`${author.name} social links`}
              className="mt-7 flex items-center justify-center gap-3 lg:justify-start"
            >
              {author.socialLinks.map((link) => {
                const Icon = socialIcon(link.label);
                return (
                  <a
                    key={`${link.label}-${link.href}`}
                    href={link.href}
                    aria-label={link.label}
                    target="_blank"
                    rel="noreferrer"
                    className="grid size-10 place-items-center rounded-full border border-stone-200 bg-white text-stone-700 transition hover:-translate-y-0.5 hover:border-stone-300 hover:text-stone-950 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4"
                  >
                    <Icon aria-hidden="true" size={18} />
                  </a>
                );
              })}
            </motion.div>
          ) : null}
        </div>
      </motion.div>
    </section>
  );
}
