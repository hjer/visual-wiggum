"""Task board view showing all tasks across specs."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from ..core.models import Phase, SpecGroup, Task


class TaskBoardScreen(Screen):
    """Screen showing all tasks grouped by status."""

    CSS = """
    TaskBoardScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr auto;
    }

    #task-content {
        padding: 1 2;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    def __init__(self, groups: list[SpecGroup]) -> None:
        super().__init__()
        self.groups = groups

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="task-content"):
            yield Static(self._build_content(), id="task-body")
        yield Footer()

    def update_groups(self, groups: list[SpecGroup]) -> None:
        """Live-update task board content."""
        self.groups = groups
        body = self.query_one("#task-body", Static)
        body.update(self._build_content())

    def _build_content(self) -> str:
        """Build the full Rich-formatted task board text."""
        active = [g for g in self.groups if "archive" not in g.tags]
        archived = [g for g in self.groups if "archive" in g.tags]

        all_flat: list[Task] = []
        for group in active:
            all_flat.extend(group.all_tasks)

        total = len(all_flat)
        done_count = sum(1 for t in all_flat if t.done)

        lines: list[str] = [
            f"[bold]Task Board[/bold]  ({done_count}/{total} complete)\n",
        ]

        # Check if any active group has phases
        all_phases: list[Phase] = []
        for group in active:
            all_phases.extend(group.all_phases)

        if all_phases:
            lines.extend(self._render_phase_board(all_phases))
        else:
            all_trees: list[Task] = []
            for group in active:
                all_trees.extend(group.all_task_trees)

            pending_trees = [t for t in all_trees if not t.done]
            done_trees = [t for t in all_trees if t.done]

            if pending_trees:
                lines.append("[yellow bold]Pending[/yellow bold]")
                lines.extend(self._render_task_tree(pending_trees, indent=1))
                lines.append("")

            if done_trees:
                lines.append("[green bold]Done[/green bold]")
                lines.extend(self._render_task_tree(done_trees, indent=1))
                lines.append("")

        if not all_flat:
            lines.append("[dim]No tasks found in any specs.[/dim]")

        if archived:
            archived_tasks: list[Task] = []
            for group in archived:
                archived_tasks.extend(group.all_tasks)
            archived_done = sum(1 for t in archived_tasks if t.done)
            lines.append("")
            lines.append(
                f"[dim bold]Archive[/dim bold]  [dim]({archived_done}/{len(archived_tasks)} complete)[/dim]"
            )
            archived_trees: list[Task] = []
            for group in archived:
                archived_trees.extend(group.all_task_trees)
            lines.extend(self._render_task_tree(archived_trees, indent=1))

        return "\n".join(lines)

    def _render_phase_board(self, phases: list[Phase]) -> list[str]:
        """Render task board grouped by phase."""
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
        meta_parts: list[str] = []
        if task.task_id:
            meta_parts.append(f"[dim]{task.task_id}[/dim]")
        if task.parallel:
            meta_parts.append("\u21c4")
        if task.story:
            meta_parts.append(f"[magenta]\\[{task.story}][/magenta]")
        meta = " ".join(meta_parts) + " " if meta_parts else ""
        spec_label = f"  [dim]({task.spec_name})[/dim]" if task.spec_name and task.depth == 0 else ""

        sub_info = ""
        if task.children:
            sub_info = f" [dim]({task.subtask_done}/{task.subtask_total})[/dim]"

        lines.append(f"{prefix}{dim_start}{icon} {meta}{text}{sub_info}{spec_label}{dim_end}")

    def _render_task_tree(self, tasks: list[Task], indent: int = 0) -> list[str]:
        """Recursively render task tree with visual indentation."""
        lines: list[str] = []
        for task in tasks:
            self._append_task_line(lines, task, indent)
            if task.children:
                lines.extend(self._render_task_tree(task.children, indent + 1))
        return lines
