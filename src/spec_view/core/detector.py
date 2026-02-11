"""Auto-detect spec file locations in a project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectedSource:
    """A detected spec source in the project."""

    path: str  # Relative path from project root
    source: str  # What tool/convention it came from
    description: str  # Human-readable description
    md_count: int = 0  # Number of markdown files found


# Directory names that signal spec content.
MARKER_DIRS: dict[str, str] = {
    "specs": "spec-view",
    ".kiro": "kiro",
    "openspec": "openspec",
    ".openspec": "openspec",
    ".spec": "generic",
    "docs": "generic",
}

# Directories to never descend into.
SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
    ".next",
}

# Max depth for recursive project scanning (finding marker dirs).
MAX_SCAN_DEPTH = 4


def _count_md_files(path: Path) -> int:
    """Count markdown files under a path."""
    return sum(1 for _ in path.rglob("*.md"))


def _find_openspec_leaf_dirs(openspec_root: Path, root: Path) -> list[DetectedSource]:
    """Expand an openspec directory into its actual spec locations.

    OpenSpec nests specs under changes/<change-name>/specs/ and also has
    top-level .md files at the change level (tasks.md, design.md, etc.).
    """
    results: list[DetectedSource] = []
    parent_label = _label_for_path(openspec_root, root)

    changes_dir = openspec_root / "changes"
    if changes_dir.is_dir():
        for change_dir in sorted(changes_dir.iterdir()):
            if not change_dir.is_dir() or change_dir.name == "archive":
                continue
            specs_sub = change_dir / "specs"
            if specs_sub.is_dir():
                md_count = _count_md_files(specs_sub)
                if md_count > 0:
                    rel = str(specs_sub.relative_to(root))
                    results.append(
                        DetectedSource(
                            path=rel,
                            source="openspec",
                            description=f"OpenSpec ({parent_label}): {change_dir.name}/specs",
                            md_count=md_count,
                        )
                    )
            # Top-level md files in the change dir (tasks.md, design.md)
            change_md = list(change_dir.glob("*.md"))
            if change_md:
                rel = str(change_dir.relative_to(root))
                # Don't add if we already added specs_sub from same change
                if not any(r.path.startswith(rel + "/") for r in results):
                    pass  # specs/ already covers it
                results.append(
                    DetectedSource(
                        path=rel,
                        source="openspec",
                        description=f"OpenSpec ({parent_label}): {change_dir.name}",
                        md_count=len(change_md),
                    )
                )

    # Direct specs/ under openspec root
    direct_specs = openspec_root / "specs"
    if direct_specs.is_dir():
        md_count = _count_md_files(direct_specs)
        if md_count > 0:
            rel = str(direct_specs.relative_to(root))
            results.append(
                DetectedSource(
                    path=rel,
                    source="openspec",
                    description=f"OpenSpec ({parent_label}): specs",
                    md_count=md_count,
                )
            )

    return results


def _label_for_path(path: Path, root: Path) -> str:
    """Create a human label from a path relative to root."""
    rel = path.relative_to(root)
    parts = [p for p in rel.parts if not p.startswith(".")]
    return parts[0] if parts else rel.name


def _find_kiro_spec_dir(kiro_root: Path) -> Path:
    """Find the best spec directory inside a .kiro dir.

    Prefers .kiro/specs/ if it exists, otherwise uses .kiro/ itself.
    """
    specs_sub = kiro_root / "specs"
    if specs_sub.is_dir() and _count_md_files(specs_sub) > 0:
        return specs_sub
    return kiro_root


def detect_spec_sources(root: Path) -> list[DetectedSource]:
    """Scan a project root for known spec file locations.

    Recursively walks the project tree (up to MAX_SCAN_DEPTH) looking for
    known marker directories. Returns detected sources sorted by file count.
    """
    detected: list[DetectedSource] = []
    seen_paths: set[str] = set()

    def add(source: DetectedSource) -> None:
        if source.path not in seen_paths:
            detected.append(source)
            seen_paths.add(source.path)

    def scan_dir(directory: Path, depth: int = 0) -> None:
        if depth > MAX_SCAN_DEPTH:
            return

        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if not entry.is_dir():
                continue
            if entry.name in SKIP_DIRS:
                continue

            if entry.name in MARKER_DIRS:
                source_type = MARKER_DIRS[entry.name]
                _process_marker(entry, source_type, root, add)
            else:
                # Recurse into non-marker directories to find nested projects
                scan_dir(entry, depth + 1)

    scan_dir(root)

    # Deduplicate: if a parent and child path are both present,
    # keep only the more specific (child) path.
    detected = _deduplicate(detected)

    detected.sort(key=lambda d: d.md_count, reverse=True)
    return detected


def _process_marker(
    path: Path,
    source_type: str,
    root: Path,
    add: callable,
) -> None:
    """Process a found marker directory into DetectedSource(s)."""
    label = _label_for_path(path, root)

    if source_type == "openspec":
        for src in _find_openspec_leaf_dirs(path, root):
            add(src)
        return

    if source_type == "kiro":
        best = _find_kiro_spec_dir(path)
        md_count = _count_md_files(best)
        if md_count > 0:
            rel = str(best.relative_to(root))
            add(
                DetectedSource(
                    path=rel,
                    source="kiro",
                    description=f"Kiro ({label})" if label != ".kiro" else "Kiro specs",
                    md_count=md_count,
                )
            )
        return

    # Generic markers: specs/, docs/, .spec/
    md_count = _count_md_files(path)
    if md_count > 0:
        rel = str(path.relative_to(root))
        add(
            DetectedSource(
                path=rel,
                source=source_type,
                description=f"{path.name}/ directory",
                md_count=md_count,
            )
        )


def _deduplicate(detected: list[DetectedSource]) -> list[DetectedSource]:
    """Remove parent paths when a more specific child path exists."""
    paths = {d.path for d in detected}
    result: list[DetectedSource] = []
    for d in detected:
        # Check if any other detected path is a child of this one
        is_parent = any(
            other != d.path and other.startswith(d.path + "/") for other in paths
        )
        if not is_parent:
            result.append(d)
    return result
