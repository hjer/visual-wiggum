"""Directory scanning and file discovery."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from .config import Config
from .models import SpecFile, SpecGroup
from .parser import parse_spec_file


def _matches_any(path: Path, patterns: list[str], root: Path) -> bool:
    """Check if a path matches any glob pattern."""
    rel = str(path.relative_to(root))
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)


def discover_spec_files(root: Path, config: Config) -> list[Path]:
    """Find all markdown files matching config patterns."""
    files: list[Path] = []

    for spec_path_str in config.spec_paths:
        spec_dir = root / spec_path_str
        if spec_dir.is_dir():
            for md in sorted(spec_dir.rglob("*.md")):
                if not _matches_any(md, config.exclude, root):
                    files.append(md)

    for pattern in config.include:
        for md in sorted(root.glob(pattern)):
            if md not in files and not _matches_any(md, config.exclude, root):
                files.append(md)

    return files


def scan_specs(root: Path, config: Config) -> list[SpecGroup]:
    """Scan for spec files and group them by directory."""
    files = discover_spec_files(root, config)
    groups: dict[str, SpecGroup] = {}
    standalone: list[SpecFile] = []

    for path in files:
        spec_file = parse_spec_file(path)
        parent = path.parent

        # Check if this is inside a spec group directory (has sibling spec files)
        siblings = list(parent.glob("*.md"))
        is_group = len(siblings) > 1 or parent.name != path.stem

        if is_group and parent != root:
            group_name = parent.name
            if group_name not in groups:
                groups[group_name] = SpecGroup(
                    name=group_name,
                    path=parent,
                )
            groups[group_name].files[spec_file.file_type] = spec_file
        else:
            # Standalone file gets its own group
            group_name = path.stem
            if group_name not in groups:
                groups[group_name] = SpecGroup(
                    name=group_name,
                    path=parent,
                )
            groups[group_name].files[spec_file.file_type] = spec_file

    return sorted(groups.values(), key=lambda g: g.name)
