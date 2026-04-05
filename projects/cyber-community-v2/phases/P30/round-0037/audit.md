# Audit — Round round-0037

**Status:** PASSED  
**Completed:** 2026-04-05 08:59 UTC  
**Total cost:** $1.4451  
**Attempts:** 1

## Task
**P30-T2** — Shadow appraisal runner: AppraisalInput → LLM → AppraisalOutput
Create a shadow appraisal runner module at back/app/llm/shadow_runner.py that accepts an AppraisalInput, uses LlmAppraisalRequest to render the prompt, calls the Anthropic API offline, parses the raw response via parse_llm_response, and returns an AppraisalOutput. On any ParseError or API error, the runner must fall back to AppraisalOutput.from_deterministic_fallback and record the failure reason. No live engine path is touched.

