# roadmap.md

## Purpose

This document defines the approved phase progression for CyberLife / Cyber Community.

It is used by the Designer to:
- determine what phase should come next after the current phase closes
- preserve correct sequencing
- avoid scope drift
- avoid architecture drift
- avoid prematurely optimizing for richer behavior before core contracts exist

This document is **not**:
- a task backlog
- an implementation spec
- a product pitch
- a freeform idea list

`vision.md` defines what the project is.
`current_phase.md` defines what is being worked on now.
`roadmap.md` defines the approved phase order between now and the next major milestone.

---

## Current Strategic Frame

CyberLife / Cyber Community is currently built on a:

**deterministic single-agent digital life backbone**

This backbone is already strong enough to support:
- deterministic simulation
- explainable state transitions
- cross-day continuity
- residual persistence
- contract auditing
- controlled phase-based evolution

The next major strategic milestone is:

**introduce LLM appraisal into the agent loop without breaking deterministic settlement discipline**

In other words:

- LLM should enter first as an **appraisal layer**
- engine should remain responsible for **settlement / bookkeeping / contract-bearing state transitions**
- live LLM integration must be introduced only after the minimum deterministic seam is ready

This roadmap covers the approved sequence from the current state up to that milestone.

---

## Global Sequencing Principles

- Do not skip contract-establishing phases in order to pursue richer behavior.
- Do not introduce live runtime / LLM appraisal before the required deterministic seam is explicitly established.
- Prefer minimal contract flips over broad architecture expansion.
- Prefer narrow, auditable activation slices over general-purpose abstractions.
- Every phase must preserve explainability.
- Every phase must preserve auditability.
- If a phase unlocks dormant downstream behavior, that must be treated as a deliberate contract flip, not as a side effect.
- Designer must not invent new major directions outside this roadmap unless the roadmap itself is explicitly revised.

---

## Established Ground Truth Before This Roadmap

The following are already established and should be treated as active backbone contracts:

- T1 / public residual continuity
- T2 / influencer residual continuity
- cross-day residual persistence
- world carryover distribution

The following is also established:

- SocialEventSpec schema exists
- it is attached to ArcPhase / WorldSnapshot
- it is currently schema-only and behaviorally inert

The following is **not** established:

- T4 negative relational residual continuity under the old frozen deterministic path

This roadmap begins from that exact state.

---

## Pre-Roadmap Prerequisite

Phase 25 closure is required before entering Phase 26B.

Remaining Phase 25 tasks (P25-T2 T4 freeze boundary, P25-T3 next-stage design entry points,
P25-T4 orchestrator-ready materials) must be completed or explicitly cancelled before
the roadmap sequence begins.

---

## Phase Naming Note

Phase 26A has already been completed. It established the SocialEventSpec schema seam
(schema-only, behaviorally inert). Phase 26B is the activation slice built on top of 26A.

---

## Stage 1 Bridge Scope Rule

Stage 1 bridge and appraisal-seam work is intentionally limited to T1 / T2 / T4.

T3 / T5 / T6 / T7 / T8 deterministic bridge expansion is **deferred** and is
**not Designer-discretionary**. Designer may not propose deterministic bridge work
for deferred ticks unless this roadmap is explicitly revised.

These deferred ticks are handled as follows:

- **Phase 29 (schema):** The appraisal input schema must be designed to accommodate
  all 8 tick types, so that future tick coverage does not require schema redesign.
- **Phase 31 (live authority):** Only T1 / T2 / T4 are approved for first live LLM
  appraisal path. T3 / T5 / T6 / T7 / T8 may be representable in the schema but
  do not have live authoritative coverage in Stage 1.
- **Stage 2 decision:** Whether deferred ticks enter the live LLM appraisal path
  is a Stage 2 roadmap decision, not a Stage 1 task.

This is "B for schema, A for live authority": schema-wide, authority-narrow.

---

# Phase Roadmap — Stage 1
# Goal: Reach first safe LLM appraisal integration

---

## Phase 26B — Minimal T4 Event-Aware Activation

### Goal
Enable the first narrow, explicit, auditable event-aware T4 activation path.

### Why Now
T4 negative relational residual continuity was previously structurally frozen.
A minimal event-aware activation seam must exist before broader relational appraisal logic can evolve.

### In Scope
- activate `build_signal_from_t4_relationship_tick()` to read `world.social_event`
- allow only a very narrow trigger shape
- allow only a minimal negative relational output shape
- rely on existing downstream gates to decide whether relational residual is created
- verify that the seam can produce a real T4 negative path without broad architecture changes

### Out of Scope
- no live LLM
- no broad event taxonomy expansion
- no routing based on `social_event.target_id`
- no generator rewrite to actively produce rich social events
- no settlement/substrate redesign
- no bridge redesign
- no strong negative outputs
- no attempt to solve all relational realism problems in one phase

### Exit Condition
- T4 can read a qualifying social event in the approved narrow path
- T4 can emit the approved minimal negative relational signal shape
- downstream gate behavior is observable and auditable
- resulting behavior is stable enough to confirm that the frozen T4 seam is no longer structurally inert

### Unlocks
- first real relational negative seam
- first auditable event-aware T4 contract
- safe basis for controlled relational tuning and coverage expansion

---

## Phase 27 — T4 Activation Audit and Composition Safety

### Goal
Audit and stabilize the first activated T4 negative path, especially same-day composition with T2 and downstream wake-up behavior.

### Why Now
Once 26B flips the dormant T4 seam, hidden downstream interactions become live risks.
This must be understood before adding more expressive relational behavior.

### In Scope
- audit T4 negative activation frequency
- audit same-day T2/T4 interaction on the same relationship target
- audit downstream residual creation behavior
- audit whether `_adjust_t4()` and related paths produce stable and interpretable outcomes
- calibrate thresholds / guards / narrow protections if needed
- produce explicit contract notes on what is now considered valid T4 behavior

### Out of Scope
- no large relational system redesign
- no new major event types
- no player-side new intervention systems
- no LLM integration yet
- no generalized multi-factor relational cognition layer

### Exit Condition
- T4 activation no longer behaves like a one-off hack
- same-day T2/T4 composition risks are understood and bounded
- downstream wake chain is documented and acceptable
- the activated T4 seam is stable enough to support broader deterministic relational appraisal work

### Unlocks
- safe transition from “first activation exists” to “relational negative seam is governable”
- confidence to expand deterministic relational appraisal coverage

---

## Phase 28 — Deterministic Relational Appraisal Expansion

### Goal
Expand deterministic relational appraisal coverage beyond the single minimal activation slice, while preserving auditability.

### Why Now
After T4 is proven activatable and safe, the system needs slightly richer relational interpretation capacity before LLM appraisal can be attached to a meaningful seam.

### In Scope
- carefully expand event-aware relational appraisal conditions
- allow more than one narrow approved event-to-relational interpretation path
- improve deterministic expressiveness of T4 without abandoning controllability
- make relational appraisal output shapes slightly more representative of actual social friction / trust change patterns
- keep all behavior explainable and inspectable

### Out of Scope
- no freeform natural-language appraisal
- no live LLM runtime
- no relationship graph redesign
- no social world simulation explosion
- no attempt to model full human social complexity

### Exit Condition
- deterministic relational appraisal is no longer a single special-case seam
- T4 has limited but real deterministic coverage across multiple event conditions
- outputs remain narrow, interpretable, and contract-safe
- the system has a meaningful appraisal seam that could later be replaced or assisted by LLM

### Unlocks
- an appraisal-shaped interface worth externalizing
- a real basis for separating appraisal from settlement

---

## Phase 29 — Appraisal / Settlement Boundary Extraction

### Goal
Make the appraisal layer an explicit seam in the architecture, without yet introducing live LLM runtime.

### Why Now
LLM should not be inserted directly into tangled simulation internals.
The system first needs a clean boundary showing:
- what inputs appraisal reads
- what outputs appraisal may produce
- what settlement remains engine-owned

### In Scope
- extract or formalize appraisal-facing input schema
- **input schema must accommodate all 8 tick types** (T1–T8), not just the 3 with active bridges,
  so that future tick coverage does not require schema redesign
- formalize appraisal output contract
- define what fields are advisory vs contract-bearing
- define how deterministic fallback works when no external appraisal is available
- make boundary testable and reviewable

### Out of Scope
- no production LLM integration yet
- no prompt experimentation as the main work
- no dynamic open-ended agent cognition system
- no removal of deterministic fallback behavior
- no granting live authority to T3/T5/T6/T7/T8 (schema accommodation only)

### Exit Condition
- appraisal boundary is explicit in code and docs
- input schema can represent all 8 tick types
- settlement ownership remains clearly engine-side
- a non-LLM implementation can still satisfy the same contract
- the seam is stable enough that an LLM can be plugged in as an implementation of appraisal, rather than as an architecture rewrite

### Unlocks
- safe LLM insertion point
- future model-swappability
- preservation of deterministic governance

---

## Phase 30 — Offline / Shadow LLM Appraisal Validation

### Goal
Validate LLM appraisal against the extracted appraisal seam without allowing it to drive the authoritative live path yet.

### Why Now
Before LLM enters the real agent loop, the team must compare:
- deterministic appraisal outputs
- LLM appraisal outputs
- contract compliance
- stability
- variance
- failure shape

### In Scope
- run shadow or offline appraisal comparisons
- define approved prompt / schema format
- compare LLM output against deterministic expectations and acceptance rules
- evaluate whether LLM outputs are useful, bounded, and composable
- identify failure classes and required guardrails

### Out of Scope
- no full production live control handoff
- no open-ended autonomy
- no replacing settlement with model judgment
- no prompt-only “magic” as a substitute for contract discipline

### Exit Condition
- LLM can generate appraisal outputs in the approved contract shape
- outputs can be checked, bounded, and rejected if invalid
- shadow evaluation demonstrates enough usefulness to justify controlled live entry
- failure cases are documented and guardrails are specified

### Unlocks
- first safe live-path integration candidate
- confidence that LLM can enter as appraisal, not chaos injection

---

## Phase 31 — First Live LLM Appraisal Integration

### Goal
Introduce the first controlled live LLM appraisal path into the agent loop.

### Why Now
At this point:
- deterministic backbone is established
- T4 event-aware seam exists
- relational appraisal has meaningful deterministic shape
- appraisal/settlement boundary is explicit
- LLM has passed offline/shadow validation

The system is ready for the first real LLM-assisted appraisal step.

### In Scope
- insert LLM into the appraisal seam only
- **first live authority is limited to T1 / T2 / T4 only** — deferred ticks (T3/T5/T6/T7/T8)
  remain on deterministic fallback even though the schema can represent them
- keep settlement / bookkeeping engine-authoritative
- preserve deterministic validation / fallback / guardrail path
- limit LLM responsibility to the approved appraisal contract
- audit resulting outputs and system stability

### Out of Scope
- no full agent autonomy explosion
- no replacement of simulation engine by the LLM
- no uncontrolled freeform memory/personality architecture expansion
- no multiplayer-scale live society rollout
- no granting live LLM authority to T3/T5/T6/T7/T8 (deferred to Stage 2)

### Exit Condition
- live LLM appraisal participates in the real loop for T1 / T2 / T4
- T3 / T5 / T6 / T7 / T8 remain on deterministic fallback
- engine remains authoritative for settlement
- outputs remain auditable
- fallback path remains functional
- the integration is stable enough to establish the first controlled live hybrid path
- Stage 1 closure is now pending only on the remaining T4 reality-closure gap

### Unlocks
- first controlled live hybrid path
- project has transitioned from pure deterministic baseline to controlled hybrid infrastructure:
  **LLM appraisal + engine settlement**
- safe entry into final Stage 1 closure work

---

## Phase 32 — T4 Reality Closure

### Goal
Close the remaining Stage 1 gap by turning the existing T4 event-aware seam
from a partially implemented path into a real, stage-closing relational contract.

### Why Now
By the end of Phase 31, the project already has:
- a governed deterministic backbone
- active T1 / T2 continuity
- cross-day persistence
- an explicit appraisal / settlement boundary
- a first live LLM appraisal router with narrow authority

However, Stage 1 is not yet fully closed because T4 is still only partially unlocked:
- the social-event detection seam exists
- the negative signal path exists
- but relational residual creation is still blocked
- `_adjust_t4()` is still dormant
- the project cannot yet honestly claim full T4 relational continuity

This phase exists to close that remaining gap without changing the overall Stage 1 architecture.

### In Scope
- close the remaining T4 partial-unlock gap identified in the current repo status
- make the existing T4 event-aware path capable of completing the approved relational wake chain
- validate that T4 can progress beyond detection-only / negative-signal-only behavior
- verify that downstream relational residual creation becomes real and auditable
- verify that `_adjust_t4()` is no longer permanently dormant
- audit same-day T2/T4 composition and downstream wake behavior after closure
- produce explicit contract notes describing what Stage 1 now considers valid T4 relational continuity

### Out of Scope
- no deferred tick bridge or live-authority expansion for T3 / T5 / T6 / T7 / T8
- no broad social world redesign
- no rich new event taxonomy expansion
- no settlement / substrate redesign
- no bridge architecture rewrite
- no freeform memory / personality / identity-deepening work
- no uncontrolled broadening of LLM authority
- no rewriting Stage 1 into a richer Stage 2 system

### Exit Condition
- T4 no longer remains in a merely partial-unlock state
- approved T4 event-aware activation can complete the relational wake chain in real simulation
- relational residual creation is observed and auditable under the approved Stage 1 path
- `_adjust_t4()` is confirmed live rather than permanently dormant
- same-day T2/T4 composition remains bounded and acceptable
- the project can honestly claim that Stage 1 now includes a real event-aware relational seam
- Stage 1 can close without misrepresenting T4 as either still frozen or only half-implemented

### Unlocks
- honest Stage 1 completion
- closure of the remaining mismatch between “Phase 31 complete” and actual T4 reality
- a clean transition into Stage 2
- a stronger base for later appraisal deepening, memory contracts, and agent interior growth

---

# Stage 1 End State

When Stage 1 is complete, CyberLife should have:

- a governed deterministic single-agent backbone
- active T1 / T2 residual continuity
- established cross-day residual persistence
- partially active but bounded world carryover behavior
- an explicit appraisal / settlement boundary
- AppraisalInput schema capable of representing all 8 tick types
- first live LLM appraisal authority limited to T1 / T2 / T4 only
- deterministic fallback preserved for T3 / T5 / T6 / T7 / T8
- engine-authoritative settlement / bookkeeping
- auditable per-tick live-path selection and fallback behavior
- a real event-aware relational seam for T4
- no unresolved mismatch between roadmap closure claims and actual repo reality

Stage 1 is complete only when the system can honestly be described as:

**LLM appraisal + engine settlement**
with controlled live authority, preserved deterministic governance,
and a real rather than merely partial T4 relational seam.

---

# Phase Roadmap — Stage 2
# Goal: Deepen appraisal, memory, identity continuity, and selective live intake without breaking bounded life-sim governance

Move from “LLM has entered the loop safely” to “Agent interior life becomes deeper, more continuous, and more identity-bearing” — without losing engine-authoritative settlement, auditability, explainability, bounded contracts, or the product identity of witnessing a life rather than chatting with a mind.

# Stage 2 Global Sequencing Principles

1. Phase 33 must complete before any deferred-tick live-authority expansion begins.
2. Phase 34 must complete before any memory, identity, or deferred-tick work begins — live LLM validation is a prerequisite.
3. Phase 35 must complete before any identity-growth implementation or selective recall behavior is approved.
4. Phase 36 must define the post-P32 T4 expressivity path before T4 is treated as fully expressive.
5. Phase 37 must explicitly decide deferred-tick admission policy before any specific deferred tick enters live authority.
6. Phase 38 implements only the first approved deferred-tick candidate set; broad rollout is prohibited.
6. Stage 2 may introduce only the minimum world-input enablement needed for deeper appraisal and bounded T4 progression; broad world-generator deepening remains out of scope for Stage 2.
7. Stage 2 preserves the current player loop and does not redesign player influence surfaces; Stage 3 owns player-influence maturation.
8. Engine remains authoritative for settlement / bookkeeping throughout Stage 2.
9. LLM remains appraisal-only throughout Stage 2; no direct ledger-authority transfer is permitted.
10. Selective live intake remains the default principle; all-ticks-at-once rollout is explicitly disallowed.

---

## Phase 33 — Appraisal Discipline Hardening

### Goal
Harden the live appraisal path so Stage 2 begins from explicit evaluation discipline rather than vague prompt optimism.

### In Scope
- tighten prompt / schema / evaluation discipline for current live-authority ticks
- define explicit classes for:
  - acceptable output
  - degraded-but-usable output
  - invalid / forced-fallback output
- improve live-path observability and reviewability
- audit multi-day drift and failure accumulation, not only single-tick correctness
- document what Stage 2 considers safe appraisal deepening versus dangerous narrative drift

### Out of Scope
- no deferred-tick live-authority expansion yet
- no freeform memory system
- no identity-growth implementation yet
- no player influence redesign
- no world-generator redesign

### Why Now
Stage 1 established the first controlled live hybrid path, but that is only a safe entry condition.
Stage 2 cannot responsibly deepen memory, identity, or live-intake breadth until appraisal quality is governed by an explicit discipline.

### Exit Condition
- live appraisal quality is governed by explicit, reviewable acceptance criteria
- degraded output classes are defined and intentionally handled
- multi-day drift / instability failure shapes are documented
- Stage 2 can deepen appraisal without relying on informal prompt intuition

### Unlocks
- safe basis for memory and identity contract work
- reduced risk of Stage 2 drifting into chatbot-style narrative looseness
- foundation for later deferred-tick admission decisions

---

## Phase 34 — LLM Live Validation

### Goal
在真实 LLM API 调用下，验证已建立的 appraisal discipline（prompt schema、acceptance rules、validation gate、fallback path）是否在 live 条件下仍然成立。

### Why Now
Phase 33 在 deterministic / mock 环境下 harden 了 appraisal discipline，但 deterministic 测试无法暴露真实 LLM 的两类核心风险：
1. prompt 与 schema 的实际 compliance rate（真实模型是否能稳定产出 contract-compliant AppraisalOutput）
2. validation gate 和 acceptance rules 在面对真实 LLM variance 时的 rejection/fallback 行为是否符合预期

这两个问题只能通过真实 API 调用回答。如果跳过这一步直接进入 Phase 35（Memory Scope），后续所有依赖 live appraisal 质量的 phase 都建立在未经验证的假设上。

### In Scope
- 编写 `@pytest.mark.live` 标记的测试，手动触发，不进 CI
- 对 T1 / T2 / T4 的真实 AppraisalInput 场景调用真实 LLM API，收集 raw response
- 验证 LLM 返回能否被 `response_parser` 成功解析为 AppraisalOutput
- 验证解析后的 AppraisalOutput 能否通过 `validation_gate.evaluate()` 和 `acceptance_rules` 的所有 contract-bearing 约束
- 验证 fallback path 在 LLM 返回 invalid / unparseable / timeout 时能否正确触发
- 收集 compliance rate、failure mode distribution、rejection reason 统计
- 记录观察到的 deviation pattern（例如：LLM 是否倾向于某些 field 的系统性偏移）
- 测试结果以 audit 数据形式输出，不写入 production 代码路径

### Out of Scope
- 不修改 AppraisalOutput schema 或 AppraisalSignal v1
- 不修改 settlement engine
- 不修改 validation gate / acceptance rules 的逻辑（如果发现问题，记录为 finding，留待后续 phase 处理）
- 不引入 prompt tuning / prompt engineering 迭代循环
- 不扩展 live authority 到 deferred ticks（T3/T5/T6/T7/T8）
- 不建立 LLM 调用的 production runtime 基础设施（API key 管理、rate limiting、cost tracking 等）
- 不修改 deterministic fallback 行为

### Exit Condition
- 至少覆盖 T1 / T2 / T4 各一个代表性场景的 live 测试存在且可运行
- compliance rate 和 failure mode distribution 有明确的数据记录
- 如果 compliance rate 不足以支撑后续 phase，该事实被显式记录为 blocking finding
- 如果 compliance rate 足够，该事实被显式记录为 Phase 33 discipline 的 live confirmation
- 所有测试标记为 `@pytest.mark.live`，不在 CI 中运行

### Unlocks
- 对 Phase 33 appraisal discipline 的 live-condition 信心确认（或显式否定）
- 如果 compliance rate 不足，产生明确的 prompt/schema 改进需求列表，可在后续 phase 处理
- 为 Phase 35 及之后的 memory / identity / deferred-tick 工作提供真实 LLM 行为的经验数据
- 减少"deterministic 测试全通过但 live 部署时大面积 fallback"的风险

---

## Phase 35 — Memory Scope and Authority Contract

### Goal
Define what memory already exists, what is still missing, and what authority boundaries memory is allowed to have.

### In Scope
- inventory the current memory substrate, including at minimum:
  - DaySnapshot-style carryover artifacts
  - residuals and cross-day persistence
  - residual-aware bridging
  - archive / history / continuity-bearing records already owned by the engine
- distinguish between:
  - narrative-only memory
  - appraisal-visible memory
  - settlement-relevant memory
  - identity-bearing memory
- define missing memory capabilities that Stage 2 may later introduce, including:
  - selective recall
  - relevance decay
  - resurfacing rules
  - bounded memory selection for appraisal input
- define engine-owned versus LLM-influenced memory boundaries

### Out of Scope
- no unconstrained autobiographical memory engine
- no vector-memory-first architecture expansion
- no freeform rumination system
- no direct ledger writing by LLM memory outputs
- no identity-growth implementation yet

### Why Now
Memory is already one of the system’s shaping forces, but it still exists mostly as substrate and carryover mechanics rather than as an explicit contract.
Stage 2 cannot safely deepen continuity until memory scope and authority are clearly defined.

### Exit Condition
- the project has an explicit memory scope matrix
- existing substrate versus missing capability is clearly documented
- memory authority boundaries are explicit and reviewable
- selective recall / decay / resurfacing are defined as governed mechanisms rather than vague future ideas

### Unlocks
- real basis for identity continuity work
- safer integration of memory into later appraisal deepening
- stronger distinction between noise, carryover, and lasting significance

---

## Phase 36 — T4 Expressivity Path and World-Input Enablement

### Goal
Define the bounded post-P32 path for T4 expressivity and the minimum world-side input enrichment required to support it.

### In Scope
- define the approved T4 expressivity ladder after P32, including:
  - what “partial” means
  - what “deep” means
  - whether “full” belongs in Stage 2 or remains deferred
- define when and why T4 absorption is allowed to progress beyond the P32 state
- define the approved relationship between T4 expressivity depth and downstream residual / wake-chain behavior
- define the minimum additional world-side input shapes needed to support deeper relational appraisal
- define the minimum generator-side enrichment allowed in Stage 2 to produce those inputs
- audit same-day composition and downstream consequences at each approved T4 depth

### Out of Scope
- no broad social world redesign
- no rich world-event grammar expansion
- no shared-world deepening program
- no unrestricted T4 expressivity expansion
- no multi-agent relational system redesign

### Why Now
P32 closes the Stage 1 reality gap, but it does not automatically answer how T4 continues to evolve afterward.
Stage 2 must explicitly define the next bounded path, or T4 will either stagnate or drift into uncontrolled expansion.

### Exit Condition
- the post-P32 T4 expressivity ladder is explicitly documented
- approved world-input enablement for Stage 2 is explicitly bounded
- the project knows which T4 depth transitions belong to Stage 2 and which remain deferred
- deeper T4 behavior is connected to explicit contract language rather than informal intuition

### Unlocks
- safe continuation of relational appraisal depth
- a bounded world-input enabling line for Stage 2
- reduced risk of confusing Stage 2 with Stage 4 world deepening

---

## Phase 37 — Deferred-Tick Admission Contract

### Goal
Make deferred-tick live-intake expansion an explicit Stage 2 decision rather than an implicit future guess.

### In Scope
- define admission criteria for T3 / T5 / T6 / T7 / T8 live-authority entry
- evaluate each deferred tick against:
  - expected value to interior continuity
  - risk to settlement discipline
  - dependency on memory contract maturity
  - dependency on identity contract maturity
  - dependency on world-input quality
- classify each deferred tick as:
  - not yet eligible
  - eligible later in Stage 2
  - candidate for first-wave live admission
- choose the first approved deferred-tick candidate set for implementation
- preserve deterministic fallback for all non-approved deferred ticks

### Out of Scope
- no all-at-once deferred-tick rollout
- no hidden expansion of live authority
- no production all-ticks-to-LLM mode
- no implementation of second-wave tick admission yet

### Why Now
Stage 1 explicitly deferred live authority for T3 / T5 / T6 / T7 / T8.
Stage 2 must therefore answer this question directly.
If it does not, the system will either stall or drift into accidental breadth-first expansion.

### Exit Condition
- every deferred tick has an explicit admission status
- first-wave deferred-tick candidates are explicitly chosen
- deterministic fallback remains explicit for all others
- selective intake is established as policy, not just preference

### Unlocks
- a governed path into Stage 2 live-authority expansion
- a reusable admission template for future ticks
- reduced ambiguity for Designer and Claude during later phases

---

## Phase 38 — Selective Deferred-Tick Live Intake I

### Goal
Implement the first approved deferred-tick candidate set under explicit Stage 2 constraints.

### In Scope
- add live appraisal authority for the first approved deferred-tick candidate set
- preserve deterministic fallback for all non-approved deferred ticks
- audit whether the newly live deferred tick(s) actually improve interior continuity
- audit whether the new live tick(s) remain compatible with bounded settlement and reviewability
- document any new failure modes introduced by selective live-intake expansion

### Out of Scope
- no second-wave deferred-tick admission yet
- no broad deferred-tick rollout
- no abandonment of deterministic fallback
- no player influence redesign

### Why Now
Once admission criteria and the first approved candidate set exist, Stage 2 needs one real implementation slice.
Otherwise the roadmap would define a policy but never test whether selective live-intake expansion actually works.

### Exit Condition
- the first deferred-tick candidate set is live and auditable
- selective intake is proven in real use rather than only in planning
- deterministic fallback remains preserved for all still-deferred ticks
- the project has evidence that interior depth can increase without breadth-first rollout

### Unlocks
- first true Stage 2 expansion beyond the Stage 1 live-authority set
- evidence for or against further deferred-tick rollout
- stronger basis for cross-tick continuity work

---

## Phase 39 — Identity Continuity Contract

### Goal
Define what counts as short-term drift, long-term growth, regression, and merely contextual behavior.

### In Scope
- define identity drift versus identity growth
- define what repeated patterns are allowed to contribute to identity continuity
- distinguish between:
  - situational state
  - recurring tendency
  - meaningful growth
  - regression
  - temporary relational reaction
- define how memory classes may or may not contribute to identity continuity
- define how appraisal may reference continuity of self without collapsing into vague roleplay

### Out of Scope
- no open-ended personality fiction layer
- no full trait-engine rewrite
- no product/UI redesign for identity presentation
- no broad social identity system

### Why Now
Deeper memory without an identity contract will produce continuity-shaped language without continuity-shaped governance.
Stage 2 needs a principled basis for selfhood before it can claim real interior growth.

### Exit Condition
- identity continuity has explicit contract language
- growth is distinguishable from temporary fluctuation
- appraisal can reference continuity of self without becoming freeform personality improvisation
- the project has a governed basis for later interior-life deepening

### Unlocks
- credible agent interior growth foundation
- safer relationship between memory and self
- stronger basis for later player-facing emotional legibility

---

## Phase 40 — Cross-Tick Continuity and Consequence Shaping

### Goal
Strengthen the connection between events, appraisal, memory, identity, and later behavior across multiple days.

### In Scope
- improve continuity between daily events and later appraisal
- define how memory and identity contracts shape future interpretation
- strengthen the distinction between:
  - public meaning
  - relational meaning
  - internal meaning
- improve longer-horizon consequence shaping without surrendering bounded settlement
- audit whether deeper continuity creates meaningful life-shaping rather than uncontrolled noise accumulation

### Out of Scope
- no shared-world deepening program
- no major district-system expansion
- no multi-agent emergence work
- no player influence redesign

### Why Now
After Stage 2 has stronger appraisal discipline, memory scope, T4 pathing, and at least one deferred-tick live slice, it becomes possible to deepen multi-day interior continuity in a governed way.

### Exit Condition
- continuity across days is deeper, more legible, and more identity-bearing
- longer-horizon consequence shaping is real but bounded
- future behavior is shaped by prior interpreted experience in a governed manner
- the system remains a life-sim entity rather than a freeform conversational mind

### Unlocks
- a credible Stage 2 completion candidate
- stronger emotional and structural basis for later player and world work
- a cleaner handoff into later stages

---

## Phase 41 — Stage 2 / Stage 3 Player Boundary Freeze

### Goal
Explicitly define what Stage 2 preserves about the player loop and what Stage 3 will own about player influence maturation.

### In Scope
- document the current player-loop assumptions that Stage 2 must preserve
- define what forms of player input Stage 2 may continue to pass through unchanged
- define the compatibility boundary for future Stage 3 work, including:
  - influence surfaces
  - cadence
  - scarcity / cost
  - how player intent enters appraisal rather than direct scripting
- ensure Stage 2 additions do not create a future redesign trap for Stage 3

### Out of Scope
- no new player influence surfaces
- no scarcity / cost rebalance
- no cadence redesign
- no direct player scripting expansion
- no Stage 3 implementation work yet

### Why Now
If Stage 2 says nothing about the player boundary, it becomes unclear whether player influence is being ignored or silently redesigned.
This phase prevents that ambiguity and gives Stage 3 a cleaner starting point.

### Exit Condition
- Stage 2 / Stage 3 player boundary is explicitly documented
- Stage 2 is confirmed compatible with future player-influence maturation
- no hidden player-loop redesign remains embedded in Stage 2 work

### Unlocks
- clean handoff into Stage 3
- reduced ambiguity about what Stage 2 intentionally does not do
- stronger protection against product-identity drift

# Stage 2 End State

When Stage 2 is complete, CyberLife should have:

- hardened live appraisal discipline
- explicit memory scope and authority contracts
- a bounded post-P32 T4 expressivity path
- an explicit deferred-tick admission policy
- at least one selective deferred-tick live-intake slice beyond Stage 1
- explicit identity continuity contracts
- deeper cross-day continuity between event, interpretation, persistence, and later behavior
- preserved engine-authoritative settlement
- preserved deterministic fallback outside approved live-authority scope
- an explicit Stage 2 / Stage 3 player boundary
- no collapse into vague chatbot-style interior narration

Stage 2 is complete only when the project can honestly say:

the agent now has deeper interior continuity, deeper but still bounded appraisal,
and selectively expanded live authority — without breaking settlement governance
or drifting into chatbot-style mind simulation.

---

## Stage 3 — Player Influence Maturation

### Strategic Goal
Refine how the player influences the agent without becoming a direct controller.

### Likely Themes
- limited guidance actions becoming more meaningful
- player influence timing / scarcity / legibility
- clearer difference between care, nudging, and command
- better emotional and narrative consequence of player intervention
- preserving “caregiver, not controller”

### Likely Necessary Steps
- define influence surfaces
- define influence cost / scarcity / cadence
- define how player intent becomes appraisal input rather than direct scripting
- improve feedback loops so player influence feels real but not absolute

### Main Risk
Accidentally turning the product into a command interface or branching narrative game.

---

## Stage 4 — Shared World Deepening

### Strategic Goal
Make the world feel more socially alive, structured, and historically continuous.

### Likely Themes
- richer district/world dynamics
- stronger arc-phase consequences
- meaningful social events beyond isolated triggers
- better shared-world texture
- more visible world-to-agent shaping

### Likely Necessary Steps
- expand world event grammar
- improve world continuity systems
- tie world structure to relationship and opportunity surfaces
- increase legibility of shared society without overcomplicating simulation

### Main Risk
Overbuilding world machinery before the agent loop is emotionally convincing.

---

## Stage 5 — Multi-Agent / Shared Society Emergence

### Strategic Goal
Evolve from a single-agent backbone toward a truly shared social field with multiple active agents.

### Likely Themes
- multiple agents with overlapping world participation
- relationship chains across agents
- indirect social influence
- shared event participation
- social memory / reputation / diffusion

### Likely Necessary Steps
- define multi-agent computation boundaries
- define what must remain deterministic vs what may be probabilistic/appraised
- define interaction contracts between agents
- manage combinatorial explosion
- preserve auditability despite increased social density

### Main Risk
System complexity grows faster than meaning, producing simulation noise rather than lived social texture.

---

## Stage 6 — Productization of the Caregiver Experience

### Strategic Goal
Turn the simulation architecture into a strong player-facing game/product loop.

### Likely Themes
- observation surfaces
- emotional readability
- retention loop
- day-to-day ritual
- narrative payoff
- onboarding into care rather than control

### Likely Necessary Steps
- refine player-facing UI around witnessing, not dashboarding
- define what the player sees vs what remains system-internal
- improve pacing of emotional payoff
- build stronger continuity between daily simulation and player interpretation
- ensure the product still feels like raising/witnessing a life

### Main Risk
A technically impressive system that does not produce a compelling player experience.

---

## Ultimate Vision Reference

Long-term, CyberLife / Cyber Community should become:

a shared cyber society in which each player places one developing agent into a living world,
then influences that agent through care, timing, and limited guidance,
while the agent is continuously shaped by world events, relationships, memory, inner appraisal, and the player's presence.

The product should feel like:
- witnessing a life
- nurturing a becoming self
- observing social fate unfold
- participating through care, not control

It should not collapse into:
- chatbot
- dashboard
- task executor
- freeform roleplay shell
- pure simulation sandbox with no emotional product loop

---

## Usage Rules For Designer

When selecting the next phase:
- first read `vision.md`
- then read `roadmap.md`
- then read `current_phase.md`

Designer may:
- refine task sequencing within the approved current phase
- define rounds inside the active phase
- update current status and risks

Designer may not:
- skip forward to a later roadmap phase without explicit authorization
- merge multiple roadmap phases into one large phase
- invent a new strategic direction outside the roadmap
- broaden a phase beyond its approved scope in the name of completeness

If reality changes, revise `roadmap.md` explicitly.
Do not silently drift around it.