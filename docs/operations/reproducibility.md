# Reproducibility

> See also: [PROJECT_DOSSIER.md § Invariants](../../PROJECT_DOSSIER.md#10-invariants) (invariant #3) · [experiments/templates/](../../experiments/templates/)

## Principle

**Config + seed + data = same result.** This is invariant #3. Every experiment must be fully determined by its recorded configuration.

## What Must Be Recorded

For every experiment run (fields match [`ExperimentRecord`](../../schemas/experiment_record.py)):

| Field | Example | Schema field |
|-------|---------|-------------|
| Git commit hash | `a1b2c3d` | `git_commit` |
| Config file (exact) | `experiments/runs/2026-03-16_baseline/config.toml` | `config_snapshot` |
| Model provider + model ID | `anthropic/claude-sonnet-4-6` | in `config_snapshot` |
| Random seed | `42` | `seed` |
| Input data reference | `benchmarks/tier1_v1.json` | in `artifacts` |
| Python version | `3.11.8` | `python_version` |
| Key dependency versions | `{'pydantic': '2.6.0'}` | `dependency_versions` |
| Start/end timestamps | `2026-03-16T14:30:00Z` | `started_at`, `completed_at` |

## Seed Management

- All randomness flows from a single configurable seed
- Default seed: `42` (set in [`config/experiments.toml`](../../config/experiments.toml))
- Seeds are set per-experiment, not hardcoded in source

## Lockfile Discipline

- `uv.lock` is committed and used for all experiment runs
- Pin exact versions for reproducibility
- Document system-level dependencies

## Assumption: API Determinism

LLM API calls may not be perfectly deterministic even with temperature=0. For strict reproducibility, cache API responses during experiments. This is configured via `cache_llm_responses` in [`config/experiments.toml`](../../config/experiments.toml).

## Open Design Question

Response caching implementation is not yet built. See [tasks/backlog.md](../../tasks/backlog.md).
