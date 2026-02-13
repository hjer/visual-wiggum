"""Tests for archive sub-grouping: plan sections grouped under 'Implementation Plan' within Archive."""

from pathlib import Path

import httpx
import pytest

from spec_view.core.config import Config
from spec_view.core.models import SpecFile, SpecGroup, Status, Task
from spec_view.tui.dashboard import DashboardScreen
from spec_view.tui.task_board import TaskBoardScreen
from spec_view.web.server import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_group(
    name: str,
    title: str,
    tags: list[str],
    tasks: list[Task] | None = None,
    status: Status = Status.DONE,
) -> SpecGroup:
    """Create a minimal SpecGroup with given tags and tasks."""
    if tasks is None:
        tasks = [Task(text="t", done=True)]
    sf = SpecFile(
        path=Path(f"/tmp/{name}.md"),
        title=title,
        body="",
        status=status,
        tasks=tasks,
        tags=tags,
    )
    return SpecGroup(name=name, path=Path(f"/tmp/{name}"), files={"spec": sf})


# ---------------------------------------------------------------------------
# TUI Dashboard — archive sub-grouping
# ---------------------------------------------------------------------------

class TestTUIDashboardArchiveSubgroup:
    def test_archived_plan_under_implementation_plan_subnode(self):
        """Archived plan groups appear under 'Implementation Plan' sub-node within Archive."""
        groups = [
            _make_group("active-spec", "Active Spec", [], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
            _make_group("archived-plan", "Archived Plan Section", ["plan", "archive"],
                        tasks=[Task(text="t", done=True)]),
            _make_group("archived-spec", "Archived Spec", ["archive"],
                        tasks=[Task(text="t", done=True)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        # Find the Archive node
        archive_node = None
        for child in tree.root.children:
            if "Archive" in str(child.label):
                archive_node = child
                break
        assert archive_node is not None

        # Archive should have an "Implementation Plan" sub-node
        sub_labels = [str(child.label) for child in archive_node.children]
        plan_sub = [l for l in sub_labels if "Implementation Plan" in l]
        assert len(plan_sub) == 1
        assert "1/1" in plan_sub[0]  # aggregate counts

    def test_archived_specs_under_specs_subnode(self):
        """Archived spec groups with 'specs' tag appear under 'Specs' sub-node within Archive."""
        groups = [
            _make_group("archived-plan", "Plan Done", ["plan", "archive"]),
            _make_group("archived-spec", "Spec Done", ["specs", "archive"],
                        tasks=[Task(text="t", done=True)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        archive_node = None
        for child in tree.root.children:
            if "Archive" in str(child.label):
                archive_node = child
                break
        assert archive_node is not None

        # Archive should have: "Implementation Plan" sub-node + "Specs" sub-node
        direct_labels = [str(child.label) for child in archive_node.children]
        specs_labels = [l for l in direct_labels if "Specs" in l and "Implementation" not in l]
        assert len(specs_labels) == 1
        assert "1/1" in specs_labels[0]  # aggregate counts

    def test_archived_other_directly_under_archive(self):
        """Archived groups without 'plan' or 'specs' tags appear directly under Archive."""
        groups = [
            _make_group("archived-plan", "Plan Done", ["plan", "archive"]),
            _make_group("archived-other", "Other Done", ["archive"],
                        tasks=[Task(text="t", done=True)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        archive_node = None
        for child in tree.root.children:
            if "Archive" in str(child.label):
                archive_node = child
                break
        assert archive_node is not None

        # Archive should have: "Implementation Plan" sub-node + "Other Done" group node
        direct_labels = [str(child.label) for child in archive_node.children]
        other_labels = [l for l in direct_labels if "Other Done" in l]
        assert len(other_labels) == 1

    def test_no_plan_subnode_when_only_archived_specs(self):
        """No 'Implementation Plan' sub-node when there are no archived plan groups."""
        groups = [
            _make_group("archived-spec", "Spec Done", ["specs", "archive"]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        archive_node = None
        for child in tree.root.children:
            if "Archive" in str(child.label):
                archive_node = child
                break
        assert archive_node is not None

        sub_labels = [str(child.label) for child in archive_node.children]
        plan_sub = [l for l in sub_labels if "Implementation Plan" in l]
        assert len(plan_sub) == 0
        # Should have a "Specs" sub-node though
        specs_sub = [l for l in sub_labels if "Specs" in l]
        assert len(specs_sub) == 1

    def test_only_archived_plan_no_bare_items(self):
        """When only archived plan groups exist, all appear under plan sub-node."""
        groups = [
            _make_group("ap1", "Plan A", ["plan", "archive"], tasks=[Task(text="t", done=True)]),
            _make_group("ap2", "Plan B", ["plan", "archive"], tasks=[Task(text="t", done=True), Task(text="t2", done=True)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        archive_node = None
        for child in tree.root.children:
            if "Archive" in str(child.label):
                archive_node = child
                break
        assert archive_node is not None

        # Archive should have exactly 1 child: the "Implementation Plan" sub-node
        assert len(archive_node.children) == 1
        assert "Implementation Plan" in str(archive_node.children[0].label)
        assert "3/3" in str(archive_node.children[0].label)


# ---------------------------------------------------------------------------
# TUI Dashboard — active "Specs" section
# ---------------------------------------------------------------------------

class TestTUIDashboardSpecsSection:
    def test_specs_groups_under_specs_node(self):
        """Groups with 'specs' tag appear under collapsible 'Specs' node."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t1", done=True), Task(text="t2", done=False)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        root_labels = [str(child.label) for child in tree.root.children]
        # Should have "Active Item" at root and a "Specs" node
        active_labels = [l for l in root_labels if "Active Item" in l]
        specs_labels = [l for l in root_labels if l.startswith("\u25b8 Specs")]
        assert len(active_labels) == 1
        assert len(specs_labels) == 1
        assert "1/2" in specs_labels[0]

    def test_no_specs_node_when_no_specs_groups(self):
        """No 'Specs' node when there are no specs-tagged groups."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        root_labels = [str(child.label) for child in tree.root.children]
        specs_labels = [l for l in root_labels if "Specs" in l and "Implementation" not in l]
        assert len(specs_labels) == 0

    def test_specs_node_before_plan_node(self):
        """Specs node appears before Implementation Plan node in tree."""
        groups = [
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
            _make_group("plan-item", "Plan Item", ["plan"], status=Status.IN_PROGRESS,
                        tasks=[Task(text="t", done=False)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        root_labels = [str(child.label) for child in tree.root.children]
        specs_idx = next(i for i, l in enumerate(root_labels) if "Specs" in l and "Implementation" not in l)
        plan_idx = next(i for i, l in enumerate(root_labels) if "Implementation Plan" in l)
        assert specs_idx < plan_idx

    def test_specs_groups_not_in_active_root(self):
        """Groups with 'specs' tag should NOT appear at tree root as active items."""
        groups = [
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
        ]
        screen = DashboardScreen(groups, Path("/tmp"))
        from spec_view.tui.dashboard import SpecTree
        tree = SpecTree("Specs")
        tree.show_root = False
        screen._populate_tree(tree)

        root_labels = [str(child.label) for child in tree.root.children]
        # "My Spec" should only be under the "Specs" node, not at root
        direct_spec = [l for l in root_labels if "My Spec" in l]
        assert len(direct_spec) == 0
        # Should be inside the Specs node
        specs_node = [c for c in tree.root.children if "Specs" in str(c.label) and "Implementation" not in str(c.label)][0]
        child_labels = [str(c.label) for c in specs_node.children]
        spec_in_node = [l for l in child_labels if "My Spec" in l]
        assert len(spec_in_node) == 1


# ---------------------------------------------------------------------------
# TUI Task Board — archive sub-grouping
# ---------------------------------------------------------------------------

class TestTUITaskBoardArchiveSubgroup:
    def test_archived_plan_under_implementation_plan_heading(self):
        """Archived plan tasks grouped under 'Implementation Plan' heading in archive section."""
        groups = [
            _make_group("active", "Active", [], status=Status.READY,
                        tasks=[Task(text="active task", done=False)]),
            _make_group("archived-plan", "Plan Done", ["plan", "archive"],
                        tasks=[Task(text="plan task", done=True)]),
            _make_group("archived-spec", "Spec Done", ["archive"],
                        tasks=[Task(text="spec task", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        # Archive heading exists
        assert "Archive" in content
        # Implementation Plan sub-heading within archive
        assert "Implementation Plan" in content
        # Both archived groups appear
        assert "Plan Done" in content
        assert "Spec Done" in content

    def test_no_plan_heading_when_only_archived_specs(self):
        """No 'Implementation Plan' heading when archive has only spec groups."""
        groups = [
            _make_group("archived-spec", "Spec Done", ["archive"],
                        tasks=[Task(text="spec task", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        assert "Archive" in content
        # The active plan section heading should NOT appear — count occurrences
        # "Implementation Plan" appears in the active plan section when plan groups exist,
        # but should not appear in archive when there are no archived plan groups
        lines = content.split("\n")
        impl_plan_lines = [l for l in lines if "Implementation Plan" in l]
        assert len(impl_plan_lines) == 0

    def test_only_archived_plan_all_under_heading(self):
        """When only archived plan groups exist, all appear under plan heading."""
        groups = [
            _make_group("ap1", "Plan A", ["plan", "archive"],
                        tasks=[Task(text="plan task a", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        assert "Archive" in content
        assert "Implementation Plan" in content
        assert "Plan A" in content

    def test_archived_specs_under_specs_heading(self):
        """Archived specs-tagged groups appear under 'Specs' heading in archive section."""
        groups = [
            _make_group("archived-spec", "Spec Done", ["specs", "archive"],
                        tasks=[Task(text="spec task", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        assert "Archive" in content
        lines = content.split("\n")
        specs_lines = [l for l in lines if "Specs" in l and "Task Board" not in l]
        assert len(specs_lines) >= 1
        assert "Spec Done" in content

    def test_archived_other_directly_in_archive(self):
        """Archived groups without plan or specs tags appear directly under archive."""
        groups = [
            _make_group("archived-plan", "Plan Done", ["plan", "archive"],
                        tasks=[Task(text="pt", done=True)]),
            _make_group("archived-other", "Other Done", ["archive"],
                        tasks=[Task(text="ot", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        assert "Archive" in content
        assert "Implementation Plan" in content
        assert "Other Done" in content
        # "Other Done" should NOT be under "Specs" heading since it has no specs tag
        lines = content.split("\n")
        specs_heading_lines = [l for l in lines if "Specs" in l and "dim bold" in l]
        assert len(specs_heading_lines) == 0


# ---------------------------------------------------------------------------
# TUI Task Board — active "Specs" section
# ---------------------------------------------------------------------------

class TestTUITaskBoardSpecsSection:
    def test_specs_groups_under_specs_heading(self):
        """Groups with 'specs' tag appear under 'Specs' heading in task board."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="active task", done=False)]),
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t1", done=True), Task(text="t2", done=False)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        # Active item should be present
        assert "Active Item" in content
        # Specs heading should be present with aggregate counts
        assert "Specs" in content
        assert "1/2" in content
        assert "My Spec" in content

    def test_no_specs_heading_when_no_specs_groups(self):
        """No 'Specs' heading when there are no specs-tagged groups."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="active task", done=False)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        lines = content.split("\n")
        # Only "Task Board" header should appear, no "Specs" section heading
        specs_heading_lines = [l for l in lines if l.strip().startswith("[bold]Specs[/bold]")]
        assert len(specs_heading_lines) == 0

    def test_specs_heading_before_plan_heading(self):
        """Specs section appears before Implementation Plan section."""
        groups = [
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
            _make_group("plan-item", "Plan Item", ["plan"], status=Status.IN_PROGRESS,
                        tasks=[Task(text="t", done=False)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        specs_pos = content.index("[bold]Specs[/bold]")
        plan_pos = content.index("[bold]Implementation Plan[/bold]")
        assert specs_pos < plan_pos

    def test_specs_groups_not_in_active_section(self):
        """Groups with 'specs' tag should NOT appear in the active section (before Specs heading)."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="active task", done=False)]),
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t", done=False)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        # "My Spec" should appear after the "Specs" heading, not before it
        specs_heading_pos = content.index("[bold]Specs[/bold]")
        my_spec_pos = content.index("My Spec")
        assert my_spec_pos > specs_heading_pos

    def test_specs_tasks_included_in_total_count(self):
        """Specs tasks are included in the top-level task board count."""
        groups = [
            _make_group("active-item", "Active Item", [], status=Status.READY,
                        tasks=[Task(text="t1", done=True)]),
            _make_group("my-spec", "My Spec", ["specs"], status=Status.READY,
                        tasks=[Task(text="t2", done=False), Task(text="t3", done=True)]),
        ]
        board = TaskBoardScreen(groups)
        content = board._build_content()
        # Total should be 3 tasks, 2 done
        assert "2/3 complete" in content


# ---------------------------------------------------------------------------
# Web Dashboard — archive sub-grouping
# ---------------------------------------------------------------------------

PLAN_WITH_ARCHIVED = """\
# Implementation Plan

## Active Feature

**Status:** in-progress | **Priority:** high | **Tags:** core

### Tasks

- [x] Step one
- [ ] Step two

---

## Archived Feature — DONE

**Status:** done | **Priority:** medium | **Tags:** web

### Tasks

- [x] Build it
- [x] Test it
"""


def _make_web_config(tmp_path: Path) -> Config:
    return Config(
        spec_paths=[str(tmp_path / "specs")],
        include=["IMPLEMENTATION_PLAN.md"],
    )


@pytest.fixture()
def _web_setup(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    archive = specs / "archive"
    archive.mkdir()
    (specs / "my-spec.md").write_text(
        "---\ntitle: My Spec\nstatus: ready\n---\n# My Spec\n- [ ] Spec task\n"
    )
    (archive / "old-spec.md").write_text(
        "---\ntitle: Old Spec\nstatus: done\n---\n# Old Spec\n- [x] Old task\n"
    )
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(PLAN_WITH_ARCHIVED)
    return tmp_path


@pytest.mark.asyncio
async def test_web_dashboard_archive_plan_subheading(_web_setup):
    """Web dashboard archive section has 'Implementation Plan' sub-heading for plan groups."""
    tmp_path = _web_setup
    app = create_app(tmp_path, _make_web_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    assert "archive-sub-heading" in html
    assert "Implementation Plan" in html
    # Archived Feature should be in the archive section
    assert "Archived Feature" in html


@pytest.mark.asyncio
async def test_web_dashboard_archive_no_plan_subheading_without_plan(tmp_path):
    """No 'Implementation Plan' sub-heading when archive has only spec groups."""
    specs = tmp_path / "specs"
    specs.mkdir()
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old.md").write_text(
        "---\ntitle: Old\nstatus: done\n---\n# Old\n- [x] Task\n"
    )
    config = Config(spec_paths=[str(specs)])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    # Should have "Specs" sub-heading (archived spec group) but not "Implementation Plan"
    assert ">Specs (" in html
    assert ">Implementation Plan (" not in html


@pytest.mark.asyncio
async def test_web_tasks_archive_plan_subheading(_web_setup):
    """Web tasks archive section has 'Implementation Plan' sub-heading for plan groups."""
    tmp_path = _web_setup
    app = create_app(tmp_path, _make_web_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    assert "archive-section" in html
    assert "archive-sub-heading" in html
    assert "Implementation Plan" in html


@pytest.mark.asyncio
async def test_web_tasks_archive_no_plan_subheading_without_plan(tmp_path):
    """No 'Implementation Plan' sub-heading when tasks archive has only spec groups."""
    specs = tmp_path / "specs"
    specs.mkdir()
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old.md").write_text(
        "---\ntitle: Old\nstatus: done\n---\n# Old\n- [x] Task\n"
    )
    config = Config(spec_paths=[str(specs)])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    # Archive should exist (there's an archived spec) with Specs sub-heading
    assert "archive-section" in html
    assert "Specs (" in html
    # No Implementation Plan sub-heading since there are no archived plan groups
    assert ">Implementation Plan" not in html


# ---------------------------------------------------------------------------
# Web Dashboard & Tasks — "Other" archive sub-group
# ---------------------------------------------------------------------------


@pytest.fixture()
def _web_other_setup(tmp_path):
    """Setup with an include file in an archive/ dir outside spec_paths (→ 'Other')."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "my-spec.md").write_text(
        "---\ntitle: My Spec\nstatus: ready\n---\n# My Spec\n- [ ] Spec task\n"
    )
    # Create an archive directory outside spec_paths with an included file
    other_archive = tmp_path / "docs" / "archive"
    other_archive.mkdir(parents=True)
    (other_archive / "misc-notes.md").write_text(
        "---\ntitle: Misc Notes\nstatus: done\n---\n# Misc Notes\n- [x] Note task\n"
    )
    return tmp_path


def _make_other_config(tmp_path) -> Config:
    return Config(
        spec_paths=[str(tmp_path / "specs")],
        include=["docs/archive/misc-notes.md"],
    )


@pytest.mark.asyncio
async def test_web_dashboard_archive_other_subheading(_web_other_setup):
    """Web dashboard archive section has 'Other' sub-heading for non-plan/non-specs groups."""
    tmp_path = _web_other_setup
    app = create_app(tmp_path, _make_other_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    assert ">Other (" in html
    assert "Misc Notes" in html


@pytest.mark.asyncio
async def test_web_tasks_archive_other_subheading(_web_other_setup):
    """Web tasks archive section has 'Other' sub-heading for non-plan/non-specs groups."""
    tmp_path = _web_other_setup
    app = create_app(tmp_path, _make_other_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    assert "archive-section" in html
    assert ">Other (" in html
    assert "Misc Notes" in html


@pytest.mark.asyncio
async def test_web_dashboard_no_other_subheading_without_other(tmp_path):
    """No 'Other' sub-heading when all archived groups are plan or specs."""
    specs = tmp_path / "specs"
    specs.mkdir()
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old.md").write_text(
        "---\ntitle: Old\nstatus: done\n---\n# Old\n- [x] Task\n"
    )
    config = Config(spec_paths=[str(specs)])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    assert ">Other (" not in html


@pytest.mark.asyncio
async def test_web_tasks_no_other_subheading_without_other(tmp_path):
    """No 'Other' sub-heading when all archived groups are plan or specs."""
    specs = tmp_path / "specs"
    specs.mkdir()
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old.md").write_text(
        "---\ntitle: Old\nstatus: done\n---\n# Old\n- [x] Task\n"
    )
    config = Config(spec_paths=[str(specs)])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    assert "archive-section" in html
    assert ">Other (" not in html
