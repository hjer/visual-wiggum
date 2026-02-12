"""Tests for core/history.py — git history parsing."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from spec_view.core.history import CommitEntry, get_history


def _git(cwd: Path, *args: str) -> str:
    """Run a git command in the given directory."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"
    return result.stdout


def _init_repo(tmp_path: Path) -> Path:
    """Initialise a git repo in tmp_path and return its root."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@test.com")
    _git(tmp_path, "config", "user.name", "Test")
    return tmp_path


def test_not_a_git_repo(tmp_path: Path) -> None:
    """Non-git directory returns empty list, no crash."""
    result = get_history(tmp_path)
    assert result == []


def test_empty_repo(tmp_path: Path) -> None:
    """Repo with no commits returns empty list."""
    _init_repo(tmp_path)
    result = get_history(tmp_path)
    assert result == []


def test_single_commit(tmp_path: Path) -> None:
    """Single manual commit is parsed correctly."""
    _init_repo(tmp_path)
    (tmp_path / "readme.md").write_text("# Hello")
    _git(tmp_path, "add", "readme.md")
    _git(tmp_path, "commit", "-m", "Initial commit")

    entries = get_history(tmp_path)
    assert len(entries) == 1

    e = entries[0]
    assert len(e.hash) >= 7
    assert e.message == "Initial commit"
    assert e.is_loop is False
    assert e.files_changed == 1
    assert "readme.md" in e.changed_files
    assert e.insertions >= 1
    assert e.tasks_completed == []


def test_loop_commit_detection(tmp_path: Path) -> None:
    """Commits with Co-Authored-By: Claude are detected as loop commits."""
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", "a.py")
    _git(
        tmp_path, "commit", "-m",
        "Add feature\n\nSome explanation.\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
    )

    entries = get_history(tmp_path)
    assert len(entries) == 1
    assert entries[0].is_loop is True


def test_loop_detection_case_insensitive(tmp_path: Path) -> None:
    """Loop detection works regardless of case."""
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", "a.py")
    _git(
        tmp_path, "commit", "-m",
        "Add feature\n\nco-authored-by: claude <noreply@anthropic.com>",
    )

    entries = get_history(tmp_path)
    assert entries[0].is_loop is True


def test_manual_commit_not_loop(tmp_path: Path) -> None:
    """Regular commits without the trailer are not loop commits."""
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", "a.py")
    _git(tmp_path, "commit", "-m", "Manual fix\n\nDone by hand.")

    entries = get_history(tmp_path)
    assert entries[0].is_loop is False


def test_multiple_commits_order(tmp_path: Path) -> None:
    """Multiple commits come back newest-first."""
    _init_repo(tmp_path)

    for i in range(3):
        (tmp_path / f"file{i}.txt").write_text(f"content {i}\n")
        _git(tmp_path, "add", f"file{i}.txt")
        _git(tmp_path, "commit", "-m", f"Commit {i}")

    entries = get_history(tmp_path)
    assert len(entries) == 3
    assert entries[0].message == "Commit 2"
    assert entries[1].message == "Commit 1"
    assert entries[2].message == "Commit 0"


def test_limit_parameter(tmp_path: Path) -> None:
    """The limit parameter caps the number of entries returned."""
    _init_repo(tmp_path)

    for i in range(5):
        (tmp_path / f"file{i}.txt").write_text(f"content {i}\n")
        _git(tmp_path, "add", f"file{i}.txt")
        _git(tmp_path, "commit", "-m", f"Commit {i}")

    entries = get_history(tmp_path, limit=3)
    assert len(entries) == 3
    assert entries[0].message == "Commit 4"


def test_file_stats(tmp_path: Path) -> None:
    """File change stats (insertions, deletions) are parsed correctly."""
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("line1\nline2\nline3\n")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-m", "Add file")

    # Now modify the file
    (tmp_path / "a.txt").write_text("line1\nmodified\nline3\nnew line\n")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-m", "Modify file")

    entries = get_history(tmp_path)
    modify_entry = entries[0]  # newest first
    assert modify_entry.message == "Modify file"
    assert modify_entry.files_changed == 1
    assert modify_entry.insertions >= 1
    assert modify_entry.deletions >= 1
    assert "a.txt" in modify_entry.changed_files


def test_tasks_completed_extraction(tmp_path: Path) -> None:
    """Tasks marked done in IMPLEMENTATION_PLAN.md are extracted."""
    _init_repo(tmp_path)

    # Create initial plan with unchecked tasks
    plan = "# Plan\n\n- [ ] Build the widget\n- [ ] Write tests\n"
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(plan)
    _git(tmp_path, "add", "IMPLEMENTATION_PLAN.md")
    _git(tmp_path, "commit", "-m", "Add plan")

    # Check off a task
    plan2 = "# Plan\n\n- [x] Build the widget\n- [ ] Write tests\n"
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(plan2)
    _git(tmp_path, "add", "IMPLEMENTATION_PLAN.md")
    _git(tmp_path, "commit", "-m", "Complete widget task")

    entries = get_history(tmp_path)
    latest = entries[0]
    assert latest.message == "Complete widget task"
    assert "Build the widget" in latest.tasks_completed


def test_tasks_completed_strips_markdown(tmp_path: Path) -> None:
    """Task text has markdown formatting stripped."""
    _init_repo(tmp_path)

    plan = "# Plan\n\n- [ ] **Bold task** with `code` and [link](http://example.com)\n"
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(plan)
    _git(tmp_path, "add", "IMPLEMENTATION_PLAN.md")
    _git(tmp_path, "commit", "-m", "Add plan")

    plan2 = "# Plan\n\n- [x] **Bold task** with `code` and [link](http://example.com)\n"
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text(plan2)
    _git(tmp_path, "add", "IMPLEMENTATION_PLAN.md")
    _git(tmp_path, "commit", "-m", "Done")

    entries = get_history(tmp_path)
    assert "Bold task with code and link" in entries[0].tasks_completed


def test_no_plan_changes_empty_tasks(tmp_path: Path) -> None:
    """Commits not touching IMPLEMENTATION_PLAN.md have empty tasks_completed."""
    _init_repo(tmp_path)
    (tmp_path / "other.txt").write_text("hello\n")
    _git(tmp_path, "add", "other.txt")
    _git(tmp_path, "commit", "-m", "Unrelated change")

    entries = get_history(tmp_path)
    assert entries[0].tasks_completed == []


def test_multiple_files_changed(tmp_path: Path) -> None:
    """Commits touching multiple files report correct count."""
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("a\n")
    (tmp_path / "b.txt").write_text("b\n")
    (tmp_path / "c.txt").write_text("c\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Add three files")

    entries = get_history(tmp_path)
    assert entries[0].files_changed == 3
    assert len(entries[0].changed_files) == 3


def test_commit_entry_dataclass() -> None:
    """CommitEntry can be constructed with default field values."""
    from datetime import datetime, timezone

    entry = CommitEntry(
        hash="abc1234",
        timestamp=datetime.now(timezone.utc),
        message="Test",
        body="",
        is_loop=False,
        files_changed=0,
        insertions=0,
        deletions=0,
    )
    assert entry.changed_files == []
    assert entry.tasks_completed == []
