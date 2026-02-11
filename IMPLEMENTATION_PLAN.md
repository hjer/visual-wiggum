# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.

---

## Spec: Track IMPLEMENTATION_PLAN.md (`specs/track-implementation-plan.md`)

**Status:** ready | **Priority:** high | **Tags:** core, dogfooding

### Gap Analysis

The spec requires that `IMPLEMENTATION_PLAN.md` (at the project root) appears in the spec-view dashboard so the Ralph Wiggum loop progress is visible.

**Current state:**
- `Config.include` supports glob patterns (list[str], default empty). The scanner (`scanner.py:discover_spec_files`) already iterates `config.include` patterns and runs `root.glob(pattern)` to find matching files — so the mechanism works.
- No `.spec-view/config.yaml` file exists yet. Without it, auto-detection runs and only finds `specs/`.
- The parser already handles generic markdown with checkboxes, so `IMPLEMENTATION_PLAN.md` will parse correctly — no parser changes needed.
- The scanner's grouping logic will create a standalone `SpecGroup` for the file (since it's a single file in the project root, it'll get `group_name = "IMPLEMENTATION_PLAN"` with `path = root`).

**What's missing:**
- A `.spec-view/config.yaml` with `include: ["IMPLEMENTATION_PLAN.md"]` so the scanner picks up the file.
- Verification that the title is correctly derived (the parser's `parse_title_from_body()` should extract `"Implementation Plan"` from the `# Implementation Plan` heading).

### Tasks

#### 1. Create `.spec-view/config.yaml` with include pattern
- [x] Create `.spec-view/config.yaml` with `spec_paths: [specs/]` and `include: ["IMPLEMENTATION_PLAN.md"]`.
- **Why:** Without this config, the scanner only looks in `specs/` and never sees the root-level implementation plan. The spec requires this file to be tracked.
- **Done when:** `spec-view list` (or the TUI/web dashboard) shows `IMPLEMENTATION_PLAN` as a spec group with its checkbox task counts.

#### 2. Verify parsing and display of IMPLEMENTATION_PLAN.md
- [x] Run `spec-view list` and confirm the file appears with correct title and task counts.
- [ ] Verify in TUI (`spec-view`) that the group shows up in the tree.
- **Why:** The spec says "no parser changes should be needed" — this task confirms that assumption is correct.
- **Done when:** The implementation plan appears in both TUI and web dashboards with accurate checkbox counts matching the actual `- [ ]` / `- [x]` items in the file.

### Iteration Plan

- **Iteration 1:** Task 1 + Task 2 (create config file + verify — minimal work, ~5 lines in 1 file)

---

## Spec: Global Progress Bar (`specs/global-progress-bar.md`)

**Status:** ready | **Priority:** high | **Tags:** tui, web, ux

### Gap Analysis

The spec requires a persistent, always-visible progress bar at the bottom of both the TUI and web UI showing overall task completion. Here's what exists vs. what's needed:

**TUI — Current state:**
- `DashboardScreen` has a `#status-bar` (1-row `Static` widget docked to bottom) that shows plain text like `" 3 specs: 1 draft, 2 done | Tasks: 5/12"`. No visual bar characters, no percentage.
- `TaskBoardScreen` has **no** status bar or progress indicator at all — just Header, task content, and Footer.
- Neither screen uses Textual's `ProgressBar` or Rich bar characters (`━`/`─`).

**Web — Current state:**
- `dashboard_content.html` has a progress bar (`.summary-bar` with `.progress-container` + `.progress-bar`) at the top of the dashboard page. Shows filled bar + text like `"5/12 tasks complete (41%)"`.
- This bar is **not** in `base.html` — it lives inside the dashboard partial, so it disappears on `/tasks` and `/spec/{name}`.
- No `/partials/global-progress` endpoint exists.
- SSE + htmx infrastructure is already in place (specchange events, partial refresh pattern).

**Shared:**
- The progress computation (`sum(group.task_done) / sum(group.task_total)`) is already done in `server.py:_dashboard_context()` and `dashboard.py:_status_summary()`, but it's not extracted into a shared/reusable spot.

---

### Tasks

#### 1. TUI: Create shared progress bar widget and add to DashboardScreen
- [ ] Create a reusable progress bar widget (or rendering function) in `src/spec_view/tui/` that both screens can use. Use Rich bar characters (`━` filled, `─` unfilled) in a `Static` widget — simpler than Textual's `ProgressBar` and fits the 1-row constraint.
- [ ] In `src/spec_view/tui/dashboard.py`, replace the plain-text `#status-bar` with this widget. Display: green-filled bar + percentage + fraction (`done/total`) + existing spec status counts (e.g. "3 draft, 2 done").
- [ ] Keep it exactly 1 row tall, docked to bottom, above the Footer. Green fill on dark surface background.
- **Why:** The spec requires a visual progress indicator on DashboardScreen. Both screens need the same bar, so extract it from the start to avoid duplication.
- **Done when:** `DashboardScreen` shows a green-filled bar with percentage, fraction, and status counts in a single bottom row above Footer. The widget is importable by TaskBoardScreen.

#### 2. TUI: Add progress bar to TaskBoardScreen
- [ ] In `src/spec_view/tui/task_board.py`, add the shared progress bar widget (from task 1), docked to bottom, above Footer.
- [ ] Must live-update when `update_groups()` is called (same pattern as dashboard).
- **Why:** The spec says "The progress bar must also appear on `TaskBoardScreen`, not just the dashboard." Currently TaskBoardScreen has zero progress indication.
- **Done when:** `TaskBoardScreen` has the same visual progress bar as DashboardScreen, and it updates live via the watcher.

#### 3. Web: Add global progress bar to `base.html` with partial endpoint and SSE wiring
- [ ] Add `GET /partials/global-progress` route in `src/spec_view/web/server.py` returning a progress bar HTML fragment. Compute `sum(group.task_done) / sum(group.task_total)` as integer percentage. 0% with empty bar when zero tasks.
- [ ] Create a `partials/global_progress.html` template with the bar markup.
- [ ] Add a fixed-position progress bar div to `src/spec_view/web/templates/base.html`, pinned to the bottom of the viewport. Use `hx-get="/partials/global-progress"` `hx-trigger="load, specchange from:body"` `hx-swap="innerHTML"` so it self-loads on page load and auto-updates on SSE events.
- [ ] Style: `--bg` background, `--green` fill, subtle top border, ~32-36px tall. Add `padding-bottom` to `.container` in `style.css` to prevent content overlap.
- **Why:** The spec requires the bar on all pages. Using `hx-trigger="load"` avoids changing every route's context dict — the bar fetches its own data.
- **Done when:** A thin progress bar is visible at the bottom of every page (`/`, `/tasks`, `/spec/{name}`), updates live via SSE, and doesn't overlap content.

#### 4. Tests: Add tests for progress bar computation
- [ ] Add tests verifying progress percentage: normal case, zero tasks (0%), all done (100%), single task.
- [ ] Test that both TUI screens include the progress bar widget.
- **Why:** The spec emphasizes correct behavior with zero tasks (0% + empty bar, not an error).
- **Done when:** `python -m pytest` passes with new tests covering the progress computation and widget presence.

### Priority Order & Dependencies

1. **Task 1** (TUI shared widget + dashboard) — foundational
2. **Task 2** (TUI task board) — depends on task 1
3. **Task 3** (Web global bar) — independent of TUI track, can be done in parallel with 1+2
4. **Task 4** (Tests) — after implementation

### Iteration Plan

- **Iteration 1:** Tasks 1 + 2 (TUI progress bar — shared widget + both screens, ~60 lines across 2-3 files)
- **Iteration 2:** Task 3 (Web progress bar — template + endpoint + CSS, ~50 lines across 4 files)
- **Iteration 3:** Task 4 (Tests)

### Notes & Potential Issues

- The dashboard's existing inline progress bar (`.summary-bar` in `dashboard_content.html`) is page-level, not global. The spec says to add a **global** bar to `base.html`. Keep both — the spec doesn't say to remove the dashboard's inline bar.
- Textual's built-in `ProgressBar` widget has animation/ETA features we don't need. Rich bar characters (`━`/`─`) in a `Static` widget are simpler and fit the 1-row constraint better.
- Using `hx-trigger="load, specchange from:body"` on the bar div is the cleanest approach — it fetches from the partial on page load AND on SSE events, keeping `base.html` self-contained without changing every route's context dict.

---

## Discovered Issues

- None yet.

## Learnings

- The `Config.include` pattern mechanism in `scanner.py` already supports root-level file inclusion — no scanner changes needed for the IMPLEMENTATION_PLAN tracking spec.
- The SSE + htmx infrastructure is well-established; new partial endpoints just need a route + template.
