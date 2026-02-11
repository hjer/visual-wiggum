#!/usr/bin/env bash
set -euo pipefail

MODE="build"
MAX_ITERATIONS=0
ITERATION=0

if [[ "${1:-}" == "plan" ]]; then
  MODE="plan"
  shift
fi

if [[ -n "${1:-}" ]]; then
  MAX_ITERATIONS="$1"
fi

PROMPT_FILE="PROMPT_${MODE}.md"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Error: $PROMPT_FILE not found"
  exit 1
fi

echo "=== Ralph Wiggum Loop ==="
echo "Mode: $MODE"
echo "Max iterations: ${MAX_ITERATIONS:-unlimited}"
echo ""

while true; do
  ITERATION=$((ITERATION + 1))

  if [[ "$MAX_ITERATIONS" -gt 0 && "$ITERATION" -gt "$MAX_ITERATIONS" ]]; then
    echo "=== Reached max iterations ($MAX_ITERATIONS) ==="
    break
  fi

  echo "=== Iteration $ITERATION ($MODE mode) ==="

  # Each iteration gets a fresh context window
  cat "$PROMPT_FILE" | claude --dangerously-skip-permissions -p -

  EXIT_CODE=$?
  if [[ $EXIT_CODE -ne 0 ]]; then
    echo "=== Claude exited with code $EXIT_CODE, stopping ==="
    break
  fi

  echo "=== Iteration $ITERATION complete ==="
  echo ""
done

echo "=== Loop finished after $ITERATION iterations ==="
