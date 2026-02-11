# spec-view - Universal Spec-Driven Development Dashboard

## Context

AI-driven development tools (Claude Code, Cursor, Kiro, Copilot) are converging on spec-driven workflows where requirements, design, and tasks live as markdown files. But there's no simple, universal **viewer** for these specs. Kiro is a full IDE, spec-kit is GitHub-specific, and others are tightly coupled to specific tools.

**spec-view** is a lightweight Python package that gives any developer - regardless of their AI tool or IDE - a clear dashboard of their project's specs, tasks, and design docs. Install with `pip install spec-view`, run `spec-view` in your project, done.

---

## Spec Format (Default Convention)

### Directory structure (user-facing)
```
project-root/
├── .spec-view/              # Config (optional)
│   └── config.yaml         # Custom paths, format overrides
└── specs/                  # Default spec directory
    ├── overview.md          # Project-level overview (optional)
    ├── auth-system/
    │   ├── spec.md          # Requirements + acceptance criteria
    │   ├── design.md        # Technical design
    │   └── tasks.md         # Implementation tasks
    └── payment-flow/
        ├── spec.md
        ├── design.md
        └── tasks.md
```

### Markdown + YAML frontmatter format
```markdown
---
title: User Authentication
status: in-progress        # draft | ready | in-progress | done | blocked
priority: high             # low | medium | high | critical
tags: [auth, backend]
---

## Overview
Brief description of this feature/component.

## Requirements
- [ ] OAuth2 provider integration
- [x] JWT token generation
- [ ] Refresh token rotation

## Acceptance Criteria
- Users can sign in via Google/GitHub
- Sessions persist across reloads
```

### Flexible reading
- Default: reads from `specs/` directory
- Config can point to any glob pattern (e.g., `docs/**/*.md`, `.kiro/**/*.md`)
- Parses any markdown with YAML frontmatter - missing fields get sensible defaults
- Also reads plain markdown without frontmatter (title from first `#` heading, status defaults to `draft`)

---

## Architecture

### Tech Stack
- **Python 3.10+**
- **Textual** - TUI framework (Rich under the hood)
- **FastAPI** - Web server (lightweight, async)
- **Jinja2** + **htmx** + vanilla CSS - Web UI (no JS build step, no npm)
- **gray-matter equivalent**: `python-frontmatter` for parsing
- **watchfiles** - File watching for live reload
- **Click** - CLI framework

### Package structure
```
spec-view/
├── pyproject.toml
├── README.md
├── src/
│   └── spec_view/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py       # Config loading (.spec-view/config.yaml)
│       │   ├── parser.py       # Markdown + frontmatter parser
│       │   ├── models.py       # Spec, Task, Design dataclasses
│       │   ├── scanner.py      # Directory scanning, file discovery
│       │   └── watcher.py      # File change watching
│       ├── tui/
│       │   ├── __init__.py
│       │   ├── app.py          # Textual app
│       │   ├── dashboard.py    # Main dashboard screen
│       │   ├── spec_view.py    # Spec detail view
│       │   └── task_board.py   # Task progress view
│       └── web/
│           ├── __init__.py
│           ├── server.py       # FastAPI app
│           ├── templates/      # Jinja2 HTML templates
│           │   ├── base.html
│           │   ├── dashboard.html
│           │   ├── spec.html
│           │   └── tasks.html
│           └── static/         # CSS, minimal JS (htmx)
│               ├── style.css
│               └── htmx.min.js
└── tests/
    ├── test_parser.py
    ├── test_scanner.py
    └── test_models.py
```

---

## CLI Commands

```bash
spec-view init              # Create specs/ dir with example spec
spec-view                   # Launch TUI dashboard (default)
spec-view list              # Simple text table of all specs + status
spec-view serve             # Start web dashboard at localhost:8080
spec-view serve --port 3000 # Custom port
spec-view watch             # TUI with live file watching
spec-view validate          # Check specs for format issues
```

---

## Key Views

### TUI (Textual)
1. **Dashboard** - Split view:
   - Left panel: Spec tree (collapsible directories)
   - Right panel: Selected spec content rendered as rich markdown
   - Bottom bar: Status summary (3 done, 2 in-progress, 1 blocked)
2. **Task Board** - Table/list view:
   - All tasks across specs, grouped by status
   - Checkbox markers from markdown rendered visually
   - Filter by status, priority, tags
3. **Keyboard navigation**: j/k to move, Enter to expand, q to quit, / to search

### Web UI (FastAPI + Jinja2 + htmx)
1. **Dashboard page** (`/`):
   - Progress cards per spec (title, status badge, task completion %)
   - Overall project progress bar
   - Quick filters by status/priority/tag
2. **Spec detail page** (`/spec/<name>`):
   - Rendered markdown with nice typography
   - Tab navigation: Requirements | Design | Tasks
   - Status and metadata sidebar
3. **Task board page** (`/tasks`):
   - Kanban columns: Draft | Ready | In Progress | Done | Blocked
   - Cards show task title, parent spec, priority
4. **Live reload**: watchfiles + htmx polling or SSE for auto-refresh when specs change

---

## Implementation Phases

### Phase 1: Core + CLI basics
- `pyproject.toml` with Click entry point
- `core/parser.py` - Parse markdown + YAML frontmatter using `python-frontmatter`
- `core/models.py` - Spec, Task dataclasses
- `core/scanner.py` - Walk `specs/` dir, discover and parse all spec files
- `core/config.py` - Load `.spec-view/config.yaml` (optional)
- `cli.py` - `spec-view init`, `spec-view list` (simple Rich table output)
- Tests for parser and scanner

### Phase 2: TUI
- Textual app with dashboard screen
- Spec tree navigation (left panel)
- Markdown rendering in detail pane (right panel)
- Task board view
- Status bar with summary counts
- Keyboard shortcuts

### Phase 3: Web UI
- FastAPI server with Jinja2 templates
- Dashboard page with spec cards
- Spec detail page with rendered markdown
- Task board page (kanban-style)
- Static CSS (clean, modern, no framework needed)
- htmx for interactivity without a JS build step

### Phase 4: Polish + Distribution
- `spec-view watch` with live reload (both TUI and web)
- `spec-view validate` command
- Package on PyPI: `pip install spec-view`
- Also support `pipx install spec-view` for isolated install
- README with usage examples

### Phase 5: Format-Aware Parsing (spec-kit, Kiro, OpenSpec)

Auto-detect which spec tool produced files, extract tool-specific metadata, and display it in both TUI and web UI.

**Models:**
- `Task` — new fields: `task_id` (e.g. "T001"), `parallel` (bool, `[P]` marker), `story` (e.g. "US1")
- New `Phase` dataclass — number, title, subtitle, tasks, checkpoint; computed `task_total`/`task_done`/`task_percent`
- `SpecFile` — new fields: `phases` list, `format_type` string
- `SpecGroup` — new properties: `all_phases`, `format_type`, `stories`

**Parser:**
- `detect_format(body, path)` — returns `"spec-kit"` | `"kiro"` | `"openspec"` | `"generic"` based on path patterns and content signatures
- `_extract_task_metadata(text)` — strips `T\d+` IDs, `[P]` parallel markers, `[US\d+]` story refs from task text
- `_parse_phases(body, flat_tasks)` — splits on `## Phase N:` headings, assigns tasks by position, extracts `**Checkpoint**:` lines
- `parse_spec_file()` — calls format detection, metadata extraction, and phase parsing

**TUI:**
- Detail pane: phase-structured view with `⇄` parallel icons, dim task IDs, colored story tags, `⏸` checkpoints
- Task board: groups by phase when available, falls back to pending/done
- Dashboard tree: format badge (`[spec-kit]`) and phase sub-nodes with progress

**Web UI:**
- Phase sections with collapsible headers and progress bars in tasks and spec detail pages
- Task ID badges, parallel icons, story tags, checkpoint dividers
- Format badge on dashboard spec cards, mini phase progress bars
- CSS: `.task-id`, `.parallel-badge`, `.story-tag`, `.phase-section`, `.checkpoint`, `.format-badge`

---

## Config Format (`.spec-view/config.yaml`)

```yaml
# Where to find spec files (default: specs/)
spec_paths:
  - specs/
  - docs/specs/

# Glob patterns for additional spec files
include:
  - "**/*.spec.md"

# File patterns to ignore
exclude:
  - "**/node_modules/**"
  - "**/.git/**"

# Web server settings
serve:
  port: 8080
  open_browser: true

# Status values (customizable)
statuses:
  - draft
  - ready
  - in-progress
  - done
  - blocked
```

---

## Verification

1. **Unit tests**: `pytest tests/` - parser, scanner, models
2. **Manual TUI test**: `spec-view` in a project with sample specs
3. **Manual web test**: `spec-view serve` and check all pages
4. **Init test**: `spec-view init` creates correct directory structure
5. **Edge cases**: No specs dir, empty specs, malformed frontmatter, plain markdown without frontmatter
6. **Install test**: `pip install -e .` then run `spec-view` from another directory
