# P34: LLM Live Validation
<!-- status: approved -->

## Phase Goal
在真实 LLM API 调用下，验证已建立的 appraisal discipline（prompt schema、acceptance rules、validation gate、fallback path）是否在 live 条件下仍然成立。

## In Scope
- 编写 `@pytest.mark.live` 标记的测试，手动触发，不进 CI
- 对 T1 / T2 / T4 的真实 AppraisalInput 场景调用真实 LLM API，收集 raw response
- 验证 LLM 返回能否被 `response_parser` 成功解析为 AppraisalOutput
- 验证解析后的 AppraisalOutput 能否通过 `validation_gate.evaluate()` 和 `acceptance_rules` 的所有 contract-bearing 约束
- 验证 fallback path 在 LLM 返回 invalid / unparseable / timeout 时能否正确触发
- 收集 compliance rate、failure mode distribution、rejection reason 统计
- 记录观察到的 deviation pattern（例如：LLM 是否倾向于某些 field 的系统性偏移）
- 测试结果以 audit 数据形式输出，不写入 production 代码路径

## LLM Configuration
- Model: **Kimi 2.5** (Moonshot AI)
- Base URL: read from env var `KIMI_BASE_URL` (https://api.moonshot.ai/v1)
- API key: read from env var `KIMI_API_KEY` (already in `.env`)
- Use OpenAI-compatible client — Kimi 2.5 is OpenAI API compatible

## Out of Scope
- 不修改 AppraisalOutput schema 或 AppraisalSignal v1
- 不修改 settlement engine
- 不修改 validation gate / acceptance rules 的逻辑（如果发现问题，记录为 finding，留待后续 phase 处理）
- 不引入 prompt tuning / prompt engineering 迭代循环
- 不扩展 live authority 到 deferred ticks（T3/T5/T6/T7/T8）
- 不建立 LLM 调用的 production runtime 基础设施（API key 管理、rate limiting、cost tracking 等）
- 不修改 deterministic fallback 行为

## Task Queue
- [ ] P34-T1: Build live test infrastructure — create `@pytest.mark.live` marker configuration, API client setup for real LLM calls, and representative AppraisalInput scenario fixtures covering T1 (headline exposure), T2 (influencer social interaction), and T4 (relationship shift with social event context)
- [ ] P34-T2: Implement end-to-end live validation tests for T1/T2/T4 — call real LLM API through `appraisal_router.route()`, verify `response_parser` successfully parses raw responses into AppraisalOutput, verify parsed output passes `validation_gate.evaluate()` and `acceptance_rules.compare()` contract checks, and verify fallback path activates correctly on invalid/unparseable/timeout LLM responses
- [ ] P34-T3: Implement compliance statistics collection and deviation pattern audit — aggregate live test results into per-tick-type compliance rate, acceptance rate, failure mode distribution by FailureModeCategory, rejection reason breakdown, and systematic field-level deviation patterns; output as structured audit data suitable for informing future phase decisions
