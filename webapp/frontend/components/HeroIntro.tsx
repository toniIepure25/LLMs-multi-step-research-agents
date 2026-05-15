"use client";

import { motion } from "framer-motion";
import {
  BeakerIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import type { InfoResponse } from "@/lib/types";

interface HeroIntroProps {
  info: InfoResponse | null;
  /**
   * When true, render a slim *centered* version of the hero (smaller logo,
   * smaller title, tighter spacing).  This is used once a research result
   * is on screen so the answer takes priority but the brand identity
   * stays consistent with the landing state.
   */
  compact?: boolean;
}

/**
 * Centered hero with a large glass logo, title, subtitle, and identity pills.
 *
 * In `compact` mode the same structure shrinks proportionally — same
 * centered layout, just less vertical real estate — so the answered
 * state feels like the landing page compressed upward, not a separate
 * dashboard.
 */
export function HeroIntro({ info, compact = false }: HeroIntroProps) {
  // Size constants per mode.  All other layout is identical.
  const iconBox = compact ? "h-10 w-10 rounded-[14px]" : "h-20 w-20 rounded-[22px]";
  const iconInner = compact ? "rounded-[12px]" : "rounded-[20px]";
  const iconSize = compact ? "h-5 w-5" : "h-9 w-9";
  const titleSize = compact
    ? "text-xl md:text-2xl"
    : "text-5xl md:text-6xl";
  const subtitle = compact
    ? "Local research answers, grounded in retrieved evidence."
    : "A local multi-step research agent that plans, retrieves, synthesizes, and verifies evidence-grounded answers.";
  const sectionPad = compact ? "pt-4 md:pt-6" : "pt-12 md:pt-16";
  const titleSpacing = compact ? "mt-2.5" : "mt-6";
  const subtitleSpacing = compact ? "mt-1 text-[12.5px] md:text-[13px]" : "mt-4 text-[15px] md:text-base";
  const pillsSpacing = compact ? "mt-2.5" : "mt-6";

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
      className={`relative z-10 mx-auto w-full max-w-3xl px-6 ${sectionPad}`}
    >
      <div className="flex flex-col items-center text-center">
        {/* Glass logo with halo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
          className="relative"
        >
          <div className="pointer-events-none absolute inset-0 -z-10 rounded-[28px] bg-gradient-to-br from-brand-500/40 via-accent-violet/30 to-accent-cyan/35 blur-2xl" />
          <div
            className={`relative flex ${iconBox} items-center justify-center border border-white/10 bg-gradient-to-br from-white/[0.07] via-white/[0.03] to-white/[0.01] shadow-glow backdrop-blur-xl ring-1 ring-inset ring-white/[0.06]`}
          >
            <div className={`pointer-events-none absolute inset-px ${iconInner} bg-gradient-to-br from-white/10 via-transparent to-transparent`} />
            <BeakerIcon className={`relative ${iconSize} text-white drop-shadow-[0_0_18px_rgba(94,234,212,0.7)]`} />
          </div>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08, duration: 0.5 }}
          className={`${titleSpacing} bg-gradient-to-br from-white via-brand-200 to-accent-cyan bg-clip-text font-semibold tracking-tight text-transparent drop-shadow-[0_0_30px_rgba(94,234,212,0.25)] ${titleSize}`}
        >
          Ask the agent.
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.16, duration: 0.5 }}
          className={`mx-auto max-w-2xl leading-relaxed text-ink-300 ${subtitleSpacing}`}
        >
          {subtitle}
        </motion.p>

        {/* Identity pills */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24, duration: 0.45 }}
          className={`flex flex-wrap items-center justify-center gap-2 ${pillsSpacing}`}
        >
          <GlassPill icon={<CpuChipIcon className="h-3.5 w-3.5" />} label="model">
            {info ? shortModel(info.base_model) : "Qwen2.5-0.5B-Instruct"}
          </GlassPill>
          <GlassPill icon={<SparklesIcon className="h-3.5 w-3.5" />} label="adapter">
            {info?.adapter_path
              ? shortAdapter(info.adapter_path)
              : "asar-qwen-0.5b-scifact-dpo-v3"}
          </GlassPill>
          <GlassPill icon={<ShieldCheckIcon className="h-3.5 w-3.5" />} label="safety">
            <span className={info?.safety_enabled === false ? "text-ink-300" : "text-accent-green"}>
              {info?.safety_enabled === false ? "off" : "on"}
            </span>
          </GlassPill>
        </motion.div>
      </div>
    </motion.section>
  );
}

function GlassPill({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] text-ink-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur transition hover:border-brand-300/30 hover:bg-white/[0.07]">
      <span className="text-ink-400">{icon}</span>
      <span className="text-ink-400">{label}</span>
      <span className="font-medium text-ink-100">{children}</span>
    </span>
  );
}

function shortModel(name: string): string {
  if (!name) return "—";
  const slash = name.lastIndexOf("/");
  return slash >= 0 ? name.slice(slash + 1) : name;
}

function shortAdapter(path: string): string {
  if (!path) return "—";
  const parts = path.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? path;
}
