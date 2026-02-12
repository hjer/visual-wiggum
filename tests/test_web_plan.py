"""Tests for web dashboard and tasks page plan section rendering."""

from pathlib import Path

import httpx
import pytest

from spec_view.core.config import Config
from spec_view.web.server import create_app


PLAN_CONTENT = """\
# Implementation Plan

> Auto-generated and maintained by the planning loop.

---

## Feature Alpha

**Status:** in-progress | **Priority:** high | **Tags:** core, ux

### Tasks

- [x] Build the widget
- [ ] Wire up events
- [ ] Add tests

---

## Feature Beta — DONE

**Status:** done | **Priority:** medium | **Tags:** web

### Tasks

- [x] Implement endpoint
- [x] Add template

---

## Discovered Issues

Some notes about problems found.
"""


def _make_config(tmp_path: Path) -> Config:
    return Config(
        spec_paths=[str(tmp_path / "specs")],
        include=["IMPLEMENTATION_PLAN.md"],
    )


@pytest.fixture()
def _setup(tmp_path):
    """Create a project with an active spec and a wiggum-format plan file."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "my-spec.md").write_text(
        "---\ntitle: My Spec\nstatus: ready\n---\n# My Spec\n- [ ] A task\n"
    )
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(PLAN_CONTENT)
    return tmp_path


@pytest.mark.asyncio
async def test_dashboard_shows_plan_section(_setup):
    """Dashboard renders an 'Implementation Plan' collapsible section with active plan groups."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "Implementation Plan" in html
    assert "plan-section" in html
    assert "Feature Alpha" in html


@pytest.mark.asyncio
async def test_dashboard_plan_section_aggregate_progress(_setup):
    """Plan section header shows aggregate task progress (active plan only)."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Only active plan groups (Feature Alpha: 1/3 done). Beta is archived.
    assert "1/3" in html


@pytest.mark.asyncio
async def test_dashboard_done_plan_sections_in_archive(_setup):
    """Done plan sections appear in the archive section, not the plan section."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "archive-section" in html
    assert "Feature Beta" in html


@pytest.mark.asyncio
async def test_dashboard_active_plan_in_plan_section_done_in_archive(_setup):
    """Active plan groups appear in plan section; done plan groups in archive."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Plan section should exist with active plan groups
    assert "plan-section" in html
    assert "Feature Alpha" in html
    # Archive section should exist with done plan groups
    assert "archive-section" in html


@pytest.mark.asyncio
async def test_tasks_page_shows_plan_section(_setup):
    """Tasks page renders active plan tasks grouped by section."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tasks")
    assert resp.status_code == 200
    html = resp.text
    assert "Implementation Plan" in html
    assert "plan-section" in html
    assert "Feature Alpha" in html


@pytest.mark.asyncio
async def test_tasks_page_plan_group_headings(_setup):
    """Tasks page shows per-section headings with task counts."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    assert "plan-group-heading" in html
    assert "plan-group-title" in html
    assert "plan-group-count" in html


@pytest.mark.asyncio
async def test_tasks_page_done_plan_in_archive(_setup):
    """Done plan sections appear in the archive section, not in the plan section."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    # No completed separator in plan section
    assert "plan-completed-separator" not in html
    assert "plan-group-done" not in html
    # Archive section exists with done plan tasks
    assert "archive-section" in html


@pytest.mark.asyncio
async def test_global_progress_includes_plan_tasks(_setup):
    """Global progress bar includes active plan task counts alongside active specs."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    html = resp.text
    # Active spec: 0/1 tasks. Active plan (Alpha): 1/3 tasks. Total: 1/4 = 25%
    # (Beta is archived, excluded from progress)
    assert "1/4" in html
    assert "25%" in html


@pytest.mark.asyncio
async def test_no_plan_section_when_no_plan_file(tmp_path):
    """Dashboard and tasks pages render fine without any plan file."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "test.md").write_text(
        "---\ntitle: Test\nstatus: ready\n---\n# Test\n- [ ] Task\n"
    )
    config = Config(spec_paths=[str(specs)])
    app = create_app(tmp_path, config)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        dash = await client.get("/")
        tasks = await client.get("/tasks")
    assert dash.status_code == 200
    assert tasks.status_code == 200
    assert "plan-section" not in dash.text
    assert "plan-section" not in tasks.text
