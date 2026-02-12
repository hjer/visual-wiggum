# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.

---

## Spec: Track IMPLEMENTATION_PLAN.md (`specs/track-implementation-plan.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, dogfooding

### Tasks

- [x] Create `.spec-view/config.yaml` with `spec_paths: [specs/]` and `include: ["IMPLEMENTATION_PLAN.md"]`.
- [x] Run `spec-view list` and confirm the file appears with correct title and task counts.
- [x] Verify in TUI (`spec-view`) that the group shows up in the tree.

---

## Collapsible Archive Section — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, web, ux

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

**Status:** done | **Priority:** medium | **Tags:** tui, ux

### Tasks

- [x] Change `SpecDetailView` from `Static` to `VerticalScroll` container with inner `Static` for content
- [x] Add `j`/`k` scroll bindings and `h` to return focus to tree
- [x] Auto-focus detail pane on spec selection (enter)
- [x] Remove 2000-character content truncation (scrolling makes it unnecessary)
- [x] Show navigation bindings (j/k/h) in footer when detail pane is focused

---

## TUI Task Board: Group Tasks by Spec — DONE

**Status:** done | **Priority:** medium | **Tags:** tui, ux

### Tasks

- [x] Add `_render_group_tasks()` method to render tasks under spec headings
- [x] Refactor `_build_content()` to iterate groups instead of merging all tasks into flat lists
- [x] Archived groups render with dimmed headings

---

## Watcher: Watch Include Pattern Files — DONE

**Status:** done | **Priority:** high | **Tags:** core, bugfix

### Tasks

- [x] Extract `_collect_watch_paths()` helper that builds watch paths from both `spec_paths` and parent directories of `include` pattern matches
- [x] Refactor `watch_specs()` (TUI) and `start_watcher_thread()` (web) to use the shared helper
- [x] Deduplicate paths to avoid watching the same directory twice

---

## Spec: Global Progress Bar (`specs/global-progress-bar.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** tui, web, ux

### Tasks

- [x] TUI: Create shared `ProgressBarWidget` in `progress_bar.py` with Rich bar chars, add to `DashboardScreen`
- [x] TUI: Add `ProgressBarWidget` to `TaskBoardScreen`
- [x] Web: Add `GET /partials/global-progress` endpoint, `global_progress.html` partial, fixed bar in `base.html` with SSE wiring
- [x] Tests: 6 async tests for progress computation and presence in `test_web_progress.py`

---

## Spec: Loop History View (`specs/loop-history.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, tui, web, ux

### Tasks

- [x] Core: `history.py` with `CommitEntry` model, `get_history()` parsing git log + task extraction
- [x] TUI: `HistoryScreen` with two-pane layout (commit list + detail), `l` keybinding
- [x] Web: `/history` page + `/partials/history-content` partial + nav link + htmx/SSE
- [x] Tests: 14 core tests in `test_history.py`, 8 web tests in `test_web_history.py`

---

## Spec: Wiggum Plan Section Parsing (`specs/wiggum-plan-sections.md`) — DONE

**Status:** done | **Priority:** high | **Tags:** core, tui, web, parser

### Tasks

- [x] Core: `PlanSection` model, `detect_format("wiggum")`, `parse_plan_sections()`, `_expand_wiggum_sections()`
- [x] TUI: Dashboard and task board plan grouping under "Implementation Plan" parent node
- [x] Tests: 50 tests in `test_wiggum.py` covering parsing, expansion, edge cases
- [x] Web: `_partition_groups()` returns `(active, plan, archived)` triple
- [x] Web: Dashboard plan section grouping with collapsible "Implementation Plan" section
- [x] Web: Tasks page plan section grouping with per-section headings
- [x] Web tests: 9 tests in `test_web_plan.py`

---

## Spec: Archive Completed Plan Sections (`specs/archive-done-plan-sections.md`)

**Status:** ready | **Priority:** medium | **Tags:** core, tui, web, ux

### Gap Analysis

The spec requires automatically archiving completed JTBD sections from `IMPLEMENTATION_PLAN.md` so they move from the "Implementation Plan" parent node to the "Archive" node in both UIs.

**Current state:**

- **Scanner (`scanner.py:_expand_wiggum_sections()`)**: When all tasks in a plan section are done, the section gets `"plan-done"` tag — but NOT the `"archive"` tag. The section stays under "Implementation Plan" (just dimmed in TUI task board with a "Completed" separator).
- **TUI dashboard (`dashboard.py:_populate_tree()`)**: Partitions on `"archive" in g.tags` for Archive and `"plan" in g.tags and "archive" not in g.tags` for Plan. Since done plan sections have `"plan"` but not `"archive"`, they stay under Plan. No code change needed — once scanner adds `"archive"`, they'll automatically move to Archive.
- **TUI task board (`task_board.py:_build_content()`)**: Has separate `"plan-done"` handling: a "Completed" separator within the Plan section, with dimmed done groups. The spec says to **remove** this — done plan sections should flow into the Archive section at bottom instead.
- **Web server (`server.py:_partition_groups()`)**: Partitions `(active, plan, archived)` where plan = `"plan" in g.tags and "archive" not in g.tags` and archived = `"archive" in g.tags`. Once scanner adds `"archive"`, done plan sections will correctly move from `plan` to `archived`. No code change needed.
- **Web templates**: Dashboard and tasks templates have `"plan-done"` handling within the plan section (dimmed cards, "Completed" separator). Same as TUI — this should be removed since archived plan sections will move to the archive section.
- **Progress bar**: TUI `progress_bar.py` counts all non-archived groups (active + plan). Web progress counts `active + plan`. Once done plan sections get `"archive"` tag, they'll be excluded from the progress count — which is the correct behavior per spec ("archived work shouldn't inflate the remaining work view").

**What needs to change:**

1. **Scanner**: Add `"archive"` tag (alongside `"plan"`) to done plan sections. Remove `"plan-done"` tag — it's no longer needed.
2. **TUI task board**: Remove the separate `"plan-done"` handling (the "Completed" separator within plan). Done plan sections will appear in the Archive section at bottom.
3. **Web templates**: Remove `"plan-done"` handling from dashboard and tasks templates.
4. **Tests**: Update existing tests that check for `"plan-done"` tag behavior.

**What does NOT need to change:**

- TUI dashboard — the existing `"archive" in g.tags` partitioning already handles this.
- Web `_partition_groups()` — already partitions on `"archive" in g.tags`.
- Web server routes — no code changes needed.
- Progress bar — already excludes `"archive"` tagged groups.

### Tasks

#### 1. Core: Add `"archive"` tag to done plan sections, remove `"plan-done"` tag
- [ ] In `scanner.py:_expand_wiggum_sections()`, change the tag logic: when a plan section has all tasks done (`task_done == task_total` and `task_total > 0`) OR its status is `done`, add `"archive"` to the group's tags alongside `"plan"`. Remove the `"plan-done"` tag entirely — replace it with `"archive"`.
- [ ] Handle the edge case: section with status `done` but no tasks (e.g., just notes with `**Status:** done`) should also get `"archive"`.
- [ ] Verify that sections with partial completion (e.g., 9/10 tasks done, status not `done`) do NOT get `"archive"`.
- **Done when:** `_expand_wiggum_sections()` adds `"archive"` (not `"plan-done"`) to completed plan sections. Both `"plan"` and `"archive"` tags are present on archived plan sections.

#### 2. TUI task board: Remove `"plan-done"` handling
- [ ] In `task_board.py:_build_content()`, remove the separate `plan_completed` list and the "Completed" separator within the Plan section. Active plan sections remain under "Implementation Plan". Done plan sections (now tagged `"archive"`) will naturally appear in the Archive section at bottom (the existing `archived = [g for g in self.groups if "archive" in g.tags]` already captures them).
- [ ] The Plan section header's aggregate count should only count non-archived plan groups: change `plan` filter to exclude `"archive"` tagged groups (i.e., `"plan" in g.tags and "archive" not in g.tags`).
- **Done when:** TUI task board shows no "Completed" separator within Plan. Done plan sections appear in Archive at bottom.

#### 3. Web templates: Remove `"plan-done"` handling
- [ ] In `partials/dashboard_content.html`, remove the dimmed "done plan cards" section within the Implementation Plan group. Done plan sections will appear in the Archive section instead.
- [ ] In `partials/tasks_content.html`, remove the "Completed" separator and dimmed done groups within the Implementation Plan section. Done plan tasks will appear in the Archive section.
- **Done when:** Web dashboard and tasks pages show no done plan sections within the Implementation Plan group. They appear in Archive instead.

#### 4. Tests: Update for archive-based plan section archiving
- [ ] Update `test_wiggum.py` tests that check for `"plan-done"` tag: change expectations to check for `"archive"` tag on completed plan sections.
- [ ] Add test: plan section with all tasks done has both `"plan"` and `"archive"` tags.
- [ ] Add test: plan section with status `done` but no tasks gets `"archive"` tag.
- [ ] Add test: partially complete plan section does NOT get `"archive"` tag.
- [ ] Update `test_web_plan.py` tests that reference `"plan-done"` card styling or completed separator — verify done plan sections appear in archive section instead.
- [ ] Run full test suite to verify no regressions.
- **Done when:** `.venv/bin/pytest` passes with updated tests. No references to `"plan-done"` remain in test expectations.

### Priority Order & Dependencies

1. **Task 1** (Core scanner) — foundational; everything else depends on the tag change
2. **Task 2** (TUI task board) — depends on task 1
3. **Task 3** (Web templates) — depends on task 1, can run parallel with task 2
4. **Task 4** (Tests) — after implementation, but should be done incrementally with each task

Tasks 2 and 3 can be done in parallel once task 1 is complete.

### Notes

- The `"plan-done"` tag is used in: `scanner.py` (assignment), `task_board.py` (filtering), `dashboard_content.html` (card styling), `tasks_content.html` (completed separator), and tests. All need updating.
- After this change, a plan section's lifecycle is: `"plan"` → `"plan" + "archive"`. The `"plan"` tag is preserved so UIs can still identify it as originating from the implementation plan (useful for rendering context).
- The progress bar behavior change is automatic: archived plan sections are excluded from active counts, which is the correct spec behavior.

---

## Housekeeping: Tech Debt & Code Quality

**Status:** draft | **Priority:** medium | **Tags:** chore, quality

### Tasks

- [ ] Fix version mismatch: `pyproject.toml` says `0.3.2` but `src/spec_view/__init__.py` says `0.2.2`. Sync `__init__.py` to match `pyproject.toml` (source of truth for the build system).
- [ ] Fix deprecated `TemplateResponse` signature in `src/spec_view/web/server.py` (9 call sites). Change from `TemplateResponse(name, context)` to `TemplateResponse(request, name)` with context as keyword arg — eliminates 26 deprecation warnings in tests.
- [ ] Remove unused `CommitEntry` import in `src/spec_view/web/server.py` (line 18). Only `get_history` is used.

---

## Discovered Issues

(No outstanding issues beyond housekeeping above.)

## Learnings

- The `Config.include` pattern mechanism in `scanner.py` already supports root-level file inclusion — no scanner changes needed for the IMPLEMENTATION_PLAN tracking spec.
- The SSE + htmx infrastructure is well-established; new partial endpoints just need a route + template.
- Textual's `Static` widget auto-sizes to fit content — for scrollable detail views, use `VerticalScroll` with a `Static` child instead.
- The scanner already auto-tags archived specs with `"archive"` in their tags, making partitioning straightforward via `"archive" in g.tags`.
- The watcher must watch both `spec_paths` directories and parent directories of `include` pattern matches — otherwise root-level included files won't trigger live reloads.
- Plan sections use the `"plan"` tag (auto-applied by scanner) for UI grouping. Done plan sections additionally get `"plan-done"`. These are distinct from `"archive"` — plan sections are not archived specs.
- The existing UI partitioning logic (`"archive" in g.tags`) is designed so that adding `"archive"` to any group automatically moves it to the archive section — no UI code changes needed for dashboard or web server.
