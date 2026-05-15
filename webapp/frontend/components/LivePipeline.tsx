"use client";

import { Fragment, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import {
  BeakerIcon,
  BoltIcon,
  CpuChipIcon,
  DocumentMagnifyingGlassIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

/**
 * "Live thinking" pipeline visualization shown while the backend is working.
 *
 * The backend currently returns one big POST so we don't have real-time
 * progress, but we *do* know roughly how long each stage takes (the LLM
 * generation step is the dominant cost). We use a deterministic timeline
 * so viewers can literally watch the agent reason: PLAN → RETRIEVE → MEMORY
 * → SYNTHESIZE → VERIFY → JUDGE.
 *
 * Each stage has its own "running" state with a soft spinner, then graduates
 * to "done" with a green check.  We never claim a stage is done before its
 * minimum duration has passed, but we will *hold* on the last stage until
 * the actual request resolves.
 */

interface Stage {
  id: string;
  label: string;
  desc: string;
  blurb: string;          // shown as the active-stage caption
  Icon: typeof SparklesIcon;
  durationMs: number;     // realistic time before moving to "done"
}

const STAGES: Stage[] = [
  {
    id: "plan",
    label: "Plan",
    desc: "Decompose the goal",
    blurb:
      "SimplePlanner decomposes the question into 3 web-search sub-tasks.",
    Icon: SparklesIcon,
    durationMs: 600,
  },
  {
    id: "retrieve",
    label: "Retrieve",
    desc: "Search corpus",
    blurb:
      "WebSearchExecutor queries the local SciFact corpus via Qdrant vector search.",
    Icon: DocumentMagnifyingGlassIcon,
    durationMs: 1100,
  },
  {
    id: "memory",
    label: "Memory",
    desc: "Store evidence",
    blurb: "WorkingMemory deduplicates retrieved passages and indexes by task.",
    Icon: BeakerIcon,
    durationMs: 500,
  },
  {
    id: "synth",
    label: "Synthesize",
    desc: "Form claims",
    blurb:
      "SimpleSynthesizer turns the retrieved evidence into structured candidate claims.",
    Icon: BoltIcon,
    durationMs: 900,
  },
  {
    id: "verify",
    label: "Verify",
    desc: "Ground claims",
    blurb:
      "EvidenceChecker confirms every claim cites a real, retrieved evidence item.",
    Icon: ShieldCheckIcon,
    durationMs: 600,
  },
  {
    id: "judge",
    label: "Answer",
    desc: "v3 + base LLM",
    blurb:
      "Local Qwen-0.5B writes a grounded answer with [n] citations; the v3 adapter judges each claim.",
    Icon: CpuChipIcon,
    durationMs: 7000, // dominant cost — model generation
  },
];

type StageState = "pending" | "running" | "done";

export function LivePipeline() {
  // index of currently-running stage. `done` if >= STAGES.length.
  const [active, setActive] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let i = 0;
    const advance = () => {
      if (cancelled) return;
      if (i >= STAGES.length - 1) {
        // hold on the last stage — the parent unmounts us when the
        // request resolves.
        setActive(STAGES.length - 1);
        return;
      }
      i += 1;
      setActive(i);
      window.setTimeout(advance, STAGES[i].durationMs);
    };
    setActive(0);
    const handle = window.setTimeout(advance, STAGES[0].durationMs);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, []);

  const stateFor = (idx: number): StageState => {
    if (idx < active) return "done";
    if (idx === active) return "running";
    return "pending";
  };

  const currentBlurb = STAGES[Math.min(active, STAGES.length - 1)].blurb;

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.4 }}
      className="surface-panel relative overflow-hidden rounded-3xl p-6 md:p-7"
    >
      {/* soft top hairline */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-400/50 to-transparent" />
      {/* faint corner glow to match the answer card */}
      <div className="pointer-events-none absolute -top-20 left-1/2 h-40 w-[28rem] -translate-x-1/2 rounded-full bg-brand-500/15 blur-3xl" />

      <div className="relative mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <motion.span
            className="inline-block h-4 w-4 rounded-full border-2 border-brand-400 border-t-transparent"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
          />
          <div className="leading-tight">
            <div className="text-sm font-semibold text-ink-100">
              Agent is working…
            </div>
            <div className="text-[11px] text-ink-400">
              first run loads the model — give it ~20s
            </div>
          </div>
        </div>
        <div className="hidden text-[10.5px] font-semibold uppercase tracking-[0.22em] text-ink-500 md:block">
          live pipeline
        </div>
      </div>

      {/* Horizontal flow (md+) — all stage nodes align on one horizontal axis. */}
      <div role="list" className="relative hidden items-start justify-between gap-0 md:flex">
        {STAGES.map((stage, i) => (
          <Fragment key={stage.id}>
            <StageNode stage={stage} state={stateFor(i)} />
            {i < STAGES.length - 1 && (
              <Connector active={i < active} running={i === active} />
            )}
          </Fragment>
        ))}
      </div>

      {/* Compact (sm) */}
      <ol className="grid grid-cols-2 gap-3 md:hidden">
        {STAGES.map((stage, i) => (
          <CompactNode key={stage.id} stage={stage} state={stateFor(i)} />
        ))}
      </ol>

      {/* Live caption explaining the current stage */}
      <div className="relative mt-6 min-h-[3.25rem] rounded-xl border border-white/5 bg-white/[0.02] p-3">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentBlurb}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.25 }}
            className="flex items-start gap-2 text-xs"
          >
            <SparklesIcon className="mt-0.5 h-3.5 w-3.5 flex-none text-brand-300" />
            <span className="leading-relaxed text-ink-200">{currentBlurb}</span>
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.section>
  );
}

/* ───────────────────────── Stage node ───────────────────────── */

function StageNode({ stage, state }: { stage: Stage; state: StageState }) {
  const Icon = stage.Icon;
  const isDone = state === "done";
  const isRunning = state === "running";

  return (
    <div
      role="listitem"
      title={stage.blurb}
      className="relative flex w-[88px] flex-none flex-col items-center text-center"
    >
      <div className="relative h-12 w-12">
        {/* Outer pulse ring while running — slower, breathier */}
        {isRunning && (
          <motion.span
            aria-hidden
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: [0.8, 1.6, 0.8], opacity: [0, 0.5, 0] }}
            transition={{ repeat: Infinity, duration: 2.2, ease: "easeInOut" }}
            className="absolute inset-0 rounded-full bg-brand-400/40 blur-md"
          />
        )}

        <motion.div
          animate={{
            borderColor: isDone
              ? "rgba( 16,185,129,0.55)"
              : isRunning
              ? "rgba( 94,234,212,0.85)"
              : "rgba(148,163,184,0.10)",
            boxShadow: isDone
              ? "0 0 18px -6px rgba( 16,185,129,0.45)"
              : isRunning
              ? "0 0 30px -4px rgba( 94,234,212,0.75)"
              : "0 0 0 0 rgba(0,0,0,0)",
          }}
          transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
          className="relative flex h-12 w-12 items-center justify-center rounded-full border bg-surface-inset"
        >
          <motion.span
            animate={{
              color: isDone
                ? "#CBD5E1"
                : isRunning
                ? "#FFFFFF"
                : "#64748B",
            }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
          >
            <Icon className="h-5 w-5" />
          </motion.span>

          {/* Crossfade between the running spinner badge and the done check */}
          <AnimatePresence mode="wait">
            {isDone ? (
              <motion.span
                key="check"
                initial={{ opacity: 0, scale: 0.4 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.6 }}
                transition={{ type: "spring", stiffness: 320, damping: 20 }}
                className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-green shadow-glowGreen ring-2 ring-surface-raised"
              >
                <CheckCircleIcon className="h-3 w-3 text-white" />
              </motion.span>
            ) : isRunning ? (
              <motion.span
                key="spinner"
                initial={{ opacity: 0, scale: 0.6 }}
                animate={{ opacity: 1, scale: 1, rotate: 360 }}
                exit={{ opacity: 0, scale: 0.6 }}
                transition={{
                  opacity: { duration: 0.25 },
                  scale:   { duration: 0.25 },
                  rotate:  { repeat: Infinity, duration: 1.1, ease: "linear" },
                }}
                className="absolute -bottom-1 -right-1 inline-block h-4 w-4 rounded-full border-2 border-brand-400 border-t-transparent bg-surface-raised"
              />
            ) : null}
          </AnimatePresence>
        </motion.div>
      </div>

      <motion.div
        animate={{ color: isRunning ? "#F8FAFC" : "#CBD5E1" }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        className="mt-3 text-[11px] font-semibold uppercase tracking-wide"
      >
        {stage.label}
      </motion.div>
      <div className="mt-0.5 text-[10px] leading-tight text-ink-400">
        {stage.desc}
      </div>
    </div>
  );
}

function CompactNode({ stage, state }: { stage: Stage; state: StageState }) {
  const Icon = stage.Icon;
  const isDone = state === "done";
  const isRunning = state === "running";
  return (
    <li
      title={stage.blurb}
      className={`flex items-start gap-2 rounded-xl border p-3 transition ${
        isRunning
          ? "border-brand-400/40 bg-brand-500/5"
          : isDone
          ? "border-accent-green/30 bg-accent-green/5"
          : "border-white/5 bg-white/[0.02]"
      }`}
    >
      <div
        className={`flex h-8 w-8 flex-none items-center justify-center rounded-lg ring-1 ${
          isDone
            ? "bg-accent-green/15 text-accent-green ring-accent-green/30"
            : isRunning
            ? "bg-brand-500/15 text-brand-100 ring-brand-400/40"
            : "bg-white/[0.03] text-ink-500 ring-white/10"
        }`}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-ink-100">
          {stage.label}
          {isDone && <CheckCircleIcon className="h-3.5 w-3.5 text-accent-green" />}
          {isRunning && (
            <motion.span
              className="inline-block h-3 w-3 rounded-full border-2 border-brand-400 border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
            />
          )}
        </div>
        <div className="truncate text-[11px] text-ink-400">{stage.desc}</div>
      </div>
    </li>
  );
}

/* ───────────────────────── Connector ───────────────────────── */

function Connector({ active, running }: { active: boolean; running: boolean }) {
  // Smooth easeOutExpo — feels liquid when the line draws in.
  const drawEase = [0.22, 1, 0.36, 1] as const;
  // Symmetric easeInOut for the comet so it glides instead of jerks at the ends.
  const cometEase = [0.45, 0.05, 0.55, 0.95] as const;

  return (
    <div className="pointer-events-none relative mt-6 flex-1 self-start" aria-hidden>
      {/* Resting track */}
      <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 rounded-full bg-white/[0.06]" />

      {/* Soft underlying glow — draws in together with the hairline */}
      <motion.div
        initial={false}
        animate={{ scaleX: active ? 1 : 0, opacity: active ? 0.7 : 0 }}
        transition={{
          scaleX: { duration: 1.1, ease: drawEase },
          opacity: { duration: 0.6, ease: "easeOut" },
        }}
        style={{ transformOrigin: "left center", willChange: "transform, opacity" }}
        className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-gradient-to-r from-brand-400/40 via-accent-cyan/40 to-accent-violet/40 blur-md"
      />

      {/* Crisp hairline */}
      <motion.div
        initial={false}
        animate={{ scaleX: active ? 1 : 0 }}
        transition={{ duration: 1.1, ease: drawEase }}
        style={{ transformOrigin: "left center", willChange: "transform" }}
        className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 rounded-full bg-gradient-to-r from-brand-400 via-accent-cyan to-accent-violet"
      />

      {/* Comet — head + soft trail glide together while the next stage runs */}
      {running && (
        <motion.div
          className="absolute top-1/2"
          initial={{ left: "-6%", opacity: 0 }}
          animate={{ left: "106%", opacity: [0, 1, 1, 0] }}
          transition={{
            repeat: Infinity,
            duration: 2.0,
            ease: cometEase,
            times: [0, 0.12, 0.88, 1],
          }}
          style={{ willChange: "left, opacity" }}
        >
          {/* Soft trail extending backwards from the head */}
          <span
            className="absolute right-0 top-0 h-px w-12 -translate-y-1/2 rounded-full"
            style={{
              background:
                "linear-gradient(270deg, rgba(56,189,248,0.9), rgba(56,189,248,0))",
            }}
          />
          {/* Bright head */}
          <span className="absolute left-0 top-0 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent-cyan shadow-[0_0_18px_5px_rgba(56,189,248,0.65)]" />
        </motion.div>
      )}
    </div>
  );
}
