#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"

# Start the devcontainer (no-op if already running)
echo "Starting devcontainer..."
devcontainer up --workspace-folder "$WORKSPACE"

# Run claude (or any command) inside the container
if [[ $# -eq 0 ]]; then
  echo "Launching Claude with --dangerously-skip-permissions..."
  devcontainer exec --workspace-folder "$WORKSPACE" claude --dangerously-skip-permissions
else
  devcontainer exec --workspace-folder "$WORKSPACE" "$@"
fi
