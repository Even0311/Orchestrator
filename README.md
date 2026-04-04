# Agent Orchestrator

CLI 工具，将长期软件项目变成 **phase / round / artifact / human resolution** 工程流程。Orchestrator 管控状态机和治理层，Claude Code 负责设计、实现、评审。

## 架构

```
  Human (orch CLI)
       |
       v
  ORCHESTRATOR ──────────────── Hard Gates (7 gates)
  |  SOT Manager                  git_changes
  |  Round Engine                 protected_files
  |  Briefing Engine              allowed/forbidden
  |  Phase Planner                round_dir_boundary
       |                          sot_mutation
       | claude -p ... --agent    pytest
       | round-driver
       | --add-dir <attempt_dir>
       v
  CLAUDE CODE (target repo)
  |  Round Driver (sonnet)
  |    -> Designer  (opus)   -> task_contract.json
  |    -> Executor  (sonnet) -> code + tests + execution_evidence.json
  |    -> Reviewer  (sonnet) -> review_verdict.json
```

详细架构图和数据流见 [docs/architecture.md](docs/architecture.md)。

## 核心概念

- **Phase**: 来自 road_map.md 的阶段，包含 Goal / Scope / Task Queue
- **Round**: 一个 task 的单次执行尝试（最多 2 次 attempt）
- **Artifact**: Designer/Executor/Reviewer 三个 subagent 的结构化输出
- **Hard Gate**: Orchestrator 端的程序化验证，override Claude 的 review verdict
- **Escalation**: 2 次 attempt 都失败后，escalate 给人工决策

## 执行模型

Orchestrator 控制：
- 状态机（phase/round 生命周期）
- SOT 文件管理（vision, roadmap, phase, decisions）
- Hard gate 验证（pytest、文件边界、SOT 不可变性）
- Git 提交策略（双 repo commit）
- 人工介入流程（escalation / resolution）

Claude Code 负责：
- Task 设计（Designer, Opus）
- 代码实现 + 测试（Executor, Sonnet）
- 实现评审（Reviewer, Sonnet）

## SOT 目录结构

```
projects/<project_name>/
  vision.md                  # 项目目标、技术栈、约束
  road_map.md                # 阶段路线图（H2 per phase）
  current_phase.md           # 当前 phase：goal, scope, task queue
  decisions.md               # 追加式决策日志
  context/                   # 可选持久上下文
  P28/                       # phase 目录
    round-0028/
      attempt_1/
        round_brief.md       # orchestrator -> Claude
        task_contract.json   # designer 输出
        execution_evidence.json  # executor 输出
        review_verdict.json  # reviewer 输出
        attempt_report.json  # orchestrator 记录
      audit.md               # round 总结
  P29/
    round-0030/
      ...
```

## CLI 命令

| 命令 | 功能 |
|------|------|
| `orch new <name> --path <path>` | 创建新项目 |
| `orch list` | 列出所有项目 |
| `orch switch <name>` | 切换当前项目 |
| `orch set-path <name> <path>` | 更新目标代码库路径 |
| `orch set-test-cmd <name> <cmd>` | 设置 pytest 命令 |
| `orch config set/show` | 配置管理（model, email） |
| `orch run [--once]` | 运行自动化循环 |
| `orch status` | 查看项目状态 |
| `orch review` | 查看 escalated rounds |
| `orch decide "<note>" --action <action> [--all]` | 记录人工 resolution |
| `orch log [round-id]` | 查看 round 历史 |
| `orch rollback <round-id>` | 回退到指定 round |
| `orch phase next` | 生成下一 phase（Claude Opus 分解 task） |
| `orch phase approve` | 批准 draft phase，允许 orch run |
| `orch phase status` | 查看当前 phase 状态 |

## Resolution 机制

Round escalation 后，人工选择：

| Action | 效果 |
|--------|------|
| `reject_and_redo` | 作废当前 round，下次 run 开新 round |
| `accept_and_close` | 人工 override 接受，task 标记完成 |
| `resume_round` | 保留上下文 + 人工说明，继续重试 |

## 配置

`~/.orch/config.yaml`:

```yaml
agents:
  executor_model: sonnet       # round-driver/executor/reviewer
  designer_model: opus         # designer + phase planning
notification:
  email:
    smtp_host: smtp.gmail.com
    from_addr: you@email.com
    to_addr: you@email.com
```

## Hard Gates

| Gate | 检查内容 |
|------|---------|
| `git_changes` | Claude 必须产生 git 变更 |
| `target_protected_files` | CLAUDE.md, .claude/agents/** 不可修改 |
| `allowed_files` | 变更文件必须匹配 allowed glob |
| `forbidden_files` | 变更文件不得匹配 forbidden glob |
| `round_dir_boundary` | round 目录只允许 3 个 artifact 文件 |
| `sot_mutation` | SOT 文件（vision/roadmap/phase/decisions）不可变 |
| `pytest` | 项目测试套件必须通过 |

Hard gate verdict **覆盖** Claude reviewer 的判断。
