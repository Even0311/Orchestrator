# Designer Brief — round-0054

## Roadmap / Phase Context
## Phase 31 — First Live LLM Appraisal Integration
### Goal
Introduce the first controlled live LLM appraisal path into the agent loop.

### Why Now
At this point:
- deterministic backbone is established
- T4 event-aware seam exists
- relational appraisal has meaningful deterministic shape
- appraisal/settlement boundary is explicit
- LLM has passed offline/shadow validation

The system is ready for the first real LLM-assisted appraisal step.

### In Scope
- insert LLM into the appraisal seam only
- **first live authority is limited to T1 / T2 / T4 only** — deferred ticks (T3/T5/T6/T7/T8)
  remain on deterministic fallback even though the schema can represent them
- keep settlement / bookkeeping engine-authoritative
- preserve deterministic validation / fallback / guardrail path
- limit LLM responsibility to the approved appraisal contract
- audit resulting outputs and system stability

### Out of Scope
- no full agent autonomy explosion
- no replacement of simulation engine by the LLM
- no uncontrolled freeform memory/personality architecture expansion
- no multiplayer-scale live society rollout
- no granting live LLM authority to T3/T5/T6/T7/T8 (deferred to Stage 2)

### Exit Condition
- live LLM appraisal participates in the real loop for T1 / T2 / T4
- T3 / T5 / T6 / T7 / T8 remain on deterministic fallback
- engine remains authoritative for settlement
- outputs remain auditable
- fallback path remains functional
- the integration is stable enough to establish the first controlled live hybrid path
- Stage 1 closure is now pending only on the remaining T4 reality-closure gap

### Unlocks
- first controlled live hybrid path
- project has transitioned from pure deterministic baseline to controlled hybrid infrastructure:
  **LLM appraisal + engine settlement**
- safe entry into final Stage 1 closure work

---

## Phase 32 — T4 Reality Closure
### Goal
Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a
...(truncated)

## Current Phase: P32: T4 Reality Closure
**Phase ID:** P32
**Phase Goal:** Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a real, stage-closing relational contract.

**In Scope:**
- close the remaining T4 partial-unlock gap identified in the current repo status
- make the existing T4 event-aware path capable of completing the approved relational wake chain
- validate that T4 can progress beyond detection-only / negative-signal-only behavior
- verify that downstream relational residual creation becomes real and auditable
- verify that `_adjust_t4()` is no longer permanently dormant
- audit same-day T2/T4 composition and downstream wake behavior after closure
- produce explicit contract notes describing what Stage 1 now considers valid T4 relational continuity

**Out of Scope:**
- no deferred tick bridge or live-authority expansion for T3 / T5 / T6 / T7 / T8
- no broad social world redesign
- no rich new event taxonomy expansion
- no settlement / substrate redesign
- no bridge architecture rewrite
- no freeform memory / personality / identity-deepening work
- no uncontrolled broadening of LLM authority
- no rewriting Stage 1 into a richer Stage 2 system

## Recently Completed Tasks (same phase)
- P32-T1: Audit the current T4 path end-to-end in a live multi-day simulation — confirm actual activation rate is zero, identify every point where the path goes dormant, and document the exact chain of blockers preventing real T4 relational output — Round round-0048 — T4 End-to-End Audit: Confirm Zero Activation Rate and Docume

## Selected Task
**Task Key:** P32-T2
**Description:** Make the world generator produce qualifying social events at a controlled, low frequency so that the T4 event-aware detection path can actually trigger during real simulation runs

## Decisions Context (recent)
## 17. 一句话总结
> 当前项目已经明确决定：以 deterministic single-agent backbone 作为最终多主体数字社会系统的迁移母体；以”LLM appraisal + engine settlement”作为长期方向；以 selective tick intake、结构化 appraisal signal、bounded settlement、cross-day residual carryover 作为基础 contract。
> 当前 T1/T2 continuity 已成立，cross-day persistence 已成立，world-side carryover 已完成第一轮长周期校准。
> T4 relational continuity 在旧 deterministic path 下 frozen；已批准 Phase 26B 通过 social event-aware activation 作为唯一解冻路径。
> Stage 1 appraisal schema 按 8 tick 设计，但 first live LLM authority 仅限 T1/T2/T4；deferred ticks 进入 live path 留给 Stage 2。

## 18. Stage 2 顺序规则：先 appraisal discipline / memory contract / identity contract，再谈扩 live authority。


## 19. Deferred tick intake 规则：Stage 2 采用 selective expansion，不是 all-at-once breadth-first rollout。

## Recent Rounds
Most recent rounds (do not redo completed work):
- **round-0053** [REDO_CONSUMED] — Modify the world generator so that WorldSnapshot objects carry a non-None social
- **round-0052** [REDO_CONSUMED] — Attach SocialEventSpec instances with qualifying event types (confrontation or w
- **round-0051** [RESUME_CONSUMED] — Modify back/app/world/generator.py (and/or back/app/world/arcs.py) so that get_w

## Prior Round Failed — Issues to Address
The previous round for this task failed. Your new contract must address these issues:
## Evaluator Contract Feedback
The evaluator could not verify some criteria. Revise them:
- Cannot evaluate: 7 (partial): Criterion 7 only requires intra-process call-level determinism ('calling get_world_snapshot(d) twice returns identical objects'). Criteria 1-5 require stable *count* outcomes across independent pytest runs. If the generator seeds from entropy at startup rather than a fixed constant, counts will vary between test runs, making criteria 1-5 non-deterministically verifiable even if criterion 7 passes within a single run.
- Suggested change: criterion_7_rewrite

## Your Task
Produce a `task_contract.json` file with the following fields:
- `phase_id`, `task_key`, `title`, `objective`, `exact_scope`
- `constraints` — architectural constraints the executor must respect
- `forbidden_files` — glob patterns for files the executor must NOT touch
- `non_goals` — what is explicitly out of scope
- `acceptance_criteria` — each criterion must be objectively verifiable
- `review_focus` — what the evaluator should pay special attention to

Write the contract to tell the executor WHAT to do and WHAT NOT to touch,
not HOW to implement it. The executor decides implementation details.
