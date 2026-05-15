"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDownIcon, ListBulletIcon } from "@heroicons/react/24/outline";
import { useState } from "react";

import type { ResearchPlan } from "@/lib/types";

interface PlanDetailsProps {
  plan: ResearchPlan;
  /** Render the panel collapsed by default. */
  defaultCollapsed?: boolean;
}

export function PlanDetails({ plan, defaultCollapsed = true }: PlanDetailsProps) {
  const [open, setOpen] = useState(!defaultCollapsed);

  return (
    <section className="surface-panel overflow-hidden rounded-2xl">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition hover:bg-white/[0.03]"
      >
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-brand-300">
            <ListBulletIcon className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-100">
              Research plan
            </h2>
            <p className="mt-1 text-xs text-ink-400">
              The planner decomposed the question into {plan.steps.length} steps for the executor.
            </p>
          </div>
        </div>
        <ChevronDownIcon
          className={`h-4 w-4 flex-none text-ink-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <ol className="space-y-2 px-6 pb-6">
              {plan.steps.map((step, idx) => (
                <li
                  key={step.step_id}
                  className="flex gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-3 transition hover:border-white/10"
                >
                  <div className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-brand-500/15 text-xs font-semibold text-brand-300 ring-1 ring-brand-400/30">
                    {idx + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-ink-100">{step.description}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-ink-400">
                      <span><b className="font-mono text-ink-500">expects</b> {step.expected_output}</span>
                      {step.tool_hint && (
                        <span className="rounded bg-white/[0.04] px-1.5 py-0.5 font-mono text-ink-300">
                          {step.tool_hint}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
