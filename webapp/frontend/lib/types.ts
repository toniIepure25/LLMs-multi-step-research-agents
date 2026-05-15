// Mirror of the JSON shapes returned by the FastAPI backend.

export type EpistemicStatus =
  | "high_confidence"
  | "moderate_confidence"
  | "low_confidence"
  | "contested"
  | "speculative"
  | "unknown";

export interface PlanStep {
  step_id: string;
  description: string;
  expected_output: string;
  success_criteria: string;
  dependency_type: "sequential" | "parallel" | "conditional";
  depends_on: string[];
  tool_hint?: string | null;
  priority: number;
}

export interface ResearchPlan {
  plan_id: string;
  goal: string;
  steps: PlanStep[];
  constraints?: string | null;
  revision: number;
  parent_plan_id?: string | null;
}

export interface EvidenceItem {
  evidence_id: string;
  task_id: string;
  content: string;
  source: {
    source_type: string;
    url?: string | null;
    title?: string | null;
    author?: string | null;
    publication_date?: string | null;
    raw_snippet?: string | null;
    additional?: Record<string, unknown>;
  };
  confidence: number;
  relevance: number;
  tags: string[];
}

export interface Claim {
  claim_id: string;
  text: string;
  /** Original full text, present only when the backend has shortened `text`. */
  text_full?: string;
  epistemic_status: EpistemicStatus;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  reasoning_trace?: string | null;
}

export interface DecisionPacket {
  decision_id: string;
  plan_id: string;
  claims: Claim[];
  conflicts: unknown[];
  synthesis?: string | null;
  information_gaps: string[];
}

export interface ClaimVerification {
  claim_id: string;
  is_grounded: boolean;
  is_consistent: boolean;
  is_within_scope: boolean;
  notes?: string | null;
}

export interface VerificationResult {
  verification_id: string;
  decision_id: string;
  claim_verifications: ClaimVerification[];
  any_failures: boolean;
  summary?: string | null;
}

export interface ExperimentRecord {
  experiment_id: string;
  config?: Record<string, unknown>;
  artifacts: string[];
  metrics?: Record<string, unknown>;
}

export interface ResearchOutput {
  goal: string;
  plan: ResearchPlan;
  evidence: EvidenceItem[];
  decision?: DecisionPacket | null;
  verification?: VerificationResult | null;
  experiment?: ExperimentRecord | null;
}

export interface ResearchSafetyReport {
  blocked_pre: boolean;
  blocked_post: boolean;
  blocked_reason: string | null;
  max_toxicity_pre: number;
  max_injection_pre: number;
  max_toxicity_post: number;
  max_injection_post: number;
}

export interface GroundedAnswer {
  text: string;
  cited_indices: number[];
  cited_evidence_ids: string[];
  elapsed_seconds: number;
  generated: boolean;
  note?: string | null;
}

export interface ResearchResponse {
  goal: string;
  elapsed_seconds: number;
  adapter_metadata: Record<string, unknown>;
  output: ResearchOutput;
  safety: ResearchSafetyReport;
  answer?: GroundedAnswer | null;
}

export interface InfoResponse {
  base_model: string;
  adapter_path: string | null;
  adapter_metadata: Record<string, unknown> | null;
  search_provider: string | null;
  safety_enabled: boolean;
  adapter_loaded: boolean;
}

export interface RerankResponse {
  preferred: "A" | "B" | string;
  raw: string;
  elapsed_seconds: number;
}

export interface WarmupResponse {
  adapter_loaded: boolean;
  elapsed_seconds: number;
  sample: string | null;
}
