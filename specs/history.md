---
title: Git History
status: in-progress
priority: high
tags: [core, tui, web]
---

# Git History

Parses git log to show development activity timeline.

## Data Extraction

`get_history(root, limit=50)` runs `git log --format=<custom> --numstat` and returns `CommitEntry` objects, newest first.

Per commit:
- **hash**: 7-char short hash
- **timestamp**: ISO datetime
- **message**: first line of commit message
- **body**: full commit body
- **is_loop**: `True` if body contains `Co-Authored-By:.*Claude` (case-insensitive)
- **files_changed**, **insertions**, **deletions**: from numstat
- **changed_files**: list of file paths
- **tasks_completed**: tasks marked done in IMPLEMENTATION_PLAN.md (from diff)

## Task Extraction

`_extract_tasks_from_diff(hash, root)` runs `git show <hash> -- IMPLEMENTATION_PLAN.md`, finds added lines matching `+- [x] <text>`, strips markdown formatting and `— DONE` markers.

## Edge Cases

- Not a git repo → empty list, no crash
- No commits → empty list
- No IMPLEMENTATION_PLAN.md changes → empty `tasks_completed`
- Binary files → shown by name only
