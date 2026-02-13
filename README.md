# spec-view

A dashboard for spec-driven development. Terminal and web UI for tracking specs, tasks, and progress across your project.

Works with **spec-kit**, **Kiro**, **OpenSpec**, **Ralph Wiggum**, and plain markdown — auto-detected, zero config.

```bash
pip install spec-view
spec-view
```

That's it. Point it at a project with markdown specs and you get a live dashboard.

## Why

AI coding tools are converging on spec-driven workflows — requirements, design, and tasks as markdown files. But none of them ship a good way to *see* what's happening across all your specs at once.

spec-kit has no monitoring. Kiro locks you into their IDE. OpenSpec is just files.

spec-view reads all of them and gives you a single view of progress.

## Quick Start

```bash
spec-view init       # Scaffold a specs/ directory with examples
spec-view            # Launch TUI dashboard
spec-view serve      # Start web dashboard at localhost:8080
spec-view watch      # TUI with live file watching
spec-view list       # Simple text table of specs + status
spec-view validate   # Check specs for format issues
```

## What It Reads

Put specs in `specs/` (or configure any path):

```
specs/
├── auth-system/
│   ├── spec.md       # Requirements + acceptance criteria
│   ├── design.md     # Technical design
│   └── tasks.md      # Implementation tasks
└── payment-flow/
    ├── spec.md
    └── tasks.md
```

Each file supports optional YAML frontmatter:

```markdown
---
title: User Authentication
status: in-progress
priority: high
tags: [auth, backend]
---

## Requirements
- [ ] OAuth2 provider integration
- [x] JWT token generation
```

No frontmatter? That's fine — spec-view infers title from the first heading and treats everything as draft.

## Format-Aware Parsing

spec-view auto-detects which tool produced your files:

| Format | How it's detected | What's extracted |
|--------|-------------------|-----------------|
| **spec-kit** | `## Phase N:` + `T001` task IDs | Phases, task IDs, parallel markers, story refs, checkpoints |
| **Kiro** | `.kiro/` in file path | Indentation-based subtask trees |
| **OpenSpec** | `## 1.` numbered sections | Section structure |
| **Ralph Wiggum** | `IMPLEMENTATION_PLAN.md` at project root (auto-detected) | Per-JTBD sections with status, tasks, progress |
| **Generic** | Fallback | Checkbox tasks with subtask hierarchy |

### Ralph Wiggum Loop Support

spec-view is built to work with the [Ralph Wiggum loop](https://github.com/hjers/ralph-wiggum) — an iterative, autonomous spec-driven development workflow. The loop writes specs as requirements, tracks tasks in an `IMPLEMENTATION_PLAN.md`, and iterates with fresh context windows.

spec-view automatically detects `IMPLEMENTATION_PLAN.md` at the project root — no configuration needed. Loop progress is visible in the dashboard immediately, and the live watcher updates it in real time as each iteration completes.

### spec-kit Support

spec-kit generates structured task files but has zero monitoring — no watch, no status dashboard, no progress view. spec-view fills that gap.

A spec-kit `tasks.md`:

```markdown
## Phase 1: Setup
- [x] T001 [P] Configure project structure
- [x] T002 [P] Set up testing framework
- [x] T003 Install dependencies

**Checkpoint**: Foundation ready

## Phase 2: US1 - Login Flow
- [x] T004 [P] [US1] Create User model
- [ ] T005 [US1] Implement JWT validation
- [ ] T006 [P] [US1] Create login form
```

In the TUI:

```
Phase 1: Setup ✓ (3/3)
  ✓ T001 ⇄ Configure project structure
  ✓ T002 ⇄ Set up testing framework
  ✓ T003 Install dependencies
  ⏸ Checkpoint: Foundation ready

Phase 2: US1 - Login Flow (1/3)
  ✓ T004 ⇄ [US1] Create User model
  ○ T005 [US1] Implement JWT validation
  ○ T006 ⇄ [US1] Create login form
```

The web UI shows the same structure with collapsible phases, progress bars, and colored story tags.

## Dashboard Sections

Both UIs organize specs into collapsible sections:

- **Active** — ungrouped items
- **Specs** — spec files from your `spec_paths` directories
- **Implementation Plan** — per-JTBD sections parsed from `IMPLEMENTATION_PLAN.md`
- **Archive** — completed specs and plan sections, sub-grouped by source

There's also a **History** view showing recent git commits with loop iteration detection and completed task extraction.

## Live Updates

Both dashboards watch for file changes. Check off a task in your editor — the dashboard updates within a second.

## Running in a Dev Container

Sandboxed environment for running `claude --dangerously-skip-permissions`. The container can only access this repo — no home directory, SSH keys, or other repos. Git push is scoped via a fine-grained GitHub token.

```bash
# Prerequisites
colima start                          # or Docker Desktop
npm install -g @devcontainers/cli

# Setup (one time)
cp .devcontainer/.env.example .devcontainer/.env
# Edit .devcontainer/.env with your GitHub token + git identity

# Build container
devcontainer up --workspace-folder .

# First time: login to Claude inside the container
devcontainer exec --workspace-folder . claude  # then /login

# Run the Wiggum loop
./run-container.sh ./loop.sh

# Run any command
./run-container.sh .venv/bin/pytest
```

## Configuration

Optional `.spec-view/config.yaml`:

```yaml
spec_paths:
  - specs/
  - docs/specs/
include:
  - "**/*.spec.md"
exclude:
  - "**/node_modules/**"
serve:
  port: 8080
```

## License

MIT
