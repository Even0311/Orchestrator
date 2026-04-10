# Evaluator Code Review — round-0061

**Task Key:** P33-T2
**Title:** Tighten prompt schema and output-format instructions to reduce LLM deviation rate

## Acceptance Criteria
1. OUTPUT_FORMAT_SECTION in prompt_schema.py contains at least one explicit negative example per deviation pattern: (1) absorption over-enrichment, (2) valence drift from neutral, (3) phantom growth dimensions, (4) guidance_resonance inflation beyond neutral when no player guidance is active.
2. OUTPUT_FORMAT_SECTION includes an explicit T4 no-event constraint: when no SOCIAL EVENT CONTEXT section is present, absorption must be none.
3. PromptTemplate.system_prompt explicitly instructs the LLM to prefer conservative/baseline-matching outputs over enriched ones when input context is ambiguous.
4. The rendered user prompt for T1, T2, and T4 tick types all include the new constraint language (verified by test assertions on rendered prompt substrings).
5. A test file exists that programmatically asserts the presence of key constraint phrases in (a) OUTPUT_FORMAT_SECTION and (b) rendered prompts for each active tick type.
6. All existing tests in back/tests/ pass without modification (zero regressions).
7. No new fields or field name changes appear in the OUTPUT_FORMAT_SECTION JSON schema block.
8. The placeholder names in user_prompt_template remain unchanged.

## Review Focus
- Verify the negative examples are specific to observed deviation patterns (not generic 'be careful' language) — each should reference the concrete failure mode it addresses.
- Verify the prompt constraints do not accidentally prevent valid LLM enrichment (e.g., a legitimate deep absorption on a truly impactful headline should still be possible).
- Verify the T4 no-event constraint is clear and unambiguous — the LLM must understand that absence of the SOCIAL EVENT CONTEXT section means absorption=none.
- Check that no forbidden files were modified.
- Check that the test assertions are on meaningful constraint phrases, not trivially passing substrings.
- Verify all existing tests still pass.

## Code Changes (git diff)
```diff

diff --git a/back/app/llm/prompt_schema.py b/back/app/llm/prompt_schema.py
index ad49b35..01114c8 100644
--- a/back/app/llm/prompt_schema.py
+++ b/back/app/llm/prompt_schema.py
@@ -77,6 +77,17 @@ OUTPUT_FORMAT_SECTION = dedent("""\
     - growth list: max 3 entries, no duplicate dimension values.
     - relational block (required for T2 and T4): {"target_id": "<str>", "trust_shift": "<strong_increase | mild_increase | neutral | mild_decrease | strong_decrease>", "closeness_delta": <-2 to 2>, "risk_delta": <-10 to 10>}
     - Do not include any fields not listed above.
+
+    Deviation prevention rules (apply to all tick types):
+    - Absorption over-enrichment: Do not escalate absorption beyond "surface" unless the headline or event content explicitly warrants deep engagement. When context is ambiguous, default to "surface" or "none". Disallowed example: returning absorption=deep for a routine daily headline with no extraordinary content.
+    - Valence drift: Do not shift valence away from "neutral" unless the event content carries an explicit positive or negative emotional charge. Default to "neutral" when input signals are ambiguous or mixed. Disallowed example: returning valence=positive for a neutral informational headline.
+    - Phantom growth dimensions: Do not add growth dimensions that are not directly triggered by the event content. When no clear growth trigger exists in the provided context, return growth=[]. Disallowed example: adding curiosity or expression growth for a mundane social exchange with no learning or creative element.
+    - guidance_resonance inflation: Do not set guidance_resonance to "aligned" or "resisted" when no player guidance data is present in this prompt. When no player guidance is active, return guidance_resonance="neutral". Disallowed example: returning guidance_resonance=aligned in the absence of any player action.
+
+    Tick-type-specific constraints:
+    - T1 (information_exposure): Rarely produce absorption=deep. Reserve deep only when the headline content is extraordinary and directly contradicts the agent's established worldview. For ordinary headlines, default to absorption=surface or absorption=none.
+    - T2 (social_interaction): Absorption reflects influencer signal strength combined with relational trust. Default to absorption=surface unless the influencer opinion quote directly and forcefully challenges the agent's current beliefs.
+    - T4 (relationship_shift): When no social event data block is included in this prompt, absorption MUST be none, aftershock_days MUST be 0, and growth MUST be []. Do not generate any engagement signal for T4 without an explicit social event.
     ===END OUTPUT FORMAT===
 """)
 
@@ -103,7 +114,12 @@ class PromptTemplate(BaseModel):
             "You receive structured context about an agent's world and internal state "
             "at a specific simulation tick, and return a structured JSON appraisal. "
             "Your output must conform exactly to the spe
...(truncated)
```

## Your Task
1. Check each acceptance criterion against the actual code changes
2. Pay special attention to the review focus items
3. If existing test files were modified, examine whether the modifications are justified
4. Verify tests pass and no regressions were introduced

Write `review_verdict.json` with:
- `verdict` — PASS, FAIL, or REVISION_REQUIRED
- `confidence` — high, medium, or low
- `met_criteria` — list of criteria that passed
- `unmet_criteria` — list of criteria that failed
- `blocker_fixes` — must-fix issues (empty if PASS)
- `non_blocking_suggestions` — nice-to-have improvements
- `rationale` — explanation of verdict
