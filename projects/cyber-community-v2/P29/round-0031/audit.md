# Audit — Round round-0031

**Status:** PASSED  
**Completed:** 2026-04-04 13:37 UTC  
**Total cost:** $0.9051  
**Attempts:** 1

## Task
**P29-T2** — Formalize AppraisalOutput contract with advisory vs contract-bearing field annotations
Introduce a new Pydantic v2 model called AppraisalOutput in back/app/domain/ that captures everything the appraisal layer returns after processing one tick. Each field must be annotated as either contract-bearing (the settlement engine reads it and may not ignore it) or advisory (provides interpretive context but the engine is not obligated to act on it). The model must also specify deterministic fallback behavior: when no external appraisal source is available, every field has a well-defined default or derivation rule so the engine can always produce a valid AppraisalOutput without external input.

