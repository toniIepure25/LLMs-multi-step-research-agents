"use client";

import { motion } from "framer-motion";
import {
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

/**
 * Two visual modes:
 *  - `safety`   → friendly explanation that the question tripped the safety filter
 *  - `generic`  → fallback for any other backend error (HTTP, network, etc.)
 *
 * The page wires this up based on `ApiError.kind`.
 */
export type ErrorBannerKind = "safety" | "generic";

interface ErrorBannerProps {
  kind?: ErrorBannerKind;
  /** Human-readable headline for `generic`; safety reason code for `safety`. */
  message: string;
  onDismiss: () => void;
}

const SAFETY_REASON_COPY: Record<string, { title: string; body: string }> = {
  injection: {
    title: "Your prompt looked like an instruction-override attempt.",
    body:
      "The safety filter matched a prompt-injection pattern (e.g. “ignore previous instructions”). Rephrase your research question without trying to override the agent's behavior and run it again.",
  },
  toxicity: {
    title: "Your prompt contained content the safety filter flagged as toxic.",
    body:
      "Reword the question to focus on the research topic without abusive or hateful language.",
  },
  harm_intent: {
    title: "Your prompt was flagged as describing harmful intent.",
    body:
      "Rephrase the question as a research query and avoid wording that asks for instructions to cause harm.",
  },
  goal_failed_safety_check: {
    title: "Your prompt failed the safety check.",
    body:
      "The pre-flight safety filter classified the question as unsafe. Edit the wording and try again.",
  },
  unsafe_goal: {
    title: "Your prompt was blocked by the safety filter.",
    body:
      "Reword the question as a neutral research query and run it again.",
  },
};

function safetyCopy(reason: string): { title: string; body: string } {
  return (
    SAFETY_REASON_COPY[reason] ?? {
      title: "Your prompt was blocked by the safety filter.",
      body:
        "Reword the question and run it again. The agent is unaffected; only this request was filtered.",
    }
  );
}

export function ErrorBanner({ kind = "generic", message, onDismiss }: ErrorBannerProps) {
  if (kind === "safety") {
    const { title, body } = safetyCopy(message);
    return (
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.3 }}
        role="status"
        aria-live="polite"
        className="surface-panel relative mx-auto mt-6 w-full max-w-3xl overflow-hidden rounded-2xl border-accent-amber/25"
      >
        {/* soft amber wash */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-accent-amber/[0.06] via-transparent to-transparent" />
        <div className="pointer-events-none absolute -top-12 left-1/2 h-24 w-[28rem] -translate-x-1/2 rounded-full bg-accent-amber/[0.10] blur-3xl" />

        <div className="relative flex items-start gap-4 px-5 py-4">
          <div className="mt-0.5 flex h-9 w-9 flex-none items-center justify-center rounded-xl border border-accent-amber/30 bg-accent-amber/10 text-accent-amber">
            <ShieldExclamationIcon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent-amber">
                Safety filter
              </span>
              <span className="rounded-full border border-accent-amber/25 bg-accent-amber/10 px-1.5 py-0.5 font-mono text-[10px] text-accent-amber">
                {message}
              </span>
            </div>
            <p className="mt-1 text-sm font-semibold leading-snug text-ink-50">{title}</p>
            <p className="mt-1 text-[12.5px] leading-relaxed text-ink-300">{body}</p>
            <p className="mt-2 text-[11px] text-ink-500">
              Tip: this only blocks the offending request — your next question runs normally.
            </p>
          </div>
          <button
            onClick={onDismiss}
            aria-label="Dismiss"
            className="flex h-7 w-7 flex-none items-center justify-center rounded-full text-ink-400 transition hover:bg-white/[0.06] hover:text-ink-100"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      </motion.div>
    );
  }

  // Generic fallback.
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.3 }}
      role="alert"
      className="mx-auto mt-6 flex w-full max-w-3xl items-start gap-3 rounded-xl border border-accent-red/30 bg-accent-red/10 px-4 py-3 text-sm text-red-200 shadow-[0_0_30px_-12px_rgba(239,68,68,0.5)] backdrop-blur"
    >
      <ExclamationTriangleIcon className="mt-0.5 h-4 w-4 flex-none text-accent-red" />
      <div className="flex-1 break-words font-mono text-xs leading-relaxed">{message}</div>
      <button
        onClick={onDismiss}
        className="text-xs font-medium text-red-200 underline-offset-2 hover:underline"
      >
        dismiss
      </button>
    </motion.div>
  );
}

