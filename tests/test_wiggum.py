"""Tests for wiggum-format plan section parsing, scanner expansion, and model."""

from pathlib import Path

from spec_view.core.config import Config
from spec_view.core.models import PlanSection, Priority, Status, Task
from spec_view.core.parser import (
    _clean_section_title,
    _slugify,
    detect_format,
    parse_plan_sections,
)
from spec_view.core.scanner import _expand_wiggum_sections, scan_specs
from spec_view.core.parser import parse_spec_file


# ---------------------------------------------------------------------------
# detect_format — wiggum detection
# ---------------------------------------------------------------------------

class TestDetectFormatWiggum:
    def test_wiggum_with_multiple_sections_and_status_lines(self):
        body = """\
## Feature A

**Status:** done | **Priority:** high

- [x] Task A1
- [x] Task A2

## Feature B

**Status:** in-progress | **Priority:** medium

- [ ] Task B1
"""
        assert detect_format(body, Path("IMPLEMENTATION_PLAN.md")) == "wiggum"

    def test_wiggum_needs_at_least_two_h2_and_two_status(self):
        body = """\
## Only One Section

**Status:** done

- [x] Task 1
"""
        # Only 1 h2 + 1 status: not enough
        assert detect_format(body, Path("plan.md")) != "wiggum"

    def test_wiggum_not_triggered_by_speckit(self):
        body = """\
## Phase 1: Setup
- [x] T001 Configure project
## Phase 2: Core
- [ ] T002 Build API
"""
        # spec-kit format takes precedence (phase headers + T### ids)
        assert detect_format(body, Path("tasks.md")) == "spec-kit"

    def test_wiggum_not_triggered_by_openspec_without_status(self):
        body = """\
## 1. Authentication
- [ ] Login flow
## 2. Authorization
- [ ] Role system
"""
        # openspec has numbered section headers but no **Status:** lines
        assert detect_format(body, Path("spec.md")) == "openspec"

    def test_wiggum_minimal_two_sections(self):
        body = """\
## A
**Status:** done
## B
**Status:** ready
"""
        assert detect_format(body, Path("plan.md")) == "wiggum"


# ---------------------------------------------------------------------------
# _clean_section_title
# ---------------------------------------------------------------------------

class TestCleanSectionTitle:
    def test_strips_done_suffix_em_dash(self):
        assert _clean_section_title("Feature A — DONE") == "Feature A"

    def test_strips_done_suffix_en_dash(self):
        assert _clean_section_title("Feature A – DONE") == "Feature A"

    def test_strips_done_suffix_hyphen(self):
        assert _clean_section_title("Feature A - DONE") == "Feature A"

    def test_strips_spec_prefix(self):
        assert _clean_section_title("Spec: My Feature") == "My Feature"

    def test_strips_spec_prefix_case_insensitive(self):
        assert _clean_section_title("spec: My Feature") == "My Feature"

    def test_strips_parenthetical_md_refs(self):
        assert _clean_section_title("Feature A (specs/feature-a.md)") == "Feature A"

    def test_combined_cleaning(self):
        title = "Spec: Feature A (specs/feature-a.md) — DONE"
        assert _clean_section_title(title) == "Feature A"

    def test_no_cleaning_needed(self):
        assert _clean_section_title("Plain Title") == "Plain Title"


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic_title(self):
        assert _slugify("My Feature") == "my-feature"

    def test_special_characters(self):
        assert _slugify("Feature: Auth & Tokens!") == "feature-auth-tokens"

    def test_leading_trailing_dashes(self):
        assert _slugify("--- hello ---") == "hello"


# ---------------------------------------------------------------------------
# parse_plan_sections — core parsing
# ---------------------------------------------------------------------------

class TestParsePlanSections:
    def test_multi_section_split(self):
        body = """\
# Implementation Plan

## Feature A — DONE

**Status:** done | **Priority:** high | **Tags:** core, api

### Tasks
- [x] Build API
- [x] Add tests

## Feature B

**Status:** in-progress | **Priority:** medium | **Tags:** tui

### Tasks
- [x] Create widget
- [ ] Add styling
"""
        sections = parse_plan_sections(body, Path("PLAN.md"))
        assert len(sections) == 2

        a = sections[0]
        assert a.title == "Feature A"
        assert a.status == Status.DONE
        assert a.priority == Priority.HIGH
        assert "plan" in a.tags
        assert "core" in a.tags
        assert "api" in a.tags
        assert a.task_total == 2
        assert a.task_done == 2
        assert a.task_percent == 100

        b = sections[1]
        assert b.title == "Feature B"
        assert b.status == Status.IN_PROGRESS
        assert b.priority == Priority.MEDIUM
        assert "plan" in b.tags
        assert "tui" in b.tags
        assert b.task_total == 2
        assert b.task_done == 1
        assert b.task_percent == 50

    def test_skips_structural_sections(self):
        body = """\
## Feature A

**Status:** done

- [x] Task 1

## Discovered Issues

Some notes about issues.

## Feature B

**Status:** ready

- [ ] Task 2
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert len(sections) == 2
        titles = [s.title for s in sections]
        assert "Discovered Issues" not in titles
        assert "Feature A" in titles
        assert "Feature B" in titles

    def test_status_from_heading_done_suffix(self):
        body = """\
## Feature X — DONE

### Tasks
- [x] All done
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert len(sections) == 1
        assert sections[0].status == Status.DONE

    def test_status_from_body_line(self):
        body = """\
## Feature Y

**Status:** blocked | **Priority:** critical

- [ ] Blocked task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].status == Status.BLOCKED
        assert sections[0].priority == Priority.CRITICAL

    def test_title_cleaning_combined(self):
        body = """\
## Spec: Track IMPLEMENTATION_PLAN.md (specs/track-impl.md) — DONE

**Status:** done

- [x] Task 1
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].title == "Track IMPLEMENTATION_PLAN.md"

    def test_tasks_are_section_specific(self):
        body = """\
## Section A

**Status:** done

- [x] Task from A

## Section B

**Status:** ready

- [ ] Task from B
- [ ] Another from B
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].task_total == 1
        assert sections[1].task_total == 2
        assert sections[0].tasks[0].text == "Task from A"
        assert sections[1].tasks[0].text == "Task from B"

    def test_plan_tag_always_present(self):
        body = """\
## Feature

**Status:** ready

- [ ] Task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert "plan" in sections[0].tags

    def test_no_duplicate_plan_tag(self):
        body = """\
## Feature

**Status:** ready | **Tags:** plan, tui

- [ ] Task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].tags.count("plan") == 1

    def test_priority_defaults_to_medium(self):
        body = """\
## Feature

**Status:** ready

- [ ] Task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].priority == Priority.MEDIUM

    def test_single_section(self):
        body = """\
## Only Section

**Status:** in-progress

- [ ] The task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert len(sections) == 1
        assert sections[0].title == "Only Section"

    def test_section_with_no_tasks_but_has_status(self):
        body = """\
## Planning Phase

**Status:** done

No tasks here, just text.

## Execution Phase

**Status:** in-progress

- [ ] Execute plan
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        # Planning Phase has status but no tasks — still included
        assert len(sections) == 2
        assert sections[0].title == "Planning Phase"
        assert sections[0].task_total == 0

    def test_nested_subsections_tasks_belong_to_parent(self):
        body = """\
## Feature A

**Status:** in-progress

### Sub-feature 1
- [x] Sub task 1

### Sub-feature 2
- [ ] Sub task 2
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert len(sections) == 1
        assert sections[0].title == "Feature A"
        # Both sub-section tasks should belong to Feature A
        assert sections[0].task_total == 2

    def test_body_includes_heading(self):
        body = """\
## Feature A

**Status:** done

- [x] Task
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert sections[0].body.startswith("## Feature A")

    def test_source_path_set(self):
        path = Path("/project/IMPLEMENTATION_PLAN.md")
        body = """\
## Feature

**Status:** done

- [x] Task
"""
        sections = parse_plan_sections(body, path)
        assert sections[0].source_path == path

    def test_task_tree_built(self):
        body = """\
## Feature

**Status:** in-progress

- [ ] Parent task
  - [x] Child task
  - [ ] Another child
"""
        sections = parse_plan_sections(body, Path("plan.md"))
        assert len(sections[0].tasks) == 3  # flat
        assert len(sections[0].task_tree) == 1  # one top-level
        parent = sections[0].task_tree[0]
        assert parent.text == "Parent task"
        assert len(parent.children) == 2

    def test_empty_body_returns_no_sections(self):
        assert parse_plan_sections("", Path("plan.md")) == []

    def test_body_with_no_h2(self):
        body = "# Just a heading\nSome text."
        assert parse_plan_sections(body, Path("plan.md")) == []


# ---------------------------------------------------------------------------
# PlanSection model computed properties
# ---------------------------------------------------------------------------

class TestPlanSectionModel:
    def test_task_total(self):
        ps = PlanSection(
            title="Test",
            tasks=[Task(text="a", done=True), Task(text="b")],
        )
        assert ps.task_total == 2

    def test_task_done(self):
        ps = PlanSection(
            title="Test",
            tasks=[Task(text="a", done=True), Task(text="b", done=True), Task(text="c")],
        )
        assert ps.task_done == 2

    def test_task_percent(self):
        ps = PlanSection(
            title="Test",
            tasks=[Task(text="a", done=True), Task(text="b")],
        )
        assert ps.task_percent == 50

    def test_task_percent_zero_tasks(self):
        ps = PlanSection(title="Empty")
        assert ps.task_percent == 0

    def test_task_percent_all_done(self):
        ps = PlanSection(
            title="Done",
            tasks=[Task(text="a", done=True), Task(text="b", done=True)],
        )
        assert ps.task_percent == 100


# ---------------------------------------------------------------------------
# _expand_wiggum_sections — scanner expansion
# ---------------------------------------------------------------------------

class TestExpandWiggumSections:
    def _make_spec_file(self, tmp_path: Path):
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text("""\
# Implementation Plan

## Feature Alpha — DONE

**Status:** done | **Priority:** high | **Tags:** core

- [x] Build it
- [x] Test it

## Feature Beta

**Status:** in-progress | **Priority:** medium | **Tags:** tui, web

- [x] Start it
- [ ] Finish it

## Learnings

Just notes, no status, no tasks.
""")
        return parse_spec_file(plan), plan

    def test_produces_correct_number_of_groups(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        # "Learnings" is structural (no status, no tasks) — skipped
        assert len(groups) == 2

    def test_groups_have_plan_tag(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        for g in groups:
            assert "plan" in g.tags

    def test_done_section_gets_archive_tag(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        alpha = groups[0]
        assert "archive" in alpha.tags
        assert "plan" in alpha.tags
        beta = groups[1]
        assert "archive" not in beta.tags

    def test_slug_names(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        assert groups[0].name == "feature-alpha"
        assert groups[1].name == "feature-beta"

    def test_group_titles(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        assert groups[0].title == "Feature Alpha"
        assert groups[1].title == "Feature Beta"

    def test_group_task_counts(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        assert groups[0].task_total == 2
        assert groups[0].task_done == 2
        assert groups[1].task_total == 2
        assert groups[1].task_done == 1

    def test_group_status_and_priority(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        assert groups[0].status == Status.DONE
        assert groups[0].priority == Priority.HIGH
        assert groups[1].status == Status.IN_PROGRESS
        assert groups[1].priority == Priority.MEDIUM

    def test_group_format_type_is_wiggum(self, tmp_path):
        spec_file, path = self._make_spec_file(tmp_path)
        groups = _expand_wiggum_sections(spec_file, path)
        assert groups[0].format_type == "wiggum"
        assert groups[1].format_type == "wiggum"

    def test_empty_sections_returns_empty(self, tmp_path):
        plan = tmp_path / "plan.md"
        plan.write_text("# Plan\n\nJust some text, no ## sections.")
        spec_file = parse_spec_file(plan)
        groups = _expand_wiggum_sections(spec_file, plan)
        assert groups == []


# ---------------------------------------------------------------------------
# scan_specs integration — wiggum files expand into plan groups
# ---------------------------------------------------------------------------

class TestScanSpecsWiggum:
    def test_wiggum_file_expands_to_plan_groups(self, tmp_path):
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "feature.md").write_text(
            "---\ntitle: Feature\nstatus: ready\n---\n# Feature\n- [ ] Task\n"
        )
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text("""\
# Implementation Plan

## Feature A — DONE

**Status:** done

- [x] Done task

## Feature B

**Status:** in-progress

- [ ] Open task
""")
        config = Config(
            spec_paths=["specs/"],
            include=["IMPLEMENTATION_PLAN.md"],
        )
        groups = scan_specs(tmp_path, config)
        # 1 regular group (feature) + 2 plan groups (A, B)
        assert len(groups) == 3
        names = [g.name for g in groups]
        assert "feature" in names
        assert "feature-a" in names
        assert "feature-b" in names

    def test_plan_groups_come_after_regular_groups(self, tmp_path):
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "zzz.md").write_text("---\ntitle: ZZZ\n---\n# ZZZ\n")
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text("""\
# Plan

## Alpha

**Status:** done

- [x] Task

## Beta

**Status:** ready

- [ ] Task
""")
        config = Config(
            spec_paths=["specs/"],
            include=["IMPLEMENTATION_PLAN.md"],
        )
        groups = scan_specs(tmp_path, config)
        # Regular groups sorted alphabetically first, then plan groups in file order
        assert groups[0].name == "zzz"
        assert groups[1].name == "alpha"
        assert groups[2].name == "beta"

    def test_plan_groups_preserve_section_order(self, tmp_path):
        plan = tmp_path / "PLAN.md"
        plan.write_text("""\
# Plan

## Zebra

**Status:** ready

- [ ] Task

## Apple

**Status:** done

- [x] Task
""")
        config = Config(spec_paths=[], include=["PLAN.md"])
        groups = scan_specs(tmp_path, config)
        # Plan sections should be in file order, not alphabetical
        assert groups[0].name == "zebra"
        assert groups[1].name == "apple"
