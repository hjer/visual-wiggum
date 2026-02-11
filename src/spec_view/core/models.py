"""Data models for spec-view."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(Enum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    BLOCKED = "blocked"

    @classmethod
    def from_str(cls, value: str) -> Status:
        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.DRAFT


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_str(cls, value: str) -> Priority:
        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.MEDIUM


@dataclass
class Task:
    """A single checkbox task extracted from markdown."""

    text: str
    done: bool = False
    spec_name: str = ""
    source_file: str = ""
    depth: int = 0
    children: list[Task] = field(default_factory=list)
    task_id: str = ""
    parallel: bool = False
    story: str = ""

    @property
    def subtask_total(self) -> int:
        """Total number of descendant tasks."""
        count = len(self.children)
        for child in self.children:
            count += child.subtask_total
        return count

    @property
    def subtask_done(self) -> int:
        """Number of completed descendant tasks."""
        count = sum(1 for c in self.children if c.done)
        for child in self.children:
            count += child.subtask_done
        return count


@dataclass
class Phase:
    """A phase section in a spec-kit tasks file."""

    number: int
    title: str
    subtitle: str = ""
    tasks: list[Task] = field(default_factory=list)
    checkpoint: str = ""

    @property
    def task_total(self) -> int:
        return len(self.tasks)

    @property
    def task_done(self) -> int:
        return sum(1 for t in self.tasks if t.done)

    @property
    def task_percent(self) -> int:
        if self.task_total == 0:
            return 0
        return int(self.task_done / self.task_total * 100)


@dataclass
class SpecFile:
    """A parsed spec/design/tasks markdown file."""

    path: Path
    title: str = ""
    status: Status = Status.DRAFT
    priority: Priority = Priority.MEDIUM
    tags: list[str] = field(default_factory=list)
    content: str = ""
    body: str = ""
    tasks: list[Task] = field(default_factory=list)
    task_tree: list[Task] = field(default_factory=list)
    file_type: str = "spec"  # spec | design | tasks
    phases: list[Phase] = field(default_factory=list)
    format_type: str = "generic"  # "spec-kit" | "kiro" | "openspec" | "generic"

    @property
    def task_total(self) -> int:
        return len(self.tasks)

    @property
    def task_done(self) -> int:
        return sum(1 for t in self.tasks if t.done)

    @property
    def task_percent(self) -> int:
        if self.task_total == 0:
            return 0
        return int(self.task_done / self.task_total * 100)


@dataclass
class SpecGroup:
    """A group of related spec files (spec.md, design.md, tasks.md) in one directory."""

    name: str
    path: Path
    files: dict[str, SpecFile] = field(default_factory=dict)

    @property
    def spec(self) -> SpecFile | None:
        return self.files.get("spec")

    @property
    def design(self) -> SpecFile | None:
        return self.files.get("design")

    @property
    def tasks_file(self) -> SpecFile | None:
        return self.files.get("tasks")

    @property
    def title(self) -> str:
        if self.spec and self.spec.title:
            return self.spec.title
        for f in self.files.values():
            if f.title:
                return f.title
        return self.name.replace("-", " ").replace("_", " ").title()

    @property
    def status(self) -> Status:
        if self.spec:
            return self.spec.status
        for f in self.files.values():
            return f.status
        return Status.DRAFT

    @property
    def priority(self) -> Priority:
        if self.spec:
            return self.spec.priority
        for f in self.files.values():
            return f.priority
        return Priority.MEDIUM

    @property
    def tags(self) -> list[str]:
        all_tags: list[str] = []
        for f in self.files.values():
            for tag in f.tags:
                if tag not in all_tags:
                    all_tags.append(tag)
        return all_tags

    @property
    def all_tasks(self) -> list[Task]:
        tasks: list[Task] = []
        for f in self.files.values():
            tasks.extend(f.tasks)
        return tasks

    @property
    def all_task_trees(self) -> list[Task]:
        """Hierarchical task trees aggregated across all files."""
        trees: list[Task] = []
        for f in self.files.values():
            trees.extend(f.task_tree)
        return trees

    @property
    def task_total(self) -> int:
        return len(self.all_tasks)

    @property
    def task_done(self) -> int:
        return sum(1 for t in self.all_tasks if t.done)

    @property
    def task_percent(self) -> int:
        if self.task_total == 0:
            return 0
        return int(self.task_done / self.task_total * 100)

    @property
    def all_phases(self) -> list[Phase]:
        """Phases from the tasks file (or first file with phases)."""
        if self.tasks_file and self.tasks_file.phases:
            return self.tasks_file.phases
        for f in self.files.values():
            if f.phases:
                return f.phases
        return []

    @property
    def format_type(self) -> str:
        """Detected format from the tasks file."""
        if self.tasks_file and self.tasks_file.format_type != "generic":
            return self.tasks_file.format_type
        for f in self.files.values():
            if f.format_type != "generic":
                return f.format_type
        return "generic"

    @property
    def stories(self) -> list[str]:
        """Unique story refs across all tasks (e.g. ['US1', 'US2'])."""
        seen: list[str] = []
        for t in self.all_tasks:
            if t.story and t.story not in seen:
                seen.append(t.story)
        return seen
