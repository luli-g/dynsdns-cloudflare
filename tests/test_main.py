"""Tests for CLI entry point."""

import logging
from unittest.mock import patch

import pytest


class TestMainSuccess:
    """Tests for successful main() execution."""

    @patch("cloudflare_ddns.__main__.run_update", return_value=True)
    @patch("cloudflare_ddns.__main__.load_config")
    def test_successful_run_does_not_exit(self, mock_config, mock_update, cfg):
        from cloudflare_ddns.__main__ import main

        mock_config.return_value = cfg
        main()
        mock_update.assert_called_once_with(cfg)

    @patch("cloudflare_ddns.__main__.run_update", return_value=False)
    @patch("cloudflare_ddns.__main__.load_config")
    def test_failed_run_exits_with_code_1(self, mock_config, mock_update, cfg):
        from cloudflare_ddns.__main__ import main

        mock_config.return_value = cfg
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


class TestLoggingConfiguration:
    """Tests for logging setup in main()."""

    @patch("cloudflare_ddns.__main__.run_update", return_value=True)
    @patch("cloudflare_ddns.__main__.load_config")
    @patch("logging.basicConfig")
    def test_stdout_handler_always_present(self, mock_basic, mock_config, mock_update, cfg):
        from cloudflare_ddns.__main__ import main

        mock_config.return_value = cfg
        main()
        call_kwargs = mock_basic.call_args[1]
        handlers = call_kwargs["handlers"]
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    @patch("cloudflare_ddns.__main__.run_update", return_value=True)
    @patch("cloudflare_ddns.__main__.load_config")
    @patch("logging.basicConfig")
    def test_file_handler_added_when_log_file_set(self, mock_basic, mock_config, mock_update, tmp_path):
        from cloudflare_ddns.config import Config
        from cloudflare_ddns.__main__ import main

        log_path = str(tmp_path / "test.log")
        cfg = Config(
            api_token="t", zone_id="z", record_name="r",
            record_type="A", log_file=log_path, log_level="INFO",
        )
        mock_config.return_value = cfg
        main()
        call_kwargs = mock_basic.call_args[1]
        handlers = call_kwargs["handlers"]
        assert any(isinstance(h, logging.FileHandler) for h in handlers)

    @patch("cloudflare_ddns.__main__.run_update", return_value=True)
    @patch("cloudflare_ddns.__main__.load_config")
    @patch("logging.basicConfig")
    def test_no_file_handler_when_log_file_none(self, mock_basic, mock_config, mock_update, cfg):
        from cloudflare_ddns.__main__ import main

        mock_config.return_value = cfg
        main()
        call_kwargs = mock_basic.call_args[1]
        handlers = call_kwargs["handlers"]
        assert not any(isinstance(h, logging.FileHandler) for h in handlers)


class TestLogFileErrorHandling:
    """Tests for error handling when log file path is invalid."""

    @patch("cloudflare_ddns.__main__.load_config")
    def test_bad_log_path_exits_with_message(self, mock_config):
        from cloudflare_ddns.config import Config
        from cloudflare_ddns.__main__ import main

        cfg = Config(
            api_token="t", zone_id="z", record_name="r",
            record_type="A", log_file="/nonexistent/dir/log.txt", log_level="INFO",
        )
        mock_config.return_value = cfg
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert "Cannot open log file" in str(exc_info.value)
        assert "/nonexistent/dir/log.txt" in str(exc_info.value)
