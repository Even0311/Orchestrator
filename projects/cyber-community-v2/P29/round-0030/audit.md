# Audit — Round round-0030

**Status:** PASSED  
**Completed:** 2026-04-04 13:30 UTC  
**Total cost:** $0.7449  
**Attempts:** 1

## Task
**P29-T1** — Define unified AppraisalInput schema for all 8 tick types
Introduce a new Pydantic model called AppraisalInput in back/app/domain/ that represents the structured context slice each of the 8 ticks passes to the appraisal layer. The schema must accommodate all tick types (T1–T8) in a single unified model, even though only T1, T2, and T4 have active bridges today. No engine logic, no bridge wiring, and no settlement behavior is changed in this task — only the schema is introduced.

