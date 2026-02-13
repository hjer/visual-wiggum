# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**spec-view** — a universal spec-driven development dashboard (TUI + web) for tracking specs, tasks, and design docs across projects. Supports multiple spec formats: spec-kit, Kiro, OpenSpec, and plain markdown. Python 3.10+, published to PyPI as `spec-view`.

## Build & Development

```bash
# Install in development mode (requires venv)
.venv/bin/pip install -e ".[dev]"

# Run all tests
.venv/bin/pytest

# Run a single test file
.venv/bin/pytest tests/test_parser.py

# Run a specific test
.venv/bin/pytest tests/test_parser.py::test_parse_tasks_checked -v

# Launch TUI
spec-view

# Launch web dashboard
spec-view serve

# Auto-detect spec sources in current directory
spec-view detect
```

Build system: **Hatchling** (pyproject.toml). Entry point: `spec-view = spec_view.cli:cli`. Python venv at `.venv/`.

## Releasing

Releases are done via **GitHub release flow** — not manual PyPI uploads. To release:
1. Bump version in `pyproject.toml`
2. Run `.venv/bin/python -m build` to verify the build succeeds before pushing
3. Commit and push to `main`
4. Create a GitHub release (tag + release notes) — this triggers the CI pipeline to publish to PyPI

Never run `twine upload` manually for releases.

## Architecture

The package lives in `src/spec_view/` and has three layers:

### Core (`core/`)
- **models.py** — Frozen-style dataclasses: `Status`/`Priority` enums, `Task` (recursive tree with subtask counting), `Phase`, `SpecFile`, `SpecGroup` (aggregates related files in a directory). All computed properties (task totals, percentages) are derived, not stored.
- **parser.py** — Regex-based markdown parsing pipeline: frontmatter extraction → format detection (spec-kit/kiro/openspec/generic) → checkbox task extraction with indentation-based tree building → phase parsing → metadata stripping (task IDs `T001`, parallel `[P]`, story refs `[US1]`).
- **scanner.py** — Walks configured `spec_paths`, applies include/exclude glob patterns, groups files by directory into `SpecGroup` objects. Auto-tags files in `archive/` directories with the `"archive"` tag.
- **detector.py** — Auto-detects spec sources by walking for marker directories (`specs/`, `.kiro/`, `openspec/changes/*/specs/`, `.spec/`, `docs/`). Max depth 4, skips node_modules/.git/.venv.
- **config.py** — Loads/saves `.spec-view/config.yaml`. Falls back to auto-detection if no config exists.
- **watcher.py** — Background thread watches `.md`/`.yaml` changes via `watchfiles`. Watches both `spec_paths` directories and parent directories of `include` pattern matches. `SpecChangeNotifier` provides async pub/sub for SSE.

### TUI (`tui/`)
Built on **Textual**. Main app (`app.py`) runs a background watcher thread and uses `call_from_thread()` for safe UI updates. Three screens: dashboard (two-pane spec tree + detail), spec view, task board.

- **dashboard.py** — Two-pane layout: spec tree (left) + scrollable detail pane (right). Active specs shown normally, archived specs grouped under a collapsible "Archive" node. Status bar excludes archived specs from active counts.
- **spec_view.py** — `SpecDetailView` extends `VerticalScroll` with an inner `Static` for rendered content. Vim-style navigation: `j`/`k` scroll, `h` returns focus to tree. Bindings shown in footer when focused.
- **task_board.py** — Tasks grouped under spec name headings with task counts. Archived tasks in a dimmed section at bottom.
- **app.py** — Keybindings: `q` quit, `d` dashboard, `t` tasks, `r` refresh.

### Web (`web/`)
**FastAPI** with **Jinja2** templates and **htmx** for partial updates. Full-page routes (`/`, `/spec/{name}`, `/tasks`) plus `/partials/*` endpoints for htmx fragments. `/events` SSE endpoint with debounced notifications for live reload.

- Groups are partitioned into active/plan/archived via `_partition_groups()` helper (returns triple).
- Dashboard and tasks pages have collapsible archive sections (collapsed by default, click to expand).

### CLI (`cli.py`)
**Click** command group. Commands: `init`, default (TUI), `watch`, `serve`, `list`, `validate`, `detect`, `config`. Auto-resolves config via `_resolve_config()` which tries config file then auto-detection.

## Key Patterns

- All internal paths use `pathlib.Path`
- Task trees are built by indentation depth; `Task.children` forms the recursive structure
- `SpecGroup` aggregates a directory's spec/design/tasks files and exposes unified task counts
- Archive detection: scanner auto-tags specs in `archive/` directories; UIs partition on `"archive" in g.tags`
- Format detection (`detect_format()`) uses heuristics: phase headers for spec-kit, path patterns for kiro, numbered sections for openspec, multiple `## ` sections with `**Status:**` for wiggum
- Wiggum plan sections: `IMPLEMENTATION_PLAN.md` is split into per-JTBD `SpecGroup` objects tagged `"plan"` (and `"plan-done"` when all tasks complete). UIs group these under a collapsible "Implementation Plan" section, separate from active specs and archive.
- Config is stored in `.spec-view/config.yaml`, created on demand

## Spec Archive Rules

- Never delete finished specs
- Set `status: done` in frontmatter
- Move from `specs/` to `specs/archive/`
- Update `specs/todo.md` to mark the item as `[x]`

## Specs Are Immutable

Files in `specs/` are requirements — **never modify them** during build or implementation. All progress tracking, gap analysis, and context updates go in `IMPLEMENTATION_PLAN.md`. Only humans create or edit specs.

## Post-Implementation Rule

After completing any fix, feature, or loop iteration:
1. Update `IMPLEMENTATION_PLAN.md` — mark tasks as done, add new sections for work completed
2. Update `specs/todo.md` — check off completed items (this is the only `specs/` file agents may update)
3. Update `CLAUDE.md` — reflect any architectural changes, new patterns, or new files
4. Update `AGENTS.md` — if agent workflow or conventions changed

## Testing

230 tests across 11 modules in `tests/`. Uses `tmp_path` fixtures extensively for filesystem tests. Test coverage focuses on parsing edge cases, model aggregation, detection heuristics, scanner glob patterns, config round-trip, web endpoint behavior, plan section rendering, progress bar, history views, and archive sub-grouping.
