"""
Planning — Goal decomposition for the frozen v0 pipeline.

v0 responsibilities:
- Decompose one research goal into a `ResearchPlan`
- Produce sequential `PlanStep`s for the orchestrator to execute
- Keep planning separate from execution and verification

Implements: `PlannerProtocol` (see `asar/core/protocols.py`)
Input: research goal (`str`) + optional constraints
Output: `ResearchPlan` (see `schemas/research_plan.py`)

v0 implementation target: `SimplePlanner`
v0 note: orchestration, not planning, creates `TaskPacket`s
v0 note: `replan()` remains part of the protocol but the re-planning loop is out of scope

TODO: Implement `SimplePlanner` — one LLM call, goal → `ResearchPlan`
TODO: Implement lightweight plan validation for v0 sequential steps
FUTURE: re-planning, conditional branches, and richer planning strategies after v0
"""

from asar.planning.simple_planner import SimplePlanner

__all__ = ["SimplePlanner"]
