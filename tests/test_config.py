"""Tests for spec-view config save/load round-trip."""

from spec_view.core.config import Config, ServeConfig, load_config, save_config, _auto_detect_config


class TestSaveConfigRoundTrip:
    def test_save_default_config_omits_serve_and_statuses(self, tmp_path):
        """Default serve and statuses should not appear in YAML output."""
        config = Config(spec_paths=["specs/"])
        save_config(tmp_path, config)

        yaml_text = (tmp_path / ".spec-view" / "config.yaml").read_text()
        assert "serve" not in yaml_text
        assert "statuses" not in yaml_text

    def test_save_custom_serve_port_round_trips(self, tmp_path):
        """Custom serve port is preserved across save/load."""
        config = Config(
            spec_paths=["specs/"],
            serve=ServeConfig(port=9090),
        )
        save_config(tmp_path, config)
        reloaded = load_config(tmp_path)

        assert reloaded.serve.port == 9090
        assert reloaded.serve.open_browser is True  # default preserved

    def test_save_custom_open_browser_round_trips(self, tmp_path):
        """Custom open_browser=False is preserved across save/load."""
        config = Config(
            spec_paths=["specs/"],
            serve=ServeConfig(open_browser=False),
        )
        save_config(tmp_path, config)
        reloaded = load_config(tmp_path)

        assert reloaded.serve.open_browser is False
        assert reloaded.serve.port == 8080  # default preserved

    def test_save_custom_statuses_round_trips(self, tmp_path):
        """Custom statuses list is preserved across save/load."""
        custom_statuses = ["todo", "doing", "done"]
        config = Config(
            spec_paths=["specs/"],
            statuses=custom_statuses,
        )
        save_config(tmp_path, config)
        reloaded = load_config(tmp_path)

        assert reloaded.statuses == custom_statuses

    def test_save_all_custom_fields_round_trips(self, tmp_path):
        """All non-default fields round-trip correctly together."""
        config = Config(
            spec_paths=["docs/"],
            include=["PLAN.md"],
            exclude=["**/dist/**"],
            serve=ServeConfig(port=3000, open_browser=False),
            statuses=["backlog", "active", "review", "shipped"],
        )
        save_config(tmp_path, config)
        reloaded = load_config(tmp_path)

        assert reloaded.spec_paths == ["docs/"]
        assert reloaded.include == ["PLAN.md"]
        assert reloaded.exclude == ["**/dist/**"]
        assert reloaded.serve.port == 3000
        assert reloaded.serve.open_browser is False
        assert reloaded.statuses == ["backlog", "active", "review", "shipped"]

    def test_save_only_non_default_serve_fields(self, tmp_path):
        """Only changed serve fields appear in YAML."""
        config = Config(
            spec_paths=["specs/"],
            serve=ServeConfig(port=4000),
        )
        save_config(tmp_path, config)

        yaml_text = (tmp_path / ".spec-view" / "config.yaml").read_text()
        assert "port: 4000" in yaml_text
        assert "open_browser" not in yaml_text


class TestAutoDetectConfig:
    def test_plan_file_goes_to_include(self, tmp_path):
        """IMPLEMENTATION_PLAN.md should be auto-detected into include, not spec_paths."""
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "feature.md").write_text("# Feature")
        (tmp_path / "IMPLEMENTATION_PLAN.md").write_text("# Plan\n")

        config = _auto_detect_config(tmp_path)
        assert "IMPLEMENTATION_PLAN.md" not in config.spec_paths
        assert "IMPLEMENTATION_PLAN.md" in config.include
        assert "specs" in config.spec_paths

    def test_plan_and_archive_both_in_include(self, tmp_path):
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "feature.md").write_text("# Feature")
        (tmp_path / "IMPLEMENTATION_PLAN.md").write_text("# Plan\n")
        (tmp_path / "IMPLEMENTATION_PLAN_ARCHIVE.md").write_text("# Archive\n")

        config = _auto_detect_config(tmp_path)
        assert "IMPLEMENTATION_PLAN.md" in config.include
        assert "IMPLEMENTATION_PLAN_ARCHIVE.md" in config.include
        assert config.auto_detected is True

    def test_no_plan_file_empty_include(self, tmp_path):
        specs = tmp_path / "specs"
        specs.mkdir()
        (specs / "feature.md").write_text("# Feature")

        config = _auto_detect_config(tmp_path)
        assert config.include == []
        assert "specs" in config.spec_paths
