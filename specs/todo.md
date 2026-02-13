---
title: spec-view human todo-list
status: in-progress
priority: high
tags: [meta]
---

# spec-view development todo

## System Specs

Living documentation of how spec-view works. Keep current as the system evolves.

- [x] `specs/parsing.md` — format detection, task extraction, plan sections
- [x] `specs/scanning.md` — file discovery, grouping, archive tagging
- [x] `specs/models.md` — data models and computed properties
- [x] `specs/config.md` — configuration, auto-detection, file watching
- [x] `specs/tui.md` — terminal UI screens and navigation
- [x] `specs/web.md` — web UI routes, partials, SSE
- [x] `specs/history.md` — git history parsing

## Completed Features

- [x] Archive completed plan sections — prompt/config update, no code needed
- [x] Preserve group headings in archive sections
- [x] Global progress bar in TUI and web UI
- [x] Loop history view in TUI and web UI
- [x] Wiggum plan section parsing — split IMPLEMENTATION_PLAN.md into per-JTBD sections
- [x] Track IMPLEMENTATION_PLAN.md in spec-view
- [x] Archive function in TUI and web UI
- [x] TUI detail pane scrolling with vim navigation
- [x] TUI task board: group tasks under spec headings
- [x] Watcher: watch include pattern files for live reload
- [x] TUI keyboard navigation with vim keys
