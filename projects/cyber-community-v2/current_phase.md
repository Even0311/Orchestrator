# Current Phase

## Phase Goal

在不继续强推当前 deterministic backbone 不支持的能力前提下，完成当前 continuity 技术线的阶段收口，明确哪些能力已经成立、哪些能力应冻结、哪些问题应留给下一阶段设计处理。

本阶段不以扩展 runtime 能力为目标。  
本阶段的目标是：

- 准确确认当前 backbone continuity 的真实状态
- 固化当前已成立的 contract
- 冻结当前不应继续 patch 的路径
- 为下一阶段设计问题准备清晰入口

---

## In Scope

- 归纳当前 backbone continuity 状态
- 明确 T1 / T2 / T4 continuity 的当前判定
- 保留当前可工作的 T1/T2 residual continuity 路径
- 保留当前 world carryover calibration 结果
- 明确冻结当前 deterministic backbone 下的 T4 residual patching
- 收敛下一阶段真正该讨论的问题
- 生成适合 orchestrator round workflow 的阶段材料

---

## Out of Scope

- 不扩 bridge coverage 到 T3 / T5 / T6 / T7 / T8
- 不接入 live LLM appraisal
- 不进入 variable-tick orchestration
- 不再继续放宽 T1/T2 residual creation gate
- 不再尝试 T4 adversarial residual 分支
- 不通过人工负向分支强推 relational continuity
- 不做 background / APB / Warmth Buffer 主流水线接入
- 不做 MemoryResurface / rumination
- 不做前端 / 体验 / 视觉工作

---

## Task Queue

### P25-T2 — 固化 T4 冻结边界
明确记录当前 T4 relational residual activation 的冻结边界：
- strict negative T4 residual activation 在当前 deterministic backbone 下结构性不可达
- riskScore-only adversarial activation 已被否决
- 当前 T4 same-target carry path 结构上存在，但行为上不活跃

目标产物：
- freeze 边界写入当前 phase/context 材料
- 不涉及实现改动

Priority: High

---

### P25-T3 — 收敛下一阶段设计入口
定义下一阶段真正要讨论的问题，不再继续围绕“怎么 patch T4 residual gate”打转，而是转向：

- 什么样的 future deterministic/social input source 才足以合理地产生 negative T4 base signal？
- 这个问题应该在什么层次上设计，而不是现在就实现什么？

目标产物：
- 下一阶段设计入口问题集
- 不直接生成实现 spec

Priority: Medium

---

### P25-T4 — 清理为 orchestrator round-ready 的阶段材料
确保当前阶段文件适合结构化 round workflow：
- Task Queue 粒度适合拆 round
- 不混入过多历史流水账
- Current Status / Risks / Next Recommended Task 足够清晰
- 能让 orchestrator 直接挑出下一轮任务

目标产物：
- 稳定的 current_phase.md
- 稳定的 context/designer.md

Priority: High

---

## Completed Tasks

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
- [x] P25-T1 — 整理当前 continuity 状态结论：docs/phase25_continuity_status.md 已创建，明确分类 T1/T2 active、T4 inactive，60-day 审计数据（18 total, 12/6/0 split），区分 contract 与 calibration artifacts

---

## Current Status

P25-T1 已完成 — Phase 25 continuity 状态总结文档已创建并验证，准确分类 T1/T2 为 active、T4 为 inactive，区分 established contracts 与 calibration artifacts，为阶段收口提供基础材料。

---

## Risks / Blockers

### R1 — 容易误判 T4 问题为 gate 问题
当前 T4 不活，不是因为 gate 稍微再调一下就能开，而是因为 base builder 本身没有 negative 分支。  
如果误判为“再 patch 一点就行”，很容易重新走回不自然的 adversarial branch。

---

### R2 — continuity 目前仍明显由 T1/T2 主导
当前 residual continuity 已经成立，但主要来源仍是：
- public/world
- influencer

如果后续讨论不小心夸大，会误说成“整体 relational continuity 已成立”。

---

### R3 — 可能重新发散到大架构或体验线
当前阶段最重要的是收口和定边界。  
如果不控制，很容易重新跳去：
- multi-agent runtime 大发散
- live LLM appraisal 大发散
- 体验线/UI 讨论
这会让当前 phase 失焦。

---

### R4 — orchestrator 可能拿到过宽任务
如果 current_phase 里的任务写得太泛，Designer/Orchestrator 可能又生成“大而散”的 round，导致当前阶段重新扩张。

---

## Next Recommended Task

### P25-T2 — 固化 T4 冻结边界

这是当前最推荐的下一步，因为：

- P25-T1 已完成状态文档，现在需要明确记录 T4 的冻结边界
- 必须明确记录 strict negative T4 residual activation 在当前 deterministic backbone 下结构性不可达
- 防止后续 round 重新误把 T4 当成可 patch 目标

这一任务范围清晰，不涉及实现改动，只涉及边界文档化，适合作为 orchestrator 下一轮起点。