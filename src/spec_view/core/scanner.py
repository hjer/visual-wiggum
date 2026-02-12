"""Directory scanning and file discovery."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from .config import Config
from .models import SpecFile, SpecGroup
from .parser import _slugify, parse_plan_sections, parse_spec_file


def _matches_any(path: Path, patterns: list[str], root: Path) -> bool:
    """Check if a path matches any glob pattern."""
    rel = str(path.relative_to(root))
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)


def discover_spec_files(root: Path, config: Config) -> list[Path]:
    """Find all markdown files matching config patterns."""
    files: list[Path] = []
    seen: set[Path] = set()

    for spec_path_str in config.spec_paths:
        spec_dir = root / spec_path_str
        if spec_dir.is_dir():
            for md in sorted(spec_dir.rglob("*.md")):
                resolved = md.resolve()
                if resolved not in seen and not _matches_any(md, config.exclude, root):
                    files.append(md)
                    seen.add(resolved)

    for pattern in config.include:
        for md in sorted(root.glob(pattern)):
            resolved = md.resolve()
            if resolved not in seen and not _matches_any(md, config.exclude, root):
                files.append(md)
                seen.add(resolved)

    return files


def _is_spec_path_root(parent: Path, root: Path, config: Config) -> bool:
    """Check if a directory is a configured spec_path root."""
    for spec_path_str in config.spec_paths:
        spec_dir = root / spec_path_str
        if parent == spec_dir or parent == spec_dir.resolve():
            return True
    return False


def _expand_wiggum_sections(
    spec_file: SpecFile, path: Path
) -> list[SpecGroup]:
    """Expand a wiggum-format file into one SpecGroup per plan section."""
    sections = parse_plan_sections(spec_file.body, path)
    if not sections:
        return []

    result: list[SpecGroup] = []
    for section in sections:
        slug = _slugify(section.title)
        tags = list(section.tags)  # already includes "plan"
        if section.task_total > 0 and section.task_done == section.task_total:
            if "plan-done" not in tags:
                tags.append("plan-done")

        virtual_file = SpecFile(
            path=path,
            title=section.title,
            status=section.status,
            priority=section.priority,
            tags=tags,
            content=section.body,
            body=section.body,
            tasks=section.tasks,
            task_tree=section.task_tree,
            file_type="spec",
            format_type="wiggum",
        )
        group = SpecGroup(
            name=slug,
            path=path.parent,
            files={"spec": virtual_file},
        )
        result.append(group)

    return result


def scan_specs(root: Path, config: Config) -> list[SpecGroup]:
    """Scan for spec files and group them by directory."""
    files = discover_spec_files(root, config)
    groups: dict[str, SpecGroup] = {}
    # Preserve insertion order for plan sections
    plan_groups: list[SpecGroup] = []

    for path in files:
        spec_file = parse_spec_file(path)
        parent = path.parent

        # Auto-tag specs in an archive directory
        if "archive" in path.parts and "archive" not in spec_file.tags:
            spec_file.tags.append("archive")

        # Wiggum-format files get expanded into per-section groups
        if spec_file.format_type == "wiggum":
            plan_groups.extend(_expand_wiggum_sections(spec_file, path))
            continue

        # Files directly in a spec_path root (or project root) are standalone.
        # Files in subdirectories of a spec_path are grouped by directory.
        is_in_subdir = (
            parent != root
            and not _is_spec_path_root(parent, root, config)
        )

        if is_in_subdir:
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

    # Sort non-plan groups alphabetically, then append plan groups in file order
    sorted_groups = sorted(groups.values(), key=lambda g: g.name)
    sorted_groups.extend(plan_groups)
    return sorted_groups
