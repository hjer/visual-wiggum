"""Tests for spec-view auto-detector."""

from pathlib import Path

from spec_view.core.detector import detect_spec_sources


class TestDetectSpecSources:
    def test_finds_specs_dir(self, tmp_path):
        specs = tmp_path / "specs" / "auth"
        specs.mkdir(parents=True)
        (specs / "spec.md").write_text("# Auth")

        detected = detect_spec_sources(tmp_path)
        assert len(detected) == 1
        assert detected[0].path == "specs"
        assert detected[0].source == "spec-view"

    def test_finds_kiro_specs(self, tmp_path):
        kiro = tmp_path / ".kiro" / "specs" / "my-feature"
        kiro.mkdir(parents=True)
        (kiro / "requirements.md").write_text("# Reqs")
        (kiro / "tasks.md").write_text("- [ ] Do stuff")

        detected = detect_spec_sources(tmp_path)
        assert any(d.source == "kiro" for d in detected)

    def test_finds_openspec(self, tmp_path):
        ospec = tmp_path / "openspec" / "changes" / "initial" / "specs" / "auth"
        ospec.mkdir(parents=True)
        (ospec / "spec.md").write_text("# Auth spec")

        detected = detect_spec_sources(tmp_path)
        assert any(d.source == "openspec" for d in detected)

    def test_finds_nested_kiro_in_subproject(self, tmp_path):
        kiro = tmp_path / "my-app" / ".kiro" / "specs" / "feature"
        kiro.mkdir(parents=True)
        (kiro / "spec.md").write_text("# Feature")

        detected = detect_spec_sources(tmp_path)
        assert any(d.source == "kiro" for d in detected)
        assert any("my-app" in d.path for d in detected)

    def test_finds_nested_openspec_in_subproject(self, tmp_path):
        ospec = (
            tmp_path / "backend" / "openspec" / "changes" / "init" / "specs" / "feat"
        )
        ospec.mkdir(parents=True)
        (ospec / "spec.md").write_text("# Feat")

        detected = detect_spec_sources(tmp_path)
        assert any(d.source == "openspec" for d in detected)

    def test_finds_docs_dir(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "architecture.md").write_text("# Arch")

        detected = detect_spec_sources(tmp_path)
        assert any(d.path == "docs" for d in detected)

    def test_empty_project(self, tmp_path):
        detected = detect_spec_sources(tmp_path)
        assert detected == []

    def test_ignores_dirs_without_md(self, tmp_path):
        (tmp_path / "specs").mkdir()
        (tmp_path / "specs" / "readme.txt").write_text("not markdown")

        detected = detect_spec_sources(tmp_path)
        assert detected == []

    def test_multiple_sources_sorted_by_count(self, tmp_path):
        # specs/ has 1 file
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "overview.md").write_text("# Overview")

        # docs/ has 3 files
        docs = tmp_path / "docs"
        docs.mkdir()
        for name in ["a.md", "b.md", "c.md"]:
            (docs / name).write_text(f"# {name}")

        detected = detect_spec_sources(tmp_path)
        assert len(detected) == 2
        # docs should come first (more files)
        assert detected[0].path == "docs"
        assert detected[1].path == "specs"

    def test_openspec_picks_up_toplevel_md(self, tmp_path):
        """OpenSpec changes often have tasks.md and design.md at change root."""
        change = tmp_path / "openspec" / "changes" / "my-change"
        change.mkdir(parents=True)
        (change / "tasks.md").write_text("- [ ] Do stuff")
        (change / "design.md").write_text("# Design")

        detected = detect_spec_sources(tmp_path)
        assert any(d.source == "openspec" for d in detected)
