# Agent Orchestrator

个人开发者用的 **CLI 工具**，用于把一个长期软件项目变成有 `phase / round / artifact / human resolution` 的工程流程。

---

## 当前定位

Orchestrator 的核心不再是“外部多模型调度器”，而是：

- **项目状态机**
- **round 驱动器**
- **artifact 管理器**
- **治理与人工介入层**

模型协作正在逐步下沉到 Claude Code / repo 内 subagents。

---

## Repo-local 项目状态

项目 source of truth 现在以 **repo-local `.orch/`** 为目标形态：

```text
<target-repo>/
  .orch/
    vision.md
    roadmap.md
    current_phase.md
    decisions.md
    context/
      designer.md
    phases/
      phase-0001/
        round-0001/
          task.md
          execution_report_attempt_1.json
          review_attempt_1.json
          audit.md
    runtime/
      current_task.md
      recent_rounds.md
```

说明：

- `.orch/` 是 **项目状态层**，应该被提交到 target repo。
- `.orch/runtime/` 是 **临时运行时文件**，供 Claude Code 读，不应和 source of truth 混在一起。
- round 结束后，清理的只应是 `.orch/runtime/`，不是整个 `.orch/`。

SQLite 仍保留在 `~/.orch/orchestrator.db`，仅作索引和快速查询。

---

## Claude Code / Subagents

目标架构是：

- project state 在 target repo 内
- Claude Code 直接读 `.orch/`
- repo 内 `.claude/agents/` 保存项目级 subagents

预期角色：

```text
.claude/agents/
  designer.md
  executor.md
  reviewer.md
```

它们都是 **project-level**，不是用户全局 agent。

---

## Resolution 机制

当 round escalation 后，人工必须能做 3 种决定：

1. `reject_and_redo`
   - 当前 round 作废
   - 不接受结果
   - 下一次运行开 fresh replacement round

2. `accept_and_close`
   - 人工 override 接受当前 round
   - 当前 round 结束
   - 允许 phase 正常推进

3. `resume_round`
   - 保留当前 round 的上下文与人工说明
   - 继续运行后续 follow-up work

当前 CLI：

```bash
orch review
orch decide "<note>" --action reject_and_redo
orch decide "<note>" --action accept_and_close
orch decide "<note>" --action resume_round
```

每次 resolution 都会写入：

- DB 状态字段
- `current_phase.md` 中的 `## Human Resolution (...)`

---

## 当前执行模型

当前 round 仍由程序驱动：

1. 读取 `current_phase.md`
2. 生成 task
3. Executor 执行
4. Hard gate：pytest
5. Soft gate：Reviewer
6. PASS / escalate
7. 写回 artifacts 与文档

程序控制：

- 状态机
- 文件写回策略
- round 生命周期
- escalation / resolution
- artifact 落盘

LLM 负责：

- task proposal
- implementation
- review proposal
- document update proposal

---

## CLI 命令

| 命令 | 功能 |
|------|------|
| `orch new` | 创建新项目（repo-local `.orch/`） |
| `orch list` | 列出所有项目 |
| `orch switch` | 切换当前项目 |
| `orch set-path` | 更新目标代码库路径，并重建 repo-local state |
| `orch set-test-cmd` | 设置 hard gate pytest 命令 |
| `orch config set/show` | 配置管理 |
| `orch run` | 运行自动化循环 |
| `orch status` | 查看状态 |
| `orch review` | 查看 escalated round |
| `orch decide` | 记录人工 resolution |
| `orch log` | 查看 round 历史 |
| `orch rollback <round-id>` | 回退 |

---

## 说明

这个仓库目前处于架构迁移中：

- 从 orchestrator repo 内 `projects/` 状态，迁向 target repo 内 `.orch/`
- 从外部多 agent provider，迁向 Claude Code / repo 内 subagents

因此 README 只描述当前收敛方向，不宣称所有迁移已经完成。
