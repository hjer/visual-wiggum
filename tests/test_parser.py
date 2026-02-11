"""Tests for spec-view markdown parser."""

from pathlib import Path

from spec_view.core.models import Priority, Status
from spec_view.core.parser import (
    _extract_task_metadata,
    _parse_phases,
    detect_file_type,
    detect_format,
    parse_spec_file,
    parse_tasks,
    parse_title_from_body,
)


class TestParseTasks:
    def test_extracts_checked_and_unchecked(self):
        text = """\
## Tasks
- [ ] Not done
- [x] Done
- [X] Also done
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 3
        assert flat[0].text == "Not done"
        assert flat[0].done is False
        assert flat[1].text == "Done"
        assert flat[1].done is True
        assert flat[2].text == "Also done"
        assert flat[2].done is True
        # All top-level, so tree == flat (structurally)
        assert len(tree) == 3

    def test_no_tasks(self):
        flat, tree = parse_tasks("Just some text\nWith no tasks")
        assert len(flat) == 0
        assert len(tree) == 0

    def test_indented_tasks(self):
        text = "  - [ ] Indented task"
        flat, tree = parse_tasks(text)
        assert len(flat) == 1
        assert flat[0].text == "Indented task"

    def test_task_with_spec_name(self):
        flat, tree = parse_tasks("- [ ] Do stuff", spec_name="auth", source_file="auth/tasks.md")
        assert flat[0].spec_name == "auth"
        assert flat[0].source_file == "auth/tasks.md"

    def test_returns_tuple(self):
        result = parse_tasks("- [ ] A task")
        assert isinstance(result, tuple)
        assert len(result) == 2
        flat, tree = result
        assert isinstance(flat, list)
        assert isinstance(tree, list)

    def test_kiro_3_level_tree(self):
        text = """\
- [ ] Define API
  - [x] REST endpoints
  - [ ] WebSocket handlers
    - [ ] Connection manager
    - [x] Message parser
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 5
        assert len(tree) == 1  # one top-level task

        root_task = tree[0]
        assert root_task.text == "Define API"
        assert root_task.depth == 0
        assert len(root_task.children) == 2

        child1, child2 = root_task.children
        assert child1.text == "REST endpoints"
        assert child1.done is True
        assert child1.depth == 1

        assert child2.text == "WebSocket handlers"
        assert child2.depth == 1
        assert len(child2.children) == 2

        grandchild1, grandchild2 = child2.children
        assert grandchild1.text == "Connection manager"
        assert grandchild1.depth == 2
        assert grandchild2.text == "Message parser"
        assert grandchild2.done is True

    def test_openspec_2_level(self):
        text = """\
## Authentication
- [ ] Login flow
- [x] Logout flow
- [ ] Session management
  - [x] Token refresh
  - [ ] Token revocation
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 5
        assert len(tree) == 3  # Login, Logout, Session management

        session = tree[2]
        assert session.text == "Session management"
        assert len(session.children) == 2
        assert session.children[0].text == "Token refresh"
        assert session.children[0].done is True

    def test_kiro_optional_star_marker(self):
        text = """\
- [x]* Completed with star marker
- [ ] Normal task
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 2
        assert flat[0].text == "Completed with star marker"
        assert flat[0].done is True
        assert flat[1].text == "Normal task"
        assert flat[1].done is False

    def test_mixed_indentation(self):
        """4-space indent detected from first indented task."""
        text = """\
- [ ] Parent
    - [ ] Child (4-space)
        - [ ] Grandchild (8-space)
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 3
        assert len(tree) == 1
        assert tree[0].depth == 0
        assert tree[0].children[0].depth == 1
        assert tree[0].children[0].children[0].depth == 2

    def test_empty_input(self):
        flat, tree = parse_tasks("")
        assert flat == []
        assert tree == []

    def test_non_checkbox_bullets_ignored(self):
        text = """\
- Regular bullet point
- Another bullet
- [ ] Actual task
* Star bullet
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 1
        assert flat[0].text == "Actual task"

    def test_multiple_top_level_groups(self):
        text = """\
- [ ] Group A
  - [ ] A.1
  - [x] A.2
- [x] Group B
  - [x] B.1
"""
        flat, tree = parse_tasks(text)
        assert len(flat) == 5
        assert len(tree) == 2

        assert tree[0].text == "Group A"
        assert len(tree[0].children) == 2
        assert tree[1].text == "Group B"
        assert len(tree[1].children) == 1


class TestDetectFileType:
    def test_spec(self):
        assert detect_file_type(Path("spec.md")) == "spec"
        assert detect_file_type(Path("requirements.md")) == "spec"

    def test_design(self):
        assert detect_file_type(Path("design.md")) == "design"

    def test_tasks(self):
        assert detect_file_type(Path("tasks.md")) == "tasks"
        assert detect_file_type(Path("todo.md")) == "tasks"


class TestParseTitleFromBody:
    def test_finds_h1(self):
        assert parse_title_from_body("# My Title\nSome text") == "My Title"

    def test_empty_body(self):
        assert parse_title_from_body("") == ""

    def test_no_heading(self):
        assert parse_title_from_body("Just text\nMore text") == ""


class TestParseSpecFile:
    def test_full_frontmatter(self, tmp_path):
        md = tmp_path / "spec.md"
        md.write_text("""\
---
title: User Auth
status: in-progress
priority: high
tags: [auth, backend]
---

## Overview
Auth system.

## Requirements
- [x] JWT tokens
- [ ] OAuth2
""")
        spec = parse_spec_file(md)
        assert spec.title == "User Auth"
        assert spec.status == Status.IN_PROGRESS
        assert spec.priority == Priority.HIGH
        assert spec.tags == ["auth", "backend"]
        assert spec.file_type == "spec"
        assert len(spec.tasks) == 2
        assert spec.tasks[0].done is True
        assert spec.tasks[1].done is False

    def test_no_frontmatter(self, tmp_path):
        md = tmp_path / "spec.md"
        md.write_text("# My Feature\n\nSome description\n- [ ] Task 1\n")
        spec = parse_spec_file(md)
        assert spec.title == "My Feature"
        assert spec.status == Status.DRAFT
        assert spec.priority == Priority.MEDIUM
        assert len(spec.tasks) == 1

    def test_empty_file(self, tmp_path):
        md = tmp_path / "spec.md"
        md.write_text("")
        spec = parse_spec_file(md)
        # spec.md uses parent dir name as title fallback
        assert spec.title == tmp_path.name.replace("-", " ").replace("_", " ").title()
        assert spec.status == Status.DRAFT

    def test_generic_filename_uses_parent_dir(self, tmp_path):
        feature_dir = tmp_path / "auth-system"
        feature_dir.mkdir()
        md = feature_dir / "spec.md"
        md.write_text("Some content without a heading")
        spec = parse_spec_file(md)
        assert spec.title == "Auth System"

    def test_nongeneric_filename_uses_stem(self, tmp_path):
        md = tmp_path / "my-feature.md"
        md.write_text("Some content without a heading")
        spec = parse_spec_file(md)
        assert spec.title == "My Feature"

    def test_tags_as_string(self, tmp_path):
        md = tmp_path / "spec.md"
        md.write_text("---\ntags: auth, backend\n---\nContent")
        spec = parse_spec_file(md)
        assert spec.tags == ["auth", "backend"]

    def test_design_file_type(self, tmp_path):
        md = tmp_path / "design.md"
        md.write_text("---\ntitle: Design Doc\n---\nContent")
        spec = parse_spec_file(md)
        assert spec.file_type == "design"

    def test_task_tree_populated(self, tmp_path):
        md = tmp_path / "tasks.md"
        md.write_text("""\
---
title: Tasks
---

- [ ] Parent task
  - [x] Child 1
  - [ ] Child 2
- [x] Standalone task
""")
        spec = parse_spec_file(md)
        assert len(spec.tasks) == 4  # flat list
        assert len(spec.task_tree) == 2  # two top-level

        parent = spec.task_tree[0]
        assert parent.text == "Parent task"
        assert len(parent.children) == 2
        assert parent.children[0].done is True

        standalone = spec.task_tree[1]
        assert standalone.text == "Standalone task"
        assert standalone.done is True
        assert len(standalone.children) == 0


class TestDetectFormat:
    def test_detect_format_speckit(self):
        body = """\
## Phase 1: Setup
- [x] T001 Configure project
- [x] T002 Set up testing

## Phase 2: Core
- [ ] T003 Build API
"""
        assert detect_format(body, Path("specs/auth/tasks.md")) == "spec-kit"

    def test_detect_format_kiro(self):
        body = "- [ ] Some task\n- [x] Another task"
        assert detect_format(body, Path("/project/.kiro/specs/auth/tasks.md")) == "kiro"

    def test_detect_format_openspec(self):
        body = """\
## 1. Authentication
- [ ] Login flow
## 2. Authorization
- [ ] Role system
"""
        assert detect_format(body, Path("specs/auth/spec.md")) == "openspec"

    def test_detect_format_generic(self):
        body = "- [ ] Just a plain task\n- [x] Another one"
        assert detect_format(body, Path("specs/tasks.md")) == "generic"


class TestExtractTaskMetadata:
    def test_task_id(self):
        text, task_id, parallel, story = _extract_task_metadata("T001 Configure project")
        assert text == "Configure project"
        assert task_id == "T001"
        assert parallel is False
        assert story == ""

    def test_parallel_marker(self):
        text, task_id, parallel, story = _extract_task_metadata("T002 [P] Set up testing")
        assert text == "Set up testing"
        assert task_id == "T002"
        assert parallel is True

    def test_story_ref(self):
        text, task_id, parallel, story = _extract_task_metadata("T003 [US1] Create user model")
        assert text == "Create user model"
        assert task_id == "T003"
        assert story == "US1"

    def test_all_markers(self):
        text, task_id, parallel, story = _extract_task_metadata("T010 [P] [US2] Build login form")
        assert text == "Build login form"
        assert task_id == "T010"
        assert parallel is True
        assert story == "US2"

    def test_no_markers(self):
        text, task_id, parallel, story = _extract_task_metadata("Just a plain task")
        assert text == "Just a plain task"
        assert task_id == ""
        assert parallel is False
        assert story == ""


class TestParsePhases:
    def test_three_phases(self):
        body = """\
# Auth System Tasks

## Phase 1: Setup
- [x] T001 [P] Configure project structure
- [x] T002 Set up testing framework

**Checkpoint**: Foundation ready

## Phase 2: Core
- [ ] T003 [US1] Create user model
- [ ] T004 [P] [US1] Implement JWT

## Phase 3: Polish
- [ ] T005 [US2] Add error handling
"""
        flat, _ = parse_tasks(body)
        phases = _parse_phases(body, flat)

        assert len(phases) == 3

        p1 = phases[0]
        assert p1.number == 1
        assert p1.title == "Setup"
        assert len(p1.tasks) == 2
        assert p1.checkpoint == "Foundation ready"
        assert p1.task_done == 2
        assert p1.task_total == 2
        assert p1.task_percent == 100

        p2 = phases[1]
        assert p2.number == 2
        assert p2.title == "Core"
        assert len(p2.tasks) == 2
        assert p2.checkpoint == ""

        p3 = phases[2]
        assert p3.number == 3
        assert p3.title == "Polish"
        assert len(p3.tasks) == 1

    def test_phase_subtitle(self):
        body = """\
## Phase 1: US1 - Login Flow
- [ ] T001 Create login form
"""
        flat, _ = parse_tasks(body)
        phases = _parse_phases(body, flat)
        assert phases[0].title == "US1 - Login Flow"
        assert phases[0].subtitle == "Login Flow"


class TestSpeckitFullParse:
    def test_end_to_end(self, tmp_path):
        md = tmp_path / "tasks.md"
        md.write_text("""\
---
title: Auth System
status: in-progress
---

# Auth System Tasks

## Phase 1: Setup
- [x] T001 [P] Configure project structure
- [x] T002 [P] Set up testing framework
- [x] T003 Install dependencies

**Checkpoint**: Foundation ready - user story implementation can begin

## Phase 2: US1 - Login Flow
- [x] T004 [P] [US1] Create User model
- [ ] T005 [US1] Implement JWT validation
- [ ] T006 [P] [US1] Create login form
- [ ] T007 [US1] Add login tests

## Phase 3: US2 - Profile
- [ ] T008 [US2] Create profile page
- [ ] T009 [P] [US2] Add avatar upload
""")
        spec = parse_spec_file(md)
        assert spec.format_type == "spec-kit"
        assert len(spec.phases) == 3
        assert len(spec.tasks) == 9

        # Phase 1
        p1 = spec.phases[0]
        assert p1.number == 1
        assert p1.title == "Setup"
        assert p1.task_done == 3
        assert p1.task_total == 3
        assert p1.task_percent == 100
        assert p1.checkpoint == "Foundation ready - user story implementation can begin"

        # Task metadata
        t1 = spec.tasks[0]
        assert t1.task_id == "T001"
        assert t1.parallel is True
        assert t1.story == ""
        assert t1.text == "Configure project structure"

        t4 = spec.tasks[3]
        assert t4.task_id == "T004"
        assert t4.parallel is True
        assert t4.story == "US1"

        # Phase 2
        p2 = spec.phases[1]
        assert p2.number == 2
        assert p2.title == "US1 - Login Flow"
        assert p2.subtitle == "Login Flow"
        assert p2.task_done == 1
        assert p2.task_total == 4

        # Phase 3
        p3 = spec.phases[2]
        assert p3.number == 3
        assert len(p3.tasks) == 2
