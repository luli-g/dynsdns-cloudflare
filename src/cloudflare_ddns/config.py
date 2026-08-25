"""Configuration loading and validation."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

VALID_RECORD_TYPES = {"A", "AAAA"}
VALID_LOG_LEVELS = {
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
}


@dataclass(frozen=True)
class Config:
    api_token: str
    zone_id: str
    record_name: str
    record_type: str = "A"
    log_file: str | None = None
    log_level: str = "INFO"


def load_config() -> Config:
    load_dotenv(override=False)

    required = {
        "CLOUDFLARE_API_TOKEN": "api_token",
        "ZONE_ID": "zone_id",
        "RECORD_NAME": "record_name",
    }

    missing = [
        name for name in required if not os.environ.get(name, "").strip()
    ]
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    record_type = os.environ.get("RECORD_TYPE", "A").strip().upper()
    if record_type not in VALID_RECORD_TYPES:
        raise SystemExit(
            f"Invalid RECORD_TYPE '{record_type}': must be one of {', '.join(sorted(VALID_RECORD_TYPES))}"
        )

    log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    if log_level not in VALID_LOG_LEVELS:
        raise SystemExit(
            f"Invalid LOG_LEVEL '{log_level}': must be one of {', '.join(sorted(VALID_LOG_LEVELS))}"
        )

    log_file = os.environ.get("LOG_FILE", "").strip() or None

    return Config(
        api_token=os.environ["CLOUDFLARE_API_TOKEN"].strip(),
        zone_id=os.environ["ZONE_ID"].strip(),
        record_name=os.environ["RECORD_NAME"].strip(),
        record_type=record_type,
        log_file=log_file,
        log_level=log_level,
    )
