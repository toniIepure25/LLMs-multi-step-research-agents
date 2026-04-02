## Handoff: v1 Mocked Integration Checkpoint

### What was done
- widened the candidate-only claim cap from 3 to 6 so the selector can be tested on a realistic choice set
- added a focused mocked 2008-style integration checkpoint for v1-minimal deliberation
- kept final `DecisionPacket` behavior unchanged and selector-capped

### What was NOT done
- no live runs
- no orchestration redesign
- no verification changes

### Decisions made
- widened only the candidate-generation side, not the final selected output
- kept the checkpoint local to tests and a small handoff note

### Open questions
- whether the widened candidate pool improves live 2008 stability without harming groundedness

### Suggested next steps
1. Run the focused live 2008 probe against `v0_tier1_eval_set_004`
2. Compare claim count, groundedness, and mechanism preservation
3. Only then consider a full 3-question rerun
