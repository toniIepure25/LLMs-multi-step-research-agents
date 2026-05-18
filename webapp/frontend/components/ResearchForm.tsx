"use client";

import { AnimatePresence, motion } from "framer-motion";
import { PaperAirplaneIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { useEffect, useState } from "react";

interface ResearchFormProps {
  onSubmit: (goal: string) => void;
  isLoading: boolean;
  /**
   * Compact, command-bar look used once a result is on screen.  Smaller
   * vertical footprint, single-row textarea, "Try asking" chips hidden.
   */
  compact?: boolean;
}

// Suggestion chips. These are tuned to the SciFact corpus that ships with
// the demo — each one maps to claims/abstracts with strong coverage so
// retrieval returns on-topic passages instead of nearest-neighbour drift.
const EXAMPLES = [
  "Does tamoxifen metabolism affect breast cancer treatment outcomes?",
  "How does folate deficiency affect homocysteine levels?",
  "What role does PD-1 blockade play in melanoma treatment?",
  "Does 4-PBA treatment reduce endoplasmic reticulum stress?",
];

export function ResearchForm({ onSubmit, isLoading, compact = false }: ResearchFormProps) {
  const [goal, setGoal] = useState("");

  useEffect(() => {
    if (!goal && !isLoading) setGoal("");
  }, [isLoading, goal]);

  function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = goal.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
  }

  // Layout constants per mode — keeps everything else identical.
  const rowPad      = compact ? "px-4 py-2 md:px-5" : "px-5 py-4 md:px-6";
  const textareaPad = compact ? "py-1" : "py-1";
  const textareaTxt = compact ? "text-sm leading-snug" : "text-base leading-relaxed";
  const textRows    = compact ? 1 : 2;
  const btnHeight   = compact ? "h-9" : "h-9";
  const formMargin  = compact ? "mt-4" : "mt-8";

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="relative z-10 mx-auto w-full max-w-3xl px-6"
    >
      <motion.form
        onSubmit={submit}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className={formMargin}
      >
        <div className="surface-panel group relative rounded-3xl transition focus-within:border-brand-400/40">
          {/* soft teal/violet focus ring — aurora glow */}
          <div className="pointer-events-none absolute -inset-px rounded-3xl bg-gradient-to-r from-brand-500/15 via-accent-violet/12 to-accent-cyan/15 opacity-0 blur-md transition group-focus-within:opacity-100" />
          <div className={`relative flex items-center gap-3 ${rowPad}`}>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
              }}
              disabled={isLoading}
              rows={textRows}
              placeholder="Ask a research question…"
              className={`min-w-0 flex-1 resize-none bg-transparent ${textareaPad} ${textareaTxt} text-ink-50 placeholder:text-ink-500 focus:outline-none disabled:opacity-60`}
            />
            <button
              type="submit"
              disabled={!goal.trim() || isLoading}
              className={`inline-flex ${btnHeight} min-w-[148px] flex-none items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 via-brand-400 to-accent-cyan px-4 text-sm font-semibold text-white shadow-glow ring-1 ring-white/15 transition hover:from-brand-400 hover:to-accent-cyan hover:shadow-[0_0_36px_-8px_rgba(94,234,212,0.7)] disabled:cursor-not-allowed disabled:bg-none disabled:bg-white/[0.04] disabled:text-ink-500 disabled:shadow-none disabled:ring-white/10`}
            >
              {isLoading ? (
                <>
                  <motion.span
                    className="inline-block h-3.5 w-3.5 rounded-full border-2 border-white/70 border-t-transparent"
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
                  />
                  <span>Running</span>
                </>
              ) : (
                <>
                  <PaperAirplaneIcon className="h-4 w-4" />
                  <span>Run research</span>
                </>
              )}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {!isLoading && !compact && (
            <motion.div
              key="examples"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={{ duration: 0.3 }}
              className="mx-auto mt-6 w-full max-w-2xl"
            >
              <div className="mb-3 flex items-center justify-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.18em] text-ink-400">
                <span className="h-px w-8 bg-white/10" />
                <SparklesIcon className="h-3 w-3 text-brand-300" />
                Try asking
                <span className="h-px w-8 bg-white/10" />
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => setGoal(ex)}
                    className="w-full truncate rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-center text-xs text-ink-300 backdrop-blur transition hover:-translate-y-px hover:border-brand-400/50 hover:bg-white/[0.07] hover:text-ink-50 hover:shadow-glowSoft"
                    title={ex}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.form>
    </motion.section>
  );
}
