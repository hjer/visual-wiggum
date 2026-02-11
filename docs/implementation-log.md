# Implementation Log

Record of what was built during the initial implementation session.

## What was implemented

All four phases from the plan were completed in a single session.

### Phase 1: Core + CLI

- **`pyproject.toml`** - Hatchling build, Click entry point, all dependencies declared
- **`core/models.py`** - `Status` and `Priority` enums with `from_str()`, `Task`, `SpecFile`, and `SpecGroup` dataclasses with computed properties (task_percent, all_tasks, etc.)
- **`core/config.py`** - `Config` and `ServeConfig` dataclasses, `load_config()` reads `.spec-view/config.yaml` with sensible defaults
- **`core/parser.py`** - Uses `python-frontmatter` to parse YAML frontmatter + markdown body; extracts checkbox tasks via regex; auto-detects file type from filename; falls back to first `#` heading for title
- **`core/scanner.py`** - Walks configured `spec_paths`, respects `include`/`exclude` glob patterns, groups files by directory into `SpecGroup` objects
- **`cli.py`** - Click group with `init`, `list`, `serve`, `watch`, `validate` commands

### Phase 2: TUI (Textual)

- **`tui/app.py`** - Main app with keybindings (q=quit, d=dashboard, t=tasks, r=refresh), optional watch mode with background thread
- **`tui/dashboard.py`** - Split view with `SpecTree` (left) and `SpecDetailView` (right), status bar with summary counts, j/k navigation
- **`tui/spec_view.py`** - Rich-rendered spec detail showing title, status, priority, tags, task progress, and body content for all files in a group
- **`tui/task_board.py`** - Lists all tasks across all specs grouped by pending/done

### Phase 3: Web UI (FastAPI + Jinja2 + htmx)

- **`web/server.py`** - FastAPI app factory with 3 routes: dashboard (`/`), spec detail (`/spec/{name}`), task board (`/tasks`); renders markdown via `markdown` library
- **`web/templates/`** - 4 Jinja2 templates: base layout with nav, dashboard with spec cards + progress bar, spec detail with tab navigation, task board with kanban columns
- **`web/static/style.css`** - Dark theme CSS (GitHub-dark inspired), responsive grid, kanban columns, badges, progress bars
- **`web/static/htmx.min.js`** - htmx 1.9.12 for future interactivity

### Phase 4: Polish

- **`core/watcher.py`** - Uses `watchfiles` to watch spec directories, filters for `.md`/`.yaml` changes
- **`cli.py validate`** - Checks for missing titles, missing frontmatter status, empty body content
- **`README.md`** - Quick start guide, spec format docs, config example

### Tests

36 tests, all passing:
- **`tests/test_models.py`** - 13 tests: Status/Priority parsing, Task defaults, SpecFile task percentages, SpecGroup aggregation and deduplication
- **`tests/test_parser.py`** - 12 tests: checkbox extraction, file type detection, title parsing, full frontmatter parsing, no-frontmatter fallback, empty files, string tags
- **`tests/test_scanner.py`** - 8 tests: file discovery, exclude patterns, include patterns, empty/missing dirs, directory grouping, task aggregation across groups, multiple groups (replaced 3 with correct count)

## Dependencies

```
click>=8.0
python-frontmatter>=1.0
pyyaml>=6.0
rich>=13.0
textual>=0.40
fastapi>=0.100
uvicorn[standard]>=0.20
jinja2>=3.1
watchfiles>=0.20
markdown>=3.5
```

Dev: `pytest>=7.0`, `pytest-asyncio>=0.21`, `httpx>=0.24`

---

## Session 2: Format-Aware Parsing (spec-kit, Kiro, OpenSpec)

Added auto-detection of spec tool formats with enriched metadata and display.

### Phase 5.1: Model Enrichment

- **`core/models.py`** — Added `task_id`, `parallel`, `story` fields to `Task` dataclass. New `Phase` dataclass with `number`, `title`, `subtitle`, `tasks`, `checkpoint` and computed `task_total`/`task_done`/`task_percent` properties. Added `phases` list and `format_type` string to `SpecFile`. Added `all_phases`, `format_type`, `stories` properties to `SpecGroup`.

### Phase 5.2: Format Detection + Parsing

- **`core/parser.py`** — New `detect_format(body, path)` function: detects `"spec-kit"` (phases + task IDs), `"kiro"` (`.kiro/` in path), `"openspec"` (`## 1.` section headers), or `"generic"`. New `_extract_task_metadata(text)` helper: strips `T\d+` task IDs, `[P]` parallel markers, `[US\d+]` story refs from checkbox text, returns clean text + metadata. New `_parse_phases(body, flat_tasks)`: splits body on `## Phase N:` headings, assigns tasks to phases by position in the document, extracts `**Checkpoint**:` lines. Updated `parse_spec_file()` to call all three and populate new SpecFile fields.

### Phase 5.3: TUI Display

- **`tui/spec_view.py`** — Detail pane renders phase-structured view when phases exist: phase headers with completion counts, `⇄` icon for parallel tasks, dim task ID prefixes, `[magenta]` story tags, `⏸ Checkpoint:` lines. Falls back to flat tree for non-phase specs. Refactored task rendering into `_append_task_line()` and `_format_task_prefix()` helpers.
- **`tui/task_board.py`** — Task board groups by phase when phases exist (new `_render_phase_board()`), falls back to pending/done grouping. Added `_append_task_line()` with metadata display. Simplified `_render_task_tree()` to reuse the shared helper.
- **`tui/dashboard.py`** — Tree labels show format badge (`[spec-kit]`) and phase sub-nodes with progress counts instead of file-type children when phases are available.

### Phase 5.4: Web Display

- **`web/server.py`** — `_tasks_context()` now passes `all_phases` to template. `_spec_context()` passes `phases`, `format_type`, `stories`.
- **`web/templates/partials/tasks_content.html`** — Renders phase sections with collapsible headers, progress bars, task ID badges, parallel icons, story tags, and checkpoint dividers when phases exist. Falls back to flat task list.
- **`web/templates/partials/spec_content.html`** — Shows format badge in header, story tags in meta, phase sections with progress before tab content.
- **`web/templates/partials/dashboard_content.html`** — Format badge on spec cards, mini phase progress bars on cards when phases exist.
- **`web/static/style.css`** — New styles: `.task-id` (monospace dim badge), `.parallel-badge` (⇄ yellow), `.story-tag` with per-story colors (US1=blue, US2=purple, US3=green, US4=yellow, US5=red), `.format-badge` (pill), `.phase-section` (collapsible), `.phase-header`, `.checkpoint` (dashed divider), `.card-phases` with `.phase-mini` progress bars.

### Phase 5.5: Tests

24 new tests added (89 total, all passing):
- **`tests/test_parser.py`** — `TestDetectFormat` (4 tests: spec-kit, kiro, openspec, generic), `TestExtractTaskMetadata` (5 tests: task ID, parallel, story, all markers, no markers), `TestParsePhases` (2 tests: 3-phase split with checkpoints, subtitle parsing), `TestSpeckitFullParse` (1 end-to-end test: full tasks.md with phases + enriched metadata)
- **`tests/test_models.py`** — `TestTaskMetadataFields` (2 tests: defaults, with metadata), `TestPhase` (5 tests: task_total, task_done, task_percent, empty percent, checkpoint), `TestSpecFilePhases` (2 tests: populated, defaults), `TestSpecGroupPhases` (5 tests: all_phases from tasks file, format_type priority, generic fallback, stories collected, stories empty)
