# Implementation Plan — Archive

> Completed JTBD sections moved here per plan archive convention.

---

## Config: Persist `serve` and `statuses` Settings — DONE

**Status:** done | **Priority:** low | **Tags:** core

`save_config()` only persisted `spec_paths`/`include`/`exclude`, dropping custom `serve` (port, open_browser) and `statuses` on save. Fixed to include non-default serve and statuses fields in YAML output. Only changed fields are written (e.g., custom port without open_browser).

- [x] In `config.py:save_config()`, include `serve` section (port, open_browser) in YAML output when values differ from defaults
- [x] In `config.py:save_config()`, include `statuses` in YAML output when values differ from defaults
- [x] Add tests: save config with custom serve port → reload → port preserved; save with custom statuses → reload → statuses preserved (6 tests in `test_config.py`)
- [x] Definition of done: `save_config()` round-trips all config fields, not just `spec_paths`/`include`/`exclude`

---

## Preserve Group Headings in Archive Sections (`specs/archive/archive-group-headings.md`) — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, web, ux, archive

When archived plan sections move into the Archive node, they lose their "Implementation Plan" grouping and appear flat alongside archived spec files. The fix is purely UI — partition archived groups by source tag and render sub-headings.

### Tasks

- [x] TUI Dashboard: sub-group archived plan sections under "Implementation Plan" node within Archive
- [x] TUI Task Board: sub-group archived plan tasks under "Implementation Plan" heading within Archive
- [x] Web Dashboard: sub-group archived plan cards under "Implementation Plan" sub-heading within Archive
- [x] Web Tasks: sub-group archived plan tasks under "Implementation Plan" heading within Archive
- [x] Tests: add tests for archive sub-grouping in both TUI and web
- [x] Update `specs/todo.md`: mark "Preserve group headings" as complete
- [x] Update `CLAUDE.md` and `AGENTS.md` if any patterns changed

---

## Spec: Track IMPLEMENTATION_PLAN.md (`specs/track-implementation-plan.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, dogfooding, archive

### Tasks

- [x] Create `.spec-view/config.yaml` with `spec_paths: [specs/]` and `include: ["IMPLEMENTATION_PLAN.md"]`.
- [x] Run `spec-view list` and confirm the file appears with correct title and task counts.
- [x] Verify in TUI (`spec-view`) that the group shows up in the tree.

---

## Collapsible Archive Section — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, web, ux, archive

### Tasks

- [x] TUI dashboard: partition groups into active/archived, render archive as collapsed tree node with expand/collapse
- [x] TUI task board: partition groups, render archived tasks in dimmed section at bottom
- [x] TUI status bar: exclude archived specs from active counts, show separate "N archived" note
- [x] Web server: add `_partition_groups()` helper, update `_dashboard_context()` and `_tasks_context()` to pass active/archived separately
- [x] Web dashboard template: collapsible archive section with spec cards after active grid
- [x] Web tasks template: collapsible archive section with task list at bottom
- [x] CSS: archive-section collapse styles with rotating arrow indicator

---

## TUI Detail Pane Scrolling & Navigation — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, ux, archive

### Tasks

- [x] Change `SpecDetailView` from `Static` to `VerticalScroll` container with inner `Static` for content
- [x] Add `j`/`k` scroll bindings and `h` to return focus to tree
- [x] Auto-focus detail pane on spec selection (enter)
- [x] Remove 2000-character content truncation (scrolling makes it unnecessary)
- [x] Show navigation bindings (j/k/h) in footer when detail pane is focused

---

## TUI Task Board: Group Tasks by Spec — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, ux, archive

### Tasks

- [x] Add `_render_group_tasks()` method to render tasks under spec headings
- [x] Refactor `_build_content()` to iterate groups instead of merging all tasks into flat lists
- [x] Archived groups render with dimmed headings

---

## Watcher: Watch Include Pattern Files — DONE

**Status:** done | **Priority:** high | **Tags:** core, bugfix, archive

### Tasks

- [x] Extract `_collect_watch_paths()` helper that builds watch paths from both `spec_paths` and parent directories of `include` pattern matches
- [x] Refactor `watch_specs()` (TUI) and `start_watcher_thread()` (web) to use the shared helper
- [x] Deduplicate paths to avoid watching the same directory twice

---

## Spec: Global Progress Bar (`specs/global-progress-bar.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** tui, web, ux, archive

### Tasks

- [x] TUI: Create shared `ProgressBarWidget` in `progress_bar.py` with Rich bar chars, add to `DashboardScreen`
- [x] TUI: Add `ProgressBarWidget` to `TaskBoardScreen`
- [x] Web: Add `GET /partials/global-progress` endpoint, `global_progress.html` partial, fixed bar in `base.html` with SSE wiring
- [x] Tests: 6 async tests for progress computation and presence in `test_web_progress.py`

---

## Spec: Loop History View (`specs/loop-history.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, tui, web, ux, archive

### Tasks

- [x] Core: `history.py` with `CommitEntry` model, `get_history()` parsing git log + task extraction
- [x] TUI: `HistoryScreen` with two-pane layout (commit list + detail), `l` keybinding
- [x] Web: `/history` page + `/partials/history-content` partial + nav link + htmx/SSE
- [x] Tests: 14 core tests in `test_history.py`, 8 web tests in `test_web_history.py`

---

## Spec: Wiggum Plan Section Parsing (`specs/wiggum-plan-sections.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, tui, web, parser, archive

### Tasks

- [x] Core: `PlanSection` model, `detect_format("wiggum")`, `parse_plan_sections()`, `_expand_wiggum_sections()`
- [x] TUI: Dashboard and task board plan grouping under "Implementation Plan" parent node
- [x] Tests: 50 tests in `test_wiggum.py` covering parsing, expansion, edge cases
- [x] Web: `_partition_groups()` returns `(active, plan, archived)` triple
- [x] Web: Dashboard plan section grouping with collapsible "Implementation Plan" section
- [x] Web: Tasks page plan section grouping with per-section headings
- [x] Web tests: 9 tests in `test_web_plan.py`

---

## Remove `"plan-done"` tag — replace with `"archive"` convention — DONE

**Status:** done | **Priority:** medium | **Tags:** core, tui, web, cleanup, archive

### Tasks

- [x] Core: In `scanner.py:_expand_wiggum_sections()`, replace `"plan-done"` tag with `"archive"` for completed plan sections
- [x] TUI task board: Remove `plan_active`/`plan_completed` split and "Completed" separator — just render all non-archived plan groups
- [x] Web dashboard template: Remove `active_plan`/`done_plan` split and `plan-done-card` class — render all plan groups uniformly
- [x] Web tasks template: Remove `active_plan_groups`/`done_plan_groups` split and "Completed" separator
- [x] CSS: Remove `.plan-done-card { opacity: 0.5; }` rule
- [x] Tests: Update `test_wiggum.py` assertions from `"plan-done"` to `"archive"`, update `test_web_plan.py` to verify done plan sections appear in archive section

---

## Housekeeping: Tech Debt & Code Quality — DONE

**Status:** done | **Priority:** low | **Tags:** chore, quality, archive

### Tasks

- [x] Fix version mismatch: `pyproject.toml` says `0.3.2` but `src/spec_view/__init__.py` says `0.2.2`. Sync `__init__.py` to match `pyproject.toml` (source of truth for the build system).
- [x] Fix deprecated `TemplateResponse` signature in `src/spec_view/web/server.py` (9 call sites). Change from `TemplateResponse(name, context)` to `TemplateResponse(request, name, context=context)` — eliminates deprecation warnings in tests.
- [x] Remove unused `CommitEntry` import in `src/spec_view/web/server.py` (line 18). Only `get_history` is used. Also removed unused `Status` import.

---

## Add "specs" Tag and Collapsible Specs Section Across All UIs — DONE

**Status:** done | **Priority:** high | **Tags:** core, tui, web, archive

The specs require a `"specs"` tag auto-applied by the scanner to files from `spec_paths` directories (non-archived, non-wiggum). This tag drives a separate collapsible "Specs" section in both TUI and web UIs, sitting between active items and the Implementation Plan section.

### Tasks

- [x] Scanner: Apply "specs" tag to spec_paths groups
- [x] TUI Dashboard: Add collapsible "Specs" section node with archive sub-grouping
- [x] TUI Task Board: Add "Specs" section heading with archive sub-grouping
- [x] Web: Upgrade `_partition_groups()` to return quad (active, specs, plan, archived)
- [x] Web Dashboard Template: Add collapsible "Specs" section with archive sub-grouping
- [x] Web Tasks Template: Add "Specs" section with archive sub-grouping
- [x] Progress Bar: Verify correct counting — TUI `_render_bar()` and web progress both count active + specs + plan (excluding archived). Added `tests/test_progress_bar.py` with 4 unit tests.

---

## TUI: Add Missing `r` Refresh Keybinding — DONE

**Status:** done | **Priority:** low | **Tags:** tui, archive

The spec (`specs/tui.md` lines 12-18) requires app-level keybinding `r` for refresh. The `action_refresh()` method already existed in `app.py` but the `r` binding was missing from the `BINDINGS` list. Added the binding — both manual `r` refresh and background watcher auto-refresh now work as the spec requires.

- [x] Add `Binding("r", "refresh", "Refresh", show=True)` to `SpecViewApp.BINDINGS` in `app.py`

---

## TUI: Remove Undefined Search Binding — DONE

**Status:** done | **Priority:** low | **Tags:** tui, archive

`dashboard.py` had `Binding("slash", "focus_search", "Search", show=False)` but the `action_focus_search` action was never defined. Pressing `/` would cause a Textual error. The spec doesn't mention search functionality, so the binding was removed.

- [x] Remove the `Binding("slash", "focus_search", ...)` line from `DashboardScreen.BINDINGS` in `dashboard.py`

---

## Web Archive: Add "Other" Sub-group Category — DONE

**Status:** done | **Priority:** low | **Tags:** web, archive

`specs/web.md` (line 38) specifies archive sub-groups as `(plan/specs/other)`. The dashboard template already partitioned into plan/specs/other but rendered "Other" without a sub-heading. The tasks template only rendered plan and specs sub-groups, omitting "Other" entirely.

- [x] In `partials/dashboard_content.html`, add "Other (done/total)" `archive-sub-heading` for `archived_other_groups`
- [x] In `partials/tasks_content.html`, add "Other" sub-section rendering `archived_other_groups` with heading and per-group task trees
- [x] Add 4 web tests: dashboard/tasks with "Other" present, dashboard/tasks without "Other" when not applicable
- [x] Definition of done: Archived items are sub-grouped into plan/specs/other in both dashboard and tasks pages
