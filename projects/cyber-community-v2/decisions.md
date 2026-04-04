# CyberLife / Cyber Community Game — 决策文档

## 1. 文档目的

这份文档用于记录 CyberLife / Cyber Community Game 当前已经收敛下来的关键技术决策，避免后续讨论反复重开已经定过的问题，也防止项目目标发生偏移。

这份文档关注的是：

- 当前技术主线的方向性决策
- 已冻结的架构边界
- 当前阶段明确延后的内容
- 后续新窗口 / 新阶段必须继承的判断

这不是实现细节清单，也不是任务分解表。  
它记录的是“我们已经决定了什么，以及为什么这么决定”。

---

## 2. 产品定位决策

## 决策 2.1
**CyberLife 是 AI 数字生命养成式社会模拟游戏，不是 chatbot，不是 dashboard。**

### 已决定
项目的产品方向固定为：

- 玩家把一个新生 Agent 放入一个已经运转的共享社会
- 玩家通过观察与有限引导影响它
- 核心体验是见证它被世界、关系、自我与玩家共同塑造

### 明确排除
项目不是：

- chatbot
- agent dashboard
- task execution system
- orchestration panel
- 纯研究型 simulation lab
- 自由放任式 LLM 角色扮演循环

### 为什么这么决定
因为项目要构建的是：

> **数字生命的连续性与命运形成体验**

而不是：

- 命令式对话体验
- 工作流执行体验
- 控制台式 agent 管理体验

---

## 决策 2.2
**玩家是照料者，不是控制者。**

### 已决定
玩家不是直接操控 Agent 的命令输入者。  
玩家的作用是：

- 观察
- 理解
- 陪伴
- 有限 guidance

### 为什么这么决定
如果玩家成为高频控制者，系统很容易退化成：

- 对话产品
- 角色扮演产品
- agent 操作界面

这会破坏“生命被世界塑造”的核心体验。

---

## 决策 2.3
**前端定位为观察舱，不是聊天页。**

### 已决定
前端页面的本质是：

- 观察世界与 Agent 的窗口
- 展示连续状态、叙事与关系演化的界面

而不是聊天优先的命令面板。

### 为什么这么决定
前端形态会反过来塑造产品心智。  
如果前端从结构上变成 chat-first，很容易把整个项目带偏成 chatbot。

---

## 3. 技术主线决策

## 决策 3.1
**当前主线先做 deterministic single-agent backbone。**

### 已决定
当前技术阶段先建立：

> deterministic single-agent digital life backbone

而不是直接做：

- full multi-agent live runtime
- live LLM appraisal world
- full dynamic tick orchestration

### 为什么这么决定
当前最重要的问题不是“先做得像最终世界”，而是：

- 连续性是否成立
- ledger 是否可长期运行
- relationship / growth / residual 是否可积累
- appraisal 与 settlement 是否可分层
- backbone 是否可 audit、可修正、可迁移

所以当前单 Agent 并不是最终愿景缩小，而是：

> **最终系统的迁移母体。**

---

## 决策 3.2
**旧 deterministic engine 有价值，但不是最终形态。**

### 已决定
当前固定 8 tick deterministic runner 可以继续作为主流水线使用，但只作为迁移骨架，不作为最终架构。

### 当前 8 tick
- T1 public exposure
- T2 influencer reaction
- T3 self-initiated action
- T4 relationship interaction
- T5 emotional shift
- T6 learning/work
- T7 player influence
- T8 reflection

### 为什么这么决定
这个骨架已证明：

- 可运行
- 可审计
- 可 debug
- 可修正

但它不是最终动态社会世界的真实形态。  
最终系统不应被固定 8 tick 形式锁死。

---

## 4. 长期架构决策

## 决策 4.1
**最终长期架构采用“LLM appraisal + engine settlement”分层。**

### 已决定
长期架构中：

- **LLM 负责 tick appraisal（主观解释）**
- **Engine 负责 settlement / bookkeeping（长期记账）**

### LLM 负责
- 是否注意到 tick
- 是否吸收
- 吸收深度
- emotional / relational / motivational meaning
- guidance resonance
- 主观意义解释

### Engine 负责
- persistent bookkeeping
- bounded state updates
- relationship settlement
- growth settlement
- residual / aftershock
- stage eligibility
- continuity contract
- archive snapshot

### 为什么这么决定
因为项目最终需要 richer subjective interpretation，  
但同时必须保留：

- bounded arithmetic
- ledgers 的稳定性
- 可审计性
- 长期一致性

如果让 LLM 直接写核心 ledger，系统会失去边界。

---

## 决策 4.2
**LLM 不直接写最终 ledger 数值。**

### 已决定
LLM 未来只能输出结构化 appraisal signal，  
不能直接修改：

- growth ledger
- trust/closeness ledger
- residual ledger
- stage eligibility
- 其他长期状态数值

### 为什么这么决定
因为 ledger 是：

- 长期累积的
- 需要 bounded 的
- 需要可审计的
- 需要 engine 统一负责 arithmetic settlement 的

---

## 5. Tick intake 决策

## 决策 5.1
**最终 tick intake 采用 foreground / background / discard 三分法。**

### 已决定
不是所有 potential ticks 都进入完整 appraisal。

三分法如下：

#### Foreground
值得完整 appraisal、可能影响长期账本的 tick

#### Background
世界存在但今天不构成完整被经历事件的 tick，只走轻量路径

#### Discard
今天对 Milo 基本无关的 tick，不处理

### 为什么这么决定
如果所有 ticks 都直接进入重型 appraisal：

- 成本高
- 信号噪音大
- 可控性差
- 很难维持长期稳定

选择性 intake 更符合最终 production 方向。

---

## 决策 5.2
**all-ticks-to-LLM 模式只保留为实验模式。**

### 已决定
这个模式保留为：

- experimental
- calibration
- data-collection mode

但不作为长期默认生产模式。

### 为什么这么决定
它可以帮助做实验和收集边界数据，  
但不适合作为最终稳定架构。

---

## 6. AppraisalSignal / Settlement 决策

## 决策 6.1
**AppraisalSignal v1 已冻结。**

### 已决定
当前 AppraisalSignal v1 已收敛，不再继续开放式设计。

核心字段为：

- absorption
- valence
- arousal
- growth
- relational
- aftershock_days
- guidance_resonance

并已有严格 validation 规则。

### 为什么这么决定
因为它已经满足：

- 足够小
- 足够稳
- 有明确 consumer
- 不让 LLM 直接写数值
- 足以支撑 settlement substrate v1

---

## 决策 6.2
**Settlement Mapping v1 已定并实现。**

### 已决定
当前 settlement 的核心原则已固定：

- absorption 是全局 multiplier
- state 可 per tick 结算
- growth 不直接写 ledger，而写 growth buffer
- relationship 可 per tick 结算，但 bounded
- residual 由 foreground + aftershock 创建
- guidance_resonance 只影响 growth contribution

### 为什么这么决定
这样可以实现：

- 主观解释与长期记账分层
- bounded settlement
- growth / relationship / residual 的可持续积累
- 跨天 continuity 的最小可运行版本

---

## 7. 迁移路径决策

## 决策 7.1
**迁移不是一次性切换，而是分阶段并行。**

### 已决定
当前采用的是：

> **旧 deterministic 主流水线 + 新 appraisal/substrate 并行接入**

而不是一次性重写整个 engine。

### 已完成的迁移阶段
- Phase 15 — Settlement Substrate v1
- Phase 16 — Deterministic-to-Appraisal Bridge v1
- Phase 17 — Residual Persistence Across Days

### 为什么这么决定
因为这种路径：

- 更容易审计
- 更容易 debug
- 更容易比较前后行为
- 更适合逐步迁移，不会一次性失去控制

---

## 决策 7.2
**当前 bridge 只接 T1 / T2 / T4。**

### 已决定
当前 deterministic-to-appraisal bridge 只覆盖：

- T1 world signal
- T2 influencer reaction
- T4 relationship interaction

### 尚未接入
- T3
- T5
- T6
- T7
- T8

### 为什么这么决定
要先用少量高价值 tick 打通：

> deterministic tick → bridged appraisal → settlement → residual carryover

而不是一开始就横向扩太宽。

---

## 8. Residual continuity 决策

## 决策 8.1
**Residual Persistence Across Days 已正式成立。**

### 已决定
ResidualEntry 已进入 domain 层，  
pending_residuals 已进入 DaySnapshot，  
residual 可以跨天保存、加载、衰减、过期。

### 当前语义
- Day N 创建
- Day N 不做 daily effect
- Day N+1 开始第一次 daily step
- 逐日衰减，归零删除

### 为什么这么决定
因为 residual 必须从“日内临时物”提升为“跨天余波”，  
否则 continuity 无法真正建立。

---

## 决策 8.2
**Residual-Aware Bridging v1 已成立。**

### 已决定
carried residual 已经可以轻量影响 next-day bridged appraisal mapping。

当前覆盖：

- T1
- T2
- T4

当前原则：

- 先 build base signal
- 再做 bounded residual adjustment
- adjustment 是 optional / sparse / one-step bounded
- validation fail fallback 到 unchanged base

### 为什么这么决定
因为要让 residual 不只是被存起来，  
而是能进入 next-day subjective interpretation。

---

## 决策 8.3
**Residual continuity 当前以 T1/T2 为主，T4 暂不成立。**

### 当前状态
- T1/public residual continuity：active
- T2/influencer residual continuity：active
- T4/relational residual continuity：inactive

### 为什么
不是因为 T4 selection/adjustment 没接好，  
而是因为当前 deterministic T4 builder **结构上没有负向 base signal 分支**。

strict negative relational residual gate 在当前 backbone 下不可达。

### 结论
当前不要继续通过补丁硬开 T4 negative carry。

---

## 9. World carryover 决策

## 决策 9.1
**world-side carryover distribution 已做一次正式校准。**

### 已决定
在 world continuity 侧加入 district continuity bonus：

- same district: +20
- adjacent district: +10

以减少 carryover 只集中于 early arc window 的问题。

### 为什么这么决定
60-day audit 已证明：

- residual inactivity 的主要原因之一是 world carryover 分布过度前倾
- 不是单纯 residual gate 太严

所以先修 world-side stimulus distribution，  
而不是不断放宽 bridge-side creation gate。

---

## 决策 9.2
**当前 world carryover 是“分布改善了，但仍有前倾”。**

### 当前判断
long-horizon carryover 已不再完全只在前段存在，  
但仍然不是均匀分布。

因此当前状态最适合描述为：

> **partially active**

而不是“完全理想”。

---

## 10. T4 relational continuity 决策

## 决策 10.1
**不接受 riskScore-only adversarial residual creation。**

### 已发生
曾尝试过一个版本：

- 通过 riskScore >= 65 加一个 adversarial T4 分支
- 产生大量 relational residual

### 结果
- relational residual 创建过多
- same-target carry 真正被 next-day T4 使用的次数极少
- 行为形状不对

### 已决定
这个方向不接受，不作为当前主线。

---

## 决策 10.2
**当前冻结 T4 relational residual activation。**

### 已决定
当前不继续 patch T4 gate，不继续人为制造负向分支。

### 为什么这么决定
Phase 24 audit 已证明：

- 当前 T4 base signal 长跑下始终是正向模式
- strict negative relational residual 条件结构性不可达
- 继续 patch 只会重新走回不自然的人工分支

### 当前结论
> T4 relational continuity 不是当前阶段要硬解的问题。  
> 它应 defer 到未来更丰富的 social event source 或 live appraisal source 出现之后再重开。

---

## 11. 当前冻结与延期内容

## 冻结（当前不继续推进）
- T4 strict negative relational residual activation
- riskScore-only adversarial T4 branch
- 通过补丁强行制造 relational continuity

## 延期（deferred）
- live LLM appraisal
- full variable-tick orchestration
- bridge T3/T5/T6/T7/T8
- background/APB/Warmth Buffer 正式接入
- MemoryResurface / rumination / memory weight
- richer social negative event generation
- full multi-agent live runtime
- NPC cognition system

---

## 12. 当前阶段判断

## 决策 12.1
**当前 backbone 已可视为一个可工作的中间态。**

### 原因
因为它已经证明：

- deterministic backbone 可跑、可审计、可修正
- T1/T2 residual continuity 已成立
- cross-day residual persistence 已成立
- residual-aware bridge 已真实激活
- world carryover distribution 已从“早期 burst”修到“长周期稀疏分布”

### 同时也已明确
- T4 relational continuity 当前未成立
- 其未成立原因已经查清
- 不应继续硬推

---

## 13. 后续讨论的边界

后续新窗口或新阶段必须遵守以下边界：

1. 不要重新把项目带回 chatbot / dashboard
2. 不要重新打开已经冻结的问题
3. 不要让 Claude Code 做设计决策
4. 不要把当前单 Agent backbone 误认为最终世界范围
5. 不要把 T4 relational continuity 误说成“已经成立”
6. 不要通过人造 adversarial branch 去伪造当前 backbone 不支持的能力
7. 当前若要继续推进，应优先做：
   - 阶段收口
   - contract freeze
   - 或未来 richer T4 negative social input source 的设计收敛
而不是继续在当前 T4 gate 上打补丁

---

## 14. Phase 26A/26B 决策

## 决策 14.1
**Phase 26A 已完成，建立了 SocialEventSpec inert schema seam。**

### 已决定
SocialEventSpec schema 已存在并挂载到 ArcPhase / WorldSnapshot。
当前为 schema-only、behaviorally inert。这是 26B 的基础。

### 为什么这么决定
T4 relational continuity 的解冻需要一个事件输入源。
先建 schema 再激活行为，符合项目"先建 contract 再激活能力"的原则。

---

## 决策 14.2
**Phase 26B 已批准为 T4 的唯一解冻路径：minimal event-aware activation。**

### 已决定
T4 的旧 deterministic path 仍然 frozen。
26B 通过让 T4 builder 读取 social event 来建立一条窄的、可审计的负向 relational activation path。
这是 roadmap 批准的唯一 T4 解冻方式。

### 为什么这么决定
旧 T4 freeze 的根因是 base builder 缺少 negative branch（结构问题，不是 gate 问题）。
通过 social event 提供 negative input source，而不是继续调 gate 或制造 adversarial branch。

---

## 15. Stage 1 Deferred-Tick 决策

## 决策 15.1
**Stage 1 bridge/appraisal-seam 范围限定为 T1/T2/T4。**

### 已决定
T3/T5/T6/T7/T8 的 deterministic bridge 扩展在 Stage 1 期间 deferred。
Designer 不可自行提议 deferred tick 的 bridge 工作。

### 为什么这么决定
Stage 1 的目标是安全引入 LLM appraisal，不是横向扩展 bridge coverage。
3 个 tick（世界/社交/关系）已足够提取有意义的 appraisal seam。

---

## 决策 15.2
**Appraisal schema 宽、live authority 窄（"B for schema, A for live authority"）。**

### 已决定
- Phase 29：appraisal input schema 按 8 tick 设计，容纳所有 tick 类型
- Phase 31：first live LLM appraisal authority 仅限 T1/T2/T4
- T3/T5/T6/T7/T8 可被 schema 表示，但在 Stage 1 内不具备 live authoritative coverage
- 是否进入 live path 留给 Stage 2 决策

### 为什么这么决定
Schema 宽避免未来返工，authority 窄避免失控。
先在 3 个已验证的 tick 上证明 LLM appraisal 安全，再考虑扩展。

---

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

