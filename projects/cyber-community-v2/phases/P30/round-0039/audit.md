# Audit — Round round-0039

**Status:** PASSED  
**Completed:** 2026-04-05 09:12 UTC  
**Total cost:** $1.2810  
**Attempts:** 1

## Task
**P30-T4** — Comparison harness: run both paths, diff, flag violations
Build back/app/llm/comparison_harness.py that accepts an AppraisalInput, runs the deterministic fallback path and the shadow LLM path independently on the same input, produces a structured ComparisonReport (Pydantic model) capturing per-field diffs and metadata, and delegates violation detection to the existing acceptance_rules.compare() function. The harness must be purely offline with no side effects on live simulation state.

