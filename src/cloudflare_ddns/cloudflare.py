"""Cloudflare API client."""

import requests

BASE_URL = "https://api.cloudflare.com/client/v4"
TIMEOUT = 10


def _headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }


def get_dns_record(config) -> tuple[str, str]:
    response = requests.get(
        f"{BASE_URL}/zones/{config.zone_id}/dns_records",
        params={"type": config.record_type, "name": config.record_name},
        headers=_headers(config.api_token),
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("success"):
        errors = data.get("errors", [])
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        raise RuntimeError(f"Cloudflare API error: {messages}")

    result = data.get("result", [])
    if not result:
        raise RuntimeError(
            f"No DNS record found for {config.record_name} "
            f"(type {config.record_type}) in zone {config.zone_id}"
        )

    return result[0]["id"], result[0]["content"]


def update_dns_record(config, record_id: str, new_ip: str) -> None:
    response = requests.put(
        f"{BASE_URL}/zones/{config.zone_id}/dns_records/{record_id}",
        headers=_headers(config.api_token),
        json={
            "type": config.record_type,
            "name": config.record_name,
            "content": new_ip,
            "ttl": 1,
            "proxied": False,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("success"):
        errors = data.get("errors", [])
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        raise RuntimeError(f"Cloudflare API error: {messages}")
