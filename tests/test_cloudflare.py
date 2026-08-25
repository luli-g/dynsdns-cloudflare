"""Tests for Cloudflare API client."""

import json

import requests
import responses
import pytest

from cloudflare_ddns.cloudflare import BASE_URL, get_dns_record, update_dns_record
from cloudflare_ddns.config import Config


@pytest.fixture()
def cfg():
    return Config(
        api_token="test-token-abc123",
        zone_id="zone-id-xyz789",
        record_name="home.example.com",
        record_type="A",
    )


# ---------------------------------------------------------------------------
# get_dns_record
# ---------------------------------------------------------------------------

class TestGetDnsRecordSuccess:
    """Tests for successful DNS record retrieval."""

    @responses.activate
    def test_returns_record_id_and_content(self, cfg, cloudflare_record_response):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json=cloudflare_record_response,
            status=200,
        )
        record_id, content = get_dns_record(cfg)
        assert record_id == "record-id-001"
        assert content == "1.2.3.4"

    @responses.activate
    def test_sends_correct_auth_header(self, cfg, cloudflare_record_response):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json=cloudflare_record_response,
            status=200,
        )
        get_dns_record(cfg)
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"

    @responses.activate
    def test_sends_correct_query_params(self, cfg, cloudflare_record_response):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json=cloudflare_record_response,
            status=200,
        )
        get_dns_record(cfg)
        assert "type=A" in responses.calls[0].request.url
        assert "name=home.example.com" in responses.calls[0].request.url


class TestGetDnsRecordErrors:
    """Tests for DNS record retrieval error handling."""

    @responses.activate
    def test_empty_result_raises_runtime_error(self, cfg):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={"success": True, "errors": [], "result": []},
            status=200,
        )
        with pytest.raises(RuntimeError, match="No DNS record found"):
            get_dns_record(cfg)

    @responses.activate
    def test_success_false_raises_runtime_error_with_messages(self, cfg):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={
                "success": False,
                "errors": [{"code": 9999, "message": "Authentication error"}],
                "result": [],
            },
            status=200,
        )
        with pytest.raises(RuntimeError, match="Authentication error"):
            get_dns_record(cfg)

    @responses.activate
    def test_success_false_multiple_errors(self, cfg):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={
                "success": False,
                "errors": [
                    {"message": "Error one"},
                    {"message": "Error two"},
                ],
                "result": [],
            },
            status=200,
        )
        with pytest.raises(RuntimeError, match="Error one.*Error two"):
            get_dns_record(cfg)

    @responses.activate
    def test_http_401_raises_http_error(self, cfg):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={"success": False, "errors": [{"message": "Unauthorized"}]},
            status=401,
        )
        with pytest.raises(requests.HTTPError):
            get_dns_record(cfg)

    @responses.activate
    def test_http_500_raises_http_error(self, cfg):
        responses.add(
            responses.GET,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records",
            json={"success": False, "errors": [{"message": "Server Error"}]},
            status=500,
        )
        with pytest.raises(requests.HTTPError):
            get_dns_record(cfg)


# ---------------------------------------------------------------------------
# update_dns_record
# ---------------------------------------------------------------------------

class TestUpdateDnsRecordSuccess:
    """Tests for successful DNS record updates."""

    @responses.activate
    def test_successful_update(self, cfg, cloudflare_update_response):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json=cloudflare_update_response,
            status=200,
        )
        # Should not raise
        update_dns_record(cfg, "record-id-001", "5.6.7.8")

    @responses.activate
    def test_sends_correct_payload(self, cfg, cloudflare_update_response):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json=cloudflare_update_response,
            status=200,
        )
        update_dns_record(cfg, "record-id-001", "5.6.7.8")

        sent_body = json.loads(responses.calls[0].request.body)
        assert sent_body == {
            "type": "A",
            "name": "home.example.com",
            "content": "5.6.7.8",
            "ttl": 1,
            "proxied": False,
        }

    @responses.activate
    def test_sends_correct_auth_header(self, cfg, cloudflare_update_response):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json=cloudflare_update_response,
            status=200,
        )
        update_dns_record(cfg, "record-id-001", "5.6.7.8")
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


class TestUpdateDnsRecordErrors:
    """Tests for DNS record update error handling."""

    @responses.activate
    def test_success_false_raises_runtime_error(self, cfg):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json={
                "success": False,
                "errors": [{"message": "Validation failed"}],
                "result": None,
            },
            status=200,
        )
        with pytest.raises(RuntimeError, match="Validation failed"):
            update_dns_record(cfg, "record-id-001", "5.6.7.8")

    @responses.activate
    def test_http_error_raises_http_error(self, cfg):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json={"success": False, "errors": [{"message": "Server Error"}]},
            status=500,
        )
        with pytest.raises(requests.HTTPError):
            update_dns_record(cfg, "record-id-001", "5.6.7.8")

    @responses.activate
    def test_http_403_raises_http_error(self, cfg):
        responses.add(
            responses.PUT,
            f"{BASE_URL}/zones/{cfg.zone_id}/dns_records/record-id-001",
            json={"success": False, "errors": [{"message": "Forbidden"}]},
            status=403,
        )
        with pytest.raises(requests.HTTPError):
            update_dns_record(cfg, "record-id-001", "5.6.7.8")
