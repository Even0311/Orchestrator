# Designer Context

## Active Constraints

- 当前阶段不要再扩 runtime 能力
- 不要继续 patch T4 residual gate
- 不要重新引入 riskScore-only adversarial branch
- 不要让 Claude 做 phase/product 决策
- 不要把项目带偏到 chatbot / dashboard / 体验线
- 当前输出应服务于 orchestrator round workflow，而不是长篇总结

---

## Working Assumptions

- 当前 backbone 已是可工作的中间态，不再是纯概念验证
- T1/public continuity 已 active
- T2/influencer continuity 已 active
- T4/relational continuity 当前 inactive
- current T4 inactivity 的主因是 base builder 缺少 negative branch，不是 gate 细节问题
- 当前更需要阶段收口与边界固化，而不是继续写实现 patch

---

## Architecture Snapshot

- 主流水线仍是 deterministic single-agent day runner
- 新链路已成立：deterministic tick → bridged appraisal → settlement substrate → residual persistence → next-day residual-aware bridge
- 当前 bridge coverage: T1 / T2 / T4
- 当前真实 continuity 覆盖：T1/T2 active，T4 inactive
- world carryover distribution 已做过一轮 long-horizon calibration，当前已不再只集中在 early window

---

## Known Risks

- 容易误把 T4 问题继续当成 patch 问题处理
- 容易误把当前 continuity 描述得过宽，尤其误说 relational continuity 已成立
- 容易把下一阶段问题直接写成实现任务，而不是先收敛设计入口
- 容易让 task queue 变得过大，无法自然拆成 round

---

## Open Questions For Human

- 下一阶段是先做正式阶段总结 / contract freeze，还是直接进入 future T4 negative social input source 的设计收敛？
- 如果要重开 T4 negative path，是否先限定为“输入源设计问题”，而不是“residual gate 设计问题”？
- 当前是否把 T4 relational continuity 明确标记为 deferred，而不是继续保留为 active candidate？