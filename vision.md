# Agent Orchestrator — Vision

## 项目目标

构建一个给个人使用的 CLI 工具，用来全自动管理 AI 辅助的软件开发流程。

核心问题：开发者在使用 LLM 做大型项目时，需要在多个 AI 之间手动复制粘贴，同时随着对话变长，context 会发生漂移，早期的设计决策逐渐被稀释。

核心解法：用一个 Orchestrator 自动化 AI 之间的协作流程，并用结构化文档替代对话历史作为 Agent 的记忆载体，从根本上消除 context 漂移。

---

## 设计原则

**纯托管模式** — 被管理的项目只存储业务代码，完全不感知自己被托管。所有 Orchestrator 的状态和元数据存储在 Orchestrator 自身的目录里。

**文档连续性替代对话连续性** — Agent 每次启动不读历史对话，而是读结构化文档（vision、decisions、context 摘要）。文档大小可控，内容始终精准。

**最小人工介入** — 全自动运行，只在真正需要人判断时打断用户。

**完整可审计** — 每个 Round 的输入、输出、判断结果全部记录，任何时候可回溯。

---

## 核心概念

### 三个 Agent 角色

| 角色 | 职责 | 实现方式 |
|------|------|----------|
| **Designer** | 理解项目意图、规划 Phase、拆分任务、维护项目文档 | Anthropic API / OpenAI API / MiniMax API（可配置） |
| **Executor** | 执行具体编码任务，操作被管理项目的代码文件 | Claude Code CLI 子进程 |
| **Reviewer** | 验收 Executor 的输出，判断是否符合 Designer 的要求 | Anthropic API / OpenAI API / MiniMax API（可配置） |

### 层级结构

```
Project（项目）
  └── Phase（阶段，由 Designer 规划）
        └── Round（最小执行单元 = 一个子任务）
              ├── attempt_1
              ├── attempt_2（如需重试）
              └── audit.md
```

### Round 生命周期

```
Designer 定义任务
       ↓
Executor 执行（attempt 1）
       ↓
Reviewer 验收
  ├── 通过 → 更新项目文档 → Round 结束 ✓
  └── 不通过 → Executor 重试（attempt 2）
                    ↓
              Reviewer 再次验收
                ├── 通过 → 更新项目文档 → Round 结束 ✓
                └── 不通过 → 生成审计报告 → 通知用户介入
```

---

## 多项目支持

Orchestrator 可同时管理多个项目。每个项目在 Orchestrator 内有独立的状态目录。

```
orchestrator/
├── orchestrator.db              # SQLite：项目元数据、任务列表、会话索引
├── config.yaml                  # 全局配置（Agent 模型选择、API keys、通知）
└── projects/
    └── {project_id}/
        ├── vision.md            # 项目目标和边界（永远不变，Agent 的"宪法"）
        ├── decisions.md         # 关键决策记录（每次 Round 后由 Designer 更新）
        ├── current_phase.md     # 当前阶段目标和进度
        ├── context/
        │   ├── designer.md      # Designer 当前上下文摘要
        │   └── executor.md      # Executor 当前上下文摘要
        └── phases/
            └── {phase_id}/
                └── {round_id}/
                    ├── task.md       # Designer 定义的任务
                    ├── attempt_1.md  # Executor 输出 + Reviewer 判断
                    ├── attempt_2.md  # 如有重试
                    └── audit.md      # 最终审计摘要
```

被管理的项目代码库完全独立，Orchestrator 只记录其路径。项目路径存储在 SQLite 元数据中，可随时修改（例如跨机器迁移时）。

---

## Context 管理机制

**Agent 每次启动的上下文由以下文档构成：**

```
vision.md          ← 项目目标和边界，永远不变
decisions.md       ← 所有关键决策的积累
current_phase.md   ← 当前阶段目标
task.md            ← 当前 Round 的具体任务（仅 Executor）
```

**对话历史的处理：**
- 对话历史只用于提取信息，不传给下一次 Agent 调用
- 每个 Round 结束后，Orchestrator 触发 Designer 将本次 Round 的重要信息提炼写回文档
- 文档始终是压缩过的精准摘要，大小可控

---

## 可配置项

### 全局配置（config.yaml）

```yaml
agents:
  designer: opus          # opus | chatgpt | minimax
  reviewer: opus          # opus | chatgpt | minimax
  executor_model: sonnet  # sonnet | opus | haiku（Claude Code CLI --model 参数）

api_keys:
  # Executor（Claude Code CLI）使用订阅模式认证，无需 API key
  anthropic: sk-ant-...   # Designer/Reviewer 使用 Opus 时需要
  openai: sk-...          # Designer/Reviewer 使用 ChatGPT 时需要
  minimax: ...            # Designer/Reviewer 使用 MiniMax 时需要

notification:
  email:
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from: your@email.com
    to: your@email.com
```

### CLI 配置命令

```bash
orch config set designer chatgpt
orch config set reviewer opus
orch config set executor_model sonnet
```

---

## CLI 接口

### 项目管理
```bash
orch new <project-name> --path /path/to/codebase   # 创建项目，指定被管理的代码库目录
orch list                                           # 列出所有项目及状态
orch switch <project-name>                          # 切换当前活跃项目
orch set-path <project-name> /new/path             # 修改被管理项目的目录
```

### 执行控制
```bash
orch run                     # 全自动运行当前项目，直到需要人工介入才停
orch status                  # 查看当前项目状态
```

### 人工介入
```bash
orch review                  # 查看待处理的升级报告
orch decide                  # 输入决定，继续执行
```

### 审计查看
```bash
orch log                     # 查看 Round 历史
orch log <round-id>          # 查看某个 Round 的详细审计报告（Markdown）
```

### 全局配置
```bash
orch config set <key> <value>
orch config show
```

---

## Executor 容错机制

### Token 耗尽处理

Claude Code CLI 在订阅模式下有 token 用量限制，耗尽时会返回包含 reset 时间的错误。

处理流程：
```
Executor 返回 is_error: true（无论何种原因）
       ↓
计入 attempt 次数，Reviewer 判断
  ├── attempt 1 失败 → 重试
  └── attempt 2 失败 → 生成审计报告（含错误原因）→ 通知用户介入
```

**Token 耗尽时的审计报告** 会明确标注失败原因是 token 耗尽，用户收到通知后自行决定是否继续。

---

## 通知机制

- `orch run` 在后台全自动执行
- 需要人工介入时：终端打印醒目报告 + 发送邮件通知
- 触发人工介入的条件：
  - Reviewer 两次不通过
  - Designer 遇到方向性决策无法自行判断
  - 所有 Phase 完成（项目结束通知）

---

## 已有代码基础

本项目在 `agent_orchestrator` 已有代码基础上继续开发，不重写。

**保留并复用：**
- Round 生命周期状态机
- 确定性升级规则（escalation logic）
- Pydantic 数据模型（11个）
- 审计追踪机制（proposals、backups、decision log）
- 测试套件（13个测试文件）

**新增：**
- Claude Code CLI adapter（替换 manual_stub）
- Designer agent（主动规划角色，Anthropic / OpenAI / MiniMax）
- Reviewer agent API 集成
- LLM provider 抽象层（支持多 provider）
- `orch run` 全自动执行循环
- Context 管理（Round 结束后自动更新文档）
- 邮件通知
- 多项目管理（SQLite）

---

## 不做什么

- 不做 Web UI 或 Dashboard
- 不做多用户协作
- 不做云端同步
- 不做对被管理项目的任何侵入（项目无感知）
- 不做通用产品，只为个人使用优化
