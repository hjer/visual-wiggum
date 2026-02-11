"""CLI entry point for spec-view."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .core.config import Config, load_config, save_config
from .core.detector import detect_spec_sources
from .core.models import Status
from .core.scanner import scan_specs

console = Console()

EXAMPLE_SPEC = """\
---
title: Example Feature
status: draft
priority: medium
tags: [example]
---

## Overview
Describe this feature or component.

## Requirements
- [ ] First requirement
- [ ] Second requirement
- [ ] Third requirement

## Acceptance Criteria
- Define what "done" looks like
"""

EXAMPLE_DESIGN = """\
---
title: Example Feature - Design
status: draft
---

## Architecture
Describe the technical approach.

## Components
- Component A: description
- Component B: description

## API
Describe any API changes.
"""

EXAMPLE_TASKS = """\
---
title: Example Feature - Tasks
status: draft
priority: medium
---

## Tasks
- [ ] Set up project structure
- [ ] Implement core logic
- [ ] Write tests
- [ ] Update documentation
"""


def _resolve_config(root: Path, quiet: bool = False) -> Config:
    """Load config, printing auto-detection info if applicable."""
    config = load_config(root)

    if config.auto_detected and not quiet:
        console.print("[dim]Auto-detected spec locations:[/dim]")
        for p in config.spec_paths:
            console.print(f"  [cyan]{p}[/cyan]")
        console.print(
            "[dim]Run 'spec-view config --save' to save this, "
            "or create .spec-view/config.yaml manually.[/dim]\n"
        )

    return config


def _prompt_for_paths(root: Path) -> Config | None:
    """Interactive prompt when no specs are found anywhere."""
    console.print("[yellow]No spec files found in this project.[/yellow]\n")

    detected = detect_spec_sources(root)
    if detected:
        # This shouldn't happen (auto-detect would have caught it),
        # but handle it gracefully
        spec_paths = [d.path for d in detected]
        return Config(spec_paths=spec_paths, auto_detected=True)

    console.print("Would you like to:")
    console.print("  [cyan]1[/cyan] Create a specs/ directory with examples (spec-view init)")
    console.print("  [cyan]2[/cyan] Specify a custom path to your spec files")
    console.print("  [cyan]3[/cyan] Exit")
    console.print()

    choice = click.prompt("Choose", type=click.IntRange(1, 3), default=1)

    if choice == 1:
        _do_init(root)
        return load_config(root)
    elif choice == 2:
        custom_path = click.prompt(
            "Path to spec files (relative to project root)",
            type=str,
        )
        # Validate the path exists
        full_path = root / custom_path
        if not full_path.is_dir():
            console.print(f"[red]Directory not found: {full_path}[/red]")
            return None
        config = Config(spec_paths=[custom_path])
        # Offer to save
        if click.confirm("Save this to .spec-view/config.yaml?", default=True):
            saved = save_config(root, config)
            console.print(f"[green]Saved config to {saved}[/green]")
        return config
    else:
        return None


def _do_init(root: Path) -> None:
    """Create specs/ directory with example files."""
    specs_dir = root / "specs" / "example-feature"
    specs_dir.mkdir(parents=True, exist_ok=True)

    for name, content in [
        ("spec.md", EXAMPLE_SPEC),
        ("design.md", EXAMPLE_DESIGN),
        ("tasks.md", EXAMPLE_TASKS),
    ]:
        f = specs_dir / name
        if not f.exists():
            f.write_text(content)

    overview_file = root / "specs" / "overview.md"
    if not overview_file.exists():
        overview_file.write_text(
            "---\ntitle: Project Specs\nstatus: draft\n---\n\n"
            "# Project Specs\n\nOverview of project specifications.\n"
        )

    console.print(f"[green]Created spec files in {specs_dir}[/green]")


@click.group(invoke_without_command=True)
@click.option("--root", type=click.Path(exists=True, path_type=Path), default=".")
@click.pass_context
def cli(ctx: click.Context, root: Path) -> None:
    """spec-view: Universal spec-driven development dashboard."""
    ctx.ensure_object(dict)
    ctx.obj["root"] = root.resolve()
    if ctx.invoked_subcommand is None:
        # Default: launch TUI
        root_path = root.resolve()
        config = _resolve_config(root_path)
        groups = scan_specs(root_path, config)

        if not groups:
            config = _prompt_for_paths(root_path)
            if config is None:
                return
            groups = scan_specs(root_path, config)
            if not groups:
                console.print("[yellow]Still no specs found.[/yellow]")
                return

        from .tui.app import run_app

        run_app(root_path, config)  # always watches by default


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Create specs/ directory with example spec."""
    _do_init(ctx.obj["root"])


@cli.command(name="list")
@click.option(
    "--status",
    "filter_status",
    type=click.Choice(["draft", "ready", "in-progress", "done", "blocked"]),
    default=None,
    help="Filter by status",
)
@click.pass_context
def list_specs(ctx: click.Context, filter_status: str | None) -> None:
    """List all specs with status summary."""
    root = ctx.obj["root"]
    config = _resolve_config(root)
    groups = scan_specs(root, config)

    if not groups:
        config = _prompt_for_paths(root)
        if config is None:
            return
        groups = scan_specs(root, config)
        if not groups:
            console.print("[yellow]No specs found.[/yellow]")
            return

    _print_spec_table(groups, filter_status)


@cli.command()
@click.option("--port", default=None, type=int, help="Port to serve on")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
@click.pass_context
def serve(ctx: click.Context, port: int | None, no_open: bool) -> None:
    """Start web dashboard."""
    root = ctx.obj["root"]
    config = _resolve_config(root)
    groups = scan_specs(root, config)

    if not groups:
        config = _prompt_for_paths(root)
        if config is None:
            return

    serve_port = port or config.serve.port

    from .web.server import create_app

    import uvicorn

    app = create_app(root, config)

    if config.serve.open_browser and not no_open:
        import threading
        import webbrowser

        def open_browser() -> None:
            import time

            time.sleep(1)
            webbrowser.open(f"http://localhost:{serve_port}")

        threading.Thread(target=open_browser, daemon=True).start()

    console.print(f"[green]Serving at http://localhost:{serve_port}[/green]")
    uvicorn.run(app, host="0.0.0.0", port=serve_port, log_level="warning")


@cli.command()
@click.pass_context
def watch(ctx: click.Context) -> None:
    """Launch TUI with live file watching."""
    root = ctx.obj["root"]
    config = _resolve_config(root)

    from .tui.app import run_app

    run_app(root, config)


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Check specs for format issues."""
    root = ctx.obj["root"]
    config = _resolve_config(root)
    groups = scan_specs(root, config)
    issues: list[str] = []

    if not groups:
        console.print("[yellow]No specs found.[/yellow]")
        return

    for group in groups:
        for file_type, spec_file in group.files.items():
            path = spec_file.path
            if not spec_file.title or spec_file.title == path.stem.replace("-", " ").replace("_", " ").title():
                issues.append(f"  {path}: missing explicit title")
            if spec_file.status == Status.DRAFT and "status:" not in spec_file.content:
                issues.append(f"  {path}: no status in frontmatter (defaulting to draft)")
            if not spec_file.body.strip():
                issues.append(f"  {path}: empty body content")

    if issues:
        console.print(f"[yellow]Found {len(issues)} issue(s):[/yellow]")
        for issue in issues:
            console.print(issue)
    else:
        console.print(f"[green]All {len(groups)} spec group(s) look good![/green]")


@cli.command()
@click.option("--save", is_flag=True, help="Save detected config to .spec-view/config.yaml")
@click.pass_context
def config(ctx: click.Context, save: bool) -> None:
    """Show or save current configuration."""
    root = ctx.obj["root"]
    cfg = load_config(root)

    console.print("[bold]Current config:[/bold]")
    console.print(f"  spec_paths: {cfg.spec_paths}")
    console.print(f"  include: {cfg.include}")
    console.print(f"  exclude: {cfg.exclude}")
    console.print(f"  auto_detected: {cfg.auto_detected}")

    if save:
        saved = save_config(root, cfg)
        console.print(f"\n[green]Saved to {saved}[/green]")
    elif cfg.auto_detected:
        console.print(
            "\n[dim]Run 'spec-view config --save' to persist this config.[/dim]"
        )


@cli.command()
@click.pass_context
def detect(ctx: click.Context) -> None:
    """Show all detected spec locations in this project."""
    root = ctx.obj["root"]
    detected = detect_spec_sources(root)

    if not detected:
        console.print("[yellow]No spec files detected in this project.[/yellow]")
        return

    table = Table(title="Detected Spec Sources")
    table.add_column("Path", style="cyan")
    table.add_column("Source")
    table.add_column("Files", justify="right")
    table.add_column("Description")

    for d in detected:
        table.add_row(d.path, d.source, str(d.md_count), d.description)

    console.print(table)


def _print_spec_table(
    groups: list, filter_status: str | None = None
) -> None:
    """Print a Rich table of spec groups."""
    table = Table(title="Specs")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Priority")
    table.add_column("Tasks", justify="right")
    table.add_column("Files")
    table.add_column("Tags")

    status_styles = {
        Status.DRAFT: "dim",
        Status.READY: "blue",
        Status.IN_PROGRESS: "yellow",
        Status.DONE: "green",
        Status.BLOCKED: "red",
    }

    for group in groups:
        if filter_status and group.status.value != filter_status:
            continue

        status = group.status
        style = status_styles.get(status, "")
        task_str = (
            f"{group.task_done}/{group.task_total}"
            if group.task_total > 0
            else "-"
        )
        files_str = ", ".join(sorted(group.files.keys()))

        table.add_row(
            group.title,
            f"[{style}]{status.value}[/{style}]",
            group.priority.value,
            task_str,
            files_str,
            ", ".join(group.tags) if group.tags else "-",
        )

    console.print(table)

    total = len(groups)
    by_status: dict[str, int] = {}
    for g in groups:
        by_status[g.status.value] = by_status.get(g.status.value, 0) + 1
    parts = [f"{count} {status}" for status, count in by_status.items()]
    console.print(f"\n[dim]{total} specs: {', '.join(parts)}[/dim]")
