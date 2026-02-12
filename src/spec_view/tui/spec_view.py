"""Spec detail view widget."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Static

from ..core.models import Phase, SpecGroup, Status, Task

STATUS_COLORS = {
    Status.DRAFT: "dim",
    Status.READY: "blue",
    Status.IN_PROGRESS: "yellow",
    Status.DONE: "green",
    Status.BLOCKED: "red",
}


class SpecDetailView(VerticalScroll, can_focus=True):
    """Shows detail for a selected spec group."""

    DEFAULT_CSS = """
    SpecDetailView {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("down", "scroll_down", "j/↓ Scroll", show=True),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "k/↑ Scroll", show=True),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("left", "focus_tree", "h/← Back", show=True),
        Binding("h", "focus_tree", "Back", show=False),
    ]

    def action_focus_tree(self) -> None:
        self.screen.query_one("#spec-tree").focus()

    def compose(self):
        yield Static("Select a spec from the tree to view details.", id="detail-body")

    def show_group(self, group: SpecGroup) -> None:
        color = STATUS_COLORS.get(group.status, "")
        lines: list[str] = []
        lines.append(f"[bold]{group.title}[/bold]")
        status_line = f"[{color}]Status: {group.status.value}[/{color}]  |  Priority: {group.priority.value}"
        if group.format_type != "generic":
            status_line += f"  |  [dim]\\[{group.format_type}][/dim]"
        lines.append(status_line)
        if group.tags:
            lines.append(f"Tags: {', '.join(group.tags)}")
        if group.task_total > 0:
            lines.append(f"Tasks: {group.task_done}/{group.task_total} ({group.task_percent}%)")
            lines.append("")
            if group.all_phases:
                lines.extend(self._render_phases(group.all_phases))
            else:
                task_trees = group.all_task_trees
                if task_trees:
                    lines.extend(self._render_task_tree(task_trees))
        lines.append("")

        for file_type, spec_file in group.files.items():
            lines.append(f"[bold underline]{file_type.upper()}[/bold underline]")
            lines.append("")
            body = spec_file.body.strip()
            body = body.replace("[", "\\[")
            lines.append(body)
            lines.append("")

        self.query_one("#detail-body", Static).update("\n".join(lines))
        self.scroll_home(animate=False)

    def _render_phases(self, phases: list[Phase]) -> list[str]:
        """Render phase-structured view."""
        lines: list[str] = []
        for phase in phases:
            done_mark = " [green]\u2713[/green]" if phase.task_done == phase.task_total and phase.task_total > 0 else ""
            lines.append(
                f"[bold]Phase {phase.number}: {phase.title}{done_mark}[/bold]"
                f" ({phase.task_done}/{phase.task_total})"
            )
            for task in phase.tasks:
                self._append_task_line(lines, task, indent=1)
            if phase.checkpoint:
                cp = phase.checkpoint.replace("[", "\\[")
                lines.append(f"  [dim]\u23f8 Checkpoint: {cp}[/dim]")
            lines.append("")
        return lines

    def _format_task_prefix(self, task: Task) -> str:
        """Build the task ID + parallel + story prefix."""
        parts: list[str] = []
        if task.task_id:
            parts.append(f"[dim]{task.task_id}[/dim]")
        if task.parallel:
            parts.append("\u21c4")
        if task.story:
            parts.append(f"[magenta]\\[{task.story}][/magenta]")
        return " ".join(parts) + " " if parts else ""

    def _append_task_line(self, lines: list[str], task: Task, indent: int = 0) -> None:
        """Append a single task line with metadata."""
        prefix = "  " * indent
        if task.done:
            icon = "[green]\u2713[/green]"
            dim_start, dim_end = "[dim]", "[/dim]"
        else:
            icon = "\u25cb"
            dim_start, dim_end = "", ""

        text = task.text.replace("[", "\\[")
        meta = self._format_task_prefix(task)
        sub_info = ""
        if task.children:
            sub_info = f" [dim]({task.subtask_done}/{task.subtask_total})[/dim]"

        lines.append(f"{prefix}{dim_start}{icon} {meta}{text}{sub_info}{dim_end}")

    def _render_task_tree(self, tasks: list[Task], indent: int = 0) -> list[str]:
        """Recursively render a task tree with status icons."""
        lines: list[str] = []
        for task in tasks:
            self._append_task_line(lines, task, indent)
            if task.children:
                lines.extend(self._render_task_tree(task.children, indent + 1))
        return lines
