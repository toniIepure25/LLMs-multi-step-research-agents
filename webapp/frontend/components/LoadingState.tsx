"use client";

import { motion } from "framer-motion";
import { CheckCircleIcon } from "@heroicons/react/24/solid";
import { useEffect, useState } from "react";

const STAGES = [
  "Planning the research steps…",
  "Searching the SciFact corpus…",
  "Storing evidence in working memory…",
  "Synthesizing claims with the fine-tuned model…",
  "Verifying every claim against evidence…",
  "Writing the experiment record…",
];

export function LoadingState() {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    setCurrent(0);
    const t = setInterval(() => {
      setCurrent((c) => (c < STAGES.length - 1 ? c + 1 : c));
    }, 4500);
    return () => clearInterval(t);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.4 }}
      className="surface-panel mx-auto mt-12 w-full max-w-3xl rounded-2xl px-6 py-8"
    >
      <div className="flex items-center gap-3">
        <motion.span
          className="inline-block h-5 w-5 rounded-full border-2 border-brand-400 border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 0.9, ease: "linear" }}
        />
        <span className="text-sm font-medium text-ink-100">Working on it…</span>
        <span className="ml-auto text-xs text-ink-400">first run loads the model — give it ~20s</span>
      </div>

      <ol className="mt-6 space-y-3">
        {STAGES.map((stage, idx) => {
          const isDone = idx < current;
          const isActive = idx === current;
          return (
            <li key={stage} className="flex items-start gap-3">
              <div className="mt-0.5 h-4 w-4 flex-none">
                {isDone ? (
                  <CheckCircleIcon className="h-4 w-4 text-accent-green" />
                ) : (
                  <motion.span
                    className={`inline-block h-3 w-3 rounded-full border-2 ${
                      isActive ? "border-brand-400" : "border-white/15"
                    } ${isActive ? "border-t-transparent" : ""}`}
                    animate={isActive ? { rotate: 360 } : { rotate: 0 }}
                    transition={{ repeat: isActive ? Infinity : 0, duration: 0.9, ease: "linear" }}
                  />
                )}
              </div>
              <span
                className={
                  isDone
                    ? "text-sm text-ink-500 line-through decoration-white/10"
                    : isActive
                    ? "text-sm font-medium text-ink-100"
                    : "text-sm text-ink-500"
                }
              >
                {stage}
              </span>
            </li>
          );
        })}
      </ol>
    </motion.div>
  );
}
