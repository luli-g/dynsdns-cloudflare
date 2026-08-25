"""Public IP detection."""

import ipaddress

import requests

ENDPOINTS = {
    "A": "https://ipv4.icanhazip.com",
    "AAAA": "https://ipv6.icanhazip.com",
}

VALIDATORS = {
    "A": ipaddress.IPv4Address,
    "AAAA": ipaddress.IPv6Address,
}

TIMEOUT = 10


def get_public_ip(record_type: str) -> str:
    if record_type not in ENDPOINTS:
        raise ValueError(f"Unsupported record type: {record_type!r}. Must be 'A' or 'AAAA'.")

    response = requests.get(ENDPOINTS[record_type], timeout=TIMEOUT)
    response.raise_for_status()
    ip_text = response.text.strip()

    validator = VALIDATORS[record_type]
    try:
        validator(ip_text)
    except ValueError:
        raise ValueError(
            f"Invalid IP for record type {record_type!r}: {ip_text!r}"
        )

    return ip_text
