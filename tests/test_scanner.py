"""Tests for spec-view scanner."""

from pathlib import Path

from spec_view.core.config import Config
from spec_view.core.models import Status
from spec_view.core.scanner import discover_spec_files, scan_specs


class TestDiscoverSpecFiles:
    def test_finds_md_files_in_specs_dir(self, tmp_path):
        specs_dir = tmp_path / "specs" / "auth"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text("# Auth")
        (specs_dir / "design.md").write_text("# Design")
        (tmp_path / "specs" / "overview.md").write_text("# Overview")

        config = Config(spec_paths=["specs/"])
        files = discover_spec_files(tmp_path, config)
        assert len(files) == 3

    def test_respects_exclude_patterns(self, tmp_path):
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        (specs_dir / "good.md").write_text("# Good")
        node_dir = tmp_path / "node_modules" / "pkg"
        node_dir.mkdir(parents=True)
        (node_dir / "spec.md").write_text("# Bad")

        config = Config(
            spec_paths=["specs/"],
            exclude=["**/node_modules/**"],
        )
        files = discover_spec_files(tmp_path, config)
        assert len(files) == 1

    def test_include_patterns(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "feature.spec.md").write_text("# Feature")

        config = Config(spec_paths=[], include=["docs/**/*.spec.md"])
        files = discover_spec_files(tmp_path, config)
        assert len(files) == 1

    def test_empty_specs_dir(self, tmp_path):
        (tmp_path / "specs").mkdir()
        config = Config(spec_paths=["specs/"])
        files = discover_spec_files(tmp_path, config)
        assert len(files) == 0

    def test_no_specs_dir(self, tmp_path):
        config = Config(spec_paths=["specs/"])
        files = discover_spec_files(tmp_path, config)
        assert len(files) == 0


class TestScanSpecs:
    def test_groups_by_directory(self, tmp_path):
        auth_dir = tmp_path / "specs" / "auth"
        auth_dir.mkdir(parents=True)
        (auth_dir / "spec.md").write_text(
            "---\ntitle: Auth\nstatus: in-progress\n---\n# Auth\n- [ ] Task"
        )
        (auth_dir / "design.md").write_text("---\ntitle: Auth Design\n---\n# Design")
        (auth_dir / "tasks.md").write_text("---\ntitle: Auth Tasks\n---\n- [ ] A\n- [x] B")

        config = Config(spec_paths=["specs/"])
        groups = scan_specs(tmp_path, config)
        assert len(groups) == 1
        group = groups[0]
        assert group.name == "auth"
        assert group.title == "Auth"
        assert group.status == Status.IN_PROGRESS
        assert "spec" in group.files
        assert "design" in group.files
        assert "tasks" in group.files

    def test_multiple_groups(self, tmp_path):
        for name in ["auth", "payments"]:
            d = tmp_path / "specs" / name
            d.mkdir(parents=True)
            (d / "spec.md").write_text(f"# {name.title()}")

        config = Config(spec_paths=["specs/"])
        groups = scan_specs(tmp_path, config)
        assert len(groups) == 2
        names = [g.name for g in groups]
        assert "auth" in names
        assert "payments" in names

    def test_tasks_aggregated_in_group(self, tmp_path):
        d = tmp_path / "specs" / "feature"
        d.mkdir(parents=True)
        (d / "spec.md").write_text("# Feature\n- [x] Done task")
        (d / "tasks.md").write_text("# Tasks\n- [ ] Todo\n- [x] Done")

        config = Config(spec_paths=["specs/"])
        groups = scan_specs(tmp_path, config)
        assert groups[0].task_total == 3
        assert groups[0].task_done == 2
