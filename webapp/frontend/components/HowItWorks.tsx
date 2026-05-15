"use client";

import { motion } from "framer-motion";
import {
  BoltIcon,
  CpuChipIcon,
  DocumentMagnifyingGlassIcon,
  RectangleStackIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

/**
 * Four-card "How this demo works" flow shown above the form before the first run.
 *   01  Plan       — decompose the question
 *   02  Retrieve   — pull passages from the local corpus
 *   03  Synthesize — local LLM writes a grounded answer
 *   04  Verify     — fine-tuned LoRA judges every claim
 */
export function HowItWorks() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.45, delay: 0.05 }}
      className="relative z-10 mx-auto mt-14 w-full max-w-5xl px-6"
    >
      <div className="mb-5 flex items-center justify-center gap-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-brand-300">
        <span className="h-px w-10 bg-brand-400/40" />
        How this demo works
        <span className="h-px w-10 bg-brand-400/40" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Step
          n={1}
          Icon={RectangleStackIcon}
          title="Plan the research"
          body="The agent decomposes your question into focused search steps before any retrieval happens."
        />
        <Step
          n={2}
          Icon={DocumentMagnifyingGlassIcon}
          title="Retrieve from corpus"
          body={
            <>
              Relevant passages are pulled from the local{" "}
              <Term hint="A curated dataset of ~5K scientific abstracts used for fact-checking research.">
                SciFact
              </Term>{" "}
              /{" "}
              <Term hint="Vector database storing the corpus as embeddings, queried by semantic similarity.">
                Qdrant
              </Term>{" "}
              index.
            </>
          }
        />
        <Step
          n={3}
          Icon={BoltIcon}
          title="Synthesize grounded answer"
          body={
            <>
              The local{" "}
              <Term hint="Small 0.5B-parameter model that runs comfortably on a laptop GPU.">
                Qwen-0.5B
              </Term>{" "}
              writes an answer using retrieved evidence, citing passages by{" "}
              <code className="rounded bg-white/[0.06] px-1 font-mono text-[11px] text-ink-200">
                [n]
              </code>
              .
            </>
          }
        />
        <Step
          n={4}
          Icon={CpuChipIcon}
          title="Verify claims"
          body={
            <>
              A fine-tuned{" "}
              <Term hint="Low-Rank Adaptation: a small set of weights trained with DPO to prefer the more-evidence-supported claim.">
                LoRA judge
              </Term>{" "}
              checks whether each claim is actually supported by the corpus.
            </>
          }
        />
      </div>

      {/* Footer privacy note */}
      <div className="mt-6 flex items-center justify-center gap-2 text-[12px] text-ink-400">
        <ShieldCheckIcon className="h-4 w-4 text-accent-green" />
        <span>Runs locally. No external API calls during a research run.</span>
      </div>
    </motion.section>
  );
}

function Step({
  n,
  Icon,
  title,
  body,
}: {
  n: number;
  Icon: typeof BoltIcon;
  title: string;
  body: React.ReactNode;
}) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 220, damping: 18 }}
      className="surface-panel group relative overflow-hidden rounded-2xl p-5"
    >
      {/* subtle gradient sheen */}
      <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-brand-500/10 blur-3xl transition group-hover:bg-brand-500/20" />
      <div className="pointer-events-none absolute -bottom-10 -left-10 h-28 w-28 rounded-full bg-accent-violet/10 blur-3xl transition group-hover:bg-accent-violet/20" />
      {/* hover ring */}
      <div className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-inset ring-white/0 transition group-hover:ring-white/10" />

      <div className="relative flex items-start gap-3">
        <div className="flex h-10 w-10 flex-none items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/30 via-accent-violet/20 to-accent-cyan/20 text-brand-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] ring-1 ring-brand-400/30">
          <Icon className="h-[18px] w-[18px]" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] tracking-wider text-ink-500">
              {String(n).padStart(2, "0")}
            </span>
            <SparklesIcon className="h-3 w-3 text-brand-400/70" />
          </div>
          <h3 className="mt-0.5 text-[15px] font-semibold text-ink-50">{title}</h3>
          <p className="mt-1.5 text-[12.5px] leading-relaxed text-ink-300">
            {body}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

/** A jargon term with a dashed underline + native hover tooltip. */
function Term({
  children,
  hint,
}: {
  children: React.ReactNode;
  hint: string;
}) {
  return (
    <span
      title={hint}
      className="border-b border-dashed border-brand-300/40 text-ink-100 transition hover:border-brand-200/80"
    >
      {children}
    </span>
  );
}
