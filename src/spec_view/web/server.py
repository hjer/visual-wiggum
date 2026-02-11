"""FastAPI web server for spec-view dashboard."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import markdown
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.config import Config
from ..core.models import SpecGroup, Status
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

    def _render_md(text: str) -> str:
        return markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "toc", "nl2br"],
        )

    def _get_groups() -> list[SpecGroup]:
        return scan_specs(root, config)

    def _dashboard_context(request: Request) -> dict:
        groups = _get_groups()
        total_tasks = sum(g.task_total for g in groups)
        done_tasks = sum(g.task_done for g in groups)
        overall_percent = int(done_tasks / total_tasks * 100) if total_tasks else 0

        status_counts: dict[str, int] = {}
        for g in groups:
            s = g.status.value
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "request": request,
            "groups": groups,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "overall_percent": overall_percent,
            "status_counts": status_counts,
        }

    def _tasks_context(request: Request) -> dict:
        groups = _get_groups()

        columns: dict[str, list[dict]] = {
            "draft": [],
            "ready": [],
            "in-progress": [],
            "done": [],
            "blocked": [],
        }

        for group in groups:
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
        for group in groups:
            all_tasks.extend(group.all_tasks)
            all_task_trees.extend(group.all_task_trees)
            all_phases.extend(group.all_phases)

        return {
            "request": request,
            "columns": columns,
            "all_tasks": all_tasks,
            "all_task_trees": all_task_trees,
            "all_phases": all_phases,
            "total": len(all_tasks),
            "done": sum(1 for t in all_tasks if t.done),
        }

    def _spec_context(request: Request, name: str) -> dict | None:
        groups = _get_groups()
        group = next((g for g in groups if g.name == name), None)
        if group is None:
            return None

        rendered: dict[str, str] = {}
        for file_type, spec_file in group.files.items():
            rendered[file_type] = _render_md(spec_file.body)

        return {
            "request": request,
            "group": group,
            "rendered": rendered,
            "phases": group.all_phases,
            "format_type": group.format_type,
            "stories": group.stories,
        }

    # --- Full page routes ---

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("dashboard.html", _dashboard_context(request))

    @app.get("/spec/{name}", response_class=HTMLResponse)
    async def spec_detail(request: Request, name: str) -> HTMLResponse:
        ctx = _spec_context(request, name)
        if ctx is None:
            return HTMLResponse("<h1>Spec not found</h1>", status_code=404)
        return templates.TemplateResponse("spec.html", ctx)

    @app.get("/tasks", response_class=HTMLResponse)
    async def task_board(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("tasks.html", _tasks_context(request))

    # --- Partial endpoints for htmx ---

    @app.get("/partials/dashboard-content", response_class=HTMLResponse)
    async def partial_dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "partials/dashboard_content.html", _dashboard_context(request)
        )

    @app.get("/partials/tasks-content", response_class=HTMLResponse)
    async def partial_tasks(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "partials/tasks_content.html", _tasks_context(request)
        )

    @app.get("/partials/spec-content/{name}", response_class=HTMLResponse)
    async def partial_spec(request: Request, name: str) -> HTMLResponse:
        ctx = _spec_context(request, name)
        if ctx is None:
            return HTMLResponse("", status_code=404)
        return templates.TemplateResponse("partials/spec_content.html", ctx)

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
