"""
Evaluation — Experiment logging and basic metrics for the frozen v0 pipeline.

v0 responsibilities:
- Build an `ExperimentRecord` from run artifacts
- Compute basic metrics for the vertical slice
- Keep evaluation post-hoc and deterministic

Implements: `EvaluationProtocol` (see `asar/core/protocols.py`)
Input: run artifacts, config, benchmark definitions
Output: `ExperimentRecord` with metrics

Invariant: evaluation is post-hoc and deterministic given the same inputs

v0 implementation target: `ExperimentLogger`
v0 note: core metrics are groundedness, evidence utilization, and plan coverage
v0 note: citation-quality scoring belongs to Phase 2+
"""

from asar.evaluation.experiment_logger import ExperimentLogger

__all__ = ["ExperimentLogger"]
