---
title: Markdown Parsing
status: in-progress
priority: high
tags: [core]
---

# Markdown Parsing

How spec-view reads and interprets markdown files.

## Format Detection

`detect_format(body, path)` uses heuristics in this order:

1. **kiro** — `.kiro/` in file path
2. **spec-kit** — body has `## Phase N:` headers AND `T###` task IDs
3. **wiggum** — body has ≥2 `## ` sections AND ≥2 `**Status:**` lines
4. **openspec** — body has `## \d+.` numbered sections
5. **generic** — fallback for any markdown

## Frontmatter

Uses `python-frontmatter` to extract YAML header fields: `title`, `status`, `priority`, `tags`, `file_type`. All optional.

Title fallback chain: frontmatter `title` → first `# ` heading → parent directory name. Generic stems (`spec`, `design`, `tasks`, `todo`, `requirements`, `index`, `readme`) use parent dir name instead.

## Task Extraction

`parse_tasks(body)` finds checkbox lines matching `^( *)- \[([ xX])\]\*? (.+)$`.

- Indentation depth determines parent-child nesting via a stack
- Returns `(flat_list, tree)` — flat for counting, tree for rendering
- Metadata stripped from task text: `T###` task IDs, `[P]` parallel markers, `[US#]` story refs

## Phase Parsing (spec-kit only)

Finds `## Phase N: Title` headers. Tasks between phase headers belong to that phase. `**Checkpoint**: text` lines attach to the preceding phase.

## Wiggum Plan Section Parsing

`parse_plan_sections(body, path)` splits at `## ` boundaries. Per section:

- **title**: heading text, stripped of `— DONE` suffix, `Spec:` prefix, `(file.md)` parentheticals
- **status**: from `**Status:** <value>` line, or `done` if heading ends `— DONE`
- **priority**: from `**Priority:** <value>` line, default `medium`
- **tags**: from `**Tags:** <value>` line (comma-separated), always includes `"plan"`
- **tasks**: parsed via `parse_tasks()` from section body

Sections with no `**Status:**` line AND no checkboxes are skipped (structural sections like `## Discovered Issues`).

`#### ` subsection headings within a `## ` section are NOT separate sections — their tasks belong to the parent section.

## File Type Detection

From filename stem: `design` → design, `tasks`/`todo` → tasks, everything else → spec. Used for grouping within a SpecGroup.
