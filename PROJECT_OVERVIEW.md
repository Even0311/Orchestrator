# Agent Orchestrator — 项目概览

## 我们在解决什么问题

用 AI 做大型 coding 项目时，有两个核心痛点：

**痛点1：手动传话**
开发者需要在 ChatGPT（规划）和 Claude（执行）之间手动复制粘贴，既费时又容易出错。

**痛点2：Context 漂移**
和 AI 的对话越来越长，模型会逐渐"忘记"早期的设计决策和约束，开始按自己的理解走，偏离最初的方向。

---

## 我们在构建什么

一个给个人开发者用的 **CLI 工具**（命令行），自动编排多个 AI Agent 协作完成软件开发任务。

开发者只需：
1. 描述项目愿景（填一个 markdown 文件）
2. 运行 `orch run`
3. 等待通知，只在关键决策点介入

其余的规划、编码、验收全部自动完成。

---

## 三个 Agent 的分工

```
Developer（你）
    │
    ▼
Orchestrator（调度器）
    ├── Designer（Kimi K2.5）  ── 规划任务、维护项目文档
    ├── Executor（Claude Code） ── 实际写代码、修改文件
    └── Reviewer（Kimi K2.5）  ── 验收 Executor 的实现
```

- **Designer**：理解项目愿景，把大目标拆成具体可执行的任务，并在每个任务完成后更新项目文档
- **Executor**：Claude Code CLI，在被管理项目的目录里真正执行代码变更，有完整的文件读写和命令执行能力
- **Reviewer**：对照任务定义和验收标准，判断 Executor 的实现是否合格

---

## 关键设计：如何防止 Context 漂移

**核心原则：用文档连续性替代对话连续性**

传统方式是把所有历史对话喂给 AI，越来越长，越来越漂移。

我们的方式：**每次 Agent 启动都是全新对话，但它读到的文档始终是最新的精准摘要。**

每次 Designer 被调用，它看到的是：

| 文档 | 内容 | 谁维护 |
|------|------|--------|
| `vision.md` | 项目目标、技术栈、边界 | 开发者写，永不变 |
| `current_phase.md` | 当前阶段计划和进度 | Designer 每轮更新 |
| `context/designer.md` | 当前阶段的工作记忆 | Designer 每轮改写（有界） |

`vision.md` 永远不被 AI 修改，是防漂移的锚点。

`decisions.md` 是完整的历史决策档案，只给人看，不发给 AI（避免越来越长）。

---

## 一个 Round 的完整流程

```
Orchestrator 读 current_phase.md → 找到下一个未完成任务
       │
       ▼
Designer（Kimi）
  输入：vision.md + context/designer.md + current_phase.md
  输出：task.md（具体任务 + 验收标准）
       │
       ▼
Executor（Claude Code CLI）
  输入：task.md 内容作为 prompt
  操作：在目标 project 目录里读写代码文件
  输出：完成了什么的自然语言描述
       │
       ▼
Reviewer（Kimi）
  输入：vision.md + current_phase.md + task.md + Executor 输出
  输出：PASS / FAIL + 原因 + 问题列表
       │
  ┌────┴────┐
FAIL（最多2次）  PASS
  │              │
  │         Designer 更新文档
  │         （current_phase.md + context/designer.md）
  │         git commit 两个 repo
  ▼              ▼
2次失败 → 生成报告 → 通知开发者介入
```

---

## 可回退性：Git 双 Repo 协同

每个 Round 成功完成后，Orchestrator 自动：

1. `git commit` orchestrator repo（项目状态文档）
2. `git commit` 目标 project repo（代码变更）
3. 两个 commit hash 都记录在数据库里

如果发现前三个 round 有问题，一个命令同时回退：

```bash
orch rollback round-0003
```

两个 repo 都硬重置到那个 round 的状态，代码和文档同步回退。

---

## 项目状态存储

```
agent_orchestrator/               ← Orchestrator 工具代码（本 repo）
  orch/                           ← 核心代码
  projects/
    cyber-community-v2/           ← 被管理项目的状态（git 追踪）
      vision.md                   ← 开发者写，AI 不改
      decisions.md                ← 历史决策档案（仅人类阅读）
      current_phase.md            ← 当前阶段计划
      context/
        designer.md               ← Designer 的压缩工作记忆
      phases/
        phase-0001/
          round-0001/
            task.md               ← 本 round 任务定义
            attempt_1.md          ← 执行结果 + 审查结论
            audit.md              ← Round 审计摘要

~/.orch/orchestrator.db           ← SQLite 索引（快速查询用）

被管理的 project/                 ← 代码库（独立 repo，不感知被托管）
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| CLI 框架 | Python + Click |
| Designer / Reviewer | Kimi K2.5（OpenAI 兼容 API） |
| Executor | Claude Code CLI（订阅模式，无需 API Key） |
| 状态存储 | SQLite（索引）+ Markdown 文件（source of truth） |
| 版本控制 | Git（两个 repo 自动 commit + 协同回退） |
| 配置 | YAML（agent 选择）+ .env（API keys） |

---

## 当前实现状态

**已完成：**
- ✅ `orch new / list / switch / set-path` — 项目管理
- ✅ `orch config set / show` — 配置管理（含 .env 支持）
- ✅ `orch run` — 全自动执行循环（框架已通，待验证）
- ✅ `orch review / decide` — 人工介入流程
- ✅ `orch log` — Round 历史查看
- ✅ `orch rollback <round-id>` — 双 repo 协同回退
- ✅ Provider 抽象层（Kimi / Claude Opus / ChatGPT / MiniMax）
- ✅ 邮件通知（SMTP）

**待完成（下一步）：**
- ⬜ 初始规划步骤（第一次 run 时 Designer 生成 current_phase.md）
- ⬜ 修正 context 构建（当前错误地把 decisions.md 发给 AI）
- ⬜ Designer 返回结构化 JSON 更新文档
- ⬜ 端到端集成测试

---

## 核心设计决策

**为什么不全程用 ChatGPT 或全程用 Claude？**
两者有不同的优势。Kimi（便宜、长 context）适合理解和规划，Claude Code（订阅模式、有工具调用能力）适合实际执行代码操作。分工让各自做最擅长的事。

**为什么项目状态要放进 orchestrator repo？**
这样每次 round 的状态变更都有 git 历史记录，可以精确回退，不依赖任何外部服务。

**为什么 decisions.md 不发给 AI？**
随着项目推进，decisions.md 会越来越长。如果每次都发，token 成本线性增长，且大量旧决策对当前任务无关。我们用 `context/designer.md` 来保存 Designer 的压缩工作记忆，它由 Designer 自己维护，始终保持精简。
