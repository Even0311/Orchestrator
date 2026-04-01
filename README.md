# Agent Orchestrator

个人开发者用的 **CLI 工具**，自动编排多个 AI Agent 协作完成软件开发任务。

开发者只需：
1. 描述项目愿景（填一个 `vision.md`）
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

- **Designer**：理解项目愿景，把大目标拆成具体可执行的任务，每个任务必须带二进制验收标准和对应的 `verification_steps`（可执行的 shell 命令）
- **Executor**：Claude Code CLI，在目标项目目录里真正执行代码变更
- **Reviewer**：基于 mechanical verification 结果 + git evidence + 自报告，判断任务是否通过

---

## 核心设计：用文档连续性替代对话连续性

传统方式是把所有历史对话喂给 AI，越来越长，越来越漂移。

我们的方式：**每次 Agent 启动都是全新对话，但它读到的文档始终是最新的精准摘要。**

| 文档 | 内容 | 谁维护 |
|------|------|--------|
| `vision.md` | 项目目标、技术栈、边界 | 开发者写，永不变 |
| `current_phase.md` | 当前阶段计划和进度 | Designer 每轮更新 |
| `context/designer.md` | 当前阶段的工作记忆 | Designer 每轮改写（有界） |
| `decisions.md` | 历史决策档案 | 仅人类阅读，不发给 AI |

`vision.md` 永远不被 AI 修改，是防漂移的锚点。

---

## 一个 Round 的完整流程

```
Orchestrator 读 current_phase.md → 找到下一个未完成任务
       │
       ▼
Designer（Kimi）
  输入：vision.md + context/designer.md + current_phase.md
  输出：task.md（任务定义 + 验收标准 + verification_steps）
       │
       ▼
CLAUDE.md 自动生成 → 注入目标项目，Claude Code 原生加载上下文
       │
       ▼
Executor（Claude Code CLI）
  输入：task.md 内容作为 prompt
  操作：在目标项目目录里读写代码文件
       │
       ▼
Evidence 收集（orchestrator 自动执行）
  ├── git status + git diff（含 untracked 文件 diff）
  └── Mechanical Verification：逐条运行 verification_steps
       │
       ▼
Reviewer（Kimi）
  输入：mechanical verification 结果 + git evidence + executor 自报告
  规则：verification_step 通过 → 对应标准达标，不用再读 diff 猜
  输出：PASS / FAIL + 原因
       │
  ┌────┴────┐
FAIL（最多2次）  PASS
  │              │
  │         Designer 更新文档
  │         git commit 两个 repo
  ▼              ▼
2次失败 → 生成报告 → 通知开发者介入
```

---

## Evidence 管道

Reviewer 的判断基于三层证据（权威性从高到低）：

1. **Mechanical Verification**（最高权威）：orchestrator 在 Executor 完成后自动运行 Designer 写的 `verification_steps`，每条命令 exit 0 = PASS，非零 = FAIL。客观、不可伪造。
2. **Git-Verified**：orchestrator 通过 `git status` + `git diff` 收集的文件变更证据，含 untracked 文件的完整 diff。
3. **Executor Self-Report**：Executor 自己声称做了什么。仅作补充参考。

这套管道解决了早期 Reviewer 的核心问题：LLM 阅读 diff 产生幻觉，导致正确完成的任务被误判为 FAIL。

---

## Git 双 Repo 协同回退

每个 Round 成功完成后，Orchestrator 自动：

1. `git commit` orchestrator repo（项目状态文档）
2. `git commit` 目标 project repo（代码变更）
3. 两个 commit hash 都记录在数据库里

回退一个命令搞定：

```bash
orch rollback round-0003
```

---

## CLI 命令

| 命令 | 功能 |
|------|------|
| `orch new` | 创建新项目 |
| `orch list` | 列出所有项目 |
| `orch switch` | 切换当前项目 |
| `orch set-path` | 设置目标代码库路径 |
| `orch config set/show` | 配置管理（含 .env 支持） |
| `orch run` | 全自动执行循环 |
| `orch status` | 查看当前状态 |
| `orch review` | 人工审查 |
| `orch decide` | 人工决策介入 |
| `orch log` | 查看 Round 历史 |
| `orch rollback <round-id>` | 双 repo 协同回退 |

---

## 项目状态存储

```
agent_orchestrator/                ← 本 repo（Orchestrator 工具代码）
  orch/
    agents/                        ← Designer / Executor / Reviewer
    engine/                        ← orchestrator 主循环 + round_runner
    prompts/                       ← Agent prompt 模板
    providers/                     ← LLM provider 抽象层
    utils/                         ← evidence_collector / verification_runner / claudemd_manager / git_ops
    cli/                           ← Click CLI
    config/                        ← 配置加载
    db/                            ← SQLite 索引
  projects/
    cyber-community-v2/            ← 被管理项目的状态（git 追踪）
      vision.md                    ← 开发者写，AI 不改
      decisions.md                 ← 历史决策档案（仅人类阅读）
      current_phase.md             ← 当前阶段计划
      context/
        designer.md                ← Designer 的压缩工作记忆
      phases/
        phase-NNNN/
          round-NNNN/
            task.md                ← 本 round 任务定义
            execution_report.json  ← git evidence + mechanical verification + 自报告
            review.json            ← Reviewer 判定

~/.orch/orchestrator.db            ← SQLite 索引（快速查询用）
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| CLI 框架 | Python + Click |
| Designer / Reviewer | Kimi K2.5（OpenAI 兼容 API） |
| Executor | Claude Code CLI（订阅模式） |
| 状态存储 | SQLite（索引）+ Markdown 文件（source of truth） |
| 版本控制 | Git（双 repo 自动 commit + 协同回退） |
| 配置 | YAML + .env |

---

## Setup

```bash
cd agent_orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

配置 `.env`：

```bash
KIMI_API_KEY=your-kimi-key
# 或其他 provider 的 key
```

---

## 设计决策

**为什么 Designer 和 Reviewer 用 Kimi，Executor 用 Claude Code？**
Kimi 便宜、长 context，适合理解和规划。Claude Code 有完整的文件读写和命令执行能力，适合实际写代码。分工让各自做最擅长的事。

**为什么项目状态放进 orchestrator repo？**
每次 round 的状态变更都有 git 历史，可以精确回退，不依赖外部服务。

**为什么 decisions.md 不发给 AI？**
它会越来越长，token 成本线性增长，且大量旧决策对当前任务无关。用 `context/designer.md` 保存压缩工作记忆，始终精简。

**为什么需要 Mechanical Verification？**
早期 Reviewer 靠 LLM 阅读 git diff 判断任务是否完成，多次产生幻觉（声称 diff 不存在），导致正确完成的任务被 FAIL。Mechanical verification 让 orchestrator 直接运行 shell 命令验证，结果客观不可伪造。
