---
title: TUI
status: in-progress
priority: high
tags: [tui]
---

# TUI

Textual-based terminal UI. Three screens plus a shared progress bar.

## App-Level Bindings

- `q` — quit
- `d` — dashboard screen
- `t` — task board screen
- `l` — history screen
- `r` — refresh (re-scan files)

Background watcher thread auto-refreshes all screens via `call_from_thread()`.

## Dashboard Screen

Two-pane layout: spec tree (left) + scrollable detail (right).

### Tree Structure

1. **Active specs** — normal display, alphabetical
2. **Implementation Plan** — collapsible node, plan-tagged groups in file order, aggregate `(done/total)` count
3. **Archive** — collapsible (collapsed by default), sub-grouped:
   - Archived plan sections under dimmed "Implementation Plan" heading
   - Archived specs listed directly

Each tree leaf shows: status icon, title, task progress `(done/total)`.

### Navigation

Vim-style: `j`/`k` move cursor, `l`/`Enter` select leaf (shows detail), `h`/`←` return focus to tree. Arrow keys also work.

### Detail Pane

Shows selected spec: title, status/priority/format badges, tags, task progress, phases (spec-kit), task tree, full body. `j`/`k` scroll when focused.

## Task Board Screen

Tasks grouped under spec name headings with counts. Phases rendered for spec-kit specs. Task tree shows indentation + subtask counts. Archive section at bottom, dimmed, sub-grouped (plan/specs). `j`/`k` scroll.

## History Screen

Two-pane: commit list (left) + commit detail (right).

- Newest first, `[bot]` badge for loop commits, `[you]` for manual
- Shows: relative timestamp, short hash, message, file count, lines ±, tasks completed
- Detail pane: full message, changed files list, completed tasks
- `j`/`k` navigate list

## Progress Bar

1-row widget docked above footer on all screens. Shows: visual bar (20 chars, `━`/`─`), percentage, task counts, spec status counts. Excludes archived specs from active counts. Updates live.
