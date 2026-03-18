# Architecture Decision Log

> See also: [system-overview.md](system-overview.md) · [PROJECT_DOSSIER.md § Invariants](../../PROJECT_DOSSIER.md#10-invariants)

Record all non-trivial architectural decisions here. **Any change to schemas, protocols, layer boundaries, or invariants must have an entry before implementation.** See [AGENTS.md § How to Propose Architecture Changes](../../AGENTS.md#how-to-propose-architecture-changes).

## Format

```
## ADR-NNN: <Title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded | deprecated
**Context:** What prompted this decision?
**Options considered:**
1. Option A — pros/cons
2. Option B — pros/cons
**Decision:** What we chose and why.
**Consequences:** What this means for the codebase.
**Invariants affected:** none | list which
```

---

## ADR-001: Layer-Based Architecture

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need a structure that separates concerns cleanly for a multi-step research agent.
**Options considered:**
1. Monolithic agent loop — simple but hard to test, swap, or evaluate individual components
2. Pipeline architecture — clean but too rigid for re-planning loops
3. Layer architecture with orchestrator — flexible, testable, supports re-planning
**Decision:** Layer architecture with a central orchestrator. Eight layers with typed interfaces, swappable independently.
**Consequences:** Requires explicit schema definitions for all inter-layer communication. Adds boilerplate but dramatically improves testability and modularity. Orchestration is the sole router between layers.
**Invariants affected:** Establishes invariants #2 (typed boundaries), #6 (swappable modules), #7 (orchestration-only routing).

## ADR-002: Pydantic for Schema Layer

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need typed, validated data structures for inter-layer communication.
**Options considered:**
1. Plain dataclasses — lightweight but no validation
2. Pydantic v2 — validation, serialization, JSON schema generation
3. Protocol Buffers — strong typing but heavy toolchain, poor Python ergonomics
**Decision:** Pydantic v2. Provides validation, serialization, and JSON schema generation with minimal overhead.
**Consequences:** All schemas live in `schemas/` as Pydantic models. Contributors must use these — no parallel type systems.
**Invariants affected:** Reinforces invariant #2 (typed boundaries).

## ADR-003: Python + uv for Project Management

**Date:** 2026-03-16
**Status:** accepted
**Context:** Need a language and dependency management approach for the prototype.
**Options considered:**
1. Python + pip — universal but dependency resolution is slow and fragile
2. Python + Poetry — good but slower than uv
3. Python + uv — fast, modern, good lockfile support
**Decision:** Python 3.11+ with uv for dependency management.
**Consequences:** `pyproject.toml` is the single source of truth for dependencies. Use `uv sync` and `uv run`.
**Invariants affected:** none.

## ADR-004: Normalize Schema Timestamps to UTC at Validation Boundaries

**Date:** 2026-03-17
**Status:** accepted
**Context:** v0 requires timezone-aware UTC timestamps only, but schema fields accepted naive or non-UTC datetimes as user input. This made defaults UTC-aware while still allowing inconsistent runtime data across artifacts.
**Options considered:**
1. Keep UTC defaults only and rely on contributors to pass valid datetimes — simple, but correctness depends on convention and naive timestamps can leak into artifacts.
2. Validate every timestamp field at the schema boundary and normalize aware inputs to UTC — slightly more boilerplate, but makes timestamp handling deterministic and inspectable.
**Decision:** Add a shared schema timestamp type that rejects naive datetimes and normalizes aware datetimes to UTC for all typed timestamp fields.
**Consequences:** All serialized artifacts store timestamps consistently in UTC. Callers must provide timezone-aware datetimes when overriding timestamps. Existing UTC defaults continue to work unchanged.
**Invariants affected:** Reinforces invariant #2 (typed boundaries) and invariant #3 (reproducible experiments).
