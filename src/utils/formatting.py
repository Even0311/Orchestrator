import json

from src.models import HandoverPacket, TaskPacket, ImplementationRunArtifact, ReviewPacket, StateUpdateProposal, EscalationPacket, RoundState
from src.services.apply_service import ApplyResult
from src.services.round_service import RoundStartResult, RoundIngestResult
from src.services.submission_service import PrepareSubmissionResult
from src.services.invocation_service import PrepareInvocationResult
from src.services.validation_service import ArtifactValidationResult

SEVERITY_ICON = {"low": "🟢", "medium": "🟡", "high": "🔴"}


def print_handover_summary(packet: HandoverPacket) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  HANDOVER PACKET  —  {packet.project_name}")
    print(f"  Generated: {packet.generated_at}")
    print(sep)

    print(f"\n[Phase]  {packet.current_phase}")
    print(f"[Goal]   {packet.current_goal}")

    if packet.recent_progress:
        print("\n[Recent Progress]")
        for p in packet.recent_progress:
            mark = "✓" if p.completed else "○"
            print(f"  {mark}  {p.item}")

    if packet.current_risks:
        print("\n[Current Risks]")
        for r in packet.current_risks:
            icon = SEVERITY_ICON.get(r.severity, "•")
            mitigation = f"  → {r.mitigation}" if r.mitigation else ""
            print(f"  {icon}  [{r.severity.upper()}] {r.description}{mitigation}")

    print(f"\n[Next Step]  {packet.next_expected_step}")

    if packet.recent_decisions:
        print("\n[Recent Decisions]")
        for d in packet.recent_decisions:
            print(f"  • [{d.date}] {d.title}")
            print(f"      {d.decision}")

    if packet.context_notes:
        print(f"\n[Context Notes]\n  {packet.context_notes}")

    print(f"\n{sep}\n")


def print_task_packet_summary(packet: TaskPacket) -> None:
    sep = "─" * 60
    role_label = packet.role.upper().replace("_", " ")
    print(f"\n{sep}")
    print(f"  TASK PACKET [{role_label}]  —  {packet.project_name}")
    print(f"  Generated: {packet.generated_at}")
    print(sep)

    print(f"\n[Phase]  {packet.current_phase}")
    print(f"[Goal]   {packet.current_goal}")

    if packet.decision_needed:
        print(f"\n[Decision Needed]\n  {packet.decision_needed}")

    if packet.why_now:
        print(f"\n[Why Now]\n  {packet.why_now}")

    if packet.project_summary:
        print(f"\n[Project Summary]\n  {packet.project_summary}")

    if packet.recent_progress:
        print("\n[Recent Progress]")
        for p in packet.recent_progress:
            mark = "✓" if p.completed else "○"
            print(f"  {mark}  {p.item}")

    if packet.current_risks:
        print("\n[Current Risks]")
        for r in packet.current_risks:
            icon = SEVERITY_ICON.get(r.severity, "•")
            mitigation = f"  → {r.mitigation}" if r.mitigation else ""
            print(f"  {icon}  [{r.severity.upper()}] {r.description}{mitigation}")

    if packet.next_expected_step:
        print(f"\n[Next Step]  {packet.next_expected_step}")

    if packet.inspect_next:
        print(f"\n[Inspect Next]  {packet.inspect_next}")

    if packet.implementation_boundaries:
        print("\n[Implementation Boundaries]")
        for b in packet.implementation_boundaries:
            print(f"  ✗  {b}")

    if packet.recent_decisions:
        print("\n[Recent Decisions]")
        for d in packet.recent_decisions:
            print(f"  • [{d.date}] {d.title}")
            print(f"      {d.decision.strip()}")

    if packet.context_notes:
        print(f"\n[Context Notes]\n  {packet.context_notes}")

    print(f"\n{sep}\n")


STATUS_ICON = {"success": "✅", "partial": "⚠️ ", "failed": "❌"}


def print_run_artifact_summary(artifact: ImplementationRunArtifact) -> None:
    sep = "─" * 60
    icon = STATUS_ICON.get(artifact.status, "•")
    print(f"\n{sep}")
    print(f"  RUN ARTIFACT  —  {artifact.project_name}")
    print(f"  Status: {icon} {artifact.status.upper()}")
    print(f"  Generated: {artifact.generated_at}")
    print(sep)

    print(f"\n[Task]\n  {artifact.task_summary}")

    if artifact.implemented_items:
        print("\n[Implemented]")
        for item in artifact.implemented_items:
            print(f"  ✓  {item}")

    if artifact.files_changed:
        print("\n[Files Changed]")
        for f in artifact.files_changed:
            print(f"  •  {f}")

    if artifact.tests_run:
        print("\n[Tests Run]")
        for t in artifact.tests_run:
            print(f"  •  {t}")

    if artifact.unresolved_items:
        print("\n[Unresolved]")
        for item in artifact.unresolved_items:
            print(f"  ○  {item}")

    if artifact.notes:
        print(f"\n[Notes]\n  {artifact.notes}")

    print(f"\n{sep}\n")


def print_review_packet_summary(packet: ReviewPacket) -> None:
    sep = "─" * 60
    icon = STATUS_ICON.get(packet.run_summary.status, "•")
    print(f"\n{sep}")
    print(f"  REVIEW PACKET  —  {packet.project_name}")
    print(f"  Generated: {packet.generated_at}")
    print(sep)

    print(f"\n[Phase]  {packet.current_phase}")
    print(f"[Goal]   {packet.current_goal}")

    rs = packet.run_summary
    print(f"\n[Run Status]  {icon} {rs.status.upper()}")
    print(f"[Task]  {rs.task_summary}")

    if rs.implemented_items:
        print("\n[Implemented]")
        for item in rs.implemented_items:
            print(f"  ✓  {item}")

    if rs.files_changed:
        print("\n[Files Changed]")
        for f in rs.files_changed:
            print(f"  •  {f}")

    if rs.tests_run:
        print("\n[Tests Run]")
        for t in rs.tests_run:
            print(f"  •  {t}")

    if rs.unresolved_items:
        print("\n[Unresolved]")
        for item in rs.unresolved_items:
            print(f"  ○  {item}")

    if rs.notes:
        print(f"\n[Run Notes]\n  {rs.notes}")

    if packet.current_risks:
        print("\n[Current Risks]")
        for r in packet.current_risks:
            icon_r = SEVERITY_ICON.get(r.severity, "•")
            mitigation = f"  → {r.mitigation}" if r.mitigation else ""
            print(f"  {icon_r}  [{r.severity.upper()}] {r.description}{mitigation}")

    if packet.recent_decisions:
        print("\n[Recent Decisions]")
        for d in packet.recent_decisions:
            print(f"  • [{d.date}] {d.title}")

    print(f"\n[Inspect Next]\n  {packet.inspect_next}")

    print(f"\n{sep}\n")


def print_proposal_summary(proposal: StateUpdateProposal) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  STATE UPDATE PROPOSAL  —  {proposal.project_name}")
    print(f"  Generated: {proposal.generated_at}")
    print(sep)

    def _section(label: str, items: list[str], prefix: str = "  →") -> None:
        if items:
            print(f"\n[{label}]")
            for item in items:
                print(f"{prefix}  {item}")

    _section("Proposed Progress Additions", proposal.proposed_recent_progress_additions, "  +")
    _section("Proposed Progress Updates", proposal.proposed_recent_progress_updates, "  ~")

    if proposal.proposed_current_goal_update:
        print(f"\n[Proposed Current Goal Update]\n  {proposal.proposed_current_goal_update}")

    if proposal.proposed_next_expected_step_update:
        print(f"\n[Proposed Next Step Update]\n  {proposal.proposed_next_expected_step_update}")

    _section("Proposed Risk Updates", proposal.proposed_risk_updates, "  !")
    _section("Proposed Decision Log Candidates", proposal.proposed_decision_log_candidates, "  ?")

    if proposal.explicitly_unchanged:
        print("\n[Explicitly Unchanged]")
        for item in proposal.explicitly_unchanged:
            print(f"  ─  {item}")

    if proposal.rationale_notes:
        print("\n[Rationale]")
        for note in proposal.rationale_notes:
            print(f"  •  {note}")

    print(f"\n{sep}\n")


SEVERITY_LABEL = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW", "none": "✅ NONE"}


def print_escalation_summary(packet: EscalationPacket) -> None:
    sep = "─" * 60
    label = SEVERITY_LABEL.get(packet.severity, packet.severity.upper())
    print(f"\n{sep}")
    print(f"  ESCALATION PACKET  —  {packet.project_name}")
    print(f"  Category: {packet.category}  |  Severity: {label}")
    print(f"  Generated: {packet.generated_at}")
    print(sep)

    print(f"\n[Why Now]\n  {packet.why_now}")

    ev = packet.evidence
    print(f"\n[Evidence]")
    print(f"  Artifact status: {ev.artifact_status}")
    if ev.unresolved_items:
        print("  Unresolved items:")
        for item in ev.unresolved_items:
            print(f"    ○  {item}")
    if ev.relevant_risks:
        print("  Relevant risks:")
        for r in ev.relevant_risks:
            print(f"    !  {r}")
    if ev.proposal_sections:
        print("  Proposal sections triggered:")
        for s in ev.proposal_sections:
            print(f"    •  {s}")

    print(f"\n[Recommended Human Action]\n  {packet.recommended_human_action}")

    if packet.explicitly_not_decided_by_system:
        print("\n[Explicitly NOT Decided by System]")
        for item in packet.explicitly_not_decided_by_system:
            print(f"  ✗  {item}")

    print(f"\n{sep}\n")


def print_round_start_summary(result: RoundStartResult) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  ROUND STARTED  —  {result.round_id}")
    print(sep)
    print(f"\n  Round dir:   {result.round_dir}")
    print(f"  State:       {result.round_state_path.name}")
    print(f"  Task packet: {result.task_packet_path.name}")
    print(f"  Task file:   {result.task_file_path.name}")
    print(f"\n  Hand {result.task_file_path.name} to Claude to begin this round.")
    print(f"\n{sep}\n")


def print_round_state_summary(state: RoundState) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  ROUND  —  {state.round_id}  [{state.status.upper()}]")
    print(f"  Project: {state.project_name}  |  Phase: {state.based_on_phase}")
    print(f"  Goal:    {state.based_on_goal}")
    print(sep)

    print(f"\n  Created: {state.created_at}")
    if state.updated_at:
        print(f"  Updated: {state.updated_at}")

    print("\n[Artifacts]")
    checks = [
        ("run_artifact.json",         state.has_run_artifact),
        ("review_packet.json",         state.has_review_packet),
        ("state_update_proposal.json", state.has_proposal),
        ("escalation_packet.json",     state.has_escalation),
    ]
    for name, present in checks:
        mark = "✓" if present else "○"
        print(f"  {mark}  {name}")

    if state.has_escalation and state.escalation_category:
        print(f"\n  Escalation category: {state.escalation_category}")

    print(f"\n{sep}\n")


def print_round_ingest_summary(result: RoundIngestResult) -> None:
    sep = "─" * 60
    replaced = " (replaced previous)" if result.previously_had_artifact else ""
    print(f"\n{sep}")
    print(f"  RUN ATTACHED  —  {result.round_id}")
    print(sep)
    print(f"\n  Artifact stored: {result.artifact_path}{replaced}")
    print(f"  Round status:    run_received")
    print(f"\n{sep}\n")


def print_prepare_submission_summary(result: PrepareSubmissionResult) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  SUBMISSION PREPARED  —  {result.round_id}")
    print(sep)
    print(f"\n  Round dir:  {result.round_dir}")
    print(f"\n[Artifacts Written]")
    print(f"  ✓  {result.envelope_path.name}")
    print(f"  ✓  {result.template_path.name}")
    print(f"\n  Hand claude_submission_envelope.json to Claude.")
    print(f"  Claude fills and returns run_artifact_template.json.")
    print(f"\n{sep}\n")


def print_validation_result(result: ArtifactValidationResult, path: str) -> None:
    sep = "─" * 60
    status = "VALID" if result.valid else "INVALID"
    print(f"\n{sep}")
    print(f"  ARTIFACT VALIDATION  —  {status}")
    print(f"  File: {path}")
    print(sep)
    if result.valid:
        print("\n  ✓  Run artifact is valid and ready to ingest.")
    else:
        print("\n[Errors]")
        for e in result.errors:
            print(f"  ✗  {e}")
    if result.warnings:
        print("\n[Warnings]")
        for w in result.warnings:
            print(f"  ⚠  {w}")
    print(f"\n{sep}\n")


def print_invocation_summary(result: PrepareInvocationResult) -> None:
    sep = "─" * 60
    inv = json.loads(result.invocation_path.read_text(encoding="utf-8"))
    print(f"\n{sep}")
    print(f"  INVOCATION READY  —  {result.round_id}  [adapter: {inv['adapter_mode']}]")
    print(sep)
    print(f"\n{inv['invocation_preview']}")
    print(f"\nDescriptor: {result.invocation_path}")
    print(f"\n{sep}\n")


def print_apply_result_summary(result: ApplyResult) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  APPLY UPDATE  —  {result.project_name}")
    print(sep)

    if result.no_op:
        print("\n  No applicable changes in proposal. Source files unchanged.")
    else:
        if result.sections_applied:
            print("\n[Changes Applied]")
            for section in result.sections_applied:
                print(f"  ✓  {section}")

        if result.backup_paths:
            print("\n[Backups Created]")
            for bp in result.backup_paths:
                print(f"  •  {bp}")

    print(f"\n{sep}\n")
