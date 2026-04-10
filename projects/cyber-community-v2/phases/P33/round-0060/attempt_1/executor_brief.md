# Executor Brief — round-0060

## Task Contract
**Task Key:** P33-T1
**Title:** Multi-day LLM appraisal deviation audit
**Objective:** Run a controlled multi-day simulation that calls the LLM for all active ticks (T1/T2/T4), collect every raw LLM response, classify each deviation between LLM output and deterministic baseline using the existing acceptance_rules infrastructure, and produce a structured report identifying which prompt instructions the LLM most frequently violates or stretches.

**Exact Scope:**
- Create a new audit script (back/tools/audit_llm_deviation.py) that runs a multi-day bridged simulation (minimum 5 days), calling the real LLM via comparison_harness.run_comparison() or shadow_runner.run() for each active tick (T1, T2, T4).
- For each tick, record: world_day, tick_type, raw LLM response text, parsed LLM output (if parse succeeded), deterministic baseline output, the ComparisonVerdict from acceptance_rules.compare(), and the failure/deviation classification.
- Aggregate all results across all days and ticks into a structured JSON output file (back/tools/audit_outputs/p33_t1_deviation_audit.json) containing: per-tick raw data, per-field deviation frequency counts, per-tick-type deviation frequency counts, and overall deviation-rate statistics.
- Produce a human-readable markdown report (back/tools/audit_outputs/p33_t1_deviation_report.md) that ranks deviation patterns by frequency, identifies which specific prompt instructions correlate with the most common deviations, and highlights any structural failures observed.
- The script must handle LLM failures gracefully (connection errors, parse failures) — recording them as data points in the audit rather than aborting the run.

**Constraints:**
- Use existing infrastructure only: comparison_harness.run_comparison(), shadow_runner.run(), acceptance_rules.compare(), response_parser.parse_llm_response(), prompt_schema.LlmAppraisalRequest, appraisal_audit_log models. Do not duplicate or reimplement their logic.
- Do not modify any existing engine, domain, or llm module files. This is a read-only audit — it observes and reports, it does not fix.
- The audit script must be runnable standalone from back/tools/ (same pattern as existing audit_run.py).
- All simulation state must come from the existing seed data and advance_day / day_simulator pipeline. Do not invent synthetic AppraisalInput objects outside the normal simulation flow.
- The script requires ANTHROPIC_API_KEY to be set. It must fail clearly with a message if the key is missing, not silently skip LLM calls.

**Forbidden Files (DO NOT modify):**
- `back/app/engines/**`
- `back/app/domain/**`
- `back/app/llm/shadow_runner.py`
- `back/app/llm/acceptance_rules.py`
- `back/app/llm/comparison_harness.py`
- `back/app/llm/response_parser.py`
- `back/app/llm/prompt_schema.py`
- `back/app/llm/failure_taxonomy.py`
- `back/app/llm/validation_gate.py`
- `back/app/llm/appraisal_audit_log.py`
- `back/app/seed/**`
- `back/app/services/**`
- `back/app/api/**`
- `back/tests/**`
- `front/**`

**Non-Goals (DO NOT do):**
- Do not fix or tighten any prompts — that is P33-T2.
- Do not implement degradation-rate tracking or fallback thresholds — that is P33-T3.
- Do not modify the LLM prompt schema, output format contract, or system prompt.
- Do not add new fields to AppraisalOutput, AppraisalInput, or any domain model.
- Do not change acceptance_rules severity classifications or add new structural checks.
- Do not expand bridge coverage to deferred ticks (T3/T5/T6/T7/T8).
- Do not write unit tests for the audit script itself — the audit output IS the deliverable.

**Acceptance Criteria:**
- back/tools/audit_llm_deviation.py exists and is executable as a standalone script (python tools/audit_llm_deviation.py from back/).
- The script accepts --days N flag (default 5) to control simulation length.
- Running the script with a valid ANTHROPIC_API_KEY produces back/tools/audit_outputs/p33_t1_deviation_audit.json containing: (a) a list of per-tick records each with world_day, tick_type, raw_llm_response, verdict fields, and (b) an aggregate_summary section with per-field deviation counts and per-tick-type deviation counts.
- Running the script produces back/tools/audit_outputs/p33_t1_deviation_report.md containing: (a) a ranked table of deviation patterns by frequency, (b) identification of which OUTPUT_FORMAT_SECTION rules correlate with observed deviations, and (c) a summary of structural failures vs semantic deviations vs passes.
- The script does not crash on LLM connection failures — it records them as LLM_CONNECTION_FAILURE entries and continues to subsequent ticks/days.
- The script does not modify any simulation state files, seed data, or engine modules.
- The script imports and uses comparison_harness.run_comparison() or the shadow_runner + acceptance_rules pipeline (not a reimplementation).

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
