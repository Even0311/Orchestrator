# Audit — Round round-0029

**Status:** PASSED  
**Completed:** 2026-04-04 08:48 UTC  
**Total cost:** $1.6375  
**Attempts:** 1

## Task
**P28-T6** — Lock calibrated signal intensity ranges for Pattern A and Pattern B T4 outputs in dedicated tests
Create a dedicated test file that formally locks the calibrated signal intensity ranges for Pattern A (Contested Endorsement) and Pattern B (High-Intensity Unilateral Disclosure) T4 relational appraisal outputs. The calibration decision is: both patterns share the uniform signal shape (absorption=surface, valence=negative, arousal=low, trust_shift=mild_decrease, closeness_delta=-1, risk_delta=0, aftershock_days=0, guidance_resonance=neutral) identical to P0. This decision is already documented in docs/t4_negative_behavior_contract.md Sections 8.1.2 and 8.2.2. The task makes that decision executable and auditable through tests, and optionally adds missing calibration rationale prose to the contract document.

