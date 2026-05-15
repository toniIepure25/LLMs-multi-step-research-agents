"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  BoltIcon,
  CodeBracketSquareIcon,
  DocumentMagnifyingGlassIcon,
  ListBulletIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";

import { ClaimsList } from "@/components/ClaimsList";
import { EvidenceList } from "@/components/EvidenceList";
import { PipelineTimeline } from "@/components/PipelineTimeline";
import { PlanDetails } from "@/components/PlanDetails";
import type { ResearchResponse } from "@/lib/types";

type TabId = "claims" | "evidence" | "pipeline" | "plan" | "raw";

interface EvidenceWorkspaceProps {
  result: ResearchResponse;
  safetyClean: boolean;
  onAgreementUpdate: (supported: number, total: number) => void;
}

interface TabSpec {
  id: TabId;
  label: string;
  count?: number;
  Icon: typeof SparklesIcon;
}

/**
 * Grouped, tabbed workspace that absorbs Pipeline / Claims / Evidence /
 * Plan / Raw JSON into a single card so the result page reads like one
 * report instead of a stack of unrelated panels.
 *
 * All underlying components are reused unchanged so behavior (rerank,
 * citations, paper links, plan expansion, raw JSON dump) is identical.
 */
export function EvidenceWorkspace({
  result,
  safetyClean,
  onAgreementUpdate,
}: EvidenceWorkspaceProps) {
  const decision = result.output.decision;
  const claimCount = decision?.claims.length ?? 0;
  const evidenceCount = result.output.evidence.length;
  const planCount = result.output.plan.steps.length;

  const tabs: TabSpec[] = [
    { id: "claims",   label: "Claims",   count: claimCount,    Icon: SparklesIcon },
    { id: "evidence", label: "Evidence", count: evidenceCount, Icon: DocumentMagnifyingGlassIcon },
    { id: "pipeline", label: "Pipeline", Icon: BoltIcon },
    { id: "plan",     label: "Plan",     count: planCount,     Icon: ListBulletIcon },
    { id: "raw",      label: "Raw JSON", Icon: CodeBracketSquareIcon },
  ];

  // Default tab: claims (the core verification view).  Fall back to evidence
  // if the decision packet didn't materialize (no claims to show).
  const [active, setActive] = useState<TabId>(claimCount > 0 ? "claims" : "evidence");

  return (
    <section className="relative">
      {/* Tab bar — sits on its own glass strip so the active tab feels anchored
          without doubling up the surface-panel glass on the inner components. */}
      <div className="surface-panel relative overflow-hidden rounded-2xl px-3 pt-3 md:px-4">
        <div
          role="tablist"
          aria-label="Evidence workspace"
          className="flex flex-nowrap items-center gap-1 overflow-x-auto pb-2"
        >
          {tabs.map((tab) => (
            <TabButton
              key={tab.id}
              tab={tab}
              isActive={active === tab.id}
              onClick={() => setActive(tab.id)}
            />
          ))}
        </div>
      </div>

      {/* Tab panel — the inner component supplies its own surface-panel. */}
      <div className="relative mt-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -2 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            role="tabpanel"
            id={`workspace-panel-${active}`}
            aria-labelledby={`workspace-tab-${active}`}
          >
            {active === "claims" && decision && (
              <ClaimsList
                decision={decision}
                goal={result.goal}
                rerankEnabled
                onAgreementUpdate={onAgreementUpdate}
              />
            )}
            {active === "claims" && !decision && (
              <EmptyState text="No claims were produced — the run may have been blocked or returned empty." />
            )}

            {active === "evidence" && (
              <EvidenceList evidence={result.output.evidence} />
            )}

            {active === "pipeline" && (
              <PipelineTimeline
                elapsedSeconds={result.elapsed_seconds}
                evidenceCount={evidenceCount}
                claimCount={claimCount}
                safetyClean={safetyClean}
              />
            )}

            {active === "plan" && (
              <PlanDetails plan={result.output.plan} defaultCollapsed={false} />
            )}

            {active === "raw" && (
              <details
                className="surface-panel group rounded-2xl p-4 text-xs"
                open
              >
                <summary className="cursor-pointer select-none font-mono text-ink-400 transition hover:text-ink-100">
                  raw research response · {((JSON.stringify(result).length) / 1024).toFixed(1)} KB
                </summary>
                <pre className="mt-3 max-h-[28rem] overflow-auto rounded-lg border border-white/5 bg-black/40 p-4 font-mono text-[11px] leading-relaxed text-ink-200">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}

function TabButton({
  tab,
  isActive,
  onClick,
}: {
  tab: TabSpec;
  isActive: boolean;
  onClick: () => void;
}) {
  const { Icon } = tab;
  return (
    <button
      role="tab"
      id={`workspace-tab-${tab.id}`}
      aria-selected={isActive}
      aria-controls={`workspace-panel-${tab.id}`}
      onClick={onClick}
      className={`relative inline-flex flex-none items-center gap-1.5 rounded-xl px-3 py-2 text-[12px] font-semibold transition ${
        isActive
          ? "bg-white/[0.06] text-ink-50 ring-1 ring-brand-400/30"
          : "text-ink-400 hover:bg-white/[0.03] hover:text-ink-100"
      }`}
    >
      <Icon className={`h-3.5 w-3.5 ${isActive ? "text-brand-300" : "text-ink-500"}`} />
      <span className="uppercase tracking-[0.14em]">{tab.label}</span>
      {typeof tab.count === "number" && (
        <span
          className={`rounded-full px-1.5 py-0.5 font-mono text-[10px] ${
            isActive
              ? "bg-brand-500/15 text-brand-200 ring-1 ring-brand-400/30"
              : "bg-white/[0.04] text-ink-400"
          }`}
        >
          {tab.count}
        </span>
      )}
      {isActive && (
        <motion.span
          layoutId="workspace-tab-underline"
          className="absolute inset-x-2 -bottom-1 h-px rounded-full bg-gradient-to-r from-brand-400 via-accent-cyan to-accent-violet"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
        />
      )}
    </button>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 text-center text-sm text-ink-400">
      {text}
    </div>
  );
}
