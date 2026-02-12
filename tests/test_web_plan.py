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
    """Dashboard renders an 'Implementation Plan' collapsible section with plan groups."""
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
    assert "Feature Beta" in html


@pytest.mark.asyncio
async def test_dashboard_plan_section_aggregate_progress(_setup):
    """Plan section header shows aggregate task progress."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # 3 done out of 5 total (1 from Alpha + 2 from Beta)
    assert "3/5" in html


@pytest.mark.asyncio
async def test_dashboard_plan_done_cards_dimmed(_setup):
    """Done plan sections get the plan-done-card class for dimming."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    assert "plan-done-card" in html


@pytest.mark.asyncio
async def test_dashboard_plan_groups_not_in_archive(_setup):
    """Plan groups appear in the plan section, not the archive section."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/dashboard-content")
    html = resp.text
    # Archive section should not exist since there are no archived specs
    assert "archive-section" not in html
    # But plan section should exist
    assert "plan-section" in html


@pytest.mark.asyncio
async def test_tasks_page_shows_plan_section(_setup):
    """Tasks page renders plan tasks grouped by section."""
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
    assert "Feature Beta" in html


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
async def test_tasks_page_plan_completed_separator(_setup):
    """Done plan sections appear after a 'Completed' separator."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/tasks-content")
    html = resp.text
    assert "plan-completed-separator" in html
    assert "Completed" in html
    assert "plan-group-done" in html


@pytest.mark.asyncio
async def test_global_progress_includes_plan_tasks(_setup):
    """Global progress bar includes plan task counts alongside active specs."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    html = resp.text
    # Active spec: 0/1 tasks. Plan: 3/5 tasks. Total: 3/6 = 50%
    assert "3/6" in html
    assert "50%" in html


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
