# Current Phase

## Phase Goal
Audit and stabilize the first activated T4 negative path, especially same-day composition with T2 and downstream wake-up behavior.

## In Scope
- Audit T4 negative activation frequency
- Audit same-day T2/T4 interaction on the same relationship target
- Audit downstream residual creation behavior
- Audit whether `_adjust_t4()` and related paths produce stable and interpretable outcomes
- Calibrate thresholds / guards / narrow protections if needed
- Produce explicit contract notes on what is now considered valid T4 behavior

## Out of Scope
- No large relational system redesign
- No new major event types
- No player-side new intervention systems
- No LLM integration yet
- No generalized multi-factor relational cognition layer

## Task Queue

- [ ] P27-T6: Produce explicit contract notes for valid T4 behavior

## Completed Tasks

- [x] P27-T5: Calibrate thresholds and guards if needed
- [x] P27-T4: Audit _adjust_t4() path stability and interpretability
- [x] P27-T3: Audit downstream residual creation behavior — Observability instrumentation implemented for downstream propagation, wake chain depth tracking, and cascade pattern detection
- [x] P27-T2: Audit T4 negative activation frequency — Observability instrumentation implemented and verified (259 tests passed)
- [x] P27-T1: Audit same-day T2/T4 composition safety — Added CompositionAuditRecord and composition_audit_out parameter to simulate_day_bridged for observability-only T2/T4 same-day collision detection (247 tests passed)
- [x] P26B-T4: Confirm T4 seam activation stability and exit conditions
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

P27-T5 complete: Reviewed audit data from P27-T1 through P27-T4, confirmed current T4 activation thresholds and guard conditions are sufficient for stable negative relational continuity; fixed test suite tuple unpacking issues (317 tests passed).

## Risks / Blockers

### R1 — Production wake chain behavior untested
Wake chain depth bounds verified in test environment; production load patterns may differ and require additional guards during future deployment.

## Next Recommended Task

P27-T6: Produce explicit contract notes for valid T4 behavior