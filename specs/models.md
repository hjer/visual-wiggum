---
title: Data Models
status: in-progress
priority: high
tags: [core]
---

# Data Models

Frozen-style dataclasses in `core/models.py`. All computed properties are derived, never stored.

## Enums

- **Status**: `DRAFT`, `READY`, `IN_PROGRESS`, `DONE`, `BLOCKED` — parsed via `from_str()`, case-insensitive
- **Priority**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` — parsed via `from_str()`, case-insensitive

## Task

Recursive tree node for checkbox items.

- `text`, `done`, `spec_name`, `source_file`, `depth`, `children: list[Task]`
- Metadata: `task_id` (T###), `parallel` ([P]), `story` ([US#])
- Computed: `subtask_total`, `subtask_done` (recursive through children)

## Phase (spec-kit only)

- `number`, `title`, `subtitle`, `tasks`, `checkpoint`
- Computed: `task_total`, `task_done`, `task_percent`

## PlanSection (wiggum format)

- `title`, `status`, `priority`, `tags`, `tasks`, `task_tree`, `body`, `source_path`
- Computed: `task_total`, `task_done`, `task_percent`

## SpecFile

One parsed markdown file.

- `path`, `title`, `status`, `priority`, `tags`, `content`, `body`
- `tasks` (flat), `task_tree` (nested), `phases`, `format_type`, `file_type` (spec/design/tasks)
- Computed: `task_total`, `task_done`, `task_percent`

## SpecGroup

Aggregates a directory's files into one logical unit. The primary data structure consumed by UIs.

- `name`, `path`, `files: dict[str, SpecFile]`, `tags: list[str]`
- Accessors: `spec`, `design`, `tasks_file` (each nullable)
- Computed from files: `title`, `status`, `priority`, `tags`, `all_tasks`, `all_task_trees`, `task_total`, `task_done`, `task_percent`, `all_phases`, `format_type`, `stories`

## CommitEntry

Git commit data for history view.

- `hash`, `timestamp`, `message`, `body`, `is_loop`
- `files_changed`, `insertions`, `deletions`, `changed_files`
- `tasks_completed: list[str]`
