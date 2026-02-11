---
title: Track IMPLEMENTATION_PLAN.md in spec-view
status: done
priority: high
tags: [core, dogfooding]
---

# Track IMPLEMENTATION_PLAN.md in spec-view

spec-view should be able to display and track the project's own `IMPLEMENTATION_PLAN.md` file so that Ralph Wiggum loop progress is visible in the TUI and web dashboards.

## Problem

`IMPLEMENTATION_PLAN.md` lives at the project root and contains checkbox tasks (`- [ ]` / `- [x]`) managed by the planning loop. But spec-view only scans directories listed in `spec_paths` (default: `specs/`), so the implementation plan is invisible in the dashboard.

Developers using the Ralph Wiggum workflow should see their plan's progress inside spec-view without having to move or symlink the file.

## Requirements

- Add `IMPLEMENTATION_PLAN.md` to spec-view's tracked files via the `include` config glob pattern.
- Create or update `.spec-view/config.yaml` with:
  ```yaml
  spec_paths:
    - specs/
  include:
    - "IMPLEMENTATION_PLAN.md"
  ```
- The parser already extracts checkboxes from any markdown file, so no parser changes should be needed — the file should appear as a standalone `SpecGroup` in both the TUI tree and web dashboard with its task counts and completion percentage.
- Verify that the file's checkbox tasks (`- [ ]` / `- [x]`) are correctly parsed and counted.
- The implementation plan should show up with a title derived from its `# Implementation Plan` heading.
