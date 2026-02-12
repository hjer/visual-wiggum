---
title: Wiggum Plan Section Parsing
status: ready
priority: high
tags: [core, tui, web, parser]
---

# Wiggum Plan Section Parsing

Parse `IMPLEMENTATION_PLAN.md` into separate sections per JTBD, each with its own status, tasks, and progress — instead of treating the entire file as one monolithic spec.

## Problem

The wiggum loop produces an `IMPLEMENTATION_PLAN.md` with multiple independent sections, each representing a different JTBD (Job to Be Done). The current format looks like:

```markdown
## Spec: Track IMPLEMENTATION_PLAN.md (...) — DONE
**Status:** done | **Priority:** high | **Tags:** core, dogfooding
### Tasks
- [x] Task one
- [x] Task two

---

## Collapsible Archive Section — DONE
**Status:** done | **Priority:** medium | **Tags:** tui, web, ux
### Tasks
- [x] Task one
- [x] Task two

---

## Spec: Global Progress Bar (...) — DONE
**Status:** done | **Priority:** high | **Tags:** tui, web, ux
### Tasks
#### 1. TUI: Create shared progress bar widget — DONE
- [x] Subtask
#### 2. Web: Add global progress bar — DONE
- [x] Subtask
```

Currently, spec-view treats this entire file as **one** `SpecGroup` with **one** entry in the tree. All tasks from all sections are lumped together. The user sees "Implementation Plan (47/47)" as a single item — they can't tell which JTBDs are done, which are in progress, or what tasks belong to what.

The user needs:
- Each JTBD section as its own item in the tree menu
- Per-section status, progress, and task counts
- Tasks grouped by JTBD on the task board
- Done sections visually distinct from active ones

## Design

### Section Detection

The implementation plan has a clear structure that can be detected and parsed:

1. **Section boundaries**: `## ` headings (H2) separated by `---` horizontal rules
2. **Section metadata**: `**Status:** done | **Priority:** high | **Tags:** core, ux` on a line after the heading
3. **Section status shorthand**: `— DONE` suffix on the heading itself
4. **Tasks**: Standard `- [x]` / `- [ ]` checkboxes within each section
5. **Subsections**: `### Tasks`, `#### 1. Task Name — DONE` provide additional structure within a section

### Format Detection

Add a new format type `"wiggum"` in `detect_format()`. Heuristics:
- File title or `# ` heading contains "Implementation Plan" (case-insensitive)
- Contains multiple `## ` sections with `**Status:**` metadata lines
- Contains `---` horizontal rule separators between sections

This is distinct from existing formats (spec-kit uses `## Phase N:`, kiro uses `.kiro/` paths, openspec uses `## N.` numbered sections).

### Parsing Strategy

When a file is detected as `"wiggum"` format, the parser splits it into sections at `## ` boundaries and extracts per-section metadata. Each section becomes a virtual `SpecGroup` with its own title, status, priority, tags, and tasks.

The scanner handles the splitting: when it encounters a wiggum-format file, instead of creating one `SpecGroup`, it creates **one group per section**, all referencing the same source file but with scoped content.

### Data Flow

```
IMPLEMENTATION_PLAN.md (one file)
    → parser detects "wiggum" format
    → scanner splits into N sections
    → each section → virtual SpecGroup
        - name: slugified section title
        - title: section heading (cleaned)
        - status: from **Status:** line or — DONE suffix
        - priority: from **Priority:** line
        - tags: from **Tags:** line + auto-tag "plan"
        - tasks: checkboxes within that section only
    → TUI tree: sections as children under "Plan" parent node
    → Task board: tasks grouped per section
    → Web: same grouping
```

## Requirements

### Core — Parser (`parser.py`)

- Add `"wiggum"` to `detect_format()`. Trigger on: body contains `**Status:**` metadata lines AND multiple `## ` sections. The file does NOT need YAML frontmatter (the implementation plan typically has none — just a `# ` title and `> ` blockquote).
- Add a new function `parse_plan_sections(body: str, path: Path) -> list[PlanSection]` that:
  - Splits the body at `## ` heading boundaries
  - For each section, extracts:
    - **title**: The heading text, stripped of `— DONE` suffix, `Spec:` prefix, and parenthetical references like `(specs/foo.md)`
    - **status**: From `**Status:** <value>` line. If heading ends with `— DONE`, status is `done`. Fall back to `draft` if no status line.
    - **priority**: From `**Priority:** <value>` line. Fall back to `medium`.
    - **tags**: From `**Tags:** <value>` line, split by `, `. Always include `"plan"` tag.
    - **tasks**: Parse checkboxes from the section body using existing `parse_tasks()`
    - **body**: The full section text (for detail view rendering)
  - Ignore preamble text before the first `## ` (the `# ` title and blockquote)
  - Ignore sections that are purely structural (e.g., `## Discovered Issues`, `## Learnings`, `## Notes`) — detect by: section has no `**Status:**` line and no task checkboxes

### Core — Models (`models.py`)

- Add a `PlanSection` dataclass:
  ```
  PlanSection:
    title: str
    status: Status
    priority: Priority
    tags: list[str]
    tasks: list[Task]
    task_tree: list[Task]
    body: str
    source_path: Path  # the IMPLEMENTATION_PLAN.md file
  ```
  With computed properties: `task_total`, `task_done`, `task_percent` (same pattern as `SpecFile`)

### Core — Scanner (`scanner.py`)

- When `parse_spec_file()` returns a file with `format_type == "wiggum"`, the scanner should split it into multiple `SpecGroup` objects — one per `PlanSection`.
- Each virtual `SpecGroup`:
  - `name`: slugified section title (e.g., `"global-progress-bar"`)
  - `path`: same as the file's parent directory
  - `files`: contains one `SpecFile` per section, with the section's scoped tasks and body
  - Auto-tag with `"plan"` so UIs can identify plan-sourced groups
  - If all tasks in the section are done, auto-tag with `"plan-done"` (used for visual treatment, not archive)
- The original monolithic `SpecGroup` for the whole file is **not** emitted — only the per-section groups replace it.
- Preserve sort order: sections should appear in the order they occur in the file.

### TUI — Dashboard (`dashboard.py`)

- Plan-sourced groups (tagged `"plan"`) should be grouped under a collapsible **"Plan"** parent node in the tree, similar to how archived specs are grouped under an "Archive" node.
- Within the Plan node, each section appears as a child with its own status icon, title, and task counts.
- Sections where all tasks are done should be dimmed (like archived items) but stay in the Plan node, not move to Archive.
- Selecting a section (leaf) shows its detail in the right pane: section title, status, tasks, and the section body.
- The Plan node itself shows aggregate progress: `"Plan (done/total)"` across all sections.

### TUI — Task Board (`task_board.py`)

- Tasks from plan sections should be grouped under their section title as headings, not lumped under "Implementation Plan."
- Each section heading shows its task count: `"Global Progress Bar (4/4)"`.
- Done sections should appear dimmed at the bottom (same pattern as archived groups, but under a "Plan — Completed" separator instead of "Archive").
- Active plan sections appear alongside other active spec groups, sorted normally.

### Web — Dashboard and Tasks

- Same grouping as TUI: plan sections appear as separate cards/entries on the dashboard and task board.
- On the dashboard, group plan-sourced cards under a collapsible "Implementation Plan" section header, with aggregate progress.
- On tasks, group tasks by section heading (same as TUI task board).
- Done sections in a collapsible dimmed section.

### Shared

- Both UIs render plan sections identically — same titles, same task grouping, same done/active partitioning.
- Plan sections are **not** archived specs. They use the `"plan"` tag, not `"archive"`. The archive section remains for actual spec files moved to `specs/archive/`.
- The `"plan"` tag is auto-applied by the scanner and is how UIs identify and group these sections.
- Progress bar computation: plan section tasks should be included in the global progress count (they represent real work), unless the section is tagged `"plan-done"` — treat done plan sections the same as active for progress (they're completed work, not archived/excluded).

## Edge Cases

- **Empty sections**: A section with no tasks and no status line (like `## Discovered Issues` or `## Learnings`) should be skipped entirely — not shown in the tree or task board.
- **Single section**: If the plan has only one JTBD section, still show it under the Plan parent node for consistency.
- **No plan file**: If `IMPLEMENTATION_PLAN.md` doesn't exist or isn't included in config, the Plan node simply doesn't appear. No crash.
- **Nested task headings**: Sections like `#### 1. TUI: Create widget — DONE` within a section are **not** separate sections — they're subsection headings within a JTBD. Tasks under them belong to the parent `## ` section. The `#### ` heading text can be preserved in the body rendering but doesn't create separate groups.
- **Status line variations**: Handle `**Status:** done`, `**Status:** in-progress`, etc. Also handle the `— DONE` suffix on the heading as a shorthand for `status: done`.
- **Multiple status lines**: Use the first `**Status:**` line found in the section.
- **Plan file without wiggum format**: If `IMPLEMENTATION_PLAN.md` exists but doesn't match wiggum format (e.g., it's a plain markdown file with no `## ` sections or `**Status:**` lines), fall through to generic parsing — show it as a single group like today.
- **Sections with numbered sub-tasks**: `#### 1. Task Name — DONE` followed by `- [x]` items are subsections. The tasks belong to the parent `## ` section. The `#### ` numbering is decorative structure, not a section boundary.

## Performance

- Parsing plan sections adds minimal overhead — it's string splitting at `## ` boundaries plus regex matching for metadata, applied to one file.
- No additional file I/O beyond what already exists (the file is already read by `parse_spec_file()`).
- Virtual SpecGroups are lightweight dataclass instances.
