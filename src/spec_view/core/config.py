"""Configuration loading for spec-view."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .detector import DetectedSource, detect_spec_sources


@dataclass
class ServeConfig:
    port: int = 8080
    open_browser: bool = True


@dataclass
class Config:
    spec_paths: list[str] = field(default_factory=lambda: ["specs/"])
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(
        default_factory=lambda: ["**/node_modules/**", "**/.git/**"]
    )
    serve: ServeConfig = field(default_factory=ServeConfig)
    statuses: list[str] = field(
        default_factory=lambda: ["draft", "ready", "in-progress", "done", "blocked"]
    )
    auto_detected: bool = False  # True if paths were auto-detected


def load_config(project_root: Path) -> Config:
    """Load config from .spec-view/config.yaml, falling back to defaults."""
    config_path = project_root / ".spec-view" / "config.yaml"
    if config_path.exists():
        return _load_from_file(config_path)

    # No explicit config - try auto-detection
    return _auto_detect_config(project_root)


def _load_from_file(config_path: Path) -> Config:
    """Load config from a YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    serve_data = data.get("serve", {})
    serve = ServeConfig(
        port=serve_data.get("port", 8080),
        open_browser=serve_data.get("open_browser", True),
    )

    return Config(
        spec_paths=data.get("spec_paths", ["specs/"]),
        include=data.get("include", []),
        exclude=data.get("exclude", ["**/node_modules/**", "**/.git/**"]),
        serve=serve,
        statuses=data.get(
            "statuses", ["draft", "ready", "in-progress", "done", "blocked"]
        ),
    )


def _auto_detect_config(project_root: Path) -> Config:
    """Auto-detect spec locations and build config."""
    detected = detect_spec_sources(project_root)

    if not detected:
        # Nothing found - return default (specs/)
        return Config()

    spec_paths = [d.path for d in detected]
    return Config(
        spec_paths=spec_paths,
        auto_detected=True,
    )


def save_config(project_root: Path, config: Config) -> Path:
    """Save config to .spec-view/config.yaml."""
    config_dir = project_root / ".spec-view"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    data: dict = {
        "spec_paths": config.spec_paths,
    }
    if config.include:
        data["include"] = config.include
    if config.exclude != ["**/node_modules/**", "**/.git/**"]:
        data["exclude"] = config.exclude

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return config_path
