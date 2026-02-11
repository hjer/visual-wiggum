"""Main dashboard screen for the TUI."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Tree
from textual.widgets.tree import TreeNode

from ..core.models import SpecGroup, Status
from .spec_view import SpecDetailView


STATUS_ICONS = {
    Status.DRAFT: "[dim]\u25cb[/dim]",
    Status.READY: "[blue]\u25cf[/blue]",
    Status.IN_PROGRESS: "[yellow]\u25d4[/yellow]",
    Status.DONE: "[green]\u2713[/green]",
    Status.BLOCKED: "[red]\u2717[/red]",
}


class SpecTree(Tree[SpecGroup]):
    """Tree widget showing spec groups."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]


class DashboardScreen(Screen):
    """Main dashboard with spec tree and detail view."""

    CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr auto;
    }

    #main-area {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
    }

    #spec-tree {
        width: 100%;
        height: 100%;
        border-right: solid $primary;
        padding: 0 1;
    }

    #detail-pane {
        width: 100%;
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("slash", "focus_search", "Search", show=False),
    ]

    def __init__(
        self,
        groups: list[SpecGroup],
        root: Path,
    ) -> None:
        super().__init__()
        self.groups = groups
        self.root = root
        self._selected_group_name: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-area"):
            tree: SpecTree = SpecTree("Specs", id="spec-tree")
            tree.show_root = False
            self._populate_tree(tree)
            yield tree
            yield SpecDetailView(id="detail-pane")
        yield Static(self._status_summary(), id="status-bar")
        yield Footer()

    def _populate_tree(self, tree: SpecTree) -> None:
        """Add spec group nodes to the tree."""
        for group in self.groups:
            icon = STATUS_ICONS.get(group.status, "")
            task_info = f" ({group.task_done}/{group.task_total})" if group.task_total > 0 else ""
            fmt_badge = f" [dim]\\[{group.format_type}][/dim]" if group.format_type != "generic" else ""
            label = f"{icon} {group.title}{task_info}{fmt_badge}"
            node = tree.root.add(label, data=group)
            # Show phase sub-nodes when available
            phases = group.all_phases
            if phases:
                for phase in phases:
                    done_mark = " \u2713" if phase.task_done == phase.task_total and phase.task_total > 0 else ""
                    phase_info = f" ({phase.task_done}/{phase.task_total})" if phase.task_total > 0 else ""
                    node.add_leaf(
                        f"  Phase {phase.number}: {phase.title}{done_mark}{phase_info}",
                        data=group,
                    )
            else:
                for file_type, spec_file in group.files.items():
                    node.add_leaf(f"  {file_type}: {spec_file.title}", data=group)
        if not self.groups:
            tree.root.add_leaf("[dim]No specs found. Run spec-view init[/dim]")
        tree.root.expand_all()

    def on_tree_node_selected(self, event: Tree.NodeSelected[SpecGroup]) -> None:
        if event.node.data is None:
            return
        group = event.node.data
        self._selected_group_name = group.name
        detail = self.query_one("#detail-pane", SpecDetailView)
        detail.show_group(group)

    def update_groups(self, groups: list[SpecGroup]) -> None:
        """Live-update tree and status bar without replacing the screen."""
        self.groups = groups
        self._rebuild_tree()
        self._update_status_bar()
        self._refresh_detail()

    def _rebuild_tree(self) -> None:
        tree = self.query_one("#spec-tree", SpecTree)
        cursor_line = tree.cursor_line
        tree.clear()
        self._populate_tree(tree)
        try:
            tree.cursor_line = min(cursor_line, len(list(tree.root.children)) - 1)
        except Exception:
            pass

    def _update_status_bar(self) -> None:
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(self._status_summary())

    def _refresh_detail(self) -> None:
        """Re-render the detail pane if a group is selected."""
        if not self._selected_group_name:
            return
        detail = self.query_one("#detail-pane", SpecDetailView)
        for group in self.groups:
            if group.name == self._selected_group_name:
                detail.show_group(group)
                return

    def _status_summary(self) -> str:
        counts: dict[str, int] = {}
        for g in self.groups:
            s = g.status.value
            counts[s] = counts.get(s, 0) + 1
        total = len(self.groups)
        parts = [f"{v} {k}" for k, v in counts.items()]
        total_tasks = sum(g.task_total for g in self.groups)
        done_tasks = sum(g.task_done for g in self.groups)
        task_str = f" | Tasks: {done_tasks}/{total_tasks}" if total_tasks else ""
        return f" {total} specs: {', '.join(parts)}{task_str}"
