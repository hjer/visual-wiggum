"""Markdown + YAML frontmatter parser."""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter

from .models import Phase, PlanSection, Priority, SpecFile, Status, Task

TASK_RE = re.compile(r"^( *)- \[([ xX])\]\*? (.+)$", re.MULTILINE)
PHASE_RE = re.compile(r"^## Phase (\d+):\s*(.+)$", re.MULTILINE)
CHECKPOINT_RE = re.compile(r"^\*\*Checkpoint\*\*:\s*(.+)$", re.MULTILINE)
TASK_ID_RE = re.compile(r"^(T\d+)\s+")
STORY_RE = re.compile(r"\[(US\d+)\]")
OPENSPEC_SECTION_RE = re.compile(r"^## \d+\.", re.MULTILINE)
H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*\s*(\S+)", re.MULTILINE)
PRIORITY_LINE_RE = re.compile(r"\*\*Priority:\*\*\s*(\S+)", re.MULTILINE)
TAGS_LINE_RE = re.compile(r"\*\*Tags:\*\*\s*(.+?)(?:\s*\||\s*$)", re.MULTILINE)
DONE_SUFFIX_RE = re.compile(r"\s*[—–-]+\s*DONE\s*$", re.IGNORECASE)


def detect_format(body: str, path: Path) -> str:
    """Detect which spec tool produced the file."""
    if ".kiro/" in str(path) or ".kiro" in str(path.parts):
        return "kiro"
    if PHASE_RE.search(body) and re.search(r"- \[[ xX]\]\*? T\d+", body):
        return "spec-kit"
    # Wiggum: multiple ## sections with **Status:** metadata lines
    h2_count = len(H2_RE.findall(body))
    status_count = len(STATUS_LINE_RE.findall(body))
    if h2_count >= 2 and status_count >= 2:
        return "wiggum"
    if OPENSPEC_SECTION_RE.search(body):
        return "openspec"
    return "generic"


def _extract_task_metadata(text: str) -> tuple[str, str, bool, str]:
    """Strip spec-kit markers from task text.

    Returns (clean_text, task_id, parallel, story).
    """
    task_id = ""
    parallel = False
    story = ""

    # Extract task ID (e.g. T001)
    m = TASK_ID_RE.match(text)
    if m:
        task_id = m.group(1)
        text = text[m.end():]

    # Check for [P] parallel marker
    if "[P]" in text:
        parallel = True
        text = text.replace("[P]", "").strip()

    # Extract story ref (e.g. [US1])
    m = STORY_RE.search(text)
    if m:
        story = m.group(1)
        text = text.replace(m.group(0), "").strip()

    return text.strip(), task_id, parallel, story


def parse_tasks(
    text: str, spec_name: str = "", source_file: str = ""
) -> tuple[list[Task], list[Task]]:
    """Extract checkbox tasks from markdown text.

    Returns (flat_list, tree) where tree has hierarchy based on indentation.
    """
    flat_list: list[Task] = []
    tree: list[Task] = []
    stack: list[tuple[int, Task]] = []
    indent_unit: int | None = None

    for match in TASK_RE.finditer(text):
        indent_len = len(match.group(1))
        done = match.group(2).lower() == "x"
        task_text = match.group(3).strip()

        if indent_len == 0:
            depth = 0
        elif indent_unit is None:
            indent_unit = indent_len
            depth = 1
        else:
            depth = round(indent_len / indent_unit)

        clean_text, task_id, parallel, story = _extract_task_metadata(task_text)

        task = Task(
            text=clean_text,
            done=done,
            spec_name=spec_name,
            source_file=source_file,
            depth=depth,
            task_id=task_id,
            parallel=parallel,
            story=story,
        )
        flat_list.append(task)

        # Build tree: pop stack until we find a parent (depth < current)
        while stack and stack[-1][0] >= depth:
            stack.pop()

        if stack:
            stack[-1][1].children.append(task)
        else:
            tree.append(task)

        stack.append((depth, task))

    return flat_list, tree


def detect_file_type(path: Path) -> str:
    """Detect file type from filename."""
    stem = path.stem.lower()
    if stem == "design":
        return "design"
    if stem in ("tasks", "todo"):
        return "tasks"
    return "spec"


def parse_title_from_body(body: str) -> str:
    """Extract title from first markdown heading."""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _parse_phases(body: str, flat_tasks: list[Task]) -> list[Phase]:
    """Parse phase sections from a spec-kit format body.

    Assigns tasks to phases based on their position between phase headings.
    """
    phase_matches = list(PHASE_RE.finditer(body))
    if not phase_matches:
        return []

    # Build list of (start_pos, phase_number, title) for each phase
    phase_spans: list[tuple[int, int, str]] = []
    for m in phase_matches:
        phase_spans.append((m.start(), int(m.group(1)), m.group(2).strip()))

    # Get task positions in the body using TASK_RE
    task_positions: list[int] = []
    for m in TASK_RE.finditer(body):
        task_positions.append(m.start())

    phases: list[Phase] = []
    for i, (start, number, title) in enumerate(phase_spans):
        end = phase_spans[i + 1][0] if i + 1 < len(phase_spans) else len(body)
        section = body[start:end]

        # Parse subtitle from title (e.g. "US1 - Login Flow" -> title="US1 - Login Flow")
        subtitle = ""
        if " - " in title:
            parts = title.split(" - ", 1)
            subtitle = parts[1].strip()

        # Find checkpoint in this section
        checkpoint = ""
        cp_match = CHECKPOINT_RE.search(section)
        if cp_match:
            checkpoint = cp_match.group(1).strip()

        # Assign tasks that fall within this phase's body range
        phase_tasks: list[Task] = []
        for j, pos in enumerate(task_positions):
            if start <= pos < end and j < len(flat_tasks):
                phase_tasks.append(flat_tasks[j])

        phases.append(Phase(
            number=number,
            title=title,
            subtitle=subtitle,
            tasks=phase_tasks,
            checkpoint=checkpoint,
        ))

    return phases


def _clean_section_title(heading: str) -> str:
    """Clean a plan section heading for display.

    Strips '— DONE' suffix, 'Spec:' prefix, and parenthetical references.
    """
    title = DONE_SUFFIX_RE.sub("", heading).strip()
    # Strip "Spec: " prefix
    if title.lower().startswith("spec:"):
        title = title[5:].strip()
    # Strip parenthetical references like (specs/foo.md)
    title = re.sub(r"\s*\([^)]*\.md\)", "", title).strip()
    return title


def _slugify(text: str) -> str:
    """Convert text to a URL/name-friendly slug."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_plan_sections(body: str, path: Path) -> list[PlanSection]:
    """Split a wiggum-format plan body into per-JTBD sections.

    Each ``## `` heading starts a new section. Sections without a
    ``**Status:**`` line and without task checkboxes are skipped
    (structural sections like Discovered Issues / Learnings).
    """
    sections: list[PlanSection] = []

    # Split at ## boundaries, keeping the heading line
    parts = re.split(r"(?=^## )", body, flags=re.MULTILINE)

    for part in parts:
        part = part.strip()
        if not part.startswith("## "):
            continue  # preamble before first ##

        # Extract heading
        first_newline = part.find("\n")
        if first_newline == -1:
            heading_line = part[3:]
            section_body = ""
        else:
            heading_line = part[3:first_newline]
            section_body = part[first_newline + 1:]

        # Check if this is a content section (has status line or tasks)
        has_status = bool(STATUS_LINE_RE.search(section_body))
        has_tasks = bool(TASK_RE.search(section_body))
        if not has_status and not has_tasks:
            continue  # skip structural sections

        # Title
        title = _clean_section_title(heading_line)

        # Status: from **Status:** line or — DONE suffix
        status_match = STATUS_LINE_RE.search(section_body)
        if DONE_SUFFIX_RE.search(heading_line):
            status = Status.DONE
        elif status_match:
            status = Status.from_str(status_match.group(1))
        else:
            status = Status.DRAFT

        # Priority
        priority_match = PRIORITY_LINE_RE.search(section_body)
        priority = Priority.from_str(priority_match.group(1)) if priority_match else Priority.MEDIUM

        # Tags
        tags_match = TAGS_LINE_RE.search(section_body)
        tags: list[str] = ["plan"]
        if tags_match:
            raw_tags = [t.strip() for t in tags_match.group(1).split(",")]
            for t in raw_tags:
                if t and t not in tags:
                    tags.append(t)

        # Tasks
        slug = _slugify(title)
        flat_tasks, task_tree = parse_tasks(
            section_body, spec_name=slug, source_file=str(path)
        )

        sections.append(PlanSection(
            title=title,
            status=status,
            priority=priority,
            tags=tags,
            tasks=flat_tasks,
            task_tree=task_tree,
            body=part,  # full section text including heading
            source_path=path,
        ))

    return sections


def parse_spec_file(path: Path) -> SpecFile:
    """Parse a markdown file with optional YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)

    metadata = post.metadata
    body = post.content
    file_type = detect_file_type(path)

    title = metadata.get("title", "")
    if not title:
        title = parse_title_from_body(body)
    if not title:
        # For generic filenames like spec.md, use the parent directory name
        generic_stems = {"spec", "design", "tasks", "todo", "requirements", "index", "readme"}
        if path.stem.lower() in generic_stems and path.parent.name:
            title = path.parent.name.replace("-", " ").replace("_", " ").title()
        else:
            title = path.stem.replace("-", " ").replace("_", " ").title()

    status_str = metadata.get("status", "draft")
    priority_str = metadata.get("priority", "medium")
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    spec_name = path.parent.name or path.stem
    flat_tasks, task_tree = parse_tasks(body, spec_name=spec_name, source_file=str(path))

    format_type = detect_format(body, path)
    phases: list[Phase] = []
    if format_type == "spec-kit":
        phases = _parse_phases(body, flat_tasks)

    return SpecFile(
        path=path,
        title=title,
        status=Status.from_str(status_str),
        priority=Priority.from_str(priority_str),
        tags=tags,
        content=text,
        body=body,
        tasks=flat_tasks,
        task_tree=task_tree,
        file_type=file_type,
        phases=phases,
        format_type=format_type,
    )
