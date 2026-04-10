# Agent Orchestrator

CLI 工具，将长期软件项目变成 **phase / round / artifact / human resolution** 工程流程。Orchestrator 管控状态机和治理层，通过独立冷启动的 Claude CLI session 执行设计、实现、评审。

## 架构

```
  Human (orch CLI)
       |
       v
  ORCHESTRATOR (Python, 确定性) ──── Hard Gates
  |  SOT Manager                       git_changes
  |  Round Engine                      protected_files
  |  Briefing Engine (per-role)        forbidden_files
  |  Phase Planner                     round_dir_boundary
       |                               sot_mutation
       | 独立冷启动 Claude CLI          pytest
       | (每个agent独立session)
       v
  Claude CLI #1 (Designer/Opus)    → task_contract.json
  Claude CLI #2 (Evaluator/Sonnet) → contract_feedback.json
  Claude CLI #3 (Executor/Sonnet)  → code + execution_evidence.json
  Claude CLI #4 (Evaluator/Sonnet) → review_verdict.json
```

**关键设计决策：** 每个agent是独立的Claude CLI冷启动session，context完全隔离，只通过文件通信。
这遵循 Anthropic harness 文章的核心原则：生成与评估必须 context 隔离，防止自评偏差。

详细架构图和数据流见 [docs/architecture.md](docs/architecture.md)。

## 核心概念

- **Phase**: 来自 road_map.md 的阶段，包含 Goal / Scope / Task Queue
- **Round**: 一个 task 的单次执行尝试（最多 2 次 attempt）
- **Contract**: Designer 和 Evaluator 协商的任务合约（what + 边界 + 验证标准）
- **Hard Gate**: Orchestrator 端的确定性验证，override Claude 的 review verdict
- **Escalation**: 2 次 attempt 都失败后，escalate 给人工决策

## Round 执行流程

```
Step 1:  Designer (cold CLI)     → task_contract.json (含 acceptance_criteria + review_focus)
Step 2:  Evaluator contract      → contract_feedback.json (criteria 能否客观验证)
Step 3:  Designer revision       → final task_contract.json (如需修改)
Step 4:  Hard gate               → forbidden_files 合理性检查
Step 5:  Snapshot SOT + baseline commit
Step 6:  Executor (cold CLI)     → 代码变更 + execution_evidence.json
Step 7:  Hard gates              → SOT mutation, protected files, forbidden files, pytest
Step 8:  Evaluator review (cold CLI) → review_verdict.json (仅在 hard gate 通过后)
Step 9:  Adjudicate              → hard gate 结果 + evaluator verdict
Step 10: 通过 → commit / 不通过 → 问题回到 Step 1 的 designer
```

## Contract 格式

Contract 不告诉 executor 怎么做，只告诉它做什么、不能碰什么、怎么算成功：

```json
{
  "task_key": "P32-T2",
  "objective": "...",
  "exact_scope": "...",
  "constraints": ["..."],
  "forbidden_files": ["back/app/domain/appraisal_output.py"],
  "non_goals": ["..."],
  "acceptance_criteria": ["每条都是可检验的"],
  "review_focus": ["evaluator 重点关注事项"]
}
```

**设计原则：**
- 确定性边界用 hard gate（SOT mutation、protected files）
- 需要判断力的边界交给 evaluator（如"旧测试被修改是否合理"）
- 没有 `allowed_files` — executor 在 forbidden_files 之外自由发挥

## Agent Context 隔离

| Agent | 读到的 | 不读的 |
|-------|--------|--------|
| Designer | vision, roadmap, phase, decisions, 上轮问题 | executor 代码、evaluator 推理 |
| Evaluator(合约) | acceptance_criteria, review_focus | vision/roadmap/designer 推理 |
| Executor | task_contract, 源代码 | designer 推理、evaluator 反馈 |
| Evaluator(代码) | git diff, acceptance_criteria, review_focus | executor 思考、designer 推理 |

## SOT 目录结构

```
projects/<project_name>/
  vision.md                  # 项目目标、技术栈、约束 (target repo 的 vision)
  road_map.md                # 阶段路线图
  current_phase.md           # 当前 phase：goal, scope, task queue
  decisions.md               # 追加式决策日志
  context/                   # 可选持久上下文
  phases/
    P28/
      round-0028/
        attempt_1/
          designer_brief.md            # orchestrator → designer
          executor_brief.md            # orchestrator → executor
          evaluator_contract_brief.md  # orchestrator → evaluator (合约审查)
          evaluator_review_brief.md    # orchestrator → evaluator (代码审查)
          task_contract.json           # designer 输出
          contract_feedback.json       # evaluator 合约反馈
          execution_evidence.json      # executor 输出
          review_verdict.json          # evaluator 代码审查输出
          attempt_report.json          # orchestrator 记录
        audit.md                       # round 总结
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

## Hard Gates

| Gate | 检查内容 |
|------|---------|
| `git_changes` | Claude 必须产生 git 变更 |
| `target_protected_files` | CLAUDE.md, .claude/agents/** 不可修改 |
| `forbidden_files` | 变更文件不得匹配 forbidden glob |
| `round_dir_boundary` | round 目录只允许指定 artifact 文件 |
| `sot_mutation` | SOT 文件（vision/roadmap/phase/decisions）不可变 |
| `pytest` | 项目测试套件必须通过 |

Hard gate 在 evaluator 之前运行，不通过则直接 FAIL，不浪费 token 跑 evaluator。

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
  executor_model: sonnet       # executor/evaluator
  designer_model: opus         # designer + phase planning
notification:
  email:
    smtp_host: smtp.gmail.com
    from_addr: you@email.com
    to_addr: you@email.com
```
