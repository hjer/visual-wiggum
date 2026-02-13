---
title: Scanning & Grouping
status: in-progress
priority: high
tags: [core]
---

# Scanning & Grouping

How spec-view discovers files and organizes them into SpecGroups.

## File Discovery

`discover_spec_files(config)` collects markdown files from two sources:

1. **spec_paths** — recursive walk of configured directories (default: `specs/`)
2. **include** — glob patterns resolved against project root (e.g., `IMPLEMENTATION_PLAN.md`)

Filtered by `exclude` patterns (default: `**/node_modules/**`, `**/.git/**`). Deduplicated by resolved path.

## Grouping Rules

Files become SpecGroups via these rules:

- **Wiggum-format files**: expanded into one SpecGroup per `## ` section (see below)
- **Files in subdirectories of a spec_path**: grouped by parent directory. A directory with `spec.md`, `design.md`, `tasks.md` becomes one SpecGroup with three files.
- **Files directly in spec_path root or project root**: each file becomes its own SpecGroup

SpecGroup name comes from the directory name (for directory groups) or file stem (for standalone files).

## Auto-Tagging

- **archive**: files under any `archive/` directory in the path. Path-based detection, not frontmatter.
- **specs**: files from `spec_paths` directories (e.g., `specs/`) that are NOT in `archive/` and NOT wiggum-format. Identifies spec documentation for UI grouping. Applied by the scanner after grouping.
- **plan**: wiggum-format sections from `IMPLEMENTATION_PLAN.md`. Applied during wiggum expansion.
- **plan + archive**: wiggum sections where all tasks are done.

## Wiggum Expansion

When a file has `format_type == "wiggum"`, `_expand_wiggum_sections()` replaces the single SpecGroup with N groups — one per plan section.

Each virtual SpecGroup:
- `name`: slugified section title
- `files`: one SpecFile with that section's scoped tasks and body
- Auto-tagged `"plan"`
- Auto-tagged `"archive"` when all section tasks are done

Plan groups preserve file order (not alphabetical). Regular groups sort alphabetically.

## Config-Driven

Scanner reads `spec_paths`, `include`, `exclude` from `.spec-view/config.yaml`. Falls back to auto-detection if no config exists.
