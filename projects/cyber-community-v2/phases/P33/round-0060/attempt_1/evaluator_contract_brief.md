# Evaluator Contract Review — round-0060

**Task Key:** P33-T1
**Title:** Multi-day LLM appraisal deviation audit

## Proposed Acceptance Criteria
1. back/tools/audit_llm_deviation.py exists and is executable as a standalone script (python tools/audit_llm_deviation.py from back/).
2. The script accepts --days N flag (default 5) to control simulation length.
3. Running the script with a valid ANTHROPIC_API_KEY produces back/tools/audit_outputs/p33_t1_deviation_audit.json containing: (a) a list of per-tick records each with world_day, tick_type, raw_llm_response, verdict fields, and (b) an aggregate_summary section with per-field deviation counts and per-tick-type deviation counts.
4. Running the script produces back/tools/audit_outputs/p33_t1_deviation_report.md containing: (a) a ranked table of deviation patterns by frequency, (b) identification of which OUTPUT_FORMAT_SECTION rules correlate with observed deviations, and (c) a summary of structural failures vs semantic deviations vs passes.
5. The script does not crash on LLM connection failures — it records them as LLM_CONNECTION_FAILURE entries and continues to subsequent ticks/days.
6. The script does not modify any simulation state files, seed data, or engine modules.
7. The script imports and uses comparison_harness.run_comparison() or the shadow_runner + acceptance_rules pipeline (not a reimplementation).

## Proposed Review Focus
- Verify the audit script uses the existing comparison_harness / shadow_runner / acceptance_rules pipeline rather than reimplementing deviation detection.
- Verify the JSON output structure captures enough raw data (especially raw_llm_response) to be useful for P33-T2 prompt tightening.
- Verify the markdown report actually maps deviations back to specific prompt instructions from OUTPUT_FORMAT_SECTION, not just generic field names.
- Verify no forbidden files were modified.
- Verify the script handles the full multi-day simulation lifecycle correctly (seed → advance_day loop) rather than constructing artificial inputs.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
