"use client";

import { motion } from "framer-motion";
import { BeakerIcon, CpuChipIcon, ShieldCheckIcon } from "@heroicons/react/24/outline";
import type { InfoResponse } from "@/lib/types";

interface HeaderProps {
  info: InfoResponse | null;
}

export function Header({ info }: HeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6"
    >
      <div className="flex items-center gap-3">
        <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 via-brand-600 to-accent-violet text-white shadow-glow ring-1 ring-white/10">
          <BeakerIcon className="h-5 w-5" />
          <span className="pointer-events-none absolute inset-0 rounded-xl bg-white/0 ring-1 ring-inset ring-white/5" />
        </div>
        <div className="leading-tight">
          <div className="text-base font-semibold tracking-tight text-ink-50">ASAR</div>
          <div className="text-xs text-ink-400">Agentic Structured Autonomous Researcher</div>
        </div>
      </div>

      <div className="hidden items-center gap-2 md:flex">
        {info && (
          <>
            <Pill icon={<CpuChipIcon className="h-3.5 w-3.5" />}>
              <span className="text-ink-400">model</span>
              <span className="ml-1 font-medium text-ink-100">{shortModel(info.base_model)}</span>
            </Pill>
            {info.adapter_path && (
              <Pill icon={<BeakerIcon className="h-3.5 w-3.5" />}>
                <span className="text-ink-400">adapter</span>
                <span className="ml-1 font-medium text-ink-100">{shortAdapter(info.adapter_path)}</span>
              </Pill>
            )}
            <Pill icon={<ShieldCheckIcon className="h-3.5 w-3.5" />}>
              <span className={info.safety_enabled ? "text-accent-green" : "text-ink-400"}>
                {info.safety_enabled ? "safety on" : "safety off"}
              </span>
            </Pill>
          </>
        )}
      </div>
    </motion.header>
  );
}

function Pill({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-ink-200 backdrop-blur transition hover:border-white/20 hover:bg-white/[0.06]">
      {icon}
      {children}
    </span>
  );
}

function shortModel(name: string): string {
  if (!name) return "—";
  const slash = name.lastIndexOf("/");
  return slash >= 0 ? name.slice(slash + 1) : name;
}

function shortAdapter(path: string): string {
  if (!path) return "—";
  const parts = path.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? path;
}
