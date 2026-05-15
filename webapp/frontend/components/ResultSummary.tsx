"use client";

import { motion } from "framer-motion";
import {
  ClockIcon,
  CpuChipIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

interface ResultSummaryProps {
  elapsedSeconds: number;
  evidenceCount: number;
  claimCount: number;
  v3Supported: number;
  v3Total: number;
  safetyClean: boolean;
}

/**
 * Compact, centered glass stat-bar with one pill per metric.
 *
 * Designed to be the first thing the viewer reads after a run finishes —
 * passages, claims, judge agreement, safety, end-to-end latency — without
 * dominating the page.  Wraps gracefully on narrow screens.
 */
export function ResultSummary({
  elapsedSeconds,
  evidenceCount,
  claimCount,
  v3Supported,
  v3Total,
  safetyClean,
}: ResultSummaryProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-wrap items-center justify-center gap-2"
    >
      <StatPill
        icon={<DocumentTextIcon className="h-3.5 w-3.5" />}
        value={evidenceCount}
        label="passages"
        tone="brand"
      />
      <StatPill
        icon={<SparklesIcon className="h-3.5 w-3.5" />}
        value={claimCount}
        label="claims"
        tone="violet"
      />
      <StatPill
        icon={<CpuChipIcon className="h-3.5 w-3.5" />}
        value={v3Total === 0 ? "…" : `${v3Supported}/${v3Total}`}
        label="supported"
        tone={
          v3Total === 0
            ? "muted"
            : v3Supported === v3Total
            ? "green"
            : v3Supported >= v3Total / 2
            ? "brand"
            : "amber"
        }
        title="Fraction of extracted claims the fine-tuned v3 adapter judged supported in a pairwise A/B vote."
      />
      <StatPill
        icon={<ShieldCheckIcon className="h-3.5 w-3.5" />}
        value={safetyClean ? "clean" : "blocked"}
        label="safety"
        tone={safetyClean ? "green" : "red"}
      />
      <StatPill
        icon={<ClockIcon className="h-3.5 w-3.5" />}
        value={`${elapsedSeconds.toFixed(1)}s`}
        label="end-to-end"
        tone="muted"
      />
    </motion.div>
  );
}

type Tone = "brand" | "violet" | "green" | "amber" | "red" | "muted";

function StatPill({
  icon,
  value,
  label,
  tone,
  title,
}: {
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  tone: Tone;
  title?: string;
}) {
  const valueColor: Record<Tone, string> = {
    brand: "text-brand-200",
    violet: "text-accent-violet",
    green: "text-accent-green",
    amber: "text-accent-amber",
    red: "text-accent-red",
    muted: "text-ink-200",
  };
  const iconColor: Record<Tone, string> = {
    brand: "text-brand-300",
    violet: "text-accent-violet/90",
    green: "text-accent-green",
    amber: "text-accent-amber",
    red: "text-accent-red",
    muted: "text-ink-400",
  };
  return (
    <span
      title={title}
      className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-ink-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] backdrop-blur transition hover:border-brand-300/30 hover:bg-white/[0.07]"
    >
      <span className={iconColor[tone]}>{icon}</span>
      <span className={`font-mono text-[13px] font-semibold ${valueColor[tone]}`}>
        {value}
      </span>
      <span className="text-[10.5px] uppercase tracking-[0.14em] text-ink-500">
        {label}
      </span>
    </span>
  );
}
