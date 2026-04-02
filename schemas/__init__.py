"""
ASAR Schemas — Canonical typed data structures for inter-layer communication.

All data flowing between architectural layers MUST use these schemas.
Do not create parallel type systems in individual modules.
"""

from schemas.candidate_claim_set import CandidateClaim, CandidateClaimSet
from schemas.citation_record import CitationRecord
from schemas.decision_packet import Claim, DecisionPacket, EpistemicStatus
from schemas.evidence_item import EvidenceItem, SourceMetadata
from schemas.experiment_record import ExperimentRecord
from schemas.research_output import ResearchOutput
from schemas.research_plan import PlanStep, ResearchPlan
from schemas.task_packet import TaskPacket, TaskStatus
from schemas.verification_result import ClaimVerdict, ClaimVerification, VerificationResult

__all__ = [
    "ResearchPlan",
    "PlanStep",
    "TaskPacket",
    "TaskStatus",
    "EvidenceItem",
    "SourceMetadata",
    "CitationRecord",
    "CandidateClaim",
    "CandidateClaimSet",
    "DecisionPacket",
    "Claim",
    "EpistemicStatus",
    "VerificationResult",
    "ClaimVerification",
    "ClaimVerdict",
    "ResearchOutput",
    "ExperimentRecord",
]
