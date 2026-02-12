# AGENTS.md

Operational reference for autonomous Claude iterations working on spec-view.

## Build & Test

```bash
# Run all tests (do this after every change)
.venv/bin/pytest

# Run a single test file
.venv/bin/pytest tests/test_parser.py

# Run a specific test
.venv/bin/pytest tests/test_parser.py::test_parse_tasks_checked -v

# Install in dev mode (if dependencies changed)
.venv/bin/pip install -e ".[dev]"
```

Note: Always use `.venv/bin/pytest` directly — system python lacks dependencies.

## Project Layout

- `src/spec_view/` — main package
  - `cli.py` — Click CLI entry point
  - `core/` — models, parser, scanner, detector, config, watcher
  - `tui/` — Textual TUI (app, dashboard, spec_view, task_board)
  - `web/` — FastAPI server, Jinja2 templates, htmx partials, static CSS
- `tests/` — 176 pytest tests
- `specs/` — requirement specs (do not modify during build)
- `specs/archive/` — completed specs (never delete, status: done)
- `.spec-view/config.yaml` — scanner config (spec_paths, include, exclude)

## Development Loop

1. **Spec** — Humans write specs in `specs/`. Agents read them but **never modify them**.
2. **Plan** — Gap analysis and task breakdown go in `IMPLEMENTATION_PLAN.md`
3. **Implement** — Write code, run tests
4. **Update Context** — After every fix/feature/loop iteration, update:
   - `IMPLEMENTATION_PLAN.md` — mark tasks done, add sections for new work
   - `specs/todo.md` — check off completed items (only `specs/` file agents may update)
   - `CLAUDE.md` — reflect architectural changes, new patterns, new files
   - `AGENTS.md` — update if workflow or conventions changed
5. **Archive** — When a spec is fully done, move to `specs/archive/`, set `status: done`

**Specs are immutable requirements.** Never modify files in `specs/` (except `todo.md` checkboxes). All progress tracking and context updates go in `IMPLEMENTATION_PLAN.md`.

Context updates are mandatory, not optional. Stale docs cause stale decisions.

## Spec Archive Rules

- Never delete finished specs
- Set `status: done` in frontmatter
- Move from `specs/` to `specs/archive/`
- Update `specs/todo.md` to mark the item as `[x]`

## Conventions

- Dataclasses for all models (in `core/models.py`)
- `pathlib.Path` for all file paths
- Regex-based markdown parsing in `core/parser.py`
- Tests use `tmp_path` fixtures for filesystem operations
- Click for CLI, Textual for TUI, FastAPI + htmx for web

## Key Patterns

- **Archive detection**: scanner auto-tags specs in `archive/` directories; UIs partition on `"archive" in g.tags`
- **Active/archived partitioning**: both TUI and web split groups via `_partition_groups()` or inline list comprehensions
- **Watcher scope**: watches both `spec_paths` dirs and parent dirs of `include` pattern matches for live reload
- **TUI navigation**: vim-style — `j`/`k` scroll, `h` back to tree, `enter` opens detail, `q`/`d`/`t`/`l`/`r` global
- **TUI scrolling**: detail pane uses `VerticalScroll` with inner `Static` (not `Static` alone, which auto-sizes and can't scroll)
- **Task board grouping**: tasks are grouped under spec name headings, not flattened into a mixed list
- **Web collapsible sections**: reuse `.archive-section.collapsed` pattern with `onclick` toggle
