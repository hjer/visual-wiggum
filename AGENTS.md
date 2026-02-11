# AGENTS.md

Operational reference for autonomous Claude iterations working on spec-view.

## Build & Test

```bash
source .venv/bin/activate

# Run all tests (do this before every commit)
python -m pytest

# Run a single test file
python -m pytest tests/test_parser.py

# Run a specific test
python -m pytest tests/test_parser.py::test_parse_tasks_checked -v

# Install in dev mode (if dependencies changed)
pip install -e ".[dev]"
```

## Project Layout

- `src/spec_view/` — main package
  - `cli.py` — Click CLI entry point
  - `core/` — models, parser, scanner, detector, config, watcher
  - `tui/` — Textual TUI (app, dashboard, spec_view, task_board)
  - `web/` — FastAPI server, Jinja2 templates, htmx partials
- `tests/` — pytest tests
- `specs/` — requirement specs (do not modify during build)

## Conventions

- Dataclasses for all models (in `core/models.py`)
- `pathlib.Path` for all file paths
- Regex-based markdown parsing in `core/parser.py`
- Tests use `tmp_path` fixtures for filesystem operations
- Click for CLI, Textual for TUI, FastAPI + htmx for web
