"""Tests for spec-view data models."""

from pathlib import Path

from spec_view.core.models import (
    Phase,
    Priority,
    SpecFile,
    SpecGroup,
    Status,
    Task,
)


class TestStatus:
    def test_from_valid_string(self):
        assert Status.from_str("draft") == Status.DRAFT
        assert Status.from_str("in-progress") == Status.IN_PROGRESS
        assert Status.from_str("done") == Status.DONE

    def test_from_string_case_insensitive(self):
        assert Status.from_str("DRAFT") == Status.DRAFT
        assert Status.from_str("In-Progress") == Status.IN_PROGRESS

    def test_from_unknown_string_defaults_to_draft(self):
        assert Status.from_str("unknown") == Status.DRAFT
        assert Status.from_str("") == Status.DRAFT


class TestPriority:
    def test_from_valid_string(self):
        assert Priority.from_str("low") == Priority.LOW
        assert Priority.from_str("critical") == Priority.CRITICAL

    def test_from_unknown_string_defaults_to_medium(self):
        assert Priority.from_str("unknown") == Priority.MEDIUM


class TestTask:
    def test_defaults(self):
        t = Task(text="Do something")
        assert t.text == "Do something"
        assert t.done is False
        assert t.spec_name == ""
        assert t.depth == 0
        assert t.children == []

    def test_children(self):
        child1 = Task(text="Child 1", done=True, depth=1)
        child2 = Task(text="Child 2", done=False, depth=1)
        parent = Task(text="Parent", children=[child1, child2])
        assert len(parent.children) == 2
        assert parent.children[0].text == "Child 1"

    def test_subtask_total(self):
        grandchild = Task(text="GC", depth=2)
        child = Task(text="Child", depth=1, children=[grandchild])
        parent = Task(text="Parent", children=[child])
        # parent has 1 child + 1 grandchild = 2 descendants
        assert parent.subtask_total == 2
        assert child.subtask_total == 1

    def test_subtask_done(self):
        gc1 = Task(text="GC1", done=True, depth=2)
        gc2 = Task(text="GC2", done=False, depth=2)
        child = Task(text="Child", done=True, depth=1, children=[gc1, gc2])
        parent = Task(text="Parent", children=[child])
        # parent: child is done (1) + gc1 is done (1) = 2
        assert parent.subtask_done == 2
        # child: gc1 is done (1) = 1
        assert child.subtask_done == 1

    def test_subtask_total_no_children(self):
        t = Task(text="Leaf")
        assert t.subtask_total == 0
        assert t.subtask_done == 0


class TestSpecFile:
    def test_task_percent_no_tasks(self):
        sf = SpecFile(path=Path("test.md"))
        assert sf.task_percent == 0
        assert sf.task_total == 0

    def test_task_percent_with_tasks(self):
        sf = SpecFile(
            path=Path("test.md"),
            tasks=[
                Task(text="a", done=True),
                Task(text="b", done=False),
                Task(text="c", done=True),
            ],
        )
        assert sf.task_total == 3
        assert sf.task_done == 2
        assert sf.task_percent == 66

    def test_task_tree_field(self):
        child = Task(text="Sub", done=True, depth=1)
        parent = Task(text="Main", children=[child])
        sf = SpecFile(path=Path("test.md"), task_tree=[parent])
        assert len(sf.task_tree) == 1
        assert sf.task_tree[0].children[0].text == "Sub"


class TestSpecGroup:
    def test_title_from_spec_file(self):
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "spec": SpecFile(path=Path("spec.md"), title="Authentication"),
            },
        )
        assert group.title == "Authentication"

    def test_title_fallback_from_name(self):
        group = SpecGroup(name="my-feature", path=Path("specs/my-feature"))
        assert group.title == "My Feature"

    def test_status_from_spec(self):
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "spec": SpecFile(path=Path("spec.md"), status=Status.IN_PROGRESS),
            },
        )
        assert group.status == Status.IN_PROGRESS

    def test_all_tasks_aggregated(self):
        group = SpecGroup(
            name="test",
            path=Path("specs/test"),
            files={
                "spec": SpecFile(
                    path=Path("spec.md"),
                    tasks=[Task(text="a", done=True)],
                ),
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    tasks=[Task(text="b"), Task(text="c", done=True)],
                ),
            },
        )
        assert group.task_total == 3
        assert group.task_done == 2

    def test_tags_deduplicated(self):
        group = SpecGroup(
            name="test",
            path=Path("specs/test"),
            files={
                "spec": SpecFile(path=Path("spec.md"), tags=["auth", "backend"]),
                "design": SpecFile(path=Path("design.md"), tags=["auth", "api"]),
            },
        )
        assert group.tags == ["auth", "backend", "api"]

    def test_all_task_trees(self):
        child = Task(text="Sub", done=True, depth=1)
        parent = Task(text="Main", children=[child])
        group = SpecGroup(
            name="test",
            path=Path("specs/test"),
            files={
                "spec": SpecFile(
                    path=Path("spec.md"),
                    task_tree=[parent],
                ),
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    task_tree=[Task(text="Other")],
                ),
            },
        )
        trees = group.all_task_trees
        assert len(trees) == 2
        assert trees[0].text == "Main"
        assert len(trees[0].children) == 1
        assert trees[1].text == "Other"


class TestTaskMetadataFields:
    def test_defaults(self):
        t = Task(text="Do something")
        assert t.task_id == ""
        assert t.parallel is False
        assert t.story == ""

    def test_with_metadata(self):
        t = Task(text="Build login", task_id="T001", parallel=True, story="US1")
        assert t.task_id == "T001"
        assert t.parallel is True
        assert t.story == "US1"


class TestPhase:
    def test_task_total(self):
        p = Phase(number=1, title="Setup", tasks=[
            Task(text="a", done=True),
            Task(text="b", done=False),
            Task(text="c", done=True),
        ])
        assert p.task_total == 3

    def test_task_done(self):
        p = Phase(number=1, title="Setup", tasks=[
            Task(text="a", done=True),
            Task(text="b", done=False),
            Task(text="c", done=True),
        ])
        assert p.task_done == 2

    def test_task_percent(self):
        p = Phase(number=1, title="Setup", tasks=[
            Task(text="a", done=True),
            Task(text="b", done=False),
            Task(text="c", done=True),
        ])
        assert p.task_percent == 66

    def test_task_percent_empty(self):
        p = Phase(number=1, title="Empty")
        assert p.task_percent == 0

    def test_checkpoint(self):
        p = Phase(number=1, title="Setup", checkpoint="Foundation ready")
        assert p.checkpoint == "Foundation ready"


class TestSpecFilePhases:
    def test_phases_populated(self):
        p1 = Phase(number=1, title="Setup", tasks=[Task(text="a")])
        p2 = Phase(number=2, title="Core", tasks=[Task(text="b")])
        sf = SpecFile(path=Path("tasks.md"), phases=[p1, p2], format_type="spec-kit")
        assert len(sf.phases) == 2
        assert sf.format_type == "spec-kit"

    def test_phases_default_empty(self):
        sf = SpecFile(path=Path("tasks.md"))
        assert sf.phases == []
        assert sf.format_type == "generic"


class TestSpecGroupPhases:
    def test_all_phases_from_tasks_file(self):
        p1 = Phase(number=1, title="Setup")
        p2 = Phase(number=2, title="Core")
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    phases=[p1, p2],
                    format_type="spec-kit",
                ),
            },
        )
        assert len(group.all_phases) == 2
        assert group.all_phases[0].title == "Setup"

    def test_format_type_from_tasks(self):
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    format_type="spec-kit",
                ),
                "spec": SpecFile(
                    path=Path("spec.md"),
                    format_type="generic",
                ),
            },
        )
        assert group.format_type == "spec-kit"

    def test_format_type_generic_fallback(self):
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "spec": SpecFile(path=Path("spec.md")),
            },
        )
        assert group.format_type == "generic"

    def test_stories_collected(self):
        group = SpecGroup(
            name="auth",
            path=Path("specs/auth"),
            files={
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    tasks=[
                        Task(text="a", story="US1"),
                        Task(text="b", story="US2"),
                        Task(text="c", story="US1"),
                        Task(text="d", story=""),
                    ],
                ),
            },
        )
        assert group.stories == ["US1", "US2"]

    def test_stories_empty(self):
        group = SpecGroup(
            name="test",
            path=Path("specs/test"),
            files={
                "tasks": SpecFile(
                    path=Path("tasks.md"),
                    tasks=[Task(text="a"), Task(text="b")],
                ),
            },
        )
        assert group.stories == []
