# Round Brief — round-0049 (attempt 1)

## Roadmap / Phase Context
## Ultimate Vision Reference
Long-term, CyberLife / Cyber Community should become:

a shared cyber society in which each player places one developing agent into a living world,
then influences that agent through care, timing, and limited guidance,
while the agent is continuously shaped by world events, relationships, memory, inner appraisal, and the player's presence.

The product should feel like:
- witnessing a life
- nurturing a becoming self
- observing social fate unfold
- participating through care, not control

It should not collapse into:
- chatbot
- dashboard
- task executor
- freeform roleplay shell
- pure simulation sandbox with no emotional product loop

---

## Usage Rules For Designer
When selecting the next phase:
- first read `vision.md`
- then read `roadmap.md`
- then read `current_phase.md`

Designer may:
- refine task sequencing within the approved current phase
- define rounds inside the active phase
- update current status and risks

Designer may not:
- skip forward to a later roadmap phase without explicit authorization
- merge multiple roadmap phases into one large phase
- invent a new strategic direction outside the roadmap
- broaden a phase beyond its approved scope in the name of completeness

If reality changes, revise `roadmap.md` explicitly.
Do not silently drift around it.

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
## 16. Phase 26B 交付验证记录（2026-04-02）


## 决策 16.1
**Phase 26B seam 已建立，但 world generator 当前不产生 qualifying social events，T4 实际激活率为 0。**

### 已确认
Phase 26B 完成后，人工启动服务验证：
- 前端/后端正常运行，T1/T2 continuity 行为未受影响
- T4 seam 代码已存在（`T4_QUALIFYING_EVENT_TYPES`、`_detect_qualifying_t4_social_event()`），测试全部通过
- 但 `world/generator.py` 不产生 `social_event`，`world.social_event` 在真实 simulation 中始终为 `None`
- T4 qualifying event 检测路径在真实运行中永远不会被触发

### 结论
Phase 26B 建立的是"seam"（接缝），不是"live activation"（真实激活）。  
T4 当前仍然在真实 simulation 中为 inactive，原因已从"结构上无 negative branch"变为"world generator 不提供 qualifying input"。

### Phase 27 必须处理
- 审计 T4 在真实 60-day simulation 中的实际激活频率（预期为 0）
- 明确 world generator 是否需要产生 qualifying social events，以及产生的时机和频率
- 在此之前，T4 relational continuity 仍未真正成立

---

## 17. 一句话总结
> 当前项目已经明确决定：以 deterministic single-agent backbone 作为最终多主体数字社会系统的迁移母体；以”LLM appraisal + engine settlement”作为长期方向；以 selective tick intake、结构化 appraisal signal、bounded settlement、cross-day residual carryover 作为基础 contract。
> 当前 T1/T2 continuity 已成立，cross-day persistence 已成立，world-side carryover 已完成第一轮长周期校准。
> T4 relational continuity 在旧 deterministic path 下 frozen；已批准 Phase 26B 通过 social event-aware activation 作为唯一解冻路径。
> Stage 1 appraisal schema 按 8 tick 设计，但 first live LLM authority 仅限 T1/T2/T4；deferred ticks 进入 live path 留给 Stage 2。

## Recent Rounds
Most recent rounds (do not redo completed work):
- **round-0048** [PASSED] — Run a multi-day simulation using the real world generator (not synthetic fixture
- **round-0047** [PASSED] — Write a test module that runs a multi-day simulation (3–5 days) with LLM apprais
- **round-0046** [PASSED] — Write a dedicated test module that feeds synthetic LLM-shaped AppraisalOutput va

## Instructions
1. The designer subagent should read this brief and produce a task_contract.json
2. The executor subagent should implement the task
3. The reviewer subagent should verify the implementation
4. Write all artifact files to the round directory (accessible via --add-dir)

## Artifact Files to Produce
- `task_contract.json` — designer's task definition
- `execution_evidence.json` — executor's self-report
- `review_verdict.json` — reviewer's verdict
