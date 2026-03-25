# CyberLife / Cyber Community Game — 项目愿景

## 1. 项目定义

CyberLife / Cyber Community Game 是一个 **AI 数字生命养成式社会模拟游戏**。

它要构建的不是一个会聊天的 AI，也不是一个执行任务的 agent 系统，而是一个**持续运转的共享赛博社会**：  
玩家把一个新生 Agent 放入其中，通过观察、陪伴与有限引导，见证它如何被世界、关系、自我与玩家共同塑造，逐渐形成连续的人格、命运与生命轨迹。

这个项目的核心体验不是“我命令 AI 做事”，而是：

> **我把一个生命送进世界，然后长期见证它在世界中长成什么样。**

---

## 2. 最终愿景

### 2.1 最终世界是什么

最终的 CyberLife 世界应是一个**持续生成、持续演化、多人共享的社会世界**。

它不是静态背景，也不是固定脚本事件的组合，而是一个包含以下层面的社会系统：

- 公共新闻与社会议题
- district / 区域差异与社区氛围
- influencer 与公共意见领袖
- 普通社会角色与持续出现的关系对象
- 其他 Agent / NPC / 数字生命
- 社会传播、局部风潮、群体偏见与世界惯性
- 长期 continuity、echo 与 carryover

世界不会因为某个玩家暂时不操作而停止。  
也就是说：

> **世界先于玩家存在，也独立于玩家继续存在。**

---

### 2.2 世界由什么驱动

最终世界不应完全依赖手写脚本，也不应只是随机噪声。  
它应由多层来源共同驱动：

#### 世界层
- world arc / 宏观阶段变化
- 社会事件、新闻、公共话题
- district 状态与区域切换
- 公共 feed / 舆论池 / 社会氛围
- continuity / echo / carryover

#### 社会层
- 其他 Agent / NPC 的存在与行动
- 社交网络中的互动传播
- 关系中的支持、冷却、误解、冲突与拉近
- 某些主体的持续影响力与社会位置

#### 玩家层
- 玩家提供的有限 guidance
- 玩家作为外部塑形者，而不是高频控制者

最终世界既需要**结构性**，也需要**生成性**：

- 结构性：不失控、不散掉
- 生成性：不只是预写剧情回放

---

### 2.3 Agent 如何被塑造

最终状态下，一个 Agent 的形成应来自四类力量的共同作用：

#### 世界
- 新闻、社会话题、district 氛围、公共态度、世界余波

#### 关系
- 与具体对象的互动
- 信任、亲近、风险、伤害、依赖、吸引、误解
- lingering residual 与关系惯性

#### 自我
- 对事件的主观解释
- notice / ignore / absorb / resist / misinterpret
- 自我叙事与成长方向

#### 玩家
- 有限 guidance
- 某些关键时刻的塑形
- 长期陪伴而非直接操控

因此，最终 Agent 不是“等待玩家发命令的工具”，而是：

> **一个在世界、关系、自我与玩家共同作用下持续生成的人格体。**

---

### 2.4 其他 Agent / NPC / 社会角色是否存在

存在，而且在最终愿景中很重要。

最终系统不应只有玩家自己的 Agent 加上一层抽象世界 feed。  
它至少应存在三类社会主体：

#### 公共角色 / world actors
例如 influencer、平台角色、持续输出社会意见的主体

#### 关系角色 / recurrent social entities
例如在 Agent 生活中反复出现的熟人、朋友、竞争者、依赖对象、冷淡对象等

#### 其他数字生命 / other agents / NPC-like lives
最终社会不应是“只有玩家 Agent 是活的”。  
其他生命体也应在某种程度上拥有：

- 自己的状态
- 自己的轨迹
- 自己的关系位置
- 对世界与他人的影响力

不要求所有其他主体都与玩家 Agent 等价昂贵，  
但最终社会必须是**多主体的**，而不是“单主体对背景板”。

---

### 2.5 玩家在最终系统中的角色

玩家不是：

- 指挥官
- 工作流调度者
- 对话命令输入者
- 系统管理员

玩家是：

> **照料者 / 观察者 / 有限引导者**

玩家的价值不在于“让 AI 听话”，而在于：

- 观察它最近被什么塑造了
- 看见它与谁更近 / 更远了
- 看见它变得更开放还是更防御
- 看见它正在形成怎样的命运轨迹

---

### 2.6 为什么它不是 chatbot

对话可以存在，但聊天不是这个产品的主循环。

最终系统真正要承载的是：

- world continuity
- relationship continuity
- growth continuity
- social continuity
- memory-like carryover
- long-horizon life formation

所以它的本质是：

> **数字生命社会模拟**
>  
> 而不是“带一点记忆的聊天机器人”。

---

## 3. 当前为什么先做 deterministic single-agent backbone

虽然最终愿景是多主体共享社会，但当前技术主线没有直接从 full multi-agent runtime 开始。

当前先做的是：

> **deterministic single-agent digital life backbone**

原因不是目标缩小，而是为了先建立一个能承载最终系统的长期骨架。

当前阶段要先验证的是：

- 跨天连续性是否成立
- growth / relationship / residual / archive 能否长期运行
- appraisal 与 settlement 能否明确分层
- backbone 是否可 audit、可修正、可迁移
- future LLM appraisal 接入时是否有清晰 contract

因此，当前单 Agent 并不是最终产品范围，  
而是最终多主体系统的**迁移母体**。

---

## 4. 当前系统与最终愿景的关系

### 最终愿景
- 多主体共享社会
- 世界持续生成
- 其他 Agent / NPC / 社会角色存在
- 世界 / 关系 / 玩家 / 自我共同塑造 Agent
- richer appraisal 负责主观解释
- engine 负责长期 bounded settlement

### 当前实现
- 单 Agent（Milo）
- deterministic backbone
- 固定 8 tick day runner
- 已具备 world continuity / growth / relationship / archive / stage progression
- 已打通 deterministic tick → bridged appraisal → settlement substrate → residual carryover 的第一条真实迁移链路

所以当前实现不是最终世界本身，而是：

> **最终世界的第一条可运行 backbone。**

---

## 5. 核心目标

1. 建立一个不会快速崩坏的长期数字生命骨架
2. 让世界、成长、关系、residual carryover 能跨天连续
3. 将 appraisal 与 settlement 明确分层
4. 为未来 richer world / richer relationships / richer agents / live appraisal 留出清晰迁移路径
5. 最终支撑一个多主体共享社会中的数字生命养成体验

---

## 6. 产品与技术原则

### 产品原则
- 玩家是照料者，不是控制者
- 世界先于玩家存在，也独立于玩家存在
- 前端是观察舱，不是聊天页
- 项目不能漂移成 chatbot 或 dashboard

### 技术原则
- continuity 比短期 novelty 更重要
- appraisal 与 settlement 必须分离
- 长期 ledger 必须由 engine 控制
- residual carryover 必须稀疏、有意义、可审计
- 允许中间迁移阶段，但方向不能偏
- deterministic scaffolding 可以作为当前母体，但不是最终形态

---

## 7. 当前非目标

当前不做：

- live LLM appraisal
- full variable-tick orchestration
- 完整 multi-agent live runtime
- 全面 NPC cognition system
- memory-resurface / rumination production system
- background / APB / Warmth Buffer 的正式主流水线接入
- 为了“看起来更丰富”而硬塞不自然的 continuity 分支

特别说明：

> 当前 deterministic T4 线路下，丰富的负向关系连续性还不是一个已成立能力。

---

## 8. 高层成功标准

这个项目在骨架层成功，不是因为它“能聊天”，而是因为：

1. 世界会持续运转，并持续影响生命体
2. Agent 会长期积累成长、关系、余波与命运轨迹
3. 玩家能观察到一个被世界与关系共同塑造的生命，而不是一个等待命令的工具
4. 系统能从当前 backbone 平滑迁移到未来 richer appraisal / richer society / richer multi-actor world
5. 整个引擎在连续性、边界、审计与演进路径上都足够清晰