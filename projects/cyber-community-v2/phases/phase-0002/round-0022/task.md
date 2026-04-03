# Task: Catalog Additional T4 Event-to-Relational Impact Patterns

**ID:** round-0022  
**Objective:** Identify and document specific social event-to-relational impact mapping patterns that expand T4 deterministic coverage beyond the current single narrow path, producing a catalog of implementable deterministic interpretation rules for Phase 28 expansion.

**Exact Scope:** IN: Review current T4 single-path implementation and existing T4 behavior contract, analyze SocialEventSpec schema for available event attributes, identify at least 2 additional distinct event-to-relational interpretation patterns (specific event conditions mapping to negative relational outcomes), define deterministic trigger conditions (event type, attribute filters, relationship context) and output shape specifications (friction type, trust delta direction) for each pattern, document catalog in structured format. OUT: Code implementation in T4 builder, modifications to existing builder functions, signal intensity calibration, composition safety auditing, test implementation for new paths.

## Constraints
- Must not modify existing T4 builder code or break existing 338 tests
- Must remain within deterministic appraisal (no LLM/natural-language)
- Must preserve auditability (patterns must be explicit, bounded, non-ambiguous)
- Patterns must comply with existing T4 behavior contract (docs/t4_negative_behavior_contract.md)
- Must not expand scope to deferred ticks (T3/T5/T6/T7/T8)

## Acceptance Criteria
- Catalog document exists identifying minimum 2 new distinct event-to-relational impact patterns beyond current single narrow path
- Each pattern specifies triggering event conditions (type, attributes), relationship context requirements, and deterministic output shape (friction type, trust delta direction)
- All patterns validated as compliant with existing T4 behavior contract constraints
- Patterns are mutually distinct and non-overlapping with each other and the existing single path

## Required Tests
- Test that cataloged patterns are representable within existing SocialEventSpec schema constraints
- Test that cataloged patterns maintain same-day T2/T4 composition safety per existing contract

## Non-Goals
- Do not implement cataloged patterns in T4 builder (deferred to P28-T2)
- Do not modify existing T4 builder code
- Do not calibrate signal intensity ranges (deferred to P28-T6)
- Do not execute composition safety audits (deferred to P28-T5)
- Do not refactor unrelated code
