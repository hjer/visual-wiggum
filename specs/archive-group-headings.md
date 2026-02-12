---
title: Preserve Group Headings in Archive
status: ready
priority: medium
tags: [tui, web, ux]
---

# Preserve Group Headings in Archive

Keep the source grouping of items when they move into the Archive section, so archived plan sections stay grouped under for example "Implementation Plan" or other heading that the todos have.

## Problem

When plan sections get the `archive` tag and move into the Archive section, they lose for example "Implementation Plan" grouping. They appear as flat items alongside archived spec files — a confusing mix of unrelated things. The same issue applies to any future grouping (e.g., if other tagged categories get archived).

The Archive section should mirror the structure of the active view: specs stay as specs, plan sections stay grouped under their heading.

## Requirements

### TUI — Dashboard Tree (`dashboard.py`)

- In the Archive node, partition archived groups by source:
  - **Archived plan sections** (`"plan" in g.tags and "archive" in g.tags`): group under a dimmed "Implementation Plan" sub-node within Archive
  - **Archived specs** (everything else with `"archive"` tag): listed directly under Archive as today
- The plan sub-node within Archive should show aggregate counts: `"Implementation Plan (done/total)"`
- All text in the Archive section remains dimmed
- The Archive node stays collapsed by default

### TUI — Task Board (`task_board.py`)

- In the Archive section at the bottom, partition tasks by source:
  - Archived plan section tasks grouped under a dimmed "Implementation Plan" heading
  - Archived spec tasks grouped under their own spec name headings (existing behavior)
- All archived tasks remain dimmed

### Web — Dashboard and Tasks

- Same grouping in the web Archive sections: plan sections under an "Implementation Plan" or other category sub-heading, specs under their own headings
- All dimmed/muted styling preserved

### Shared

- The grouping is purely a UI concern — no model or scanner changes needed
- The `"plan"` tag is the discriminator: `"plan" in g.tags` identifies plan-sourced groups regardless of archive status
- This pattern generalizes: any future tagged category can be grouped within Archive the same way
