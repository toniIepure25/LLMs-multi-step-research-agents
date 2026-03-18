"""
Layer protocols — the contracts each architectural layer must satisfy.

These are Python Protocols (structural subtyping). Any class that implements
the required methods satisfies the protocol without explicit inheritance.

Canonical layer names: planning, execution, memory, grounding,
deliberation, verification, evaluation, orchestration.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from schemas.research_plan import ResearchPlan
from schemas.task_packet import TaskPacket
from schemas.evidence_item import EvidenceItem
from schemas.citation_record import CitationRecord
from schemas.decision_packet import DecisionPacket
from schemas.verification_result import VerificationResult
from schemas.experiment_record import ExperimentRecord


@runtime_checkable
class PlannerProtocol(Protocol):
    """
    planning layer interface.

    Turns a research goal into a structured ResearchPlan.
    May be called multiple times for re-planning.
    """

    async def plan(self, goal: str, constraints: dict | None = None) -> ResearchPlan:
        """Generate a ResearchPlan from a research goal."""
        ...

    async def replan(self, plan_id: str, feedback: str) -> ResearchPlan:
        """Revise an existing plan based on feedback."""
        ...


@runtime_checkable
class ExecutorProtocol(Protocol):
    """
    execution layer interface.

    Executes a single TaskPacket and returns evidence.
    Executors are stateless — all context is in the TaskPacket.
    """

    async def execute(self, task: TaskPacket) -> list[EvidenceItem]:
        """Execute a TaskPacket and return EvidenceItems."""
        ...


@runtime_checkable
class MemoryProtocol(Protocol):
    """
    memory layer interface.

    Stores, retrieves, and manages evidence and artifacts.
    Has explicit tiers: working, compressed, evicted.
    """

    async def store(self, item: EvidenceItem) -> str:
        """Store an item. Returns the storage key."""
        ...

    async def retrieve(self, query: str, limit: int = 10) -> list[EvidenceItem]:
        """Retrieve items matching a query."""
        ...

    async def compress(self) -> int:
        """Compress working memory. Returns number of items compressed."""
        ...


@runtime_checkable
class GroundingProtocol(Protocol):
    """
    grounding layer interface.

    Normalizes evidence and creates citation links.
    Not active in v0. Active in Phase 2 when CitationRecord generation begins.
    """

    async def ground(self, evidence: list[EvidenceItem]) -> list[CitationRecord]:
        """Normalize evidence items and produce CitationRecords."""
        ...


@runtime_checkable
class DeliberationProtocol(Protocol):
    """
    deliberation layer interface.

    Synthesizes evidence, detects conflicts, produces claims.
    v0: single-pass synthesis. Phase 3: multi-perspective debate.
    """

    async def deliberate(self, evidence: list[EvidenceItem], context: str | None = None) -> DecisionPacket:
        """Synthesize evidence into a DecisionPacket."""
        ...


@runtime_checkable
class VerificationProtocol(Protocol):
    """
    verification layer interface.

    Checks claims against evidence. Labels but never modifies claims.
    Returns a separate VerificationResult — does not mutate the DecisionPacket.
    v0: deterministic checks against evidence. Phase 2: also checks CitationRecords.
    """

    async def verify(self, decision: DecisionPacket, evidence: list[EvidenceItem]) -> VerificationResult:
        """Verify claims in a DecisionPacket against available evidence."""
        ...


@runtime_checkable
class EvaluationProtocol(Protocol):
    """
    evaluation layer interface.

    Scores runs, logs experiments, tracks failures.
    """

    async def evaluate(self, run_artifacts: dict) -> dict:
        """Evaluate a run and return metrics."""
        ...

    async def log_experiment(self, record: ExperimentRecord) -> None:
        """Log an ExperimentRecord."""
        ...
