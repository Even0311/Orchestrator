import argparse
import sys
from pathlib import Path

from src.services.handover_service import generate_handover, save_handover
from src.services.task_packet_service import generate_task_packet, save_task_packet
from src.services.ingestion_service import ingest_artifact, IngestionError
from src.services.review_service import generate_review_packet, save_review_packet, ReviewError
from src.services.proposal_service import generate_state_update_proposal, save_state_update_proposal, ProposalError
from src.services.escalation_service import generate_escalation_packet, save_escalation_packet, EscalationError
from src.services.apply_service import apply_approved_update, ApplyError
from src.services.round_service import (
    start_round,
    ingest_round_run,
    generate_round_review,
    generate_round_proposal,
    generate_round_escalation,
    close_round,
    get_round_state,
    RoundError,
)
from src.services.submission_service import prepare_round_submission, SubmissionError
from src.services.invocation_service import prepare_round_invocation, InvocationError
from src.services.validation_service import validate_run_artifact
from src.models import SUPPORTED_ROLES
from src.utils.formatting import (
    print_handover_summary,
    print_task_packet_summary,
    print_run_artifact_summary,
    print_review_packet_summary,
    print_proposal_summary,
    print_escalation_summary,
    print_apply_result_summary,
    print_round_start_summary,
    print_round_ingest_summary,
    print_round_state_summary,
    print_prepare_submission_summary,
    print_invocation_summary,
    print_validation_result,
)


def cmd_generate_handover(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet = generate_handover(state_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = save_handover(packet, state_dir)
    print_handover_summary(packet)
    print(f"Saved → {output_path}")
    return 0


def cmd_generate_task_packet(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet = generate_task_packet(state_dir, args.role)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = save_task_packet(packet, state_dir)
    print_task_packet_summary(packet)
    print(f"Saved → {output_path}")
    return 0


def cmd_ingest_run(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    artifact_path = Path(args.file)
    try:
        artifact, saved_path = ingest_artifact(artifact_path, state_dir, args.project)
    except IngestionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_run_artifact_summary(artifact)
    print(f"Saved → {saved_path}")
    return 0


def cmd_generate_review_packet(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet = generate_review_packet(state_dir)
    except ReviewError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = save_review_packet(packet, state_dir)
    print_review_packet_summary(packet)
    print(f"Saved → {output_path}")
    return 0


def cmd_generate_state_update_proposal(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        proposal = generate_state_update_proposal(state_dir)
    except (ProposalError, Exception) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = save_state_update_proposal(proposal, state_dir)
    print_proposal_summary(proposal)
    print(f"Saved → {output_path}")
    return 0


def cmd_generate_escalation_packet(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet = generate_escalation_packet(state_dir)
    except EscalationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path = save_escalation_packet(packet, state_dir)
    print_escalation_summary(packet)
    print(f"Saved → {output_path}")
    return 0


def cmd_start_round(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        result = start_round(state_dir)
    except (RoundError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_round_start_summary(result)
    return 0


def cmd_ingest_round_run(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        result = ingest_round_run(state_dir, args.round, Path(args.file), args.project)
    except RoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_round_ingest_summary(result)
    return 0


def cmd_review_round(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet, saved = generate_round_review(state_dir, args.round)
    except RoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_review_packet_summary(packet)
    print(f"Saved → {saved}")
    return 0


def cmd_propose_round_update(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        proposal, saved = generate_round_proposal(state_dir, args.round)
    except RoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_proposal_summary(proposal)
    print(f"Saved → {saved}")
    return 0


def cmd_escalate_round(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        packet, saved = generate_round_escalation(state_dir, args.round)
    except RoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_escalation_summary(packet)
    print(f"Saved → {saved}")
    return 0


def cmd_show_round(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        state = get_round_state(state_dir, args.round)
    except RoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_round_state_summary(state)
    return 0


def cmd_close_round(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        result = close_round(state_dir, args.round)
    except (RoundError, ApplyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_apply_result_summary(result)
    print(f"Round {args.round} closed.")
    return 0


def cmd_prepare_round_submission(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        result = prepare_round_submission(state_dir, args.round)
    except (RoundError, SubmissionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_prepare_submission_summary(result)
    return 0


def cmd_validate_run_artifact(args: argparse.Namespace) -> int:
    artifact_path = Path(args.file)
    result = validate_run_artifact(artifact_path)
    print_validation_result(result, args.file)
    return 0 if result.valid else 1


def cmd_prepare_round_invocation(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    try:
        result = prepare_round_invocation(state_dir, args.round)
    except (RoundError, InvocationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print_invocation_summary(result)
    return 0


def cmd_apply_approved_update(args: argparse.Namespace) -> int:
    state_dir = Path.cwd() / "projects" / args.project
    proposal_path = (
        Path(args.proposal) if args.proposal else state_dir / "state_update_proposal.json"
    )
    try:
        result = apply_approved_update(state_dir, proposal_path)
    except ApplyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_apply_result_summary(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-orchestrator",
        description="Local project state manager and handover packet generator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser(
        "generate-handover",
        help="Read project state and generate a handover packet.",
    )
    gen.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory (e.g. cyber-community-v2).",
    )
    gen.set_defaults(func=cmd_generate_handover)

    task = subparsers.add_parser(
        "generate-task-packet",
        help="Generate a role-specific task packet from project state.",
    )
    task.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    task.add_argument(
        "--role",
        required=True,
        choices=sorted(SUPPORTED_ROLES),
        metavar="ROLE",
        help=f"Target role for the packet. One of: {', '.join(sorted(SUPPORTED_ROLES))}.",
    )
    task.set_defaults(func=cmd_generate_task_packet)

    ingest = subparsers.add_parser(
        "ingest-run",
        help="Ingest a structured implementation run artifact into the project.",
    )
    ingest.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    ingest.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to the run artifact JSON file to ingest.",
    )
    ingest.set_defaults(func=cmd_ingest_run)

    review = subparsers.add_parser(
        "generate-review-packet",
        help="Generate a review/audit packet from project state and the latest run artifact.",
    )
    review.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    review.set_defaults(func=cmd_generate_review_packet)

    proposal = subparsers.add_parser(
        "generate-state-update-proposal",
        help="Generate a conservative state update proposal from the latest run artifact and review packet.",
    )
    proposal.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    proposal.set_defaults(func=cmd_generate_state_update_proposal)

    escalation = subparsers.add_parser(
        "generate-escalation-packet",
        help="Evaluate escalation conditions and generate an exception/escalation packet.",
    )
    escalation.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    escalation.set_defaults(func=cmd_generate_escalation_packet)

    apply = subparsers.add_parser(
        "apply-approved-update",
        help="Apply an already-approved state update proposal to source-of-truth files.",
    )
    apply.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    apply.add_argument(
        "--proposal",
        default=None,
        metavar="PATH",
        help=(
            "Path to proposal JSON file. "
            "Defaults to projects/<name>/state_update_proposal.json."
        ),
    )
    apply.set_defaults(func=cmd_apply_approved_update)

    start = subparsers.add_parser(
        "start-round",
        help="Initialize a new round workspace with a Claude task file.",
    )
    start.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    start.set_defaults(func=cmd_start_round)

    ingest_round = subparsers.add_parser(
        "ingest-round-run",
        help="Attach a run artifact to a specific round workspace.",
    )
    ingest_round.add_argument(
        "--project",
        required=True,
        metavar="NAME",
        help="Project name as it appears under the orchestrator's projects/ directory.",
    )
    ingest_round.add_argument(
        "--round",
        required=True,
        metavar="ROUND_ID",
        help="Round id (e.g. round-0001).",
    )
    ingest_round.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to the run artifact JSON file to attach.",
    )
    ingest_round.set_defaults(func=cmd_ingest_round_run)

    def _add_round_parser(name, help_text, func):
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("--project", required=True, metavar="NAME",
                       help="Project name under the orchestrator's projects/ directory.")
        p.add_argument("--round", required=True, metavar="ROUND_ID",
                       help="Round id (e.g. round-0001).")
        p.set_defaults(func=func)

    _add_round_parser(
        "review-round",
        "Generate a review packet for a specific round.",
        cmd_review_round,
    )
    _add_round_parser(
        "propose-round-update",
        "Generate a state update proposal for a specific round.",
        cmd_propose_round_update,
    )
    _add_round_parser(
        "escalate-round",
        "Generate an escalation packet for a specific round.",
        cmd_escalate_round,
    )
    _add_round_parser(
        "show-round",
        "Show the current status and artifact checklist for a round.",
        cmd_show_round,
    )
    _add_round_parser(
        "close-round",
        "Apply the round's approved proposal and mark the round as closed.",
        cmd_close_round,
    )
    _add_round_parser(
        "prepare-round-submission",
        "Generate (or refresh) the Claude submission envelope and run artifact template for a round.",
        cmd_prepare_round_submission,
    )
    _add_round_parser(
        "prepare-round-invocation",
        "Generate the Claude invocation descriptor (dry-run boundary) for a round.",
        cmd_prepare_round_invocation,
    )

    validate = subparsers.add_parser(
        "validate-run-artifact",
        help="Validate a run artifact JSON file against the expected contract before ingestion.",
    )
    validate.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="Path to the run artifact JSON file to validate.",
    )
    validate.set_defaults(func=cmd_validate_run_artifact)

    return parser
