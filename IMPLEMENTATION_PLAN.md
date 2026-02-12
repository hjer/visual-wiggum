# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.
> Completed sections archived to `IMPLEMENTATION_PLAN_ARCHIVE.md`.

---

## Preserve Group Headings in Archive Sections (`specs/archive-group-headings.md`)

**Status:** done | **Priority:** medium | **Tags:** tui, web, ux

When archived plan sections move into the Archive node, they lose their "Implementation Plan" grouping and appear flat alongside archived spec files. The fix is purely UI — partition archived groups by source tag and render sub-headings.

### Tasks

- [x] TUI Dashboard: sub-group archived plan sections under "Implementation Plan" node within Archive
  - In `dashboard.py` `_populate_tree()`, split `archived` into `archived_plan` (`"plan" in g.tags`) and `archived_specs` (rest)
  - If `archived_plan` is non-empty, add a dimmed "Implementation Plan (done/total)" sub-node inside the archive node, then add each archived plan group under it
  - Add remaining `archived_specs` directly under archive node as today
  - All archive text stays dimmed; archive node stays collapsed by default
  - **Done when:** archived plan sections appear under "Implementation Plan" sub-node within Archive, with aggregate counts

- [x] TUI Task Board: sub-group archived plan tasks under "Implementation Plan" heading within Archive
  - In `task_board.py` `_build_content()`, split `archived` into `archived_plan` and `archived_specs`
  - Render archived plan groups under a dimmed "Implementation Plan (done/total)" heading first
  - Then render archived spec groups under their own headings as today
  - All archived tasks remain dimmed
  - **Done when:** archived plan tasks grouped under "Implementation Plan" heading, archived spec tasks under their spec headings

- [x] Web Dashboard: sub-group archived plan cards under "Implementation Plan" sub-heading within Archive
  - In `dashboard_content.html`, partition `archived_groups` by `"plan" in group.tags`
  - Add "Implementation Plan" category heading inside the archive section for plan groups
  - Non-plan archived groups listed below without sub-heading (existing behavior)
  - Dimmed/muted styling preserved
  - **Done when:** archived plan section cards appear under "Implementation Plan" sub-heading in web archive

- [x] Web Tasks: sub-group archived plan tasks under "Implementation Plan" heading within Archive
  - In `tasks_content.html`, partition archived tasks by source
  - Need `archived_plan_groups` and `archived_spec_groups` (or `archived_plan_task_trees` / `archived_spec_task_trees`) in template context
  - Update `_tasks_context()` in `server.py` to pass plan vs spec archived groups separately
  - Render plan tasks under "Implementation Plan" heading, spec tasks under their headings
  - **Done when:** archived plan tasks grouped under "Implementation Plan" heading on web tasks page

- [x] Tests: add tests for archive sub-grouping in both TUI and web
  - Test TUI dashboard: archived plan groups appear under "Implementation Plan" sub-node within Archive
  - Test TUI task board: archived plan tasks grouped under "Implementation Plan" heading
  - Test web dashboard: archived plan cards under category heading in archive section
  - Test web tasks: archived plan tasks grouped correctly
  - Test edge case: only archived specs (no plan) — no "Implementation Plan" sub-heading appears
  - Test edge case: only archived plan sections (no specs) — no bare items outside the sub-heading
  - **Done when:** all new tests pass and existing 176 tests still pass (now 187)

- [x] Update `specs/todo.md`: mark "Preserve group headings" as complete
- [x] Update `CLAUDE.md` and `AGENTS.md` if any patterns changed

---

## Discovered Issues

(No outstanding issues.)

## Learnings

- Completed plan sections are now tagged `"archive"` (not `"plan-done"`). The scanner auto-tags sections with all tasks done, and the existing `"archive" in g.tags` partitioning in both TUI and web handles the rest.
- The `Config.include` pattern mechanism in `scanner.py` already supports root-level file inclusion — no scanner changes needed for the IMPLEMENTATION_PLAN tracking spec.
- The SSE + htmx infrastructure is well-established; new partial endpoints just need a route + template.
- Textual's `Static` widget auto-sizes to fit content — for scrollable detail views, use `VerticalScroll` with a `Static` child instead.
- The scanner already auto-tags archived specs with `"archive"` in their tags, making partitioning straightforward via `"archive" in g.tags`.
- The watcher must watch both `spec_paths` directories and parent directories of `include` pattern matches — otherwise root-level included files won't trigger live reloads.
- The existing UI partitioning logic (`"archive" in g.tags`) is designed so that adding `"archive"` to any group automatically moves it to the archive section — no UI code changes needed for dashboard or web server.
