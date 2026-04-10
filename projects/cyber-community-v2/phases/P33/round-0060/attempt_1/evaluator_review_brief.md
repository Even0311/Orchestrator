# Evaluator Code Review — round-0060

**Task Key:** P33-T1
**Title:** Multi-day LLM appraisal deviation audit

## Acceptance Criteria
1. back/tools/audit_llm_deviation.py exists and is executable as a standalone script (python tools/audit_llm_deviation.py from back/).
2. The script accepts --days N flag (default 5) to control simulation length.
3. Running the script with a valid ANTHROPIC_API_KEY produces back/tools/audit_outputs/p33_t1_deviation_audit.json containing: (a) a list of per-tick records each with world_day, tick_type, raw_llm_response, verdict fields, and (b) an aggregate_summary section with per-field deviation counts and per-tick-type deviation counts.
4. Running the script produces back/tools/audit_outputs/p33_t1_deviation_report.md containing: (a) a ranked table of deviation patterns by frequency, (b) identification of which OUTPUT_FORMAT_SECTION rules correlate with observed deviations, and (c) a summary of structural failures vs semantic deviations vs passes.
5. The script does not crash on LLM connection failures — it records them as LLM_CONNECTION_FAILURE entries and continues to subsequent ticks/days.
6. The script does not modify any simulation state files, seed data, or engine modules.
7. The script imports and uses comparison_harness.run_comparison() or the shadow_runner + acceptance_rules pipeline (not a reimplementation).

## Review Focus
- Verify the audit script uses the existing comparison_harness / shadow_runner / acceptance_rules pipeline rather than reimplementing deviation detection.
- Verify the JSON output structure captures enough raw data (especially raw_llm_response) to be useful for P33-T2 prompt tightening.
- Verify the markdown report actually maps deviations back to specific prompt instructions from OUTPUT_FORMAT_SECTION, not just generic field names.
- Verify no forbidden files were modified.
- Verify the script handles the full multi-day simulation lifecycle correctly (seed → advance_day loop) rather than constructing artificial inputs.

## Code Changes (git diff)
```diff

diff --git a/back/tools/audit_llm_deviation.py b/back/tools/audit_llm_deviation.py
new file mode 100644
index 0000000..9be8301
--- /dev/null
+++ b/back/tools/audit_llm_deviation.py
@@ -0,0 +1,874 @@
+#!/usr/bin/env python3
+"""
+CyberLife LLM Appraisal Deviation Audit — P33-T1
+
+Runs a controlled multi-day simulation calling the LLM for all active ticks
+(T1/T2/T4), collects raw LLM responses, classifies every deviation between
+LLM output and the deterministic baseline using acceptance_rules, and produces
+a structured JSON report and a human-readable markdown report.
+
+Usage:
+  python tools/audit_llm_deviation.py --days 5
+  python tools/audit_llm_deviation.py --days 10
+
+Outputs (in tools/audit_outputs/):
+  p33_t1_deviation_audit.json      per-tick records + aggregate summary
+  p33_t1_deviation_report.md       ranked deviation table + analysis
+
+Requires: ANTHROPIC_API_KEY environment variable.
+"""
+
+from __future__ import annotations
+
+import argparse
+import json
+import os
+import sys
+from collections import defaultdict
+from datetime import datetime
+from pathlib import Path
+from typing import Optional
+
+# ── Path setup — must precede all app imports ──────────────────────────────────
+SCRIPT_DIR = Path(__file__).resolve().parent     # back/tools/
+BACK_DIR   = SCRIPT_DIR.parent                   # back/
+OUTPUT_DIR = SCRIPT_DIR / "audit_outputs"
+sys.path.insert(0, str(BACK_DIR))
+
+from app.domain.appraisal_input import (
+    AgentContextSlice,
+    AppraisalInput,
+    RelationalContextSlice,
+    SocialEventContextSlice,
+    WorldContextSlice,
+)
+from app.domain.enums import EventCategory, RelationshipType
+from app.engines.world_continuity import derive_continuity
+from app.llm.comparison_harness import ComparisonReport, run_comparison
+from app.services import snapshot_store, state_store
+from app.services.advance_day import advance_day as _advance_day
+from app.world.generator import get_world_snapshot
+
+# ── Constants ──────────────────────────────────────────────────────────────────
+
+AGENT_ID = "milo-001"
+
+# Map from field name to the OUTPUT_FORMAT_SECTION rule it exercises.
+FIELD_TO_RULE: dict[str, str] = {
+    "absorption":         "OUTPUT_FORMAT: absorption field — <none|surface|partial|deep>",
+    "valence":            "OUTPUT_FORMAT: valence field — <positive|neutral|negative>",
+    "arousal":            "OUTPUT_FORMAT: arousal field — <low|medium|high>",
+    "aftershock_days":    "OUTPUT_FORMAT: aftershock_days — integer 0-3; 0 when absorption=none",
+    "growth":             "OUTPUT_FORMAT: growth list — max 3 entries, no duplicate dimensions",
+    "relational":         "OUTPUT_FORMAT: relational block — required for T2/T4; null for T1",
+    "guidance_resonance": "OUTPUT_FORMAT: guidance_resonance — <aligned|neutral|resisted>",
+    "tick_type":          "OUTPUT_FORMAT: tick_type structural agreement",
+}
+
+
+# ── Reset ──────────────────────────────────────────────────────────────────────
+
+
...(truncated)
```

## Your Task
1. Check each acceptance criterion against the actual code changes
2. Pay special attention to the review focus items
3. If existing test files were modified, examine whether the modifications are justified
4. Verify tests pass and no regressions were introduced

Write `review_verdict.json` with:
- `verdict` — PASS, FAIL, or REVISION_REQUIRED
- `confidence` — high, medium, or low
- `met_criteria` — list of criteria that passed
- `unmet_criteria` — list of criteria that failed
- `blocker_fixes` — must-fix issues (empty if PASS)
- `non_blocking_suggestions` — nice-to-have improvements
- `rationale` — explanation of verdict
