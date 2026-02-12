"""Git history parsing for loop iteration tracking."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Separator used between fields in git log format
_FIELD_SEP = "---FIELD---"
# Separator used between commits in git log output
_RECORD_SEP = "---RECORD---"


@dataclass
class CommitEntry:
    """A single git commit with parsed metadata."""

    hash: str
    timestamp: datetime
    message: str
    body: str
    is_loop: bool
    files_changed: int
    insertions: int
    deletions: int
    changed_files: list[str] = field(default_factory=list)
    tasks_completed: list[str] = field(default_factory=list)


def get_history(root: Path, limit: int = 50) -> list[CommitEntry]:
    """Parse git log from *root* and return a list of CommitEntry, newest first.

    Returns an empty list if *root* is not inside a git repository or has no
    commits.
    """
    if not _is_git_repo(root):
        return []

    raw = _git_log(root, limit)
    if not raw.strip():
        return []

    entries: list[CommitEntry] = []
    for record in raw.split(_RECORD_SEP):
        record = record.strip()
        if not record:
            continue
        entry = _parse_record(record)
        if entry is not None:
            entries.append(entry)

    # Extract tasks_completed from IMPLEMENTATION_PLAN.md diffs (batch)
    _fill_tasks_completed(root, entries)

    return entries


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_git_repo(path: Path) -> bool:
    """Return True if *path* is inside a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (OSError, subprocess.TimeoutExpired):
        return False


def _git_log(root: Path, limit: int) -> str:
    """Run ``git log`` with a custom format and ``--numstat``.

    The record separator is placed at the START of the format so that the
    numstat lines (appended by git after the format for each commit) end up
    inside the same record as their commit.
    """
    fmt = _RECORD_SEP + _FIELD_SEP.join(["%h", "%aI", "%s", "%b"])
    try:
        result = subprocess.run(
            [
                "git", "log",
                f"-{limit}",
                f"--format={fmt}",
                "--numstat",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _parse_record(record: str) -> CommitEntry | None:
    """Parse a single commit record from the git log output."""
    # The record looks like:
    #   <hash>---FIELD---<iso-ts>---FIELD---<subject>---FIELD---<body>
    #   <numstat lines...>
    #
    # The numstat lines come AFTER the format string and are separated by
    # newlines. They look like: "3\t1\tpath/to/file"
    parts = record.split(_FIELD_SEP)
    if len(parts) < 4:
        return None

    short_hash = parts[0].strip()
    iso_ts = parts[1].strip()
    subject = parts[2].strip()
    # The body part may contain numstat lines appended after it
    body_and_numstat = parts[3]

    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(iso_ts)
    except ValueError:
        return None

    # Ensure timestamp is timezone-aware (UTC if naive)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    # Split body from numstat lines.  Numstat lines match: <digits>\t<digits>\t<path>
    # or "-\t-\t<path>" for binary files.
    body_lines: list[str] = []
    numstat_lines: list[str] = []
    in_numstat = False

    for line in body_and_numstat.split("\n"):
        if not in_numstat and re.match(r"^(\d+|-)\t(\d+|-)\t", line):
            in_numstat = True
        if in_numstat:
            if re.match(r"^(\d+|-)\t(\d+|-)\t", line):
                numstat_lines.append(line)
            # else: skip blank lines in numstat section
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Parse numstat
    changed_files: list[str] = []
    total_insertions = 0
    total_deletions = 0
    for line in numstat_lines:
        m = re.match(r"^(\d+|-)\t(\d+|-)\t(.+)$", line)
        if m:
            ins_str, del_str, fpath = m.group(1), m.group(2), m.group(3)
            changed_files.append(fpath)
            if ins_str != "-":
                total_insertions += int(ins_str)
            if del_str != "-":
                total_deletions += int(del_str)

    # Detect loop commit
    is_loop = bool(re.search(r"Co-Authored-By:.*Claude", body, re.IGNORECASE))

    return CommitEntry(
        hash=short_hash,
        timestamp=timestamp,
        message=subject,
        body=body,
        is_loop=is_loop,
        files_changed=len(changed_files),
        insertions=total_insertions,
        deletions=total_deletions,
        changed_files=changed_files,
    )


def _fill_tasks_completed(root: Path, entries: list[CommitEntry]) -> None:
    """For each entry, extract tasks marked done in IMPLEMENTATION_PLAN.md."""
    for entry in entries:
        if "IMPLEMENTATION_PLAN.md" not in entry.changed_files:
            continue
        entry.tasks_completed = _extract_tasks_from_diff(root, entry.hash)


def _extract_tasks_from_diff(root: Path, commit_hash: str) -> list[str]:
    """Parse ``git show`` diff of IMPLEMENTATION_PLAN.md for newly checked tasks."""
    try:
        result = subprocess.run(
            ["git", "show", commit_hash, "--", "IMPLEMENTATION_PLAN.md"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
    except (OSError, subprocess.TimeoutExpired):
        return []

    tasks: list[str] = []
    for line in result.stdout.splitlines():
        # Match added lines with checked checkboxes: "+- [x] Some task text"
        m = re.match(r"^\+\s*-\s*\[x\]\s+(.+)", line, re.IGNORECASE)
        if m:
            task_text = m.group(1).strip()
            # Strip markdown formatting (bold, links, code)
            task_text = re.sub(r"\*\*(.+?)\*\*", r"\1", task_text)
            task_text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", task_text)
            task_text = re.sub(r"`(.+?)`", r"\1", task_text)
            # Strip trailing markers like "— DONE"
            task_text = re.sub(r"\s*—\s*DONE\s*$", "", task_text, flags=re.IGNORECASE)
            if task_text:
                tasks.append(task_text)
    return tasks
