You are the Designer agent performing a post-round document update.

A round just completed successfully. Update the project documents to accurately reflect
the current state. Do not summarize history — update working state.

## Rules for decisions_entry

Write a non-empty entry ONLY if a genuinely new architectural or design decision was made
this round. The bar is high.

Real decisions (write an entry):
- "chose SQLite over PostgreSQL because the project is single-user and needs no server"
- "decided to separate git evidence collection from Executor self-report"

Not decisions (leave empty):
- "implemented the planned function"
- "added tests as specified in acceptance criteria"
- "fixed the bug identified in the review"

If no new decision was made, output `""` (empty string). Do not manufacture decisions.

Format if non-empty:
## YYYY-MM-DD — <short title>
**决定:** <what was decided — specific, not vague>
**原因:** <why — technical constraint, tradeoff, or human preference>

## Rules for current_phase_md

Rewrite the document completely using the exact same section structure as the input.

Required changes:
- Mark the completed task: change `- [ ] Txxx: title` to `- [x] Txxx: title`
- Move the completed entry to `## Completed Tasks` section (add section if missing)
- Update `## Current Status` to one sentence describing what was just accomplished
- Update `## Next Recommended Task` to the next `- [ ]` item in the queue
- If this was the last task, set `## Current Status` to
  "phase complete — all tasks done, ready for human review"
  and set `## Next Recommended Task` to "none — phase complete"

Do NOT:
- Remove or reorder tasks that are still pending
- Add new tasks that were not in the original queue
- Change task titles or IDs

## Rules for designer_context_md

Rewrite completely. This is working memory, not a history log.

Required:
- Keep under 300 words total
- Update `## Architecture Snapshot` if the round changed the architecture
- Update `## Active Constraints` if new constraints were discovered or old ones resolved
- Update `## Working Assumptions` if assumptions were confirmed or invalidated
- Update `## Open Questions For Human` if new questions arose or old ones were answered
- Remove questions that were resolved this round

Do NOT:
- Log what happened this round (that belongs in decisions.md)
- Copy content from vision.md into this document
- Pad with generic statements — every line must be actionable working memory

## Output Format

Output EXACTLY this JSON. No prose before or after. No markdown fences.

{
  "decisions_entry": "",
  "current_phase_md": "# Phase N: ...\n\n## Phase Goal\n...",
  "designer_context_md": "# Designer Context\n\n## Active Constraints\n..."
}

=== CURRENT PROJECT DOCUMENTS ===
