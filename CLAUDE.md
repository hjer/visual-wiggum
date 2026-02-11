# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**spec-view** — a universal spec-driven development dashboard (TUI + web) for tracking specs, tasks, and design docs across projects. Supports multiple spec formats: spec-kit, Kiro, OpenSpec, and plain markdown. Python 3.10+, published to PyPI as `spec-view`.

## Build & Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_parser.py

# Run a specific test
python -m pytest tests/test_parser.py::test_parse_tasks_checked -v

# Launch TUI
spec-view

# Launch web dashboard
spec-view serve

# Auto-detect spec sources in current directory
spec-view detect
```

Build system: **Hatchling** (pyproject.toml). Entry point: `spec-view = spec_view.cli:cli`.

## Architecture

The package lives in `src/spec_view/` and has three layers:

### Core (`core/`)
- **models.py** — Frozen-style dataclasses: `Status`/`Priority` enums, `Task` (recursive tree with subtask counting), `Phase`, `SpecFile`, `SpecGroup` (aggregates related files in a directory). All computed properties (task totals, percentages) are derived, not stored.
- **parser.py** — Regex-based markdown parsing pipeline: frontmatter extraction → format detection (spec-kit/kiro/openspec/generic) → checkbox task extraction with indentation-based tree building → phase parsing → metadata stripping (task IDs `T001`, parallel `[P]`, story refs `[US1]`).
- **scanner.py** — Walks configured `spec_paths`, applies include/exclude glob patterns, groups files by directory into `SpecGroup` objects.
- **detector.py** — Auto-detects spec sources by walking for marker directories (`specs/`, `.kiro/`, `openspec/changes/*/specs/`, `.spec/`, `docs/`). Max depth 4, skips node_modules/.git/.venv.
- **config.py** — Loads/saves `.spec-view/config.yaml`. Falls back to auto-detection if no config exists.
- **watcher.py** — Background thread watches `.md`/`.yaml` changes via `watchfiles`. `SpecChangeNotifier` provides async pub/sub for SSE.

### TUI (`tui/`)
Built on **Textual**. Main app (`app.py`) runs a background watcher thread and uses `call_from_thread()` for safe UI updates. Three screens: dashboard (two-pane spec tree + detail), spec view, task board. Keybindings: q/d/t/r.

### Web (`web/`)
**FastAPI** with **Jinja2** templates and **htmx** for partial updates. Full-page routes (`/`, `/spec/{name}`, `/tasks`) plus `/partials/*` endpoints for htmx fragments. `/events` SSE endpoint with debounced notifications for live reload.

### CLI (`cli.py`)
**Click** command group. Commands: `init`, default (TUI), `watch`, `serve`, `list`, `validate`, `detect`, `config`. Auto-resolves config via `_resolve_config()` which tries config file then auto-detection.

## Key Patterns

- All internal paths use `pathlib.Path`
- Task trees are built by indentation depth; `Task.children` forms the recursive structure
- `SpecGroup` aggregates a directory's spec/design/tasks files and exposes unified task counts
- Format detection (`detect_format()`) uses heuristics: phase headers for spec-kit, path patterns for kiro, numbered sections for openspec
- Config is stored in `.spec-view/config.yaml`, created on demand

## Testing

~36 tests across 4 modules in `tests/`. Uses `tmp_path` fixtures extensively for filesystem tests. Test coverage focuses on parsing edge cases, model aggregation, detection heuristics, and scanner glob patterns.
