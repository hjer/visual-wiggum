"""File watching for live reload."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Callable

from watchfiles import watch

from .config import Config


def _collect_watch_paths(root: Path, config: Config) -> list[Path]:
    """Build the list of paths to watch from spec_paths and include patterns."""
    seen: set[Path] = set()
    paths: list[Path] = []

    for spec_path_str in config.spec_paths:
        spec_dir = root / spec_path_str
        if spec_dir.is_dir():
            resolved = spec_dir.resolve()
            if resolved not in seen:
                paths.append(spec_dir)
                seen.add(resolved)

    for pattern in config.include:
        for match in root.glob(pattern):
            parent = match.parent if match.is_file() else match
            resolved = parent.resolve()
            if resolved not in seen:
                paths.append(parent)
                seen.add(resolved)

    if not paths:
        paths.append(root)

    return paths


def watch_specs(
    root: Path,
    config: Config,
    on_change: Callable[[], None],
) -> None:
    """Watch spec directories for changes and call on_change."""
    watch_paths = _collect_watch_paths(root, config)

    for _changes in watch(
        *watch_paths,
        watch_filter=lambda _, path: path.endswith(".md") or path.endswith(".yaml"),
    ):
        on_change()


class SpecChangeNotifier:
    """Pub/sub notifier for spec file changes (used by SSE)."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[bool]] = []

    def subscribe(self) -> asyncio.Queue[bool]:
        q: asyncio.Queue[bool] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[bool]) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    def notify(self) -> None:
        for q in self._subscribers:
            q.put_nowait(True)


def start_watcher_thread(
    root: Path,
    config: Config,
    notifier: SpecChangeNotifier,
    loop: asyncio.AbstractEventLoop,
) -> threading.Thread:
    """Start a background thread that watches for file changes and notifies via the event loop."""
    watch_paths = _collect_watch_paths(root, config)

    def _watch() -> None:
        for _changes in watch(
            *watch_paths,
            watch_filter=lambda _, path: path.endswith(".md") or path.endswith(".yaml"),
        ):
            loop.call_soon_threadsafe(notifier.notify)

    thread = threading.Thread(target=_watch, daemon=True)
    thread.start()
    return thread
