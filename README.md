# spec-view

Universal spec-driven development dashboard. Works with **spec-kit**, **Kiro**, **OpenSpec**, or plain markdown specs.

Install with `pip install spec-view`, run `spec-view` in your project, done.

## Quick Start

```bash
# Initialize specs directory with examples
spec-view init

# List all specs
spec-view list

# Launch TUI dashboard
spec-view

# Start web dashboard
spec-view serve

# Watch for changes
spec-view watch

# Validate spec format
spec-view validate
```

## Spec Format

Put your specs in a `specs/` directory:

```
specs/
├── overview.md
├── auth-system/
│   ├── spec.md
│   ├── design.md
│   └── tasks.md
└── payment-flow/
    ├── spec.md
    └── tasks.md
```

Each markdown file supports optional YAML frontmatter:

```markdown
---
title: User Authentication
status: in-progress
priority: high
tags: [auth, backend]
---

## Requirements
- [ ] OAuth2 provider integration
- [x] JWT token generation
```

## Format-Aware Parsing

spec-view auto-detects which tool produced your spec files and extracts tool-specific metadata:

| Format | Detection | Extracted metadata |
|--------|-----------|-------------------|
| **spec-kit** | `## Phase N:` headings + `T001` task IDs | Phases, task IDs, `[P]` parallel markers, `[US1]` story refs, checkpoints |
| **Kiro** | `.kiro/` in file path | Indentation-based subtask trees |
| **OpenSpec** | `## 1.` numbered section headers | Section structure |
| **Generic** | Fallback | Checkbox tasks with subtask trees |

### spec-kit Example

spec-view is the missing monitoring piece for spec-kit. A spec-kit `tasks.md` with phases, task IDs, parallel markers, and story refs:

```markdown
## Phase 1: Setup
- [x] T001 [P] Configure project structure
- [x] T002 [P] Set up testing framework
- [x] T003 Install dependencies

**Checkpoint**: Foundation ready

## Phase 2: US1 - Login Flow
- [x] T004 [P] [US1] Create User model
- [ ] T005 [US1] Implement JWT validation
- [ ] T006 [P] [US1] Create login form
```

In the TUI, this renders as:

```
Phase 1: Setup ✓ (3/3)
  ✓ T001 ⇄ Configure project structure
  ✓ T002 ⇄ Set up testing framework
  ✓ T003 Install dependencies
  ⏸ Checkpoint: Foundation ready

Phase 2: US1 - Login Flow (1/3)
  ✓ T004 ⇄ [US1] Create User model
  ○ T005 [US1] Implement JWT validation
  ○ T006 ⇄ [US1] Create login form
```

The web UI shows collapsible phase sections with progress bars, task ID badges, parallel icons, and colored story tags.

## Configuration

Create `.spec-view/config.yaml` to customize:

```yaml
spec_paths:
  - specs/
  - docs/specs/
include:
  - "**/*.spec.md"
exclude:
  - "**/node_modules/**"
serve:
  port: 8080
```

## Live Updates

Both TUI and web dashboards watch for file changes and update automatically. Edit a `[ ]` to `[x]` in your editor and see progress update within ~1 second.
