# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.
> Completed sections archived to `IMPLEMENTATION_PLAN_ARCHIVE.md`.

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

- **`discover_spec_files()` loses origin information**: The function returns a flat `list[Path]` with no metadata about whether each file came from `spec_paths` or `include` patterns. When applying the `"specs"` tag, the scanner must infer origin by checking if the file's path is under a configured `spec_paths` directory. This works but is fragile — if a future `include` pattern points inside a `spec_paths` directory, it would incorrectly get the `"specs"` tag. Current approach is acceptable because the spec defines `include` for root-level files like `IMPLEMENTATION_PLAN.md`, not for files inside `spec_paths`. Note: the `"specs"` tag is now applied to ALL spec_paths groups (including archived ones) to support archive sub-grouping.

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
- The scanner now applies the `"specs"` tag to ALL spec_paths groups, including archived ones. Previously it skipped archived groups, but the archive sub-grouping in web templates needs the `"specs"` tag to distinguish archived specs from archived "other" items. The `_partition_groups()` filter `"specs" in g.tags and "archive" not in g.tags` ensures archived specs still go to the archive section, not the active specs section.
- The web Specs section uses a distinct `specs-section` CSS class (not `plan-section`) to avoid false positives in tests that check for `plan-section` absence.
