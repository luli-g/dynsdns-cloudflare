"""Tests for update orchestrator."""

import logging

import responses
import pytest

from cloudflare_ddns.cloudflare import BASE_URL
from cloudflare_ddns.config import Config, load_config
from cloudflare_ddns.ip_resolver import ENDPOINTS
from cloudflare_ddns.updater import run_update


@pytest.fixture()
def cfg():
    return Config(
        api_token="test-token-abc123",
        zone_id="zone-id-xyz789",
        record_name="home.example.com",
        record_type="A",
    )


def _mock_ip(ip="203.0.113.42"):
    """Register a mock response for the IP resolver endpoint."""
    responses.add(
        responses.GET,
        ENDPOINTS["A"],
        body=f"{ip}\n",
        status=200,
    )


def _mock_dns_record(zone_id="zone-id-xyz789", record_id="rec-001", ip="1.2.3.4"):
    """Register a mock Cloudflare GET dns_records response."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/zones/{zone_id}/dns_records",
        json={
            "success": True,
            "errors": [],
            "result": [
                {
                    "id": record_id,
                    "type": "A",
                    "name": "home.example.com",
                    "content": ip,
                    "ttl": 1,
                    "proxied": False,
                }
            ],
        },
        status=200,
    )


def _mock_update(zone_id="zone-id-xyz789", record_id="rec-001"):
    """Register a mock Cloudflare PUT dns_records response."""
    responses.add(
        responses.PUT,
        f"{BASE_URL}/zones/{zone_id}/dns_records/{record_id}",
        json={
            "success": True,
            "errors": [],
            "result": {
                "id": record_id,
                "type": "A",
                "name": "home.example.com",
                "content": "203.0.113.42",
                "ttl": 1,
                "proxied": False,
            },
        },
        status=200,
    )


# ---------------------------------------------------------------------------
# IP changed -> update
# ---------------------------------------------------------------------------

class TestIPChanged:
    """Tests when the public IP differs from the DNS record."""

    @responses.activate
    def test_run_update_returns_true_when_ip_changed(self, cfg):
        _mock_ip("203.0.113.42")
        _mock_dns_record(ip="1.2.3.4")
        _mock_update()

        result = run_update(cfg)
        assert result is True

    @responses.activate
    def test_update_is_called_when_ip_changed(self, cfg):
        _mock_ip("203.0.113.42")
        _mock_dns_record(ip="1.2.3.4")
        _mock_update()

        run_update(cfg)

        # 3 HTTP calls: IP check, DNS lookup, DNS update
        assert len(responses.calls) == 3
        assert responses.calls[2].request.method == "PUT"

    @responses.activate
    def test_logs_ip_updated_message(self, cfg, caplog):
        _mock_ip("203.0.113.42")
        _mock_dns_record(ip="1.2.3.4")
        _mock_update()

        with caplog.at_level(logging.INFO):
            run_update(cfg)

        assert any("IP updated" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# IP unchanged -> no update
# ---------------------------------------------------------------------------

class TestIPUnchanged:
    """Tests when the public IP matches the DNS record."""

    @responses.activate
    def test_run_update_returns_true_when_ip_unchanged(self, cfg):
        _mock_ip("1.2.3.4")
        _mock_dns_record(ip="1.2.3.4")

        result = run_update(cfg)
        assert result is True

    @responses.activate
    def test_no_update_call_when_ip_unchanged(self, cfg):
        _mock_ip("1.2.3.4")
        _mock_dns_record(ip="1.2.3.4")

        run_update(cfg)

        # Only 2 HTTP calls: IP check and DNS lookup (no PUT)
        assert len(responses.calls) == 2

    @responses.activate
    def test_logs_no_ip_change_detected(self, cfg, caplog):
        _mock_ip("1.2.3.4")
        _mock_dns_record(ip="1.2.3.4")

        with caplog.at_level(logging.INFO):
            run_update(cfg)

        assert any("No IP change detected" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------

class TestIPResolverFailure:
    """Tests when the IP resolver fails."""

    @responses.activate
    def test_returns_false_on_ip_resolver_network_error(self, cfg, caplog):
        import requests as req
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body=req.ConnectionError("Network unreachable"),
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Request failed" in msg for msg in caplog.messages)

    @responses.activate
    def test_returns_false_on_ip_resolver_http_error(self, cfg, caplog):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="Server Error",
            status=500,
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Request failed" in msg for msg in caplog.messages)


class TestGetDnsRecordFailure:
    """Tests when Cloudflare get_dns_record fails."""

    @responses.activate
    def test_returns_false_on_dns_record_api_error(self, cfg, caplog):
        _mock_ip("203.0.113.42")
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={
                "success": False,
                "errors": [{"message": "Auth failed"}],
                "result": [],
            },
            status=200,
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Update failed" in msg for msg in caplog.messages)

    @responses.activate
    def test_returns_false_on_dns_record_http_error(self, cfg, caplog):
        _mock_ip("203.0.113.42")
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={},
            status=401,
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Request failed" in msg for msg in caplog.messages)


class TestUpdateDnsRecordFailure:
    """Tests when Cloudflare update_dns_record fails."""

    @responses.activate
    def test_returns_false_on_update_api_error(self, cfg, caplog):
        _mock_ip("203.0.113.42")
        _mock_dns_record(ip="1.2.3.4")
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/rec-001",
            json={
                "success": False,
                "errors": [{"message": "Update rejected"}],
                "result": None,
            },
            status=200,
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Update failed" in msg for msg in caplog.messages)

    @responses.activate
    def test_returns_false_on_update_http_error(self, cfg, caplog):
        _mock_ip("203.0.113.42")
        _mock_dns_record(ip="1.2.3.4")
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/rec-001",
            json={},
            status=500,
        )

        with caplog.at_level(logging.ERROR):
            result = run_update(cfg)

        assert result is False
        assert any("Request failed" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# Integration smoke test
# ---------------------------------------------------------------------------

class TestIntegrationSmokeTest:
    """Full flow integration test: config -> IP check -> DNS lookup -> update."""

    @responses.activate
    def test_full_flow_with_ip_change(self, env_vars, caplog):
        """Exercise the entire pipeline from config loading through update."""
        cfg = load_config()

        # Mock all three HTTP calls
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="198.51.100.99\n",
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={
                "success": True,
                "errors": [],
                "result": [
                    {
                        "id": "int-rec-001",
                        "type": "A",
                        "name": cfg.record_name,
                        "content": "10.0.0.1",
                        "ttl": 1,
                        "proxied": False,
                    }
                ],
            },
            status=200,
        )
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/int-rec-001",
            json={
                "success": True,
                "errors": [],
                "result": {
                    "id": "int-rec-001",
                    "type": "A",
                    "name": cfg.record_name,
                    "content": "198.51.100.99",
                    "ttl": 1,
                    "proxied": False,
                },
            },
            status=200,
        )

        with caplog.at_level(logging.INFO):
            result = run_update(cfg)

        assert result is True
        assert len(responses.calls) == 3
        assert any("IP updated" in msg for msg in caplog.messages)

    @responses.activate
    def test_full_flow_with_no_change(self, env_vars, caplog):
        """Exercise the entire pipeline when IP is already current."""
        cfg = load_config()

        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="10.0.0.1\n",
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={
                "success": True,
                "errors": [],
                "result": [
                    {
                        "id": "int-rec-001",
                        "type": "A",
                        "name": cfg.record_name,
                        "content": "10.0.0.1",
                        "ttl": 1,
                        "proxied": False,
                    }
                ],
            },
            status=200,
        )

        with caplog.at_level(logging.INFO):
            result = run_update(cfg)

        assert result is True
        assert len(responses.calls) == 2
        assert any("No IP change detected" in msg for msg in caplog.messages)
