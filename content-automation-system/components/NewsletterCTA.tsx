"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, Loader2, Mail, Sparkles } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

const newsletterSchema = z.object({
  email: z.string().min(1, "Please enter your email").email("Please enter a valid email"),
});

type NewsletterFormValues = z.infer<typeof newsletterSchema>;

async function handleNewsletterSignup(email: string) {
  await new Promise((resolve) => setTimeout(resolve, 900));
  return { ok: true, email };
}

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

export default function NewsletterCTA() {
  const reduceMotion = useReducedMotion();
  const [isSubscribed, setIsSubscribed] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<NewsletterFormValues>({
    resolver: zodResolver(newsletterSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(values: NewsletterFormValues) {
    await handleNewsletterSignup(values.email);
    setIsSubscribed(true);
    reset();
  }

  return (
    <section
      aria-labelledby="newsletter-heading"
      className="w-full bg-white px-4 py-12 sm:px-6 sm:py-16 lg:px-8 lg:py-20"
    >
      <motion.div
        initial={reduceMotion ? false : "hidden"}
        whileInView={reduceMotion ? undefined : "show"}
        viewport={{ once: true, amount: 0.35 }}
        variants={containerVariants}
        className="mx-auto max-w-[1280px]"
      >
        <div className="relative overflow-hidden rounded-[28px] border border-[#eadfce] bg-gradient-to-br from-[#fff8ed] via-[#f7ecdc] to-[#eef0df] p-7 shadow-[0_28px_80px_rgba(67,52,35,0.13)] sm:rounded-[32px] sm:p-12 lg:rounded-[36px] lg:p-[72px]">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0">
            <div className="absolute -left-16 top-10 size-56 rounded-full bg-white/55 blur-3xl" />
            <div className="absolute bottom-0 right-1/4 size-64 rounded-full bg-[#9aa56d]/20 blur-3xl" />
          </div>

          <div className="relative grid items-center gap-12 lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
            <div className="text-center lg:text-left">
              <motion.p
                variants={itemVariants}
                className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500 sm:text-sm"
              >
                Join the community
              </motion.p>

              <motion.h2
                id="newsletter-heading"
                variants={itemVariants}
                className="mt-4 max-w-[620px] font-serif text-[34px] font-bold leading-[1.02] tracking-[-0.015em] text-stone-950 sm:text-[44px] lg:text-[56px]"
              >
                Get Fresh Recipes Delivered Weekly
              </motion.h2>

              <motion.p
                variants={itemVariants}
                className="mx-auto mt-5 max-w-[540px] text-base leading-8 text-stone-600 lg:mx-0 lg:text-lg"
              >
                Subscribe for easy weeknight dinners, indulgent desserts, cooking inspiration, and exclusive kitchen tips.
              </motion.p>

              <motion.form
                variants={itemVariants}
                onSubmit={handleSubmit(onSubmit)}
                noValidate
                className="mt-8"
              >
                <div className="flex flex-col gap-3 sm:flex-row lg:max-w-[620px]">
                  <div className="relative flex-1">
                    <label htmlFor="newsletter-email" className="sr-only">
                      Email address
                    </label>
                    <Mail
                      aria-hidden="true"
                      size={19}
                      className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-stone-400"
                    />
                    <input
                      id="newsletter-email"
                      type="email"
                      autoComplete="email"
                      placeholder="Enter your email address"
                      aria-invalid={errors.email ? "true" : "false"}
                      aria-describedby={errors.email ? "newsletter-error" : "newsletter-trust"}
                      disabled={isSubmitting}
                      className="h-14 w-full rounded-full border border-stone-200 bg-white pl-12 pr-5 text-base text-stone-950 shadow-sm outline-none transition placeholder:text-stone-400 focus:border-[#8b633f] focus:shadow-[0_0_0_4px_rgba(139,99,63,0.12)] disabled:cursor-not-allowed disabled:opacity-70"
                      {...register("email")}
                    />
                  </div>

                  <motion.button
                    type="submit"
                    disabled={isSubmitting}
                    whileHover={reduceMotion || isSubmitting ? undefined : { y: -2 }}
                    whileTap={reduceMotion || isSubmitting ? undefined : { scale: 0.98 }}
                    className="inline-flex h-14 items-center justify-center gap-2 rounded-full bg-stone-900 px-7 text-base font-semibold text-white shadow-[0_14px_30px_rgba(40,32,24,0.22)] outline-none transition hover:bg-stone-800 hover:shadow-[0_18px_36px_rgba(40,32,24,0.28)] focus-visible:ring-2 focus-visible:ring-stone-900 focus-visible:ring-offset-4 disabled:cursor-not-allowed disabled:opacity-75"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 aria-hidden="true" size={18} className="animate-spin" />
                        Subscribing
                      </>
                    ) : (
                      "Subscribe"
                    )}
                  </motion.button>
                </div>

                <div className="mt-3 min-h-6">
                  {errors.email ? (
                    <p id="newsletter-error" role="alert" className="text-sm font-medium text-red-700">
                      {errors.email.message}
                    </p>
                  ) : isSubscribed ? (
                    <motion.p
                      initial={reduceMotion ? false : { opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="inline-flex items-center gap-2 text-sm font-semibold text-[#5f743e]"
                    >
                      <CheckCircle2 aria-hidden="true" size={17} />
                      Thanks for subscribing!
                    </motion.p>
                  ) : (
                    <p id="newsletter-trust" className="text-sm text-stone-500">
                      No spam. Unsubscribe anytime.
                    </p>
                  )}
                </div>
              </motion.form>
            </div>

            <motion.div variants={itemVariants} className="hidden lg:block">
              <div className="relative mx-auto aspect-[4/5] max-w-[430px] rounded-[32px] bg-white/55 p-4 shadow-[0_26px_55px_rgba(67,52,35,0.18)]">
                <div className="h-full overflow-hidden rounded-[26px] bg-[radial-gradient(circle_at_35%_25%,#f7d89e_0_16%,transparent_17%),radial-gradient(circle_at_62%_40%,#8d9b62_0_18%,transparent_19%),linear-gradient(135deg,#b65f3c,#f1d5a5_52%,#556b39)]" />

                <motion.div
                  aria-hidden="true"
                  animate={reduceMotion ? undefined : { y: [0, -8, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute -left-7 top-10 rounded-2xl bg-white px-4 py-3 shadow-[0_16px_35px_rgba(67,52,35,0.14)]"
                >
                  <span className="flex items-center gap-2 text-sm font-semibold text-stone-800">
                    <Sparkles size={16} className="text-[#8b633f]" />
                    Weekly picks
                  </span>
                </motion.div>

                <motion.div
                  aria-hidden="true"
                  animate={reduceMotion ? undefined : { y: [0, 10, 0] }}
                  transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute -bottom-5 right-8 rounded-2xl bg-[#fff8ed] px-4 py-3 shadow-[0_16px_35px_rgba(67,52,35,0.14)]"
                >
                  <span className="text-sm font-semibold text-stone-800">Easy dinners</span>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
