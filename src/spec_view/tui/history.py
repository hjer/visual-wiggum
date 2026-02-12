"""Loop history screen showing git commit timeline."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from ..core.history import CommitEntry, get_history
from ..core.models import SpecGroup
from .progress_bar import ProgressBarWidget


def _relative_time(dt: datetime) -> str:
    """Format a datetime as a human-friendly relative time string."""
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = days // 365
    return f"{years}y ago"


class CommitListItem(ListItem):
    """A list item representing a single commit."""

    def __init__(self, entry: CommitEntry, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry = entry

    def compose(self) -> ComposeResult:
        entry = self.entry
        badge = "[cyan]\\[bot][/cyan]" if entry.is_loop else "[dim]\\[you][/dim]"
        time_str = _relative_time(entry.timestamp)
        stat = f"{entry.files_changed} files  [green]+{entry.insertions}[/green] [red]-{entry.deletions}[/red]"
        message = entry.message.replace("[", "\\[")

        lines = [
            f"{badge} [dim]{entry.hash}[/dim]  [dim]{time_str}[/dim]",
            f"  {message}",
            f"  [dim]{stat}[/dim]",
        ]

        if entry.tasks_completed:
            for task in entry.tasks_completed:
                task_text = task.replace("[", "\\[")
                lines.append(f"  [green]✓[/green] [dim]{task_text}[/dim]")

        yield Static("\n".join(lines))


class CommitDetailView(Static):
    """Shows full detail for a selected commit."""

    def show_entry(self, entry: CommitEntry) -> None:
        """Render full commit details."""
        badge = "[cyan]\\[bot][/cyan]" if entry.is_loop else "[dim]\\[you][/dim]"
        time_str = _relative_time(entry.timestamp)
        abs_time = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        lines: list[str] = [
            f"[bold]{entry.message.replace('[', chr(92) + '[')}[/bold]",
            f"{badge}  [dim]{entry.hash}[/dim]  {time_str}  [dim]({abs_time})[/dim]",
            "",
        ]

        if entry.body:
            body = entry.body.replace("[", "\\[")
            lines.append(body)
            lines.append("")

        # File stats
        stat = f"{entry.files_changed} files changed, [green]+{entry.insertions}[/green] [red]-{entry.deletions}[/red]"
        lines.append(f"[bold]Changes:[/bold]  {stat}")
        lines.append("")

        if entry.changed_files:
            for fpath in entry.changed_files:
                lines.append(f"  {fpath}")
            lines.append("")

        if entry.tasks_completed:
            lines.append("[bold]Tasks Completed:[/bold]")
            for task in entry.tasks_completed:
                task_text = task.replace("[", "\\[")
                lines.append(f"  [green]✓[/green] {task_text}")
            lines.append("")

        self.update("\n".join(lines))


class HistoryScreen(Screen):
    """Screen showing git commit history timeline."""

    CSS = """
    HistoryScreen {
        layout: vertical;
    }

    #history-area {
        layout: horizontal;
        height: 1fr;
    }

    #commit-list {
        width: 1fr;
        height: 100%;
        border-right: solid $primary;
        overflow-y: auto;
    }

    #commit-detail-scroll {
        width: 2fr;
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(
        self,
        groups: list[SpecGroup],
        root: Path,
    ) -> None:
        super().__init__()
        self.groups = groups
        self.root = root
        self._entries: list[CommitEntry] = []

    def compose(self) -> ComposeResult:
        yield Header()
        self._entries = get_history(self.root)
        with Horizontal(id="history-area"):
            lv = ListView(id="commit-list")
            yield lv
            yield CommitDetailView(
                "Select a commit to view details.",
                id="commit-detail-scroll",
            )
        yield ProgressBarWidget(self.groups, id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the commit list after mount."""
        lv = self.query_one("#commit-list", ListView)
        for entry in self._entries:
            lv.append(CommitListItem(entry))
        if not self._entries:
            lv.append(
                ListItem(Static("[dim]No git history available.[/dim]"))
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Show commit detail when an item is selected."""
        item = event.item
        if isinstance(item, CommitListItem):
            detail = self.query_one("#commit-detail-scroll", CommitDetailView)
            detail.show_entry(item.entry)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update detail pane when highlight changes."""
        item = event.item
        if isinstance(item, CommitListItem):
            detail = self.query_one("#commit-detail-scroll", CommitDetailView)
            detail.show_entry(item.entry)

    def action_cursor_down(self) -> None:
        lv = self.query_one("#commit-list", ListView)
        lv.action_cursor_down()

    def action_cursor_up(self) -> None:
        lv = self.query_one("#commit-list", ListView)
        lv.action_cursor_up()

    def update_groups(self, groups: list[SpecGroup]) -> None:
        """Live-update: re-read history and refresh progress bar."""
        self.groups = groups
        self._entries = get_history(self.root)
        lv = self.query_one("#commit-list", ListView)
        lv.clear()
        for entry in self._entries:
            lv.append(CommitListItem(entry))
        if not self._entries:
            lv.append(
                ListItem(Static("[dim]No git history available.[/dim]"))
            )
        status_bar = self.query_one("#status-bar", ProgressBarWidget)
        status_bar.update_groups(groups)
