# Build Mode

You are in BUILD mode. Implement one task per iteration.

## Instructions

1. **Study** every file in `specs/` — these are the requirements. Don't assume something is not implemented; check first.
2. **Study** `AGENTS.md` for build/test commands and project conventions.
3. **Study** `IMPLEMENTATION_PLAN.md` — select the highest-priority incomplete task.
4. **Investigate** the relevant source code before making changes.

## Your task

Implement the selected task:

1. **Implement** — Make the necessary code changes. Use up to 3 parallel subagents for independent changes. If functionality is missing then it's your job to add it.
2. **Validate** — Run tests with `.venv/bin/pytest`. Only 1 subagent for test execution (backpressure). Fix any failures before proceeding.
3. **Update** — Mark the task as complete in `IMPLEMENTATION_PLAN.md`. Note any discoveries, new issues, or blockers you found.
4. **Commit** — Stage your changes and create a git commit with a message that captures the why.

## Rules

- One task per iteration. Do not try to do everything at once.
- Always validate before committing. If tests fail, fix them.
- Don't modify `specs/` — those are the requirements, not your output.
- Keep `AGENTS.md` concise. Progress notes go in `IMPLEMENTATION_PLAN.md`.
- If a task is blocked or too large, note it in the plan and move to the next one.
