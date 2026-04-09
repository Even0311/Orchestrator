# Evaluator Contract Review — round-0057

**Task Key:** P32-T5
**Title:** Validate same-day T2/T4 composition in multi-day simulation

## Proposed Acceptance Criteria
1. A new test file exists in back/tests/ that validates same-day T2/T4 composition
2. At least one test runs a multi-day simulation (>= 3 days) with qualifying social events present
3. At least one test asserts that on a same-day T2+T4 collision, relationship trust and closeness are not double-counted (T2 bridge_mode suppresses relational writes, T4 handles them)
4. At least one test asserts that T2 residuals (ResidualKind.influencer) and T4 residuals (ResidualKind.relational) are created as distinct entries
5. At least one test asserts that residuals from day N appear in the carried_residuals on day N+1
6. At least one test asserts composition_audit_out records the T2/T4 collision when both target the same relationship
7. At least one test asserts no state value (trust, closeness, mood, stress, growth dimensions) exceeds its valid bounds after multi-day composition
8. All existing tests continue to pass: python -m pytest tests/ -v from back/
9. The new tests themselves pass: python -m pytest tests/test_p32_t5_*.py -v from back/

## Proposed Review Focus
- Verify that double-counting assertions are meaningful — they must actually detect the specific boundary where T2 bridge_mode suppresses relational writes and T4 settlement handles them
- Verify that multi-day residual carryover is tested with real simulate_day_bridged() calls chaining day-over-day, not mocked
- Verify that the test would actually fail if T2 started writing relational fields in non-bridge-mode (i.e., the double-counting check is not vacuous)
- Verify that qualifying social events are correctly constructed to trigger T4 activation (matching the patterns from round-0054/0055)
- Confirm no production code was modified

## Your Task
Review the proposed acceptance criteria and review focus above.
For each criterion, determine whether you can objectively verify it after code is written.

Write `contract_feedback.json` with:
- `can_evaluate` — list of criteria you can objectively verify
- `cannot_evaluate` — list of criteria that are too vague or subjective to verify
- `suggested_changes` — concrete rewrites for vague criteria
- `needs_revision` — true if the contract needs designer revision, false if all criteria are verifiable
