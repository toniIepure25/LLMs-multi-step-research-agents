import type { InfoResponse, RerankResponse, ResearchResponse, WarmupResponse } from "./types";

/**
 * Categorical kinds the UI can branch on.  Anything other than these
 * is treated as a generic error and shown verbatim.
 */
export type ApiErrorKind = "safety" | "http" | "network";

/** Reasons emitted by the safety pipeline; mirrored from `asar.safety`. */
export type SafetyBlockedReason =
  | "unsafe_goal"
  | "goal_failed_safety_check"
  | "injection"
  | "toxicity"
  | "harm_intent"
  | "blocked_by_safety"
  | string;

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number;
  readonly reason?: SafetyBlockedReason;
  readonly detail?: unknown;

  constructor(args: {
    kind: ApiErrorKind;
    status: number;
    message: string;
    reason?: SafetyBlockedReason;
    detail?: unknown;
  }) {
    super(args.message);
    this.name = "ApiError";
    this.kind = args.kind;
    this.status = args.status;
    this.reason = args.reason;
    this.detail = args.detail;
  }
}

export async function getInfo(): Promise<InfoResponse> {
  const res = await fetch("/api/info", { cache: "no-store" });
  if (!res.ok) throw new Error(`info ${res.status}`);
  return res.json();
}

export async function warmup(): Promise<WarmupResponse> {
  const res = await fetch("/api/warmup", { method: "POST" });
  if (!res.ok) throw new Error(`warmup ${res.status}`);
  return res.json();
}

export async function rerank(args: {
  goal: string;
  claimA: string;
  claimB: string;
}): Promise<RerankResponse> {
  const res = await fetch("/api/rerank", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal: args.goal, claim_a: args.claimA, claim_b: args.claimB }),
  });
  if (!res.ok) throw new Error(`rerank ${res.status}`);
  return res.json();
}

export async function runResearch(goal: string, safetyEnabled = true): Promise<ResearchResponse> {
  const res = await fetch("/api/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, safety_enabled: safetyEnabled }),
  });
  if (res.ok) {
    return res.json();
  }

  // ----- Error path: try to parse FastAPI's structured detail. -----
  let body: unknown = undefined;
  try {
    body = await res.json();
  } catch {
    /* non-JSON error body */
  }

  // FastAPI returns `{ detail: ... }` for HTTPException.
  const detail =
    body && typeof body === "object" && "detail" in (body as Record<string, unknown>)
      ? (body as { detail: unknown }).detail
      : body;

  // Safety pipeline returns `{ "error": "blocked_by_safety", "reason": "..." }`.
  if (
    detail &&
    typeof detail === "object" &&
    (detail as Record<string, unknown>).error === "blocked_by_safety"
  ) {
    const reason = String((detail as Record<string, unknown>).reason ?? "unsafe_goal");
    throw new ApiError({
      kind: "safety",
      status: res.status,
      reason,
      detail,
      message: reason,
    });
  }

  // Generic HTTP error — produce a single-line message.
  const message =
    typeof detail === "string"
      ? detail
      : detail && typeof detail === "object"
      ? ((detail as Record<string, unknown>).error as string | undefined) ??
        JSON.stringify(detail)
      : `HTTP ${res.status}`;
  throw new ApiError({ kind: "http", status: res.status, message, detail });
}

