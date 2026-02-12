"""Tests for the web history page and partial endpoint."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from spec_view.core.config import Config
from spec_view.core.history import CommitEntry
from spec_view.web.server import create_app


def _make_config(tmp_path: Path) -> Config:
    return Config(spec_paths=[str(tmp_path / "specs")])


def _make_entries() -> list[CommitEntry]:
    return [
        CommitEntry(
            hash="abc1234",
            timestamp=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            message="Add global progress bar to web UI with SSE live updates",
            body="Implemented progress bar.\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
            is_loop=True,
            files_changed=5,
            insertions=120,
            deletions=15,
            changed_files=[
                "src/spec_view/web/server.py",
                "src/spec_view/web/templates/base.html",
                "src/spec_view/web/static/style.css",
                "src/spec_view/web/templates/partials/global_progress.html",
                "tests/test_web_progress.py",
            ],
            tasks_completed=[
                "Add GET /partials/global-progress route",
                "Create partials/global_progress.html template",
            ],
        ),
        CommitEntry(
            hash="def5678",
            timestamp=datetime(2025, 5, 30, 10, 0, 0, tzinfo=timezone.utc),
            message="Fix typo in README",
            body="",
            is_loop=False,
            files_changed=1,
            insertions=1,
            deletions=1,
            changed_files=["README.md"],
            tasks_completed=[],
        ),
    ]


@pytest.fixture()
def _setup(tmp_path):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "test.md").write_text(
        "---\ntitle: Test\nstatus: ready\n---\n# Test\n- [ ] A task\n"
    )
    return tmp_path


@pytest.mark.asyncio
async def test_history_page_renders(_setup):
    """GET /history returns the full history page with entries."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/history")
    assert resp.status_code == 200
    html = resp.text
    assert "Loop History" in html
    assert "abc1234" in html
    assert "def5678" in html
    assert "Add global progress bar" in html
    assert "Fix typo in README" in html


@pytest.mark.asyncio
async def test_history_partial_renders(_setup):
    """GET /partials/history-content returns the partial with htmx attributes."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/partials/history-content")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="history-content"' in html
    assert 'hx-get="/partials/history-content"' in html
    assert 'hx-trigger="specchange from:body"' in html


@pytest.mark.asyncio
async def test_history_shows_loop_badges(_setup):
    """Loop commits show loop badge, manual commits show manual badge."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/partials/history-content")
    html = resp.text
    assert "badge-loop" in html
    assert "badge-manual" in html


@pytest.mark.asyncio
async def test_history_shows_tasks_completed(_setup):
    """Tasks completed in a commit are displayed."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/partials/history-content")
    html = resp.text
    assert "Add GET /partials/global-progress route" in html
    assert "Create partials/global_progress.html template" in html


@pytest.mark.asyncio
async def test_history_shows_file_stats(_setup):
    """File change counts and line stats are shown."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/partials/history-content")
    html = resp.text
    assert "5 files" in html
    assert "+120" in html
    assert "-15" in html
    assert "1 file" in html


@pytest.mark.asyncio
async def test_history_empty_state(_setup):
    """Empty history shows a friendly message."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=[]):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/history")
    assert resp.status_code == 200
    assert "No git history available" in resp.text


@pytest.mark.asyncio
async def test_history_summary_counts(_setup):
    """Summary pills show correct commit, loop, and manual counts."""
    tmp_path = _setup
    entries = _make_entries()
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    with patch("spec_view.web.server.get_history", return_value=entries):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/partials/history-content")
    html = resp.text
    assert "2 commits" in html
    assert "1 loop" in html
    assert "1 manual" in html


@pytest.mark.asyncio
async def test_history_nav_link_in_base(_setup):
    """The History nav link appears on all pages."""
    tmp_path = _setup
    app = create_app(tmp_path, _make_config(tmp_path))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/", "/tasks"]:
            resp = await client.get(path)
            assert resp.status_code == 200
            assert 'href="/history"' in resp.text
            assert ">History<" in resp.text
