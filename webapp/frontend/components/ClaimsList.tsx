"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircleIcon,
  ChevronDownIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";

import { rerank } from "@/lib/api";
import type { Claim, DecisionPacket, EpistemicStatus } from "@/lib/types";

interface ClaimsListProps {
  decision: DecisionPacket;
  goal: string;
  rerankEnabled: boolean;
  /** Called whenever a v3 rerank verdict resolves, with cumulative tally. */
  onAgreementUpdate?: (supported: number, total: number) => void;
}

export function ClaimsList({ decision, goal, rerankEnabled, onAgreementUpdate }: ClaimsListProps) {
  const [verdicts, setVerdicts] = useState<
    Record<
      string,
      { state: "idle" | "loading" | "done" | "err"; verdict: "A" | "B" | null; latency: number | null }
    >
  >({});

  // Process reranks STRICTLY SEQUENTIALLY.  The local model can only do one
  // generation at a time on MPS, and parallel calls cause some of them to
  // time out / hang up the proxy (the cause of the spurious "v3 offline").
  useEffect(() => {
    if (!rerankEnabled) return;
    let cancelled = false;
    const counter =
      "The opposite of the above claim is true and the original claim is not supported by evidence.";

    async function runAll() {
      for (const claim of decision.claims) {
        if (cancelled) return;
        setVerdicts((prev) => ({
          ...prev,
          [claim.claim_id]: { state: "loading", verdict: null, latency: null },
        }));
        try {
          // Use the SHORT claim text (not the full abstract) — it's more
          // on-task for the A/B preference call and much faster.
          const r = await rerank({ goal, claimA: claim.text, claimB: counter });
          if (cancelled) return;
          const pick: "A" | "B" = r.preferred === "B" ? "B" : "A";
          setVerdicts((prev) => ({
            ...prev,
            [claim.claim_id]: { state: "done", verdict: pick, latency: r.elapsed_seconds },
          }));
        } catch {
          if (cancelled) return;
          setVerdicts((prev) => ({
            ...prev,
            [claim.claim_id]: { state: "err", verdict: null, latency: null },
          }));
        }
      }
    }
    void runAll();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decision.decision_id, goal, rerankEnabled]);

  useEffect(() => {
    if (!onAgreementUpdate) return;
    const entries = Object.values(verdicts);
    const done = entries.filter((v) => v.state === "done");
    const sup = done.filter((v) => v.verdict === "A").length;
    onAgreementUpdate(sup, done.length);
  }, [verdicts, onAgreementUpdate]);

  return (
    <section className="surface-panel rounded-2xl p-6">
      <SectionHeader
        title="Claims"
        caption="The synthesizer extracted these candidate findings from the retrieved evidence. The fine-tuned v3 adapter is invoked on each one to judge whether the corpus supports it."
        right={
          <span className="text-xs text-ink-400">
            {decision.claims.length} item{decision.claims.length === 1 ? "" : "s"}
          </span>
        }
      />

      <ol className="mt-4 space-y-3">
        {decision.claims.map((claim, idx) => {
          const v = verdicts[claim.claim_id] ?? {
            state: "idle" as const,
            verdict: null,
            latency: null,
          };
          return (
            <ClaimRow
              key={claim.claim_id}
              claim={claim}
              index={idx}
              state={v.state}
              verdict={v.verdict}
              latency={v.latency}
            />
          );
        })}
      </ol>

      {decision.information_gaps?.length ? (
        <div className="mt-5 rounded-xl border border-accent-amber/30 bg-accent-amber/10 p-3">
          <div className="mb-1 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-accent-amber">
            <ExclamationTriangleIcon className="h-3.5 w-3.5" />
            Information gaps
          </div>
          <ul className="list-disc space-y-1 pl-5 text-xs text-amber-100">
            {decision.information_gaps.map((gap, i) => (
              <li key={i}>{gap}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function ClaimRow({
  claim,
  index,
  state,
  verdict,
  latency,
}: {
  claim: Claim;
  index: number;
  state: "idle" | "loading" | "done" | "err";
  verdict: "A" | "B" | null;
  latency: number | null;
}) {
  const [open, setOpen] = useState(false);
  const [showFull, setShowFull] = useState(false);

  const fullText = claim.text_full ?? claim.text;
  const hasMore =
    typeof claim.text_full === "string" &&
    claim.text_full.length > claim.text.length + 4;
  const displayText = showFull && hasMore ? fullText : claim.text;

  return (
    <motion.li
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index, duration: 0.3 }}
      className="overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] transition hover:border-white/10 hover:bg-white/[0.04]"
    >
      <div className="flex items-stretch">
        <div className="flex w-10 flex-none items-start justify-center bg-white/[0.03] pt-4 font-mono text-[11px] font-semibold text-ink-400">
          {index + 1}
        </div>
        <div className="min-w-0 flex-1 p-4">
          <p className="text-sm leading-relaxed text-ink-100">{displayText}</p>
          {hasMore && (
            <button
              type="button"
              onClick={() => setShowFull((v) => !v)}
              className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-brand-300 transition hover:text-brand-200"
            >
              <ChevronDownIcon
                className={`h-3 w-3 transition-transform ${showFull ? "rotate-180" : ""}`}
              />
              {showFull ? "show less" : "show full claim"}
            </button>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <EpistemicChip status={claim.epistemic_status} />
            {claim.supporting_evidence_ids.length > 0 && (
              <button
                onClick={() => setOpen((o) => !o)}
                className="inline-flex items-center gap-1 rounded-md bg-white/[0.04] px-1.5 py-0.5 text-[11px] font-medium text-ink-300 transition hover:bg-white/[0.08] hover:text-ink-100"
              >
                <ChevronDownIcon
                  className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`}
                />
                {claim.supporting_evidence_ids.length} supporting
              </button>
            )}
            {claim.contradicting_evidence_ids.length > 0 && (
              <span className="rounded-md bg-accent-red/15 px-1.5 py-0.5 text-[11px] font-medium text-accent-red">
                {claim.contradicting_evidence_ids.length} contradicting
              </span>
            )}
          </div>

          <AnimatePresence>
            {open && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-3 rounded-md border border-white/5 bg-black/30 p-3 font-mono text-[11px] text-ink-300">
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-ink-500">
                    Supporting evidence IDs
                  </div>
                  {claim.supporting_evidence_ids.join(", ")}
                </div>
                {claim.reasoning_trace && (
                  <p className="mt-2 text-xs italic text-ink-400">{claim.reasoning_trace}</p>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right rail: v3 verdict. */}
        <div className="flex w-36 flex-none items-stretch border-l border-white/5 bg-black/20">
          <V3Verdict state={state} verdict={verdict} latency={latency} />
        </div>
      </div>
    </motion.li>
  );
}

function V3Verdict({
  state,
  verdict,
  latency,
}: {
  state: "idle" | "loading" | "done" | "err";
  verdict: "A" | "B" | null;
  latency: number | null;
}) {
  if (state === "loading" || state === "idle") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-1 px-3 py-3 text-center">
        <motion.span
          className="inline-block h-4 w-4 rounded-full border-2 border-brand-400 border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
        />
        <div className="text-[10px] font-medium uppercase tracking-wide text-ink-400">
          v3 thinking
        </div>
      </div>
    );
  }
  if (state === "err") {
    return (
      <div
        className="flex flex-1 flex-col items-center justify-center gap-1 px-3 py-3 text-center"
        title="The v3 judge call did not complete in time for this claim. The rest of the run is unaffected."
      >
        <XCircleIcon className="h-5 w-5 text-ink-500" />
        <div className="text-[10px] font-medium uppercase tracking-wide text-ink-500">
          v3 timed out
        </div>
      </div>
    );
  }
  const pickedA = verdict === "A";
  const Icon = pickedA ? CheckCircleIcon : ExclamationTriangleIcon;
  const tone = pickedA ? "text-accent-green" : "text-accent-amber";
  const glow = pickedA ? "shadow-glowGreen" : "shadow-glowAmber";
  const label = pickedA ? "supports" : "prefers null";
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-1 flex-col items-center justify-center gap-1 px-3 py-3 text-center"
      title={`v3 picked ${verdict} in ${latency?.toFixed(2)}s`}
    >
      <div className="flex items-center gap-1">
        <CpuChipIcon className="h-3.5 w-3.5 text-ink-400" />
        <span className="text-[10px] font-semibold uppercase tracking-wide text-ink-400">v3</span>
      </div>
      <div className={`relative rounded-full p-1 ${glow}`}>
        <Icon className={`h-6 w-6 ${tone}`} />
      </div>
      <div className={`text-[11px] font-semibold ${tone}`}>{label}</div>
      {latency !== null && (
        <div className="font-mono text-[10px] text-ink-500">{latency.toFixed(2)}s</div>
      )}
    </motion.div>
  );
}

function EpistemicChip({ status }: { status: EpistemicStatus }) {
  const palette: Record<EpistemicStatus, string> = {
    high_confidence:     "bg-accent-green/15 text-accent-green ring-accent-green/30",
    moderate_confidence: "bg-brand-500/15 text-brand-300 ring-brand-400/30",
    low_confidence:      "bg-accent-amber/15 text-accent-amber ring-accent-amber/30",
    contested:           "bg-accent-amber/15 text-accent-amber ring-accent-amber/30",
    speculative:         "bg-white/[0.04] text-ink-300 ring-white/10",
    unknown:             "bg-white/[0.04] text-ink-400 ring-white/10",
  };
  const labels: Record<EpistemicStatus, string> = {
    high_confidence: "high confidence",
    moderate_confidence: "moderate confidence",
    low_confidence: "low confidence",
    contested: "contested",
    speculative: "speculative",
    unknown: "unknown",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${palette[status]}`}>
      {labels[status]}
    </span>
  );
}

function SectionHeader({
  title,
  caption,
  right,
}: {
  title: string;
  caption?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-2 text-brand-300">
          <SparklesIcon className="h-4 w-4" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-100">{title}</h2>
        </div>
        {caption && <p className="mt-1 max-w-2xl text-xs text-ink-400">{caption}</p>}
      </div>
      {right}
    </div>
  );
}

