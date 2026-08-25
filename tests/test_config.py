"""Tests for config module."""

from unittest.mock import patch

import pytest

from cloudflare_ddns.config import Config, load_config


class TestLoadConfigSuccess:
    """Tests for successful config loading."""

    def test_load_with_all_required_vars(self, env_vars):
        cfg = load_config()
        assert cfg.api_token == "test-token-abc123"
        assert cfg.zone_id == "zone-id-xyz789"
        assert cfg.record_name == "home.example.com"

    def test_returns_config_dataclass(self, env_vars):
        cfg = load_config()
        assert isinstance(cfg, Config)


class TestLoadConfigMissingVars:
    """Tests for missing required environment variables."""

    def test_missing_single_required_var(self, monkeypatch):
        monkeypatch.setenv("ZONE_ID", "zone-id-xyz789")
        monkeypatch.setenv("RECORD_NAME", "home.example.com")
        monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)

        with pytest.raises(SystemExit, match="CLOUDFLARE_API_TOKEN"):
            load_config()

    def test_missing_multiple_required_vars(self, monkeypatch):
        # Set none of the required vars
        monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
        monkeypatch.delenv("ZONE_ID", raising=False)
        monkeypatch.delenv("RECORD_NAME", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            load_config()

        message = str(exc_info.value)
        assert "CLOUDFLARE_API_TOKEN" in message
        assert "ZONE_ID" in message
        assert "RECORD_NAME" in message

    def test_blank_required_var_treated_as_missing(self, monkeypatch):
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "   ")
        monkeypatch.setenv("ZONE_ID", "zone-id-xyz789")
        monkeypatch.setenv("RECORD_NAME", "home.example.com")

        with pytest.raises(SystemExit, match="CLOUDFLARE_API_TOKEN"):
            load_config()


class TestDefaultValues:
    """Tests for default values of optional configuration."""

    def test_record_type_defaults_to_a(self, env_vars):
        cfg = load_config()
        assert cfg.record_type == "A"

    def test_log_file_defaults_to_none(self, env_vars):
        cfg = load_config()
        assert cfg.log_file is None

    def test_log_level_defaults_to_info(self, env_vars):
        cfg = load_config()
        assert cfg.log_level == "INFO"


class TestCustomOptionalValues:
    """Tests for custom values of optional configuration."""

    def test_custom_record_type_aaaa(self, env_vars, monkeypatch):
        monkeypatch.setenv("RECORD_TYPE", "AAAA")
        cfg = load_config()
        assert cfg.record_type == "AAAA"

    def test_custom_log_file(self, env_vars, monkeypatch):
        monkeypatch.setenv("LOG_FILE", "/var/log/ddns.log")
        cfg = load_config()
        assert cfg.log_file == "/var/log/ddns.log"

    def test_custom_log_level(self, env_vars, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        cfg = load_config()
        assert cfg.log_level == "DEBUG"

    def test_record_type_case_insensitive(self, env_vars, monkeypatch):
        monkeypatch.setenv("RECORD_TYPE", "aaaa")
        cfg = load_config()
        assert cfg.record_type == "AAAA"

    def test_log_level_case_insensitive(self, env_vars, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "debug")
        cfg = load_config()
        assert cfg.log_level == "DEBUG"

    def test_values_are_stripped(self, env_vars, monkeypatch):
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "  token-with-spaces  ")
        monkeypatch.setenv("ZONE_ID", "  zone-with-spaces  ")
        monkeypatch.setenv("RECORD_NAME", "  name-with-spaces  ")
        cfg = load_config()
        assert cfg.api_token == "token-with-spaces"
        assert cfg.zone_id == "zone-with-spaces"
        assert cfg.record_name == "name-with-spaces"


class TestInvalidValues:
    """Tests for invalid configuration values."""

    def test_invalid_record_type_raises_system_exit(self, env_vars, monkeypatch):
        monkeypatch.setenv("RECORD_TYPE", "MX")
        with pytest.raises(SystemExit, match="Invalid RECORD_TYPE"):
            load_config()

    def test_invalid_log_level_raises_system_exit(self, env_vars, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
        with pytest.raises(SystemExit, match="Invalid LOG_LEVEL"):
            load_config()


class TestDotenvLoading:
    """Tests for .env file loading behaviour."""

    def test_dotenv_is_loaded(self, env_vars):
        """load_config calls load_dotenv; verify it runs without error."""
        with patch("cloudflare_ddns.config.load_dotenv") as mock_dotenv:
            load_config()
            mock_dotenv.assert_called_once_with(override=False)

    def test_system_env_takes_precedence_over_dotenv(self, monkeypatch):
        """System env vars override .env values because override=False."""
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "system-token")
        monkeypatch.setenv("ZONE_ID", "system-zone")
        monkeypatch.setenv("RECORD_NAME", "system.example.com")

        # Simulate dotenv setting different values (they should be ignored
        # because override=False means env vars already set are kept).
        with patch("cloudflare_ddns.config.load_dotenv") as mock_dotenv:
            cfg = load_config()
            mock_dotenv.assert_called_once_with(override=False)

        assert cfg.api_token == "system-token"
        assert cfg.zone_id == "system-zone"
        assert cfg.record_name == "system.example.com"
