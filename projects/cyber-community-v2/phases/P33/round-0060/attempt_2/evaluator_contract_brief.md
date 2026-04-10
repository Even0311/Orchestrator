# Evaluator Contract Review — round-0060

**Task Key:** P33-T1
**Title:** Multi-day LLM appraisal deviation audit with raw response capture

## Proposed Acceptance Criteria
1. {'id': '1', 'description': 'back/tools/audit_llm_deviation.py exists and is executable as a CLI script with --days flag'}
2. {'id': '2', 'description': 'The script uses comparison_harness.run_comparison() for deviation detection (import and call must be present)'}
3. {'id': '3a', 'description': 'Per-tick JSON records include raw_llm_response that is NOT None when llm_used is True. The script must call shadow_runner.run() (or equivalent) to obtain ShadowRunResult.raw_response and thread it into the per-tick record.'}
4. {'id': '3b', 'description': 'Per-tick JSON records include all required fields: world_day, tick_type, agent_id, verdict, field_diffs, raw_llm_response, llm_used, failure_reason'}
5. {'id': '4', 'description': 'Deviations are mapped to specific OUTPUT_FORMAT prompt rules from prompt_schema.py in the markdown report'}
6. {'id': '5', 'description': 'Outputs are written to back/tools/audit_outputs/p33_t1_deviation_audit.json and back/tools/audit_outputs/p33_t1_deviation_report.md'}
7. {'id': '6', 'description': 'The aggregate summary includes: total ticks audited, LLM success rate, deviation count by category, and top violated prompt rules'}
8. {'id': '7', 'description': 'All existing tests in back/tests/ pass with zero regressions (python -m pytest tests/ -v from back/ directory)'}
9. {'id': '8', 'description': 'No files under back/app/, back/tests/, front/, or docs/ are modified'}

## Proposed Review Focus
- CRITICAL: Verify that raw_llm_response is actually populated (not None/null) when the LLM is called — this was the blocker in the previous attempt. Check the code path: shadow_runner.run() must be called and ShadowRunResult.raw_response must be threaded into per-tick records.
- Verify comparison_harness.run_comparison() is used for deviation detection (not reimplemented)
- Verify no files under back/app/ or back/tests/ were modified
- Check that the script handles missing ANTHROPIC_API_KEY gracefully
- Confirm the deviation-to-prompt-rule mapping references actual OUTPUT_FORMAT rules from prompt_schema.py

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
