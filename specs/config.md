---
title: Config & Detection
status: in-progress
priority: high
tags: [core]
---

# Config & Detection

How spec-view finds its configuration and discovers spec sources.

## Config File

Location: `.spec-view/config.yaml`. Structure:

```yaml
spec_paths: ["specs/"]       # directories to scan recursively
include: []                   # glob patterns for individual files (e.g., IMPLEMENTATION_PLAN.md)
exclude:                      # glob patterns to skip
  - "**/node_modules/**"
  - "**/.git/**"
serve:
  port: 8080
  open_browser: true
statuses: ["draft", "ready", "in-progress", "done", "blocked"]
```

`load_config()` reads the file. If missing, falls back to auto-detection and sets `auto_detected=True`. `save_config()` writes to the file, omitting defaults.

## Auto-Detection

`detect_spec_sources(root)` walks the project tree (max depth 4) looking for marker directories:

- `specs/` — generic spec directory
- `.kiro/` or `.kiro/specs/` — Kiro format
- `openspec/changes/<name>/specs/` — OpenSpec format
- `.spec/` — spec directory
- `docs/` — documentation directory

Skips: `node_modules`, `.git`, `__pycache__`, `.venv`, `venv`, `.tox`, `dist`, `build`, `.next`.

Deduplicates by removing parent paths when more specific child exists. Sorts by markdown file count (descending).

## File Watching

`watch_specs(config, on_change)` uses `watchfiles` to monitor `spec_paths` directories + parent directories of `include` pattern matches. Filters to `*.md` and `*.yaml` only. Calls `on_change()` callback.

`SpecChangeNotifier` provides async pub/sub for web SSE: `subscribe()` returns a queue, `notify()` pushes to all subscribers. Thread-safe bridge from sync watcher to async event loop.
