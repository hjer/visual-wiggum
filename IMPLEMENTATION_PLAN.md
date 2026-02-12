# Implementation Plan

> Auto-generated and maintained by the planning loop. Do not edit specs here — write them in `specs/`.
> Completed sections archived to `IMPLEMENTATION_PLAN_ARCHIVE.md`.

---

## Housekeeping: Tech Debt & Code Quality

**Status:** ready | **Priority:** low | **Tags:** chore, quality

### Tasks

- [x] Fix version mismatch: `pyproject.toml` says `0.3.2` but `src/spec_view/__init__.py` says `0.2.2`. Sync `__init__.py` to match `pyproject.toml` (source of truth for the build system).
- [ ] Fix deprecated `TemplateResponse` signature in `src/spec_view/web/server.py` (9 call sites). Change from `TemplateResponse(name, context)` to `TemplateResponse(request, name, context=context)` — eliminates deprecation warnings in tests.
- [ ] Remove unused `CommitEntry` import in `src/spec_view/web/server.py` (line 18). Only `get_history` is used.

---

## Discovered Issues

(No outstanding issues beyond the above.)

## Learnings

- Completed plan sections are now tagged `"archive"` (not `"plan-done"`). The scanner auto-tags sections with all tasks done, and the existing `"archive" in g.tags` partitioning in both TUI and web handles the rest.
- The `Config.include` pattern mechanism in `scanner.py` already supports root-level file inclusion — no scanner changes needed for the IMPLEMENTATION_PLAN tracking spec.
- The SSE + htmx infrastructure is well-established; new partial endpoints just need a route + template.
- Textual's `Static` widget auto-sizes to fit content — for scrollable detail views, use `VerticalScroll` with a `Static` child instead.
- The scanner already auto-tags archived specs with `"archive"` in their tags, making partitioning straightforward via `"archive" in g.tags`.
- The watcher must watch both `spec_paths` directories and parent directories of `include` pattern matches — otherwise root-level included files won't trigger live reloads.
- The existing UI partitioning logic (`"archive" in g.tags`) is designed so that adding `"archive"` to any group automatically moves it to the archive section — no UI code changes needed for dashboard or web server.
