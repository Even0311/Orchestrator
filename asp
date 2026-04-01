#!/usr/bin/env bash
# Wrapper: activates venv and forwards all args to orch CLI
source "$(dirname "$0")/.venv/bin/activate"
exec orch "$@"
