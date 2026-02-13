---
title: Web UI
status: in-progress
priority: high
tags: [web]
---

# Web UI

FastAPI + Jinja2 + htmx. Dark theme.

## Routes

### Full Pages
- `GET /` — dashboard: active items, collapsible specs section, plan section, collapsible archive
- `GET /spec/{name}` — spec detail: rendered markdown, phases, task tree
- `GET /tasks` — task board: tasks grouped by spec, kanban-style status columns, specs section, plan section, archive
- `GET /history` — git commit timeline

### Partials (htmx swap targets)
- `GET /partials/dashboard-content`
- `GET /partials/tasks-content`
- `GET /partials/history-content`
- `GET /partials/spec-content/{name}`
- `GET /partials/global-progress`

### SSE
- `GET /events` — server-sent events stream, debounced 0.3s, sends `specchange` event on file changes

## Partitioning

`_partition_groups()` splits groups into `(active, specs, plan, archived)`:
- **active**: no `archive`, `specs`, or `plan` tags
- **specs**: has `specs` tag, no `archive` tag. Spec documentation files from `spec_paths` directories.
- **plan**: has `plan` tag, no `archive` tag
- **archived**: has `archive` tag

Dashboard and tasks use this quad. Specs section is collapsible with aggregate progress. Plan section is collapsible with aggregate progress. Archive section is collapsible (collapsed by default), dimmed, with sub-groups (plan/specs/other).

## Live Updates

All pages use `hx-trigger="load, specchange from:body"` to auto-reload content when watcher detects file changes. Global progress bar in `base.html` updates the same way.

## Global Progress Bar

Fixed to viewport bottom on all pages. Shows filled bar, percentage, fraction. Excludes archived specs. Auto-updates via SSE.
