# Current Phase

## Phase Goal
Enable the first narrow, explicit, auditable event-aware T4 activation path.

## In Scope
- Activate `build_signal_from_t4_relationship_tick()` to read `world.social_event`
- Allow only a very narrow trigger shape
- Allow only a minimal negative relational output shape
- Rely on existing downstream gates to decide whether relational residual is created
- Verify that the seam can produce a real T4 negative path without broad architecture changes

## Out of Scope
- No live LLM
- No broad event taxonomy expansion
- No routing based on `social_event.target_id`
- No generator rewrite to actively produce rich social events
- No settlement/substrate redesign
- No bridge redesign
- No strong negative outputs
- No attempt to solve all relational realism problems in one phase

## Task Queue

- [ ] P26B-T4: Confirm T4 seam activation stability and exit conditions

## Completed Tasks

- [x] P26B-T3: Verify downstream gate observability and auditability
- [x] P26B-T2: Define and implement minimal negative relational output shape
- [x] P26B-T1: Implement narrow social event reading path in T4 builder
- [x] P25-T1 — 整理当前 continuity 状态结论：docs/phase25_continuity_status.md 已创建
- [x] P25-T2 — 固化 T4 冻结边界：docs/phase25_t4_freeze_boundary.md 已创建
- [x] P25-T3 — 对齐下一阶段入口与已批准 roadmap：docs/phase25_roadmap_alignment.md 已创建
- [x] P25-T4 — 清理为 orchestrator round-ready 的阶段材料
- deterministic MVP backbone 已建立
- deterministic backbone first-pass audit / stabilization 已完成
- AppraisalSignal v1 已冻结并实现
- Settlement Substrate v1 已完成
- Deterministic-to-Appraisal Bridge v1 已完成（T1 / T2 / T4）
- Residual Persistence Across Days 已完成
- Residual-Aware Bridging v1 已完成并修复 validation fallback 问题
- Phase 19 审计已证明系统最初为 dormant
- Phase 20 已完成 residual creation calibration，使 T1/T2 continuity 从 0 变为 sparse but active
- Phase 21 60-day audit 已证明早期时间分布前倾问题
- Phase 22 已完成 world carryover distribution calibration，使 residual continuity 不再只集中于 early window
- Phase 23 曾尝试 T4 relational residual activation，但宽松版本被否决
- Phase 23 patch 后已确认 strict T4 relational residual activation 重新回到 0
- Phase 24 audit 已确认：当前 deterministic T4 builder 结构上没有 negative base signal 分支
- Phase 25 status review support 已完成，已明确当前 backbone continuity 的成立边界

## Current Status

P26B-T3 complete. Downstream gate interactions audited; T4-generated AppraisalSignals confirmed stable and composable with existing T1/T2 gates. Full test suite at 219 passed / 0 failed.

## Risks / Blockers

### R1 — Scope creep beyond narrow activation
Risk of expanding T4 logic beyond the approved minimal social event path into broad relational modeling. Must constrain to narrow trigger shapes only.

### R2 — Final stability confirmation pending
P26B-T4 must confirm the entire activation seam remains stable under exit condition verification before Phase 26B closes.

### R3 — Confusing activation with full continuity
Phase 26B only establishes the activation seam; full T4 relational continuity remains future work. Avoid premature claims about relational continuity being "solved".

## Next Recommended Task

### P26B-T4: Confirm T4 seam activation stability and exit conditions

Final verification that the narrow T4 activation path meets all exit conditions: T4 can read qualifying social events, emit minimal negative relational signals, and demonstrate observable, auditable downstream behavior without architectural instability.