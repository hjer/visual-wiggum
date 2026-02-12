# Gap Analysis — 2026-02-12

## Summary

Compared all specs against the full codebase (10 source modules, 10+ templates, 176+ tests).

All 4 archived specs are fully implemented. One remaining item: cleanup of `"plan-done"` dead code.

## Completed Specs (no gaps)

| Spec | Status |
|------|--------|
| Track IMPLEMENTATION_PLAN.md | Done, archived |
| Global Progress Bar | Done, archived |
| Loop History View | Done, archived |
| Wiggum Plan Sections | Done, archived |

## Changes Made to IMPLEMENTATION_PLAN.md

1. **Archived 8 completed JTBD sections** to new `IMPLEMENTATION_PLAN_ARCHIVE.md` per AGENTS.md plan archive convention (added `archive` to Tags)

2. **Reframed remaining feature work** — "Archive completed plan sections" from `specs/todo.md` is marked done (convention-based approach via AGENTS.md). But the old `"plan-done"` tag code is dead code in 7 locations that should be cleaned up:
   - `scanner.py` — assigns `"plan-done"` tag
   - `task_board.py` — splits plan into active/completed with separator
   - `dashboard_content.html` — dimmed done-plan cards
   - `tasks_content.html` — plan-done group splitting and separator
   - `style.css` — `.plan-done-card` rule
   - `test_wiggum.py` — asserts `"plan-done"` tag
   - `test_web_plan.py` — tests `plan-done-card` class

3. **Kept housekeeping tasks** (version mismatch, deprecated TemplateResponse, unused import)

## Remaining Work

| Task | Priority | Size |
|------|----------|------|
| Remove `"plan-done"` dead code, replace with `"archive"` tag in scanner | Medium | 1 iteration |
| Housekeeping: version sync, TemplateResponse fix, unused import | Low | 1 iteration |

Both are independent. Each fits in a single build iteration.
