"""Textual TUI application."""

from __future__ import annotations

import threading
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding

from ..core.config import Config
from ..core.models import SpecGroup
from ..core.scanner import scan_specs
from .dashboard import DashboardScreen
from .task_board import TaskBoardScreen


class SpecViewApp(App):
    """The spec-view TUI application."""

    TITLE = "spec-view"
    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "switch_dashboard", "Dashboard", show=True),
        Binding("t", "switch_tasks", "Tasks", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(
        self,
        root: Path,
        config: Config,
    ) -> None:
        super().__init__()
        self.root = root
        self.config = config
        self.spec_groups: list[SpecGroup] = scan_specs(root, config)

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.spec_groups, self.root))
        self._start_watcher()

    def _start_watcher(self) -> None:
        from ..core.watcher import watch_specs

        def on_change() -> None:
            new_groups = scan_specs(self.root, self.config)
            self.call_from_thread(self._update_groups, new_groups)

        thread = threading.Thread(
            target=watch_specs,
            args=(self.root, self.config, on_change),
            daemon=True,
        )
        thread.start()

    def _update_groups(self, groups: list[SpecGroup]) -> None:
        """Push updated groups to the current screen."""
        self.spec_groups = groups
        screen = self.screen
        if hasattr(screen, "update_groups"):
            screen.update_groups(groups)

    def action_switch_dashboard(self) -> None:
        self.pop_screen()
        self.push_screen(DashboardScreen(self.spec_groups, self.root))

    def action_switch_tasks(self) -> None:
        self.pop_screen()
        self.push_screen(TaskBoardScreen(self.spec_groups))

    def action_refresh(self) -> None:
        new_groups = scan_specs(self.root, self.config)
        self._update_groups(new_groups)


def run_app(root: Path, config: Config) -> None:
    """Run the TUI app."""
    app = SpecViewApp(root, config)
    app.run()
