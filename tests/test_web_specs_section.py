"""Tests for the web dashboard and tasks page 'Specs' section rendering."""

from pathlib import Path

import httpx
import pytest

from spec_view.core.config import Config
from spec_view.web.server import create_app


def _make_config(tmp_path: Path) -> Config:
    return Config(
        spec_paths=[str(tmp_path / "specs")],
        include=["IMPLEMENTATION_PLAN.md"],
    )


@pytest.fixture()
def _setup(tmp_path):
    """Create a project with specs (get 'specs' tag) and a plan file."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "scanning.md").write_text(
        "---\ntitle: Scanning Spec\nstatus: in-progress\n---\n"
        "# Scanning\n- [x] Done task\n- [ ] Open task\n"
    )
    (specs / "models.md").write_text(
        "---\ntitle: Models Spec\nstatus: ready\n---\n"
        "# Models\n- [ ] A task\n"
    )
    # Plan file so plan section also appears (needs 2+ ## sections with **Status:** for wiggum detection)
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(
        "# Implementation Plan\n\n---\n\n"
        "## Feature X\n\n"
        "**Status:** in-progress | **Priority:** high | **Tags:** core\n\n"
        "- [ ] Plan task\n\n---\n\n"
        "## Feature Y\n\n"
        "**Status:** in-progress | **Priority:** medium | **Tags:** web\n\n"
        "- [ ] Another plan task\n"
    )
    return tmp_path


@pytest.fixture()
def _setup_with_archive(tmp_path):
    """Create a project with active specs, archived specs, and archived plan."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "active.md").write_text(
        "---\ntitle: Active Spec\nstatus: in-progress\n---\n"
        "# Active\n- [ ] Task\n"
    )
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old-spec.md").write_text(
        "---\ntitle: Old Spec\nstatus: done\n---\n"
        "# Old\n- [x] Done\n"
    )
    # Plan with done sections (becomes archived plan; needs 2+ ## for wiggum detection)
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(
        "# Implementation Plan\n\n---\n\n"
        "## Done Feature\n\n"
        "**Status:** done | **Priority:** high | **Tags:** core\n\n"
        "- [x] All done\n\n---\n\n"
        "## Another Done\n\n"
        "**Status:** done | **Priority:** medium | **Tags:** web\n\n"
        "- [x] Also done\n"
    )
    return tmp_path


@pytest.mark.asyncio
async def test_dashboard_shows_specs_section(_setup):
    """Dashboard renders a collapsible 'Specs' section with spec-tagged groups."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "Specs (" in html
    assert "Scanning Spec" in html
    assert "Models Spec" in html


@pytest.mark.asyncio
async def test_dashboard_specs_section_aggregate_progress(_setup):
    """Specs section header shows aggregate task progress."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Scanning: 1/2, Models: 0/1 => total 1/3
    assert "Specs (1/3)" in html


@pytest.mark.asyncio
async def test_dashboard_specs_section_is_collapsible(_setup):
    """Specs section uses the collapsible plan-section pattern."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Specs section should appear before plan section and use same CSS pattern
    specs_pos = html.find("Specs (1/3)")
    plan_pos = html.find("Implementation Plan (")
    assert specs_pos > -1, f"Specs section not found in HTML"
    assert plan_pos > -1, f"Plan section not found in HTML"
    assert specs_pos < plan_pos


@pytest.mark.asyncio
async def test_dashboard_archive_sub_groups_specs(_setup_with_archive):
    """Archive section shows 'Specs' sub-heading for archived spec-tagged groups."""
    tmp_path = _setup_with_archive
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    assert "archive-sub-heading" in html
    assert "Old Spec" in html


@pytest.mark.asyncio
async def test_dashboard_archive_has_plan_and_specs_sub_headings(_setup_with_archive):
    """Archive has separate sub-headings for plan and specs groups."""
    tmp_path = _setup_with_archive
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Both sub-headings should be present in the archive
    # Count archive-sub-heading occurrences - should have at least 2 (plan + specs)
    assert html.count("archive-sub-heading") >= 2


@pytest.mark.asyncio
async def test_no_specs_section_without_spec_paths(tmp_path):
    """Dashboard doesn't show Specs section when no spec_paths groups exist."""
    # Use include-only config (no spec_paths), so nothing gets "specs" tag
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(
        "# Implementation Plan\n\n---\n\n"
        "## Feature\n\n"
        "**Status:** in-progress | **Priority:** high | **Tags:** core\n\n"
        "- [ ] Task\n\n---\n\n"
        "## Feature 2\n\n"
        "**Status:** in-progress | **Priority:** medium | **Tags:** web\n\n"
        "- [ ] Task 2\n"
    )
    config = Config(spec_paths=[], include=["IMPLEMENTATION_PLAN.md"])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "Specs (" not in html
    # Plan section should still appear
    assert "Implementation Plan" in html
