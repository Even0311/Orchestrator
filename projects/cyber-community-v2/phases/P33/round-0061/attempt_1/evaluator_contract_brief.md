# Evaluator Contract Review — round-0061

**Task Key:** P33-T2
**Title:** Tighten prompt schema and output-format instructions to reduce LLM deviation rate

## Proposed Acceptance Criteria
1. OUTPUT_FORMAT_SECTION in prompt_schema.py contains at least one explicit negative example per deviation pattern: (1) absorption over-enrichment, (2) valence drift from neutral, (3) phantom growth dimensions, (4) guidance_resonance inflation beyond neutral when no player guidance is active.
2. OUTPUT_FORMAT_SECTION includes an explicit T4 no-event constraint: when no SOCIAL EVENT CONTEXT section is present, absorption must be none.
3. PromptTemplate.system_prompt explicitly instructs the LLM to prefer conservative/baseline-matching outputs over enriched ones when input context is ambiguous.
4. The rendered user prompt for T1, T2, and T4 tick types all include the new constraint language (verified by test assertions on rendered prompt substrings).
5. A test file exists that programmatically asserts the presence of key constraint phrases in (a) OUTPUT_FORMAT_SECTION and (b) rendered prompts for each active tick type.
6. All existing tests in back/tests/ pass without modification (zero regressions).
7. No new fields or field name changes appear in the OUTPUT_FORMAT_SECTION JSON schema block.
8. The placeholder names in user_prompt_template remain unchanged.

## Proposed Review Focus
- Verify the negative examples are specific to observed deviation patterns (not generic 'be careful' language) — each should reference the concrete failure mode it addresses.
- Verify the prompt constraints do not accidentally prevent valid LLM enrichment (e.g., a legitimate deep absorption on a truly impactful headline should still be possible).
- Verify the T4 no-event constraint is clear and unambiguous — the LLM must understand that absence of the SOCIAL EVENT CONTEXT section means absorption=none.
- Check that no forbidden files were modified.
- Check that the test assertions are on meaningful constraint phrases, not trivially passing substrings.
- Verify all existing tests still pass.

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
