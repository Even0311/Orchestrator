# Executor Brief — round-0060

## Task Contract
**Task Key:** P33-T1
**Title:** Multi-day LLM appraisal deviation audit with raw response capture
**Objective:** Create an audit tool that runs a controlled multi-day simulation, collects raw LLM responses for all active ticks (T1/T2/T4), classifies every deviation between LLM output and the deterministic baseline, and produces structured JSON and markdown reports. The raw LLM text must be captured and included in every per-tick record — this is the primary deliverable for downstream P33-T2 prompt tightening.

**Exact Scope:**
- Create back/tools/audit_llm_deviation.py — a standalone CLI script
- The script runs a multi-day simulation (configurable --days flag, default 5) using seed data
- For each active tick (T1, T2, T4) on each day, use comparison_harness.run_comparison() to get deviation verdicts and field diffs
- Additionally capture the raw LLM response text via shadow_runner.run() so that raw_llm_response is populated (not None) whenever the LLM was actually called
- Classify deviations by mapping them to specific OUTPUT_FORMAT prompt rules from prompt_schema.py
- Output structured JSON to back/tools/audit_outputs/p33_t1_deviation_audit.json with per-tick records and aggregate summary
- Output human-readable markdown to back/tools/audit_outputs/p33_t1_deviation_report.md with ranked deviation tables
- Each per-tick JSON record must include: world_day, tick_type, agent_id, verdict, field_diffs, raw_llm_response, llm_used, failure_reason
- Aggregate summary must include: total ticks audited, LLM success rate, deviation counts by category, top violated prompt rules

**Constraints:**
- Use comparison_harness.run_comparison() for deviation detection — do not reimplement comparison logic
- Use shadow_runner.run() to obtain ShadowRunResult.raw_response for raw LLM text capture — this is the fix for the previous attempt's blocker
- Do not modify any existing module under back/app/ — the audit script is a standalone tool
- Gracefully handle LLM API failures (missing API key, network errors) — report them, do not crash
- The script must be runnable from back/ directory: python tools/audit_llm_deviation.py --days N
- Existing tests (back/tests/) must continue to pass with zero regressions

**Forbidden Files (DO NOT modify):**
- `back/app/**/*.py`
- `back/tests/**/*.py`
- `front/**/*`
- `docs/**/*`

**Non-Goals (DO NOT do):**
- Do not modify ComparisonReport, ShadowRunResult, or any existing model/module
- Do not expand bridge coverage to deferred ticks (T3/T5/T6/T7/T8)
- Do not implement prompt fixes — this audit only identifies deviations for future P33-T2 work
- Do not add new test files — the audit script is a tool, not a test
- Do not add LLM-based classification of deviations — use deterministic rule mapping only

**Acceptance Criteria:**
- {'id': '1', 'description': 'back/tools/audit_llm_deviation.py exists and is executable as a CLI script with --days flag'}
- {'id': '2', 'description': 'The script uses comparison_harness.run_comparison() for deviation detection (import and call must be present)'}
- {'id': '3a', 'description': 'Per-tick JSON records include raw_llm_response that is NOT None when llm_used is True. The script must call shadow_runner.run() (or equivalent) to obtain ShadowRunResult.raw_response and thread it into the per-tick record.'}
- {'id': '3b', 'description': 'Per-tick JSON records include all required fields: world_day, tick_type, agent_id, verdict, field_diffs, raw_llm_response, llm_used, failure_reason'}
- {'id': '4', 'description': 'Deviations are mapped to specific OUTPUT_FORMAT prompt rules from prompt_schema.py in the markdown report'}
- {'id': '5', 'description': 'Outputs are written to back/tools/audit_outputs/p33_t1_deviation_audit.json and back/tools/audit_outputs/p33_t1_deviation_report.md'}
- {'id': '6', 'description': 'The aggregate summary includes: total ticks audited, LLM success rate, deviation count by category, and top violated prompt rules'}
- {'id': '7', 'description': 'All existing tests in back/tests/ pass with zero regressions (python -m pytest tests/ -v from back/ directory)'}
- {'id': '8', 'description': 'No files under back/app/, back/tests/, front/, or docs/ are modified'}

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
