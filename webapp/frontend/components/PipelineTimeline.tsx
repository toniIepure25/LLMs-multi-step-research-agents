"use client";

import { Fragment } from "react";
import { motion } from "framer-motion";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import {
  BeakerIcon,
  BoltIcon,
  CpuChipIcon,
  DocumentMagnifyingGlassIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

interface PipelineTimelineProps {
  elapsedSeconds: number;
  evidenceCount: number;
  claimCount: number;
  safetyClean: boolean;
}

const STAGES = [
  {
    id: "plan",
    label: "Plan",
    desc: "Decompose the goal",
    Icon: SparklesIcon,
    tooltip: "SimplePlanner: breaks the question into 3 web-search sub-tasks.",
  },
  {
    id: "retrieve",
    label: "Retrieve",
    desc: "Search corpus",
    Icon: DocumentMagnifyingGlassIcon,
    tooltip:
      "WebSearchExecutor: queries the local SciFact corpus via a Qdrant vector index.",
  },
  {
    id: "memory",
    label: "Memory",
    desc: "Store evidence",
    Icon: BeakerIcon,
    tooltip: "WorkingMemory: deduplicates passages and indexes them by task id.",
  },
  {
    id: "synth",
    label: "Synthesize",
    desc: "Form claims",
    Icon: BoltIcon,
    tooltip: "SimpleSynthesizer: turns retrieved evidence into structured claims.",
  },
  {
    id: "verify",
    label: "Verify",
    desc: "Ground claims",
    Icon: ShieldCheckIcon,
    tooltip:
      "EvidenceChecker: confirms each claim cites a real, retrieved evidence id.",
  },
  {
    id: "judge",
    label: "Judge",
    desc: "v3 adapter votes",
    Icon: CpuChipIcon,
    tooltip:
      "Local Qwen-0.5B writes the grounded answer; the v3 LoRA adapter then judges each claim against a contrary one (pairwise A/B preference).",
  },
] as const;

type Stage = (typeof STAGES)[number];

const STEP = 0.28;   // delay between consecutive stages
const FILL = 0.55;   // duration of each connector fill

export function PipelineTimeline({
  elapsedSeconds,
  evidenceCount,
  claimCount,
  safetyClean,
}: PipelineTimelineProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.05 }}
      className="surface-panel relative overflow-hidden rounded-2xl p-6"
    >
      {/* faint top sheen */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-400/40 to-transparent" />

      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-baseline gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-100">
            Pipeline
          </h3>
          <span className="font-mono text-xs text-ink-400">
            end-to-end {elapsedSeconds.toFixed(1)}s
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-ink-400">
          <span>
            <b className="text-ink-50">{evidenceCount}</b> evidence
          </span>
          <span>
            <b className="text-ink-50">{claimCount}</b> claims
          </span>
          <span className={safetyClean ? "text-accent-green" : "text-accent-red"}>
            {safetyClean ? "safety clean" : "safety blocked"}
          </span>
        </div>
      </div>

      {/* ===== Horizontal animated flow (md+) ===== */}
      <div role="list" className="relative hidden items-start md:flex">
        {STAGES.map((stage, i) => (
          <Fragment key={stage.id}>
            <StageNode stage={stage} index={i} />
            {i < STAGES.length - 1 && <Connector index={i} />}
          </Fragment>
        ))}
      </div>

      {/* ===== Compact grid (sm) ===== */}
      <ol className="grid grid-cols-2 gap-3 md:hidden">
        {STAGES.map((stage, i) => {
          const Icon = stage.Icon;
          return (
            <motion.li
              key={stage.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * STEP, duration: 0.4 }}
              title={stage.tooltip}
              className="flex items-start gap-2 rounded-xl border border-white/5 bg-white/[0.02] p-3"
            >
              <div className="flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-brand-500/15 text-brand-200 ring-1 ring-brand-400/30">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-ink-100">
                  {stage.label}
                  <CheckCircleIcon className="h-3.5 w-3.5 text-accent-green" />
                </div>
                <div className="truncate text-[11px] text-ink-400">{stage.desc}</div>
              </div>
            </motion.li>
          );
        })}
      </ol>
    </motion.section>
  );
}

/* ───────────────────────── Stage node ───────────────────────── */

function StageNode({ stage, index }: { stage: Stage; index: number }) {
  const Icon = stage.Icon;
  const arrive = index * STEP;

  return (
    <div
      role="listitem"
      title={stage.tooltip}
      className="relative flex w-24 flex-none flex-col items-center text-center"
    >
      <div className="relative h-12 w-12">
        {/* Outer pulse ring (one-shot when wave arrives) */}
        <motion.span
          aria-hidden
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: [0.6, 1.7, 1.7], opacity: [0, 0.55, 0] }}
          transition={{ delay: arrive, duration: 1.4, ease: "easeOut" }}
          className="absolute inset-0 rounded-full bg-brand-400/40 blur-md"
        />
        {/* Disc */}
        <motion.div
          initial={{
            scale: 0.85,
            borderColor: "rgba(148,163,184,0.10)",
            boxShadow: "0 0 0 0 rgba(0,0,0,0)",
          }}
          animate={{
            scale: 1,
            borderColor: [
              "rgba(148,163,184,0.10)",
              "rgba( 94,234,212,0.85)",
              "rgba( 16,185,129,0.55)",
            ],
            boxShadow: [
              "0 0 0 0 rgba(0,0,0,0)",
              "0 0 30px -4px rgba(94,234,212,0.75)",
              "0 0 18px -6px rgba(16,185,129,0.45)",
            ],
          }}
          transition={{ delay: arrive, duration: 0.7, times: [0, 0.45, 1] }}
          className="relative flex h-12 w-12 items-center justify-center rounded-full border bg-surface-inset"
        >
          <motion.div
            initial={{ opacity: 0.3, scale: 0.85 }}
            animate={{
              opacity: [0.3, 1, 1],
              scale: [0.85, 1.05, 1],
              color: ["#5EEAD4", "#F8FAFC", "#99F6E4"],
            }}
            transition={{ delay: arrive + 0.05, duration: 0.55, times: [0, 0.5, 1] }}
            className="text-brand-200"
          >
            <Icon className="h-5 w-5" />
          </motion.div>

          {/* Check overlay slides in once the wave has passed this stage */}
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: arrive + 0.55, duration: 0.3 }}
            className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-green shadow-glowGreen ring-2 ring-surface-raised"
          >
            <CheckCircleIcon className="h-3 w-3 text-white" />
          </motion.span>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: arrive + 0.2, duration: 0.4 }}
        className="mt-3 text-[11px] font-semibold uppercase tracking-wide text-ink-100"
      >
        {stage.label}
      </motion.div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: arrive + 0.25, duration: 0.4 }}
        className="mt-0.5 text-[10px] leading-tight text-ink-400"
      >
        {stage.desc}
      </motion.div>
    </div>
  );
}

/* ───────────────────────── Connector ───────────────────────── */

function Connector({ index }: { index: number }) {
  const arrive = index * STEP;

  return (
    <div className="relative mt-6 flex-1 self-start" aria-hidden>
      {/* track */}
      <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 rounded-full bg-white/[0.06]" />

      {/* gradient fill that sweeps left → right */}
      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay: arrive + 0.15, duration: FILL, ease: "easeOut" }}
        style={{ transformOrigin: "left" }}
        className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 rounded-full bg-gradient-to-r from-brand-400 via-accent-cyan to-accent-violet shadow-[0_0_12px_-2px_rgba(94,234,212,0.7)]"
      />

      {/* "comet" head riding the wave */}
      <motion.span
        initial={{ left: "0%", opacity: 0 }}
        animate={{ left: "100%", opacity: [0, 1, 1, 0] }}
        transition={{
          delay: arrive,
          duration: FILL + 0.1,
          ease: "easeOut",
          times: [0, 0.15, 0.85, 1],
        }}
        className="absolute top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent-cyan shadow-[0_0_18px_5px_rgba(56,189,248,0.6)]"
      />
    </div>
  );
}

