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
- T3/T5/T6/T7/T8 remain on deterministic fallback
- engine remains authoritative for settlement
- outputs remain auditable
- fallback path remains functional
- the integration is stable enough to count as the end of Stage 1

### Unlocks
- Stage 1 complete
- project has transitioned from pure deterministic baseline to controlled hybrid architecture:
  **LLM appraisal + engine settlement**

---

# Stage 1 End State

When Stage 1 is complete, CyberLife should have:

- a still-governed deterministic backbone
- a real event-aware relational seam
- an explicit appraisal / settlement boundary
- a validated live LLM appraisal insertion point
- a first hybrid runtime path that does not collapse explainability or auditability

This is the intended end state of this roadmap.

---

# Coarse Outlook Beyond Stage 1
# For future roadmap generation only

The following is intentionally coarse-grained.
It is not yet an approved detailed roadmap.
It exists only to guide later Stage 2 roadmap drafting.

---

## Stage 2 — Appraisal Deepening and Agent Interior Growth

### Strategic Goal
Move from “LLM has entered the loop safely” to “Agent interior life becomes deeper, more continuous, and more identity-bearing.”

### Likely Themes
- richer appraisal dimensions
- more durable personality continuity
- memory relevance and selective carryover
- stronger relation-specific interpretation
- longer-horizon consequence shaping
- better distinction between public, relational, and internal meaning

### Likely Necessary Steps
- stabilize prompt / schema / evaluation discipline
- define durable memory contracts
- define what counts as identity drift vs identity growth
- deepen appraisal types without surrendering settlement governance
- improve continuity between daily events, inner appraisal, and future behavior

### Main Risk
Turning the agent into a vague chatbot mind instead of a bounded life-sim entity.

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