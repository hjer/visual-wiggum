# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.
> Completed sections archived to `IMPLEMENTATION_PLAN_ARCHIVE.md`.

---

## Add "specs" Tag and Collapsible Specs Section Across All UIs

**Status:** in-progress | **Priority:** high | **Tags:** core, tui, web

The specs require a `"specs"` tag auto-applied by the scanner to files from `spec_paths` directories (non-archived, non-wiggum). This tag drives a separate collapsible "Specs" section in both TUI and web UIs, sitting between active items and the Implementation Plan section. Currently this tag doesn't exist, so all spec-path files appear as generic active items with no grouping.

**Specs**: `specs/scanning.md` (line 34), `specs/tui.md` (lines 28-29, 48), `specs/web.md` (lines 32-34)

#### 1. Scanner: Apply "specs" tag to spec_paths groups

- [x] In `scanner.py:scan_specs()`, after grouping is complete, iterate sorted non-plan groups and tag any group whose `path` is under a configured `spec_paths` directory (and not already tagged `"archive"`) with `"specs"`
- [x] The tag must NOT be applied to wiggum-format expanded groups (they get `"plan"`)
- [x] Add tests in `test_scanner.py`: groups from `specs/` get `"specs"` tag; groups from `specs/archive/` get `"archive"` but NOT `"specs"`; standalone `include` files do NOT get `"specs"` tag; wiggum files do NOT get `"specs"` tag
- [x] Definition of done: `scan_specs()` returns groups where spec-path files carry `"specs"` in their tags, all existing tests still pass

#### 2. TUI Dashboard: Add collapsible "Specs" section node

- [x] In `dashboard.py:_populate_tree()`, partition active groups into `specs_groups` (`"specs" in g.tags`) and `other_active` (everything else)
- [x] Render `other_active` groups at tree root (existing behavior for truly ungrouped items)
- [x] Add collapsible "Specs" node (like "Implementation Plan") with aggregate `(done/total)` count, containing `specs_groups` alphabetically
- [x] Only show "Specs" node if `specs_groups` is non-empty
- [x] Update archive sub-grouping: archived specs (`"specs" in g.tags and "archive" in g.tags`) should appear under dimmed "Specs" heading within Archive, not listed directly
- [x] Add/update tests in `test_archive_subgroups.py` for the new "Specs" sub-group within Archive
- [x] Definition of done: TUI tree shows Active items → Specs (collapsible) → Implementation Plan (collapsible) → Archive (collapsed, sub-grouped with plan/specs/other)

#### 3. TUI Task Board: Add "Specs" section heading

- [x] In `task_board.py:_build_content()`, partition active groups into `specs_groups` and `other_active`
- [x] Render `other_active` group tasks first (no heading)
- [x] Then render `specs_groups` tasks under a "Specs" heading with aggregate count (like "Implementation Plan" heading)
- [x] Update archive section: sub-group archived specs under dimmed "Specs" heading (matching dashboard pattern)
- [x] Definition of done: Task board shows: active tasks → "Specs" section → "Implementation Plan" section → "Archive" section (sub-grouped)

#### 4. Web: Upgrade `_partition_groups()` to return quad

- [x] In `server.py`, change `_partition_groups()` return type to `tuple[list, list, list, list]` returning `(active, specs, plan, archived)` where `specs` = has `"specs"` tag, no `"archive"` tag; `active` = no `"archive"`, `"specs"`, or `"plan"` tags
- [x] Update `_dashboard_context()` to unpack quad and pass `specs_groups` to template
- [x] Update `_tasks_context()` to unpack quad and pass `specs_groups`/`specs_task_trees`/`specs_phases` to template
- [x] Update `_global_progress_context()` to include specs groups in counted total
- [x] Update all existing web tests (`test_web_plan.py`, `test_web_progress.py`) for the new quad structure — all 204 tests pass without changes needed since scanner already tags spec_paths groups with "specs" and templates don't reference specs_groups yet (Task 5)
- [x] Definition of done: `_partition_groups()` returns 4-tuple, all endpoints pass correct data to templates, existing tests updated and passing

#### 5. Web Dashboard Template: Add collapsible "Specs" section

- [ ] In `partials/dashboard_content.html`, add a collapsible "Specs" section between active items and "Implementation Plan" (same pattern as plan section)
- [ ] Show aggregate progress for specs section `(done/total)`
- [ ] Update archive section to sub-group archived specs under dimmed "Specs" heading (matching plan sub-group pattern)
- [ ] Add tests for specs section presence and content in web dashboard
- [ ] Definition of done: Web dashboard shows Active → Specs (collapsible) → Plan (collapsible) → Archive (collapsed, sub-grouped)

#### 6. Web Tasks Template: Add "Specs" section

- [ ] In `partials/tasks_content.html`, add a "Specs" section between active tasks and "Implementation Plan"
- [ ] Show specs-tagged group tasks under "Specs" heading with aggregate count
- [ ] Update archive section to sub-group archived specs (matching dashboard pattern)
- [ ] Add tests for specs section presence in web tasks page
- [ ] Definition of done: Web tasks page shows Active tasks → Specs section → Plan section → Archive section (sub-grouped)

#### 7. Progress Bar: Verify correct counting

- [ ] In `tui/progress_bar.py:_render_bar()`, the current filter `"archive" not in g.tags` includes both active, specs, and plan groups in the count — this is actually correct per spec ("excludes archived specs from active counts"). The progress bar should count ALL non-archived work. Verify web progress computation also counts active + specs + plan. No code change expected here, just verification.
- [ ] Definition of done: Both TUI and web progress bars count active + specs + plan tasks (excluding archived), confirmed by test review

---

## TUI: Add Missing `r` Refresh Keybinding

**Status:** pending | **Priority:** low | **Tags:** tui

The spec (`specs/tui.md` lines 12-18) requires app-level keybinding `r` for refresh. The `action_refresh()` method already exists in `app.py:83` and works correctly, but the `r` binding is missing from the `BINDINGS` list at `app.py:29-34`. If it's done automaticcally, should we remove the key binding? 

- [ ] remove key binding, since updated automatically 

---

## TUI: Remove Undefined Search Binding

**Status:** pending | **Priority:** low | **Tags:** tui

`dashboard.py:66` has `Binding("slash", "focus_search", "Search", show=False)` but the `action_focus_search` action is never defined. This will cause a Textual error if a user presses `/`. The spec doesn't mention search functionality, so this binding should be removed.

- [ ] Remove the `Binding("slash", "focus_search", ...)` line from `DashboardScreen.BINDINGS` in `dashboard.py`
- [ ] Definition of done: No undefined action bindings in TUI; pressing `/` no longer triggers an error

---

## Config: Persist `serve` and `statuses` Settings

**Status:** pending | **Priority:** low | **Tags:** core

`specs/config.md` defines `serve` (port, open_browser) and `statuses` as config fields. `config.py` loads them correctly from YAML, but `save_config()` (lines 86-95) never writes them back. Custom serve settings and status definitions are lost on config save.

- [ ] In `config.py:save_config()`, include `serve` section (port, open_browser) in YAML output when values differ from defaults
- [ ] In `config.py:save_config()`, include `statuses` in YAML output when values differ from defaults
- [ ] Add tests: save config with custom serve port → reload → port preserved; save with custom statuses → reload → statuses preserved
- [ ] Definition of done: `save_config()` round-trips all config fields, not just `spec_paths`/`include`/`exclude`

---

## Web Archive: Add "Other" Sub-group Category

**Status:** pending | **Priority:** low | **Tags:** web

`specs/web.md` (line 38) specifies archive sub-groups as `(plan/specs/other)`. Currently the archive section only splits into `plan` and everything-else (treated as specs). Items that are archived but have neither `"plan"` nor `"specs"` tags (e.g., standalone include files that get archived) should appear under a separate "Other" heading, not mixed with specs.

- [ ] In `partials/dashboard_content.html`, split `archived_spec_groups` into `archived_specs` (`"specs" in g.tags`) and `archived_other` (neither `"plan"` nor `"specs"`)
- [ ] Render `archived_other` under their own section (no heading, or "Other" heading) if non-empty
- [ ] Apply same pattern in `partials/tasks_content.html`
- [ ] Definition of done: Archived items are sub-grouped into plan/specs/other in both dashboard and tasks pages

---

## Discovered Issues

- **`discover_spec_files()` loses origin information**: The function returns a flat `list[Path]` with no metadata about whether each file came from `spec_paths` or `include` patterns. When applying the `"specs"` tag, the scanner must infer origin by checking if the file's path is under a configured `spec_paths` directory. This works but is fragile — if a future `include` pattern points inside a `spec_paths` directory, it would incorrectly get the `"specs"` tag. Current approach is acceptable because the spec defines `include` for root-level files like `IMPLEMENTATION_PLAN.md`, not for files inside `spec_paths`.

## Learnings

- Completed plan sections are now tagged `"archive"` (not `"plan-done"`). The scanner auto-tags sections with all tasks done, and the existing `"archive" in g.tags` partitioning in both TUI and web handles the rest. The `specs/scanning.md` spec (line 36, 46) explicitly says `"plan + archive"` for done plan sections.
- The `Config.include` pattern mechanism in `scanner.py` already supports root-level file inclusion — no scanner changes needed for the IMPLEMENTATION_PLAN tracking spec.
- The SSE + htmx infrastructure is well-established; new partial endpoints just need a route + template.
- Textual's `Static` widget auto-sizes to fit content — for scrollable detail views, use `VerticalScroll` with a `Static` child instead.
- The scanner already auto-tags archived specs with `"archive"` in their tags, making partitioning straightforward via `"archive" in g.tags`.
- The watcher must watch both `spec_paths` directories and parent directories of `include` pattern matches — otherwise root-level included files won't trigger live reloads.
- The existing UI partitioning logic (`"archive" in g.tags`) is designed so that adding `"archive"` to any group automatically moves it to the archive section — no UI code changes needed for dashboard or web server.
- The "specs" tag is the missing piece that connects scanner output to UI grouping. Without it, all spec-path files appear as generic active items. The tag must be applied at the scanner level (after grouping, before return) so all UIs can partition consistently.
- The `r` keybinding gap is trivial — `action_refresh()` already exists and works; only the binding declaration is missing.
- The undefined `slash`/`focus_search` binding in dashboard.py is dead code that could cause runtime errors — safe to remove since the spec doesn't define search.
- The quad partition in `_partition_groups()` was a clean addition — `"specs"` tagged groups were previously mixed into `active`, and the existing tests passed without changes because the scanner was already tagging correctly. The `_tasks_context()` now also computes `archived_other_groups` for items with neither `"plan"` nor `"specs"` tags, preparing for the "Other" archive sub-group.
