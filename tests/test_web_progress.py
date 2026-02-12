"""Tests for the global progress bar endpoint and computation."""

from pathlib import Path

import httpx
import pytest

from spec_view.core.config import Config
from spec_view.core.models import SpecFile, SpecGroup, Status, Task
from spec_view.web.server import create_app


def _write_spec(tmp_path: Path, name: str, tasks: str) -> None:
    specs = tmp_path / "specs"
    specs.mkdir(exist_ok=True)
    (specs / name).write_text(tasks)


def _make_config(tmp_path: Path) -> Config:
    return Config(spec_paths=[str(tmp_path / "specs")])


@pytest.fixture()
def _setup_specs(tmp_path):
    """Create a basic spec structure with active and archived specs."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "feature.md").write_text(
        "---\ntitle: Feature\nstatus: in-progress\n---\n"
        "# Feature\n- [x] Task 1\n- [ ] Task 2\n- [x] Task 3\n"
    )
    archive = specs / "archive"
    archive.mkdir()
    (archive / "old.md").write_text(
        "---\ntitle: Old\nstatus: done\n---\n"
        "# Old\n- [x] Done 1\n- [x] Done 2\n"
    )
    return tmp_path


@pytest.mark.asyncio
async def test_global_progress_normal(_setup_specs):
    """Progress bar shows correct percentage for active specs only."""
    tmp_path = _setup_specs
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    assert resp.status_code == 200
    html = resp.text
    # 2 of 3 active tasks done = 66%
    assert "2/3" in html
    assert "66%" in html


@pytest.mark.asyncio
async def test_global_progress_zero_tasks(tmp_path):
    """Zero tasks shows 0% without error."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "empty.md").write_text("---\ntitle: Empty\n---\n# Empty\nNo tasks here.\n")
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    assert resp.status_code == 200
    assert "0/0" in resp.text
    assert "0%" in resp.text


@pytest.mark.asyncio
async def test_global_progress_all_done(tmp_path):
    """All tasks done shows 100%."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "done.md").write_text(
        "---\ntitle: Done\nstatus: done\n---\n# Done\n- [x] A\n- [x] B\n"
    )
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    assert resp.status_code == 200
    assert "2/2" in resp.text
    assert "100%" in resp.text


@pytest.mark.asyncio
async def test_global_progress_single_task(tmp_path):
    """Single undone task shows 0%."""
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "one.md").write_text("---\ntitle: One\n---\n# One\n- [ ] Only task\n")
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    assert resp.status_code == 200
    assert "0/1" in resp.text
    assert "0%" in resp.text


@pytest.mark.asyncio
async def test_global_progress_excludes_archived(_setup_specs):
    """Archived specs are not counted in progress computation."""
    tmp_path = _setup_specs
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/partials/global-progress")
    html = resp.text
    # Only active spec has 3 tasks (2 done), archived has 2 tasks (2 done)
    # If archived were included: 4/5 = 80%
    # With only active: 2/3 = 66%
    assert "2/3" in html
    assert "66%" in html


@pytest.mark.asyncio
async def test_global_progress_bar_in_base_html(_setup_specs):
    """The global progress bar div appears on all full pages."""
    tmp_path = _setup_specs
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/", "/tasks"]:
            resp = await client.get(path)
            assert resp.status_code == 200
            assert 'class="global-progress-bar"' in resp.text
            assert 'hx-get="/partials/global-progress"' in resp.text
