"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { EvidenceWorkspace } from "@/components/EvidenceWorkspace";
import { HeroIntro } from "@/components/HeroIntro";
import { HowItWorks } from "@/components/HowItWorks";
import { LivePipeline } from "@/components/LivePipeline";
import { ResearchForm } from "@/components/ResearchForm";
import { ResearchReport } from "@/components/ResearchReport";
import { ApiError, getInfo, runResearch, warmup } from "@/lib/api";
import type { InfoResponse, ResearchResponse } from "@/lib/types";

export default function HomePage() {
  const [info, setInfo] = useState<InfoResponse | null>(null);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<
    | { kind: "safety"; reason: string }
    | { kind: "generic"; message: string }
    | null
  >(null);
  const [isLoading, setIsLoading] = useState(false);

  // Cumulative count of v3 verdicts; bubbled up from the ClaimsList.
  const [v3Agreement, setV3Agreement] = useState<{ supported: number; total: number }>({
    supported: 0,
    total: 0,
  });

  useEffect(() => {
    getInfo()
      .then((i) => {
        setInfo(i);
        if (!i.adapter_loaded) void warmup().catch(() => {});
      })
      .catch((e) =>
        setError({
          kind: "generic",
          message: `info: ${e instanceof Error ? e.message : String(e)}`,
        }),
      );
  }, []);

  async function submit(goal: string) {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setV3Agreement({ supported: 0, total: 0 });
    try {
      const res = await runResearch(goal, info?.safety_enabled ?? true);
      setResult(res);
    } catch (e) {
      if (e instanceof ApiError && e.kind === "safety") {
        setError({ kind: "safety", reason: e.reason ?? "unsafe_goal" });
      } else {
        setError({
          kind: "generic",
          message: e instanceof Error ? e.message : String(e),
        });
      }
    } finally {
      setIsLoading(false);
    }
  }

  const safetyClean = result ? !(result.safety.blocked_pre || result.safety.blocked_post) : true;
  const showHeroFull = !isLoading && !result && !error;
  const hasResultOrLoading = isLoading || !!result;

  return (
    <main className="relative min-h-screen pb-24">
      <HeroIntro info={info} compact={!showHeroFull} />

      <ResearchForm onSubmit={submit} isLoading={isLoading} compact={hasResultOrLoading} />

      <AnimatePresence>
        {error && (
          <ErrorBanner
            key={error.kind === "safety" ? `safety-${error.reason}` : "generic"}
            kind={error.kind}
            message={error.kind === "safety" ? error.reason : error.message}
            onDismiss={() => setError(null)}
          />
        )}
      </AnimatePresence>

      {/* Onboarding explainer — only visible before the first run. */}
      <AnimatePresence>
        {showHeroFull && <HowItWorks key="how-it-works" />}
      </AnimatePresence>

      {/* Loading state: live pipeline takes center stage, narrower column. */}
      <AnimatePresence mode="wait">
        {isLoading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="mx-auto mt-5 w-full max-w-4xl px-6"
          >
            <LivePipeline />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result state: wider column hosts the integrated report + workspace. */}
      <AnimatePresence mode="wait">
        {!isLoading && result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: "easeOut" }}
            className="mx-auto mt-5 w-full max-w-5xl space-y-5 px-6 md:mt-6 md:space-y-6"
          >
            <ResearchReport
              result={result}
              v3Supported={v3Agreement.supported}
              v3Total={v3Agreement.total}
              safetyClean={safetyClean}
            />

            <EvidenceWorkspace
              result={result}
              safetyClean={safetyClean}
              onAgreementUpdate={(supported, total) =>
                setV3Agreement({ supported, total })
              }
            />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

