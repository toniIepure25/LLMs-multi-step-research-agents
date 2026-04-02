## Handoff: v1 2008 Probe 010 Blocking Fix

### What was done
- Ran the focused live `v1_2008_probe_010` 2008 checkpoint.
- Hit a candidate-generation truncation bug under the live `512`-token setting.
- Reduced candidate-generation max length from `5` to `4`.
- Tightened the prompt from `2 to 5` candidates to `2 to 4`.
- Required very short `reasoning_trace` fragments to shrink the JSON payload.
- Updated the mocked v1 integration fixture to match the new live-safe
  candidate cap.
- Revalidated with `uv run ruff check ...` and `uv run pytest`.
- Successfully reran the live probe and recorded results in
  `experiments/notes/v1_2008_probe_010.md`.

### What was NOT done
- No selector redesign beyond the already-requested narrow pass.
- No full 3-question rerun.
- No provider or schema redesign.

### Decisions made
- Treated the failure as a live token-budget compatibility bug, not a new
  architectural change.
- Kept candidate generation wider than final selection, but narrowed it just
  enough to fit the live setting more reliably.

### Open questions
- How to preserve the improved selector behavior from `010` while restoring
  stronger securitization support quality.
- Whether the next narrow pass belongs in candidate generation, in candidate
  normalization, or in selector weighting around single-evidence claims.

### Suggested next steps
1. Do one more narrow v1-minimal pass focused on support quality for otherwise
   clean direct-causal claims.
2. Rerun only the focused live 2008 probe.
3. Only if groundedness recovers, consider the full 3-question live rerun.
