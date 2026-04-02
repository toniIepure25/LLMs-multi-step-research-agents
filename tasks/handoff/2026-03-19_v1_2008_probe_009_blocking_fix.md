## Handoff: v1 2008 Probe 009 Blocking Fix

### What was done
- Ran the first live v1-minimal 2008 probe.
- Hit a real blocking bug in deliberation: candidate-generation output was too
  large for the live `ASAR_MODEL_MAX_TOKENS=512` setting and returned truncated
  JSON.
- Reduced candidate-claim generation capacity from `6` to `5`.
- Tightened the candidate-generation prompt from `3 to 6` claims to `2 to 5`
  claims.
- Revalidated with `uv run ruff check ...` and `uv run pytest`.
- Successfully reran the probe and recorded results in
  `experiments/notes/v1_2008_probe_009.md`.

### What was NOT done
- No selector redesign.
- No live rerun beyond the single 2008 probe.
- No full 3-question Tier 1 rerun.

### Decisions made
- Kept candidate generation wider than final selection, but reduced it just
  enough to fit the live token budget.
- Treated this as a tiny blocking compatibility fix, not a new architecture
  change.

### Open questions
- How should the selector penalize claims that are supported but drift from the
  target event, like `housing crisis` instead of `2008 financial crisis`?
- Should mechanism diversity be weighted more strongly so a second
  securitization-adjacent claim loses to a distinct supported mechanism?

### Suggested next steps
1. Add one narrow selector pass for target-event fidelity and mechanism
   diversity.
2. Rerun the focused 2008 live probe.
3. Only if that is stable, rerun the full 3-question Tier 1 set.
