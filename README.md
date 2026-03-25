# Agent Orchestrator

A lightweight local tool for managing AI-assisted development sessions.

## What it does

Long conversations with LLM agents (Claude, ChatGPT, etc.) hit context limits and
lose track of project state. This tool maintains structured state files for each
project and generates a compact **handover packet** — a single JSON snapshot you
can paste into a new session to immediately resume where you left off.

## v1 scope

| Feature | Status |
|---|---|
| Read `project_charter.md`, `working_state.yaml`, `decision_log.yaml` | ✓ |
| Generate `handover_packet.json` | ✓ |
| Print terminal summary | ✓ |
| CLI: `generate-handover` | ✓ |

Not included in v1: LLM API calls, notifications, web UI, multi-user sync.

## Setup

```bash
cd agent_orchestrator
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Generate a handover packet for the sample project
python main.py generate-handover --project projects/sample_project

# Point at any project directory that has the three state files
python main.py generate-handover --project /path/to/your/project
```

The command:
1. Reads `project_charter.md`, `working_state.yaml`, `decision_log.yaml`
2. Writes `handover_packet.json` into the project directory
3. Prints a concise summary to the terminal

## Project state files

### `working_state.yaml`

Tracks the live state of a project. Edit this manually or via a future CLI command.

Key fields: `current_phase`, `current_goal`, `next_expected_step`,
`recent_progress`, `current_risks`, `context_notes`.

### `decision_log.yaml`

Append-only log of key decisions. Each entry has a `date`, `title`, `decision`,
`rationale`, and optional `alternatives_considered` / `impact`.

### `project_charter.md`

Free-form Markdown. The tool extracts:
- A summary excerpt from the first prose paragraph
- Core principles from a `## Core Principles` section (bullet list)

## Extending to LLM APIs (v2 roadmap)

**OpenAI / Claude summarisation**

Add an optional `--summarise` flag to `generate-handover`. The service layer
(`src/services/handover_service.py`) can call an LLM to compress the charter
excerpt and recent progress into a tighter summary before writing the packet.

```python
# sketch
if args.summarise:
    packet.charter_excerpt = llm_client.summarise(charter, max_tokens=150)
```

**Automatic state updates**

A future `update-state` command could accept natural-language input, send it to
an LLM with the current state, and write back a structured diff to `working_state.yaml`.

**Notifications**

A `notify` service could watch for high-severity risks and post to Slack or send
an email when `generate-handover` is run. Wire it into `cmd_generate_handover`
after the packet is saved.

## Directory structure

```
agent_orchestrator/
├── src/
│   ├── models/          # Pydantic data models
│   ├── services/        # File I/O and handover generation logic
│   ├── cli/             # argparse commands
│   └── utils/           # Terminal formatting helpers
├── projects/
│   └── sample_project/  # Example project with all state files
├── main.py
├── requirements.txt
└── README.md
```
