---
title: Global Progress Bar
status: ready
priority: high
tags: [tui, web, ux]
---

# Global Progress Bar

A persistent, always-visible progress bar pinned to the bottom of both the TUI and web UI that shows overall task completion across all loaded specs.

## Problem

The current TUI status bar (`#status-bar` in `DashboardScreen`) shows task counts as plain text (e.g. "Tasks: 5/12") but has no visual progress indicator. The task board screen has no summary at all. The web UI has a progress bar at the top of the dashboard page, but it disappears when navigating to `/tasks` or `/spec/{name}` — there is no persistent global indicator.

Users should be able to glance at the bottom of the screen at any time and see how far along the project is.

## Requirements

### TUI

- Replace the plain-text `#status-bar` in `DashboardScreen` with a visual progress bar showing a filled/unfilled bar, percentage, and the fraction (e.g. `done/total`).
- Use Textual's built-in `ProgressBar` widget or Rich-renderable bar characters (e.g. `━` filled, `─` unfilled) — whichever integrates cleanly with the existing layout.
- The progress bar must also appear on `TaskBoardScreen`, not just the dashboard.
- The bar must live-update when the file watcher detects changes (same as the existing status bar does via `update_groups()`).
- Keep the existing spec status counts (e.g. "3 draft, 2 done") alongside the bar so no information is lost.
- The bar should be exactly 1 row tall, docked to the bottom, above the Textual `Footer`.
- Use colour to indicate progress: green fill on the dark surface background, matching the project's existing palette.

### Web

- Add a fixed-position progress bar pinned to the bottom of the viewport on all pages (dashboard, tasks, spec detail).
- It must be present in `base.html` so it appears globally without duplicating markup per page.
- Show the filled bar, percentage, and fraction text (same data as TUI).
- The bar should auto-update via htmx + SSE — when a `specchange` event fires, refetch the bar's content from a new partial endpoint.
- Add a new partial route `GET /partials/global-progress` that returns just the progress bar HTML.
- Style it to match the existing dark theme: `--bg` background, `--green` fill, subtle top border.
- The bar should be thin and unobtrusive — roughly 32-36px tall.

### Shared

- Both UIs must compute progress identically: `sum(group.task_done) / sum(group.task_total)` across all loaded `SpecGroup` objects, as an integer percentage.
- When there are zero tasks, show 0% and an empty bar (not an error).
- The progress bar must not interfere with existing scrolling or layout on either UI.
