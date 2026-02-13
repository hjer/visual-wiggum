"""Tests for TUI ProgressBarWidget._render_bar counting logic.

Verifies that the progress bar counts active + specs + plan groups,
excluding archived groups.
"""

from pathlib import Path

from spec_view.core.models import SpecFile, SpecGroup, Task
from spec_view.tui.progress_bar import ProgressBarWidget


def _group(name: str, tags: list[str], done: int, total: int) -> SpecGroup:
    """Helper to create a SpecGroup with the given tags and task counts."""
    tasks = [Task(text=f"t{i}", done=(i < done)) for i in range(total)]
    sf = SpecFile(path=Path(f"/{name}/spec.md"), tasks=tasks, tags=list(tags))
    return SpecGroup(name=name, path=Path(f"/{name}"), files={"spec": sf})


def test_render_bar_counts_active_specs_plan():
    """Progress bar counts tasks from active, specs, and plan groups."""
    groups = [
        _group("feature", [], done=1, total=2),        # active: 1/2
        _group("parsing", ["specs"], done=2, total=3),  # specs: 2/3
        _group("alpha", ["plan"], done=1, total=4),     # plan: 1/4
    ]
    bar = ProgressBarWidget._render_bar(groups)
    # Total: 4/9 = 44%
    assert "4/9" in bar
    assert "44%" in bar


def test_render_bar_excludes_archived():
    """Archived groups are excluded from task counting."""
    groups = [
        _group("active", [], done=1, total=2),                 # counted: 1/2
        _group("old", ["archive"], done=5, total=5),            # excluded
        _group("old-plan", ["plan", "archive"], done=3, total=3),  # excluded
        _group("old-spec", ["specs", "archive"], done=2, total=2),  # excluded
    ]
    bar = ProgressBarWidget._render_bar(groups)
    # Only active: 1/2 = 50%
    assert "1/2" in bar
    assert "50%" in bar
    assert "3 archived" in bar


def test_render_bar_specs_not_excluded():
    """Groups with 'specs' tag (non-archived) are counted, not excluded."""
    groups = [
        _group("my-spec", ["specs"], done=3, total=5),
    ]
    bar = ProgressBarWidget._render_bar(groups)
    assert "3/5" in bar
    assert "60%" in bar


def test_render_bar_zero_tasks():
    """Zero tasks shows 0% without error."""
    bar = ProgressBarWidget._render_bar([])
    assert "0/0" in bar
    assert "0%" in bar
