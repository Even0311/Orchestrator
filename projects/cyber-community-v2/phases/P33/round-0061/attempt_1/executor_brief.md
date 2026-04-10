# Executor Brief — round-0061

## Task Contract
**Task Key:** P33-T2
**Title:** Tighten prompt schema and output-format instructions to reduce LLM deviation rate
**Objective:** Revise the prompt template (system_prompt, user_prompt_template, OUTPUT_FORMAT_SECTION) in back/app/llm/prompt_schema.py to close the specific deviation patterns observed in P33-T1 shadow run data — over-enrichment of absorption/valence/arousal, phantom growth dimensions, guidance_resonance inflation, and T4 zero-absorption override — then verify the tightened prompts by extending or creating a test that exercises the rendered prompt text against the known deviation categories.

**Exact Scope:**
- Tighten OUTPUT_FORMAT_SECTION in prompt_schema.py: add explicit negative examples and field-level constraints that directly address the observed deviation patterns (e.g., 'Do not escalate absorption beyond surface unless the headline/event context explicitly warrants deep engagement', 'Do not add growth dimensions that are not directly triggered by the event content', 'For T4 without social_event_context, absorption MUST be none').
- Tighten PromptTemplate.system_prompt in prompt_schema.py: strengthen the instruction to anchor on provided context and resist embellishment, explicitly calling out that conservative (baseline-matching) outputs are preferred over enriched ones when the input context is ambiguous.
- Add tick-type-specific guidance sections within the prompt template that give the LLM per-tick constraints (e.g., T1 should rarely produce absorption=deep unless headline content is extraordinary, T4 without SOCIAL EVENT CONTEXT section must return absorption=none).
- Create or extend a test file that verifies: (a) the rendered prompt text for each active tick type (T1, T2, T4) contains the newly added negative-example and constraint language, and (b) the OUTPUT_FORMAT_SECTION includes all required field-level constraint text.
- Verify all existing tests pass after prompt changes (run back/tests/ suite).

**Constraints:**
- AppraisalSignal v1 is frozen — do not modify its field definitions.
- Do not modify any engine files (engines/*.py) — this task is prompt-layer only.
- Do not modify acceptance_rules.py, failure_taxonomy.py, validation_gate.py, comparison_harness.py, shadow_runner.py, response_parser.py, or appraisal_router.py — the evaluation infrastructure is not in scope.
- Do not modify AppraisalOutput or AppraisalInput models.
- Do not add new fields to the OUTPUT_FORMAT_SECTION JSON schema — the field surface is frozen.
- Do not change the user_prompt_template placeholder names or the section rendering functions (_render_relational_section, _render_social_event_section, _render_player_section) — only change the static text content within the template.
- All prompt text changes must be in natural language instructions to the LLM, not structural schema changes.
- Settlement belongs to engines — prompt layer only produces signals.

**Forbidden Files (DO NOT modify):**
- `back/app/engines/*.py`
- `back/app/domain/appraisal_input.py`
- `back/app/domain/appraisal_output.py`
- `back/app/domain/models.py`
- `back/app/domain/enums.py`
- `back/app/llm/acceptance_rules.py`
- `back/app/llm/failure_taxonomy.py`
- `back/app/llm/validation_gate.py`
- `back/app/llm/comparison_harness.py`
- `back/app/llm/shadow_runner.py`
- `back/app/llm/response_parser.py`
- `back/app/llm/appraisal_router.py`
- `back/app/llm/appraisal_audit_log.py`
- `back/app/seed/*.py`
- `back/app/services/*.py`
- `back/app/api/**`
- `back/app/world/**`
- `front/**`
- `back/tools/**`

**Non-Goals (DO NOT do):**
- Do not run an actual LLM shadow audit — this task tightens prompt text only; the actual LLM deviation measurement is a separate future step.
- Do not add new prompt template variants or a prompt versioning system.
- Do not modify the deterministic fallback logic in AppraisalOutput.from_deterministic_fallback.
- Do not expand bridge coverage to deferred ticks (T3/T5/T6/T7/T8).
- Do not add runtime prompt selection logic or A/B testing infrastructure.
- Do not add or modify any observability/logging code.
- Do not change the Anthropic API model or parameters in shadow_runner.py.

**Acceptance Criteria:**
- OUTPUT_FORMAT_SECTION in prompt_schema.py contains at least one explicit negative example per deviation pattern: (1) absorption over-enrichment, (2) valence drift from neutral, (3) phantom growth dimensions, (4) guidance_resonance inflation beyond neutral when no player guidance is active.
- OUTPUT_FORMAT_SECTION includes an explicit T4 no-event constraint: when no SOCIAL EVENT CONTEXT section is present, absorption must be none.
- PromptTemplate.system_prompt explicitly instructs the LLM to prefer conservative/baseline-matching outputs over enriched ones when input context is ambiguous.
- The rendered user prompt for T1, T2, and T4 tick types all include the new constraint language (verified by test assertions on rendered prompt substrings).
- A test file exists that programmatically asserts the presence of key constraint phrases in (a) OUTPUT_FORMAT_SECTION and (b) rendered prompts for each active tick type.
- All existing tests in back/tests/ pass without modification (zero regressions).
- No new fields or field name changes appear in the OUTPUT_FORMAT_SECTION JSON schema block.
- The placeholder names in user_prompt_template remain unchanged.

## Your Task
1. Read the codebase and understand the relevant code
2. Implement the changes described in the contract
3. Write/update tests as needed
4. Run the test suite to verify no regressions
5. Write `execution_evidence.json` with: summary, files_changed, commands_run, test_results, diff_summary, unresolved_issues
