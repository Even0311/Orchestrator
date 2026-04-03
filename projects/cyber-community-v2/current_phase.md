# P28: Deterministic Relational Appraisal Expansion

## Phase Goal
Expand deterministic relational appraisal coverage beyond the single minimal activation slice, while preserving auditability.

## In Scope
- carefully expand event-aware relational appraisal conditions
- allow more than one narrow approved event-to-relational interpretation path
- improve deterministic expressiveness of T4 without abandoning controllability
- make relational appraisal output shapes slightly more representative of actual social friction / trust change patterns
- keep all behavior explainable and inspectable

## Out of Scope
- no freeform natural-language appraisal
- no live LLM runtime
- no relationship graph redesign
- no social world simulation explosion
- no attempt to model full human social complexity

## Task Queue
- [ ] P28-T5: Audit same-day composition safety between T2 and expanded T4 coverage
- [ ] P28-T6: Calibrate signal intensity ranges for new relational appraisal output shapes

## Completed Tasks
- [x] P28-T4: Add comprehensive test coverage for new T4 interpretation paths and edge cases — Implemented 40 comprehensive tests for Pattern A and Pattern B covering signal intensity bounds, boundary activation thresholds, and null/malformed input edge cases (441 total tests passed)
- [x] P28-T3: Extend T4 behavior contract documentation to specify valid ranges for new expanded coverage — Extended docs/t4_negative_behavior_contract.md with explicit numerical bounds for Pattern A (Contested Endorsement) and Pattern B (High-Intensity Unilateral Disclosure), plus 15 new contract validation tests (401 total tests passed)
- [x] P28-T2: Implement expanded event condition branches in T4 builder for approved new interpretation paths — Implemented Pattern A (Contested Endorsement) and Pattern B (High-Intensity Unilateral Disclosure) branches in tick_bridge.py with 26 new validation tests (386 total tests passed)
- [x] P28-T1: Identify and catalog additional social event-to-relational impact mapping patterns beyond current single narrow path — Cataloged 2 new T4 relational impact patterns (Contested Endorsement, High-Intensity Unilateral Disclosure) in docs/p28_t4_pattern_catalog.md with 22 validation tests (360 total tests passed)
- [x] P27-T6: Produce explicit contract notes for valid T4 behavior — Created docs/t4_negative_behavior_contract.md and 21 contract-verification tests (338 total tests passed)
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
Added comprehensive test coverage for expanded T4 deterministic relational appraisal paths (Pattern A and Pattern B), including boundary conditions, invalid inputs, and edge cases (441 total tests passed)

## Risks / Blockers
- Composition complexity: Expanded T4 coverage increases the state space of potential same-day T2/T4 interactions requiring audit
- Signal calibration risk: New output intensity ranges must be bounded to prevent downstream settlement instability

## Next Recommended Task
P28-T5: Audit same-day composition safety between T2 and expanded T4 coverage