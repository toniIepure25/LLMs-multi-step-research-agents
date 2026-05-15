"use client";

import { motion } from "framer-motion";
import {
  ChevronDownIcon,
  DocumentTextIcon,
  LinkIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";
import type { EvidenceItem } from "@/lib/types";

interface EvidenceListProps {
  evidence: EvidenceItem[];
}

export function EvidenceList({ evidence }: EvidenceListProps) {
  return (
    <section className="surface-panel rounded-2xl p-6">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-brand-300">
            <DocumentTextIcon className="h-4 w-4" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-ink-100">
              Retrieved evidence
            </h2>
          </div>
          <p className="mt-1 max-w-2xl text-xs text-ink-400">
            Passages pulled from the SciFact corpus by the retriever, ranked by query relevance.
            Each claim above links back to one of these IDs.
          </p>
        </div>
        <div className="flex flex-none flex-col items-end gap-1 text-xs text-ink-400">
          <span>{evidence.length} item{evidence.length === 1 ? "" : "s"}</span>
          <span className="rounded bg-white/[0.04] px-1.5 py-0.5 font-mono text-[10px] text-ink-400">
            corpus · web_search
          </span>
        </div>
      </div>

      <ul className="divide-y divide-white/5 overflow-hidden rounded-xl border border-white/5 bg-white/[0.02]">
        {evidence.map((ev, idx) => (
          <EvidenceRow key={ev.evidence_id} evidence={ev} index={idx} />
        ))}
      </ul>
    </section>
  );
}

function buildPaperUrl(ev: EvidenceItem): string {
  const title = ev.source.title;
  // Title search on Semantic Scholar is the most reliable resolver — it
  // doesn't aggressively block automated traffic the way Google Scholar
  // does and works for both numeric doc_ids and corpus_id strings.
  if (title) {
    return `https://www.semanticscholar.org/search?q=${encodeURIComponent(title)}`;
  }
  const additional = ev.source.additional as Record<string, unknown> | undefined;
  const docIdRaw = additional?.["doc_id"];
  const docId =
    typeof docIdRaw === "string" || typeof docIdRaw === "number"
      ? String(docIdRaw)
      : null;
  if (docId && /^\d+$/.test(docId)) {
    // SciFact corpus IDs map to Semantic Scholar CorpusIDs.  The /CorpusID:
    // form is an API endpoint that returns JSON in a browser, but it's
    // strictly better than sending the user to a 404.
    return `https://api.semanticscholar.org/graph/v1/paper/CorpusID:${docId}`;
  }
  return ev.source.url ?? "#";
}

function EvidenceRow({ evidence, index }: { evidence: EvidenceItem; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const additional = evidence.source.additional as Record<string, unknown> | undefined;
  const docIdRaw = additional?.["doc_id"];
  const docId =
    typeof docIdRaw === "string" || typeof docIdRaw === "number"
      ? String(docIdRaw)
      : null;
  const relevancePct = Math.round(evidence.relevance * 100);
  const tone =
    relevancePct >= 70 ? "from-accent-green to-emerald-400 shadow-glowGreen"
    : relevancePct >= 50 ? "from-brand-500 to-accent-cyan shadow-glowSoft"
    : "from-ink-600 to-ink-500";

  const paperUrl = buildPaperUrl(evidence);
  const isLong = evidence.content.length > 320;

  return (
    <motion.li
      id={`evidence-${index + 1}`}
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.05 * index, duration: 0.25 }}
      className="group scroll-mt-24 p-4 transition target:bg-brand-500/10 hover:bg-white/[0.03]"
    >
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-ink-500">
              #{(index + 1).toString().padStart(2, "0")}
            </span>
            <h3 className="truncate text-sm font-semibold text-ink-50">
              {evidence.source.title ?? "Untitled source"}
            </h3>
          </div>
          {docId && (
            <div className="mt-1 text-[10px] font-mono text-ink-500">
              S2 CorpusID: {docId}
            </div>
          )}
        </div>

        <div className="flex flex-none flex-col items-end gap-1">
          <span className="rounded-full bg-white/[0.04] px-2 py-0.5 text-[11px] font-semibold text-ink-200">
            {relevancePct}% relevance
          </span>
          <div className="h-1 w-20 overflow-hidden rounded-full bg-white/5">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${tone}`}
              style={{ width: `${relevancePct}%` }}
            />
          </div>
        </div>
      </header>

      <p
        className={`mt-2 text-xs leading-relaxed text-ink-300 ${
          expanded ? "" : "line-clamp-3"
        }`}
      >
        {evidence.content}
      </p>

      <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px]">
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="inline-flex items-center gap-1 font-medium text-ink-300 transition hover:text-ink-100"
          >
            <ChevronDownIcon
              className={`h-3 w-3 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
            {expanded ? "collapse" : "show full passage"}
          </button>
        )}
        <a
          href={paperUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-medium text-brand-300 transition hover:text-brand-200"
        >
          <LinkIcon className="h-3 w-3" />
          view paper
        </a>
      </div>
    </motion.li>
  );
}

