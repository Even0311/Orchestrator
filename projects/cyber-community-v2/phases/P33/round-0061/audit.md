# Audit — Round round-0061

**Status:** PASSED  
**Completed:** 2026-04-10 03:14 UTC  
**Total cost:** $1.6576  
**Attempts:** 1

## Task
**P33-T2** — Tighten prompt schema and output-format instructions to reduce LLM deviation rate
Revise the prompt template (system_prompt, user_prompt_template, OUTPUT_FORMAT_SECTION) in back/app/llm/prompt_schema.py to close the specific deviation patterns observed in P33-T1 shadow run data — over-enrichment of absorption/valence/arousal, phantom growth dimensions, guidance_resonance inflation, and T4 zero-absorption override — then verify the tightened prompts by extending or creating a test that exercises the rendered prompt text against the known deviation categories.

