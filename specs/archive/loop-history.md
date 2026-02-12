---
title: Loop History View
status: done
priority: high
tags: [tui, web, core, ux]
---

# Loop History View

A dedicated view in both TUI and web UI that shows a timeline of recent development activity, giving users visibility into what each wiggum loop iteration (or manual session) accomplished.

## Problem

When the wiggum loop runs autonomously (`./loop.sh 20`), the user has no visibility into what happened across iterations without manually reading `git log` and diffing `IMPLEMENTATION_PLAN.md`. After stepping away and letting the loop run, there's no quick way to answer:

- What tasks were completed?
- Which files were changed?
- How many iterations ran?
- Did the loop make good progress or go in circles?

The user needs an at-a-glance timeline of development activity that integrates naturally into the existing spec-view dashboard.

## Design

### Data Source: Git History

Each wiggum loop iteration ends with a `git commit`. Git is the natural source of truth for development activity — no extra journal files or state tracking needed.

The system parses `git log` to extract:
- Commit hash, timestamp, message
- Files changed (with add/modify/delete classification)
- Lines added/removed (stat summary)
- Changes to `IMPLEMENTATION_PLAN.md` (tasks marked done, discoveries added)

This approach works retroactively on existing history and requires no changes to `loop.sh` or prompt files.

### Iteration Detection

Not all commits are loop iterations. The system should detect and label commits but show all recent activity:

- **Loop commits**: Detected by `Co-Authored-By: Claude` trailer in the commit message (the build prompt instructs Claude to commit, and Claude Code adds this trailer by convention). Labelled with a loop icon.
- **Manual commits**: Everything else. Labelled differently (e.g., human icon or no icon).
- **No filtering**: Show all commits — users benefit from seeing the full timeline regardless of source.

### Data Model

A new `CommitEntry` dataclass in core:

```
CommitEntry:
  hash: str               # Short hash (7 chars)
  timestamp: datetime
  message: str             # First line of commit message
  body: str                # Full commit body
  is_loop: bool            # True if Co-Authored-By: Claude detected
  files_changed: int       # Number of files changed
  insertions: int          # Lines added
  deletions: int           # Lines removed
  changed_files: list[str] # List of file paths changed
  tasks_completed: list[str]  # Task descriptions marked done in IMPLEMENTATION_PLAN.md (extracted from diff)
```

## Requirements

### Core

- Add `src/spec_view/core/history.py` with a function to parse git log from a given root directory.
- Return a list of `CommitEntry` objects, most recent first.
- Default to the last 50 commits (configurable). This keeps the view focused on recent activity without loading entire project history.
- Extract `tasks_completed` by parsing the diff of `IMPLEMENTATION_PLAN.md` for each commit: look for lines matching `+- [x]` (a checkbox that was checked in that commit). Strip markdown formatting to get clean task text.
- Detect `is_loop` by checking if the commit message body contains `Co-Authored-By:` with `Claude` (case-insensitive).
- Use `git log --format=...` and `git diff-tree` / `git show --stat` to extract data. All git operations via `subprocess.run()` with `pathlib.Path` for the working directory.
- Handle the case where the directory is not a git repository gracefully (return empty list, don't crash).

### TUI

- Add a new **Loop History screen** accessible via the `l` keybinding (add to app-level bindings alongside `d` dashboard and `t` tasks).
- The screen shows a scrollable list of commits as a timeline, newest first.
- Each entry displays:
  - Timestamp (relative, e.g., "2 min ago", "1 hour ago") and short hash
  - Loop icon indicator: a visible marker for loop commits vs manual commits (e.g., `[bot]` vs `[you]` or similar concise labels)
  - Commit message (first line)
  - Files changed count and lines added/removed summary (e.g., `3 files  +45 -12`)
  - Tasks completed (if any), listed below the commit line with a green checkmark
- Use a two-pane layout matching the dashboard pattern: commit list on the left, commit detail on the right.
- Selecting a commit in the list shows full detail in the right pane:
  - Full commit message (including body)
  - List of changed files with modification type (added/modified/deleted)
  - All tasks completed in that commit
- Vim-style navigation: `j`/`k` and arrow keys to navigate the list, `enter`/`l` to view detail, `h`/left to return to list.
- The screen should refresh when the watcher detects changes (same `update_groups()` pattern — re-read git history on refresh since new commits mean new iterations).
- Include the shared progress bar widget at the bottom (same as dashboard and task board).
- Show in the footer: key bindings for navigation.

### Web

- Add a new page at `GET /loops` (or `/history`) with a nav link "History" in `base.html` alongside Dashboard and Tasks.
- Show a timeline/feed of commits, newest first, styled as cards or rows.
- Each entry shows: timestamp, hash (linkable if remote URL is available), loop/manual badge, commit message, file count + stat summary, tasks completed.
- Clicking/expanding an entry reveals: full commit body, list of changed files, task details.
- Add partial endpoint `GET /partials/loops-content` for htmx updates.
- Wire to SSE: `hx-trigger="load, specchange from:body"` so the history refreshes when the loop commits new changes.
- Style to match the existing dark theme. Loop commits could have a subtle accent border or icon to visually distinguish from manual work.
- Include the global progress bar (already in `base.html`).

### Shared

- Both UIs use the same `history.py` core module for data.
- Both show the same commits in the same order.
- Timestamp formatting should be human-friendly (relative times for recent, absolute for older).
- The history view is read-only — no mutations, no git operations beyond `log` and `show`.

## Edge Cases

- **Not a git repo**: Show a friendly message ("No git history available") instead of crashing.
- **No commits yet**: Show "No commits found" placeholder.
- **No IMPLEMENTATION_PLAN.md changes in a commit**: `tasks_completed` is empty — that's fine, just show the commit without a tasks section.
- **Very long commit messages**: Truncate the first line in the list view, show full text in detail view.
- **Merge commits**: Show normally — they're part of the history.
- **Binary files in diff**: Just show file name with "binary" label, don't try to parse content.

## Performance

- Git log parsing should be fast for 50 commits (single `git log` call with appropriate format string, not N+1 queries).
- For `tasks_completed` extraction, batch the diffs rather than running `git show` per commit — or accept the N calls since N=50 is small.
- Cache the history in memory and only re-parse on watcher trigger, not on every render.
