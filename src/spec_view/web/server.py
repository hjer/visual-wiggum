"""FastAPI web server for spec-view dashboard."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import markdown
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.config import Config
from ..core.history import get_history
from ..core.models import SpecGroup
from ..core.scanner import scan_specs
from ..core.watcher import SpecChangeNotifier, start_watcher_thread

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_app(root: Path, config: Config) -> FastAPI:
    notifier = SpecChangeNotifier()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        loop = asyncio.get_running_loop()
        start_watcher_thread(root, config, notifier, loop)
        yield

    app = FastAPI(title="spec-view", lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

    def _timeago(dt: datetime) -> str:
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

    templates.env.filters["timeago"] = _timeago

    def _render_md(text: str) -> str:
        return markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "toc", "nl2br"],
        )

    def _get_groups() -> list[SpecGroup]:
        return scan_specs(root, config)

    def _partition_groups(
        groups: list[SpecGroup],
    ) -> tuple[list[SpecGroup], list[SpecGroup], list[SpecGroup], list[SpecGroup]]:
        active = [
            g for g in groups
            if "archive" not in g.tags and "plan" not in g.tags and "specs" not in g.tags
        ]
        specs = [g for g in groups if "specs" in g.tags and "archive" not in g.tags]
        plan = [g for g in groups if "plan" in g.tags and "archive" not in g.tags]
        archived = [g for g in groups if "archive" in g.tags]
        return active, specs, plan, archived

    def _dashboard_context() -> dict:
        groups = _get_groups()
        active, specs, plan, archived = _partition_groups(groups)
        all_counted = active + specs + plan
        total_tasks = sum(g.task_total for g in all_counted)
        done_tasks = sum(g.task_done for g in all_counted)
        overall_percent = int(done_tasks / total_tasks * 100) if total_tasks else 0

        status_counts: dict[str, int] = {}
        for g in active:
            s = g.status.value
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "groups": active,
            "specs_groups": specs,
            "plan_groups": plan,
            "archived_groups": archived,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "overall_percent": overall_percent,
            "status_counts": status_counts,
        }

    def _tasks_context() -> dict:
        groups = _get_groups()
        active, specs, plan, archived = _partition_groups(groups)

        columns: dict[str, list[dict]] = {
            "draft": [],
            "ready": [],
            "in-progress": [],
            "done": [],
            "blocked": [],
        }

        for group in active:
            col = group.status.value
            if col in columns:
                columns[col].append(
                    {
                        "name": group.name,
                        "title": group.title,
                        "status": group.status.value,
                        "priority": group.priority.value,
                        "task_done": group.task_done,
                        "task_total": group.task_total,
                        "task_percent": group.task_percent,
                        "tags": group.tags,
                    }
                )

        all_tasks = []
        all_task_trees = []
        all_phases = []
        for group in active:
            all_tasks.extend(group.all_tasks)
            all_task_trees.extend(group.all_task_trees)
            all_phases.extend(group.all_phases)

        specs_tasks = []
        specs_task_trees = []
        specs_phases = []
        for group in specs:
            specs_tasks.extend(group.all_tasks)
            specs_task_trees.extend(group.all_task_trees)
            specs_phases.extend(group.all_phases)

        plan_tasks = []
        plan_task_trees = []
        plan_groups_data = []
        for group in plan:
            plan_tasks.extend(group.all_tasks)
            plan_task_trees.extend(group.all_task_trees)
            plan_groups_data.append(group)

        archived_tasks = []
        archived_task_trees = []
        for group in archived:
            archived_tasks.extend(group.all_tasks)
            archived_task_trees.extend(group.all_task_trees)

        archived_plan = [g for g in archived if "plan" in g.tags]
        archived_specs = [g for g in archived if "specs" in g.tags]
        archived_other = [
            g for g in archived if "plan" not in g.tags and "specs" not in g.tags
        ]

        combined_tasks = all_tasks + specs_tasks + plan_tasks
        return {
            "columns": columns,
            "all_tasks": all_tasks,
            "all_task_trees": all_task_trees,
            "all_phases": all_phases,
            "specs_groups": specs,
            "specs_tasks": specs_tasks,
            "specs_task_trees": specs_task_trees,
            "specs_phases": specs_phases,
            "plan_groups": plan,
            "plan_tasks": plan_tasks,
            "plan_task_trees": plan_task_trees,
            "total": len(combined_tasks),
            "done": sum(1 for t in combined_tasks if t.done),
            "archived_tasks": archived_tasks,
            "archived_task_trees": archived_task_trees,
            "archived_plan_groups": archived_plan,
            "archived_spec_groups": archived_specs,
            "archived_other_groups": archived_other,
        }

    def _spec_context(name: str) -> dict | None:
        groups = _get_groups()
        group = next((g for g in groups if g.name == name), None)
        if group is None:
            return None

        rendered: dict[str, str] = {}
        for file_type, spec_file in group.files.items():
            rendered[file_type] = _render_md(spec_file.body)

        return {
            "group": group,
            "rendered": rendered,
            "phases": group.all_phases,
            "format_type": group.format_type,
            "stories": group.stories,
        }

    def _history_context() -> dict:
        entries = get_history(root)
        loop_count = sum(1 for e in entries if e.is_loop)
        manual_count = sum(1 for e in entries if not e.is_loop)
        return {
            "entries": entries,
            "total": len(entries),
            "loop_count": loop_count,
            "manual_count": manual_count,
        }

    # --- Full page routes ---

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "dashboard.html", context=_dashboard_context())

    @app.get("/spec/{name}", response_class=HTMLResponse)
    async def spec_detail(request: Request, name: str) -> HTMLResponse:
        ctx = _spec_context(name)
        if ctx is None:
            return HTMLResponse("<h1>Spec not found</h1>", status_code=404)
        return templates.TemplateResponse(request, "spec.html", context=ctx)

    @app.get("/tasks", response_class=HTMLResponse)
    async def task_board(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "tasks.html", context=_tasks_context())

    @app.get("/history", response_class=HTMLResponse)
    async def history(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "history.html", context=_history_context())

    # --- Partial endpoints for htmx ---

    @app.get("/partials/dashboard-content", response_class=HTMLResponse)
    async def partial_dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "partials/dashboard_content.html", context=_dashboard_context()
        )

    @app.get("/partials/tasks-content", response_class=HTMLResponse)
    async def partial_tasks(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "partials/tasks_content.html", context=_tasks_context()
        )

    @app.get("/partials/history-content", response_class=HTMLResponse)
    async def partial_history(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "partials/history_content.html", context=_history_context()
        )

    @app.get("/partials/spec-content/{name}", response_class=HTMLResponse)
    async def partial_spec(request: Request, name: str) -> HTMLResponse:
        ctx = _spec_context(name)
        if ctx is None:
            return HTMLResponse("", status_code=404)
        return templates.TemplateResponse(request, "partials/spec_content.html", context=ctx)

    @app.get("/partials/global-progress", response_class=HTMLResponse)
    async def partial_global_progress(request: Request) -> HTMLResponse:
        groups = _get_groups()
        active, specs, plan, _archived = _partition_groups(groups)
        all_counted = active + specs + plan
        total = sum(g.task_total for g in all_counted)
        done = sum(g.task_done for g in all_counted)
        percent = int(done / total * 100) if total else 0
        return templates.TemplateResponse(
            request,
            "partials/global_progress.html",
            context={"done": done, "total": total, "percent": percent},
        )

    # --- SSE endpoint ---

    @app.get("/events")
    async def events() -> StreamingResponse:
        queue = notifier.subscribe()

        async def event_stream() -> AsyncGenerator[str, None]:
            try:
                while True:
                    await queue.get()
                    # Debounce: wait briefly and drain extra notifications
                    await asyncio.sleep(0.3)
                    while not queue.empty():
                        queue.get_nowait()
                    yield "event: specchange\ndata: update\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                notifier.unsubscribe(queue)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app
