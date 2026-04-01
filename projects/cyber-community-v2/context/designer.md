# Designer Context

## Phase Transition Rule

When the current phase is closing or a next phase is being proposed,
Designer **must** read `roadmap.md` before proposing a phase transition.
Next-phase proposals must follow the approved roadmap sequence.
Designer may not invent new phases or skip ahead.

---

## Active Constraints

- 当前阶段不要再扩 runtime 能力
- 不要继续 patch T4 residual gate（T4 的唯一批准解冻路径是 Phase 26B，通过 social event）
- 不要重新引入 riskScore-only adversarial branch
- 不要让 Claude 做 phase/product 决策
- 不要把项目带偏到 chatbot / dashboard / 体验线
- 当前输出应服务于 orchestrator round workflow，而不是长篇总结
- Stage 1 期间，deferred tick（T3/T5/T6/T7/T8）的 bridge 扩展不由 Designer 自行决定

---

## Working Assumptions

- 当前 backbone 已是可工作的中间态，不再是纯概念验证
- T1/public continuity 已 active，T2/influencer continuity 已 active，T4/relational continuity 当前 inactive
- current T4 inactivity 的主因是 base builder 缺少 negative branch，不是 gate 细节问题
- Phase 25 continuity 状态已文档化（docs/phase25_continuity_status.md），contract 与 calibration artifacts 已区分
- 当前正处于 T4 冻结边界固化阶段（P25-T2）

---

## Architecture Snapshot

- 主流水线仍是 deterministic single-agent day runner
- 新链路已成立：deterministic tick → bridged appraisal → settlement substrate → residual persistence → next-day residual-aware bridge
- 当前 bridge coverage: T1 / T2 / T4
- 当前真实 continuity 覆盖：T1/T2 active，T4 inactive
- world carryover distribution 已做过一轮 long-horizon calibration，当前已不再只集中在 early window
- 状态文档已生成，为阶段收口提供材料

---

## Known Risks

- 容易误把 T4 问题继续当成 patch 问题处理（P25-T2 旨在明确冻结边界以防止此风险）
- 容易误把当前 continuity 描述得过宽，尤其误说 relational continuity 已成立
- 容易把下一阶段问题直接写成实现任务，而不是先收敛设计入口
- 容易让 task queue 变得过大，无法自然拆成 round

---

## Resolved Strategic Decisions

以下问题已由 roadmap.md 解决，不再是开放问题：

- Phase 25 closure 后，下一阶段是 Phase 26B（roadmap 已批准）
- T4 reopening 路径已确定：Phase 26B 通过 social event-aware activation，不是 gate tuning
- T4 relational continuity 在旧 deterministic path 下已标记为 frozen；26B 是唯一批准的解冻路径
- Stage 1 deferred ticks（T3/T5/T6/T7/T8）不由 Designer 决定是否扩展 bridge