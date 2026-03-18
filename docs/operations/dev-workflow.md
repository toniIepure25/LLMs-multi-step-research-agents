# Developer Workflow

> See also: [AGENTS.md](../../AGENTS.md) · [reproducibility.md](reproducibility.md) · [PROJECT_DOSSIER.md](../../PROJECT_DOSSIER.md)

## Setup

```bash
# Prerequisites: Python 3.11+, uv
curl -LsSf https://astral.sh/uv/install.sh | sh

git clone <repo-url> && cd asar
uv python install 3.11
uv sync --extra dev
uv run pytest
```

Use Python 3.11+ for development and validation. The repo root includes `.python-version` with `3.11` as the canonical local target. If tests happen to pass under Python 3.10.x locally, treat that as non-canonical rather than supported.

## Daily Development

### Running tests
```bash
uv run pytest                    # all tests
uv run pytest tests/test_foo.py  # specific file
uv run pytest -k "test_name"    # specific test
uv run ruff check asar tests     # lint
```

### Running the mocked v0 integration target
```bash
uv run pytest tests/test_v0_integration.py
```

This canonical integration test runs the full frozen v0 stack on one Tier 1 question with deterministic mocked LLM and search clients. It exercises `SimplePlanner`, `WebSearchExecutor`, `WorkingMemory`, `SimpleSynthesizer`, `EvidenceChecker`, `ExperimentLogger`, and `SequentialOrchestrator`, then asserts over the final `ResearchOutput` and written run artifacts.

### Running the local demo entrypoint
```bash
uv run python -m asar.demo
uv run python -m asar.demo "What were the main causes of the 2008 financial crisis?"
uv run python -m asar.demo "Your research goal here" --output-dir /tmp/asar-demo
```

The demo runs the real frozen v0 pipeline with deterministic local mock clients and prints the written `output.json` and `experiment.json` paths for inspection.

### Running the live v0 demo path
```bash
export OPENAI_API_KEY=...
export BRAVE_SEARCH_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL=gpt-5.2

uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live
```

Current live adapter choices are intentionally minimal:
- OpenAI for the LLM boundary
- Brave Search for the search boundary

Optional live settings:

```bash
export ASAR_SEARCH_PROVIDER=brave
export ASAR_OPENAI_BASE_URL=...
export ASAR_BRAVE_SEARCH_COUNTRY=US
export ASAR_BRAVE_SEARCH_LANG=en
```

If credentials are missing, the command fails clearly and instructively. The default demo mode remains `mock`.

### Adding dependencies
```bash
uv add <package>         # runtime dependency
uv add --dev <package>   # dev dependency
```

### Code quality
```bash
uv run ruff check asar tests  # lint
uv run ruff format asar tests # format
uv run mypy asar              # type check
```

## Branch Strategy

| Prefix | Purpose | Merged to main? |
|--------|---------|----------------|
| `feat/<name>` | Feature branches | Yes |
| `fix/<name>` | Bug fixes | Yes |
| `exp/<name>` | Experiment branches | Maybe — depends on results |

## Commit Conventions

See [AGENTS.md § Commit Message Format](../../AGENTS.md#commit-message-format). Scopes match `asar/` subdirectory names exactly.

## Configuration

All config lives in [`config/`](../../config/) as TOML files. Environment-specific overrides use variables prefixed with `ASAR_`:

```
ASAR_MODEL_PROVIDER=openai
ASAR_MODEL_MODEL=gpt-5.2
ASAR_LOG_LEVEL=debug
```

## Running Experiments

See [AGENTS.md § How to Propose an Experiment](../../AGENTS.md#how-to-propose-an-experiment) for the full workflow.

Quick version:
1. Copy template from [`experiments/templates/`](../../experiments/templates/)
2. Fill in config and hypothesis
3. Run the experiment
4. Save results to `experiments/runs/YYYY-MM-DD_<name>/`
5. Update [`experiments/registry/experiment_index.md`](../../experiments/registry/experiment_index.md)
