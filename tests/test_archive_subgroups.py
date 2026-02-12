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

    def test_archived_specs_directly_under_archive(self):
        """Archived spec groups appear directly under Archive, not under a sub-heading."""
        groups = [
            _make_group("archived-plan", "Plan Done", ["plan", "archive"]),
            _make_group("archived-spec", "Spec Done", ["archive"]),
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

        # Archive should have: "Implementation Plan" sub-node + "Spec Done" group node
        direct_labels = [str(child.label) for child in archive_node.children]
        # "Spec Done" should be a direct child (not inside plan sub-node)
        spec_labels = [l for l in direct_labels if "Spec Done" in l]
        assert len(spec_labels) == 1

    def test_no_plan_subnode_when_only_archived_specs(self):
        """No 'Implementation Plan' sub-node when there are no archived plan groups."""
        groups = [
            _make_group("archived-spec", "Spec Done", ["archive"]),
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
    assert "archive-sub-heading" not in html


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
    # Archive should exist (there's an archived spec)
    assert "archive-section" in html
    assert "archive-sub-heading" not in html
