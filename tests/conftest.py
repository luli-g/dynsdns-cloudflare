"""Shared test fixtures."""

import pytest

from cloudflare_ddns.config import Config


@pytest.fixture()
def env_vars(monkeypatch):
    """Set the required environment variables for config loading."""
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-token-abc123")
    monkeypatch.setenv("ZONE_ID", "zone-id-xyz789")
    monkeypatch.setenv("RECORD_NAME", "home.example.com")
    # Clear optional vars so tests start from a clean state
    monkeypatch.delenv("RECORD_TYPE", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)


@pytest.fixture()
def config():
    """Return a Config object with sensible test defaults."""
    return Config(
        api_token="test-token-abc123",
        zone_id="zone-id-xyz789",
        record_name="home.example.com",
        record_type="A",
        log_file=None,
        log_level="INFO",
    )


@pytest.fixture()
def cloudflare_record_response():
    """Return a standard Cloudflare DNS record API success response."""
    return {
        "success": True,
        "errors": [],
        "messages": [],
        "result": [
            {
                "id": "record-id-001",
                "type": "A",
                "name": "home.example.com",
                "content": "1.2.3.4",
                "ttl": 1,
                "proxied": False,
            }
        ],
    }


@pytest.fixture()
def cloudflare_update_response():
    """Return a standard Cloudflare DNS update success response."""
    return {
        "success": True,
        "errors": [],
        "messages": [],
        "result": {
            "id": "record-id-001",
            "type": "A",
            "name": "home.example.com",
            "content": "5.6.7.8",
            "ttl": 1,
            "proxied": False,
        },
    }
