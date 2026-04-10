# Plan: Orchestrator改造 — 从共享context sub-agent到独立冷启动

## Context

当前orchestrator在每个round中启动一个Claude CLI session，用`--agent round-driver`，round-driver在同一session内spawn三个sub-agent（designer、executor、reviewer）。三个agent共享round-driver的context，导致：
- Evaluator倾向于认同executor刚写的代码（自评偏差）
- Designer的推理过程污染executor的实现
- 违反Anthropic harness文章的核心原则：生成与评估必须context隔离

目标：改为orchestrator（Python脚本）直接启动3+次独立的Claude CLI，每次冷启动、context完全隔离，通过文件通信。

## 决策：修改现有代码，不重写

现有SOT管理、hard gates、证据收集、git操作、CLI、数据库、数据模型全部可复用（约80%代码量）。只需改造调用层。

---

## Contract格式

Contract分两部分——Planner给的 + Planner与Evaluator协商后加的：

**Planner定义（What + Why + 边界）：**
- `objective` — 做什么，为什么做
- `exact_scope` — 具体要实现什么
- `constraints` — 架构约束（如"AppraisalSignal v1 is frozen"）
- `forbidden_files` — 不能动的模块（粗粒度目录/glob）
- `non_goals` — 明确不做什么

**Planner与Evaluator协商后加的（怎么判断成功）：**
- `acceptance_criteria` — 每条都是可检验的，不是模糊描述
- `review_focus` — evaluator需要重点关注的事项（如"如果旧测试被修改，审查修改原因"）

**删掉的字段：**
- ~~`allowed_files`~~ — 删掉。防止executor乱改靠forbidden_files + hard gates足够
- ~~`required_tests`~~ — 删掉。executor自己决定怎么测

**设计原则：**
- Contract不告诉executor怎么做，只告诉它做什么、不能碰什么、怎么算成功
- Executor在forbidden_files之外的范围内自由发挥
- 确定性边界用hard gate（SOT mutation、protected files），需要判断力的边界交给evaluator
- 旧测试被修改不自动阻断——由evaluator在review_focus中审查修改原因是否合理

**示例：**
```json
{
  "task_key": "P32-T2",
  "objective": "让world generator产生qualifying social events，使T4激活路径可达",
  "exact_scope": "修改world generator使其在满足条件时产生social_event类型的stimulus",
  "constraints": [
    "AppraisalSignal v1 frozen — 不改appraisal_settlement.py",
    "不改现有deterministic T4 builder的逻辑",
    "新增stimulus类型必须通过tick_bridge现有接口"
  ],
  "forbidden_files": [
    "back/app/domain/appraisal_output.py",
    "back/app/engines/appraisal_settlement.py",
    "back/app/llm/**"
  ],
  "non_goals": [
    "不做T4的LLM appraisal集成",
    "不改UI"
  ],
  "acceptance_criteria": [
    "world generator在10天模拟中至少产生1次social_event stimulus",
    "产生的stimulus能通过tick_bridge传递到T4处理路径",
    "T4激活率从0变为>0",
    "现有全部测试不regression",
    "新增测试覆盖social_event生成条件"
  ],
  "review_focus": [
    "如果现有测试文件被修改，逐个审查修改原因",
    "确认新stimulus不绕过tick_bridge的validation",
    "确认没有hardcode测试数据让T4人为通过"
  ]
}
```

---

## 修改范围

### 1. `orch/engine/claude_round_driver.py` — 核心改造

**现状：** 一个函数`run_attempt()`调用一次Claude CLI（round-driver agent），返回三个artifact。

**改为：** 拆成4个独立的Claude CLI调用函数：

```
invoke_designer(round_dir, sot_dir, model) → task_contract.json
invoke_evaluator_contract_review(round_dir, model) → contract_feedback.json
invoke_executor(round_dir, codebase_path, model) → 代码变更 + execution_evidence.json
invoke_evaluator(round_dir, codebase_path, model) → review_verdict.json
```

每个函数：
- 独立调用`claude -p <prompt>`（不用`--agent`）
- 注入该角色专属的文件（通过`--add-dir`或prompt内嵌）
- 返回结构化结果

**各agent的context注入：**

| Agent | 读到的 | 不读的 |
|-------|--------|--------|
| Designer | vision.md, road_map.md, current_phase.md, decisions.md, 代码目录结构, 上轮evaluator问题(如有) | executor的代码、evaluator的推理 |
| Evaluator(合约审查) | task_contract.json中的acceptance_criteria和review_focus | vision/roadmap/designer推理 |
| Executor | task_contract.json(最终版), 相关源代码 | designer推理过程, vision全文, evaluator |
| Evaluator(代码审查) | 代码变更(git diff), acceptance_criteria, review_focus | executor的思考过程, designer推理 |

**Prompt构建：** 每个角色的prompt直接写在Python代码中（或作为模板文件存在orchestrator repo里），不再依赖target repo的`.claude/agents/`目录。

### 2. `orch/engine/orchestrator.py` — `_run_round()`流程改造

**现状：**
```
generate_round_brief → snapshot_sot → invoke_claude(一次) → collect_evidence → hard_gates → adjudicate
```

**改为：**
```
Step 1: invoke_designer() → task_contract.json (含proposed acceptance_criteria + review_focus)
Step 2: invoke_evaluator_contract_review() → contract_feedback.json (能评/不能评/建议修改)
Step 3: [如需修改] invoke_designer()再次 → final_task_contract.json
Step 4: hard_gate: forbidden_files合理性检查
Step 5: snapshot_sot + record baseline commit
Step 6: invoke_executor() → 代码变更 + execution_evidence.json
Step 7: hard_gates (SOT mutation、protected files、forbidden files、pytest等)
Step 8: 如果hard gate通过 → invoke_evaluator() → review_verdict.json
Step 9: adjudicate (hard gate结果 + evaluator verdict)
Step 10: 通过 → commit / 不通过 → 问题回到Step 1的designer
```

关键变化：
- Hard gate在evaluator之前跑，不通过就不浪费token跑evaluator
- Contract协商在executor之前完成
- 失败后问题回到designer，不是直接给executor

### 3. `orch/engine/hard_gates.py` — 调整

- 删掉`_gate_allowed_files()` — 不再有allowed_files字段
- 保留`_gate_forbidden_files()`、`_gate_target_protected_files()`、`detect_sot_mutation()`、`_gate_pytest()`、`_gate_has_changes()`、`_gate_round_dir_boundary()`
- 调整`validate_proposed_scope()` — 只验证forbidden_files，不再验证allowed_files

### 4. 删除/废弃

- `target_repo/.claude/agents/round-driver.md` — 不再需要
- `target_repo/.claude/agents/designer.md` — prompt移到orchestrator内部
- `target_repo/.claude/agents/executor.md` — 同上
- `target_repo/.claude/agents/reviewer.md` — 同上
- `orch/cli/project_cmds.py`中写agent模板到target repo的逻辑 — 删除

### 5. `orch/briefing.py` — 按角色生成不同brief

**现状：** `generate_round_brief()`生成一个统一的round_brief.md。

**改为：** 按角色生成不同的brief文件：
- `generate_designer_brief()` — 包含vision, roadmap, phase context, 上轮问题
- `generate_executor_brief()` — 包含task_contract(最终版)
- `generate_evaluator_contract_brief()` — 包含task_contract中的acceptance_criteria和review_focus
- `generate_evaluator_review_brief()` — 包含git diff + acceptance_criteria + review_focus

### 6. `orch/models.py` — 调整数据结构

- `TaskContract` — 删掉`allowed_files`和`required_tests`字段，新增`review_focus`字段
- 新增`ContractFeedback` — evaluator对contract的反馈（哪些标准能评/不能评、建议修改）
- 现有`ExecutionEvidence`, `ReviewVerdict`保持不变

### 7. 不变的部分

- `orch/sot.py` — 不改
- `orch/utils/evidence_collector.py` — 不改
- `orch/utils/git_ops.py` — 不改
- `orch/db/database.py` — 不改
- `orch/cli/main.py` — 不改
- `orch/cli/run_cmds.py` — 不改
- `orch/cli/review_cmds.py` — 不改
- `orch/cli/phase_cmds.py` — 不改
- `orch/cli/log_cmds.py` — 不改
- `orch/cli/rollback_cmd.py` — 不改
- `orch/cli/config_cmds.py` — 不改

---

## 新的完整Round流程

```
Orchestrator (Python, 确定性)
│
├─ 1. 生成designer_brief (vision + roadmap + phase + 上轮问题)
├─ 2. 冷启动Claude CLI #1 (Designer/Opus)
│     输入: designer_brief
│     输出: task_contract.json (含proposed验证标准)
│
├─ 3. 冷启动Claude CLI #2 (Evaluator/合约审查模式)
│     输入: acceptance_criteria + review_focus
│     输出: contract_feedback.json (能评/不能评/建议修改)
│
├─ 4. [如需修改] 冷启动Claude CLI #1b (Designer/修订)
│     输入: designer_brief + contract_feedback.json
│     输出: final_task_contract.json
│
├─ 5. Hard gate: forbidden_files合理性检查
│
├─ 6. Snapshot SOT + record baseline commit
│
├─ 7. 冷启动Claude CLI #3 (Executor/Opus或Sonnet)
│     输入: final_task_contract.json + 源代码访问权
│     输出: 代码变更 + execution_evidence.json
│
├─ 8. Hard gates (SOT mutation、protected files、forbidden files、pytest等)
│     不通过 → 直接打回, 不跑evaluator
│
├─ 9. 冷启动Claude CLI #4 (Evaluator/代码审查模式)
│     输入: git diff + acceptance_criteria + review_focus
│     输出: review_verdict.json
│
├─ 10. Adjudicate
│      通过 → commit both repos, mark task complete
│      不通过 → 问题列表回到Step 1 (新一轮designer)
│
└─ 11. 超过max_attempts → escalate to human
```

---

## 验证方式

1. 在cyber-community-v2项目上跑一个完整round，确认：
   - 4次Claude CLI调用都独立成功
   - 产出的artifact格式与现有格式兼容
   - Hard gates正常工作
   - Contract协商产生了可执行的验证标准
   - 最终代码通过测试
2. 对比改造前后的round成本和质量
3. 检查attempt_report.json包含所有步骤的记录

---

## 收尾工作

所有代码改动完成并验证通过后：

1. **更新orchestrator repo内描述性文件**，确保它们反映改造后的最新状态：
   - `README.md` — 更新架构描述、使用说明、流程图
   - `docs/` 下的相关文档
   - 删除orchestrator repo自己的`vision.md`（与README重复，注意不要与SOT中target repo的vision.md混淆）
2. **将本plan文件拷贝到repo内**（如`docs/plans/`），作为改造记录存档，后续可查
