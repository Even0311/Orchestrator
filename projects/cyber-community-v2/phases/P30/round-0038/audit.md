# Audit — Round round-0038

**Status:** PASSED  
**Completed:** 2026-04-05 09:05 UTC  
**Total cost:** $0.8259  
**Attempts:** 1

## Task
**P30-T3** — Per-field acceptance rules for LLM vs deterministic AppraisalOutput comparison
Create a module at back/app/llm/acceptance_rules.py that defines per-field comparison criteria for evaluating an LLM-produced AppraisalOutput against a deterministic baseline AppraisalOutput, with explicit separation of structural validity checks (field present, correct type, in bounds) from semantic quality checks (direction agreement, magnitude plausibility, alignment with deterministic signal). The module must expose a single public entry point that accepts an LLM output and a deterministic baseline and returns a structured verdict with per-field results and an overall pass/fail classification.

