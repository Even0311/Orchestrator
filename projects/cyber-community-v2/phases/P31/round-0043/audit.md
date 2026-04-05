# Audit — Round round-0043

**Status:** PASSED  
**Completed:** 2026-04-05 12:22 UTC  
**Total cost:** $1.1548  
**Attempts:** 1

## Task
**P31-T2** — Runtime validation gate: apply P30 acceptance rules and guardrails with deterministic fallback on rejection
Extract the inline guardrail logic currently embedded in appraisal_router.py into a dedicated, standalone validation gate module (back/app/llm/validation_gate.py). The gate takes a ShadowRunResult, a deterministic baseline AppraisalOutput, and a ComparisonVerdict, and returns a structured GateDecision that records whether the LLM output is accepted or rejected, the rejection reason, and which failure mode category triggered the rejection. The router is then updated to call the gate instead of duplicating guardrail logic inline. The gate enforces all BLOCKING guardrail policies defined in failure_taxonomy.py: STRUCTURAL_FAIL verdict triggers rejection, and a valence deviation with severity=severe triggers rejection.

