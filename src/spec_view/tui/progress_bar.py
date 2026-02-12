"""Shared progress bar widget for TUI screens."""

from __future__ import annotations

from textual.widgets import Static

from ..core.models import SpecGroup


class ProgressBarWidget(Static):
    """A 1-row progress bar showing task completion across active specs."""

    DEFAULT_CSS = """
    ProgressBarWidget {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, groups: list[SpecGroup], **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups = groups
        self.update(self._render_bar(groups))

    def update_groups(self, groups: list[SpecGroup]) -> None:
        """Update the progress bar with new groups."""
        self.groups = groups
        self.update(self._render_bar(groups))

    @staticmethod
    def _render_bar(groups: list[SpecGroup]) -> str:
        """Render the progress bar content as a Rich-formatted string."""
        active = [g for g in groups if "archive" not in g.tags]
        archived = [g for g in groups if "archive" in g.tags]

        total_tasks = sum(g.task_total for g in active)
        done_tasks = sum(g.task_done for g in active)
        percent = int(done_tasks / total_tasks * 100) if total_tasks else 0

        # Build visual bar — 20 characters wide
        bar_width = 20
        filled = round(bar_width * percent / 100)
        unfilled = bar_width - filled
        bar = f"[green]{'━' * filled}[/green]{'─' * unfilled}"

        # Spec status counts
        counts: dict[str, int] = {}
        for g in active:
            s = g.status.value
            counts[s] = counts.get(s, 0) + 1
        status_parts = ", ".join(f"{v} {k}" for k, v in counts.items())

        archive_str = f" | {len(archived)} archived" if archived else ""

        return (
            f" {bar} {percent}%  {done_tasks}/{total_tasks} tasks"
            f" | {len(active)} specs: {status_parts}{archive_str}"
        )
