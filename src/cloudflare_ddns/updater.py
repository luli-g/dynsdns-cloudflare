"""Core update orchestration logic."""

import logging

import requests

from cloudflare_ddns.cloudflare import get_dns_record, update_dns_record
from cloudflare_ddns.ip_resolver import get_public_ip

logger = logging.getLogger(__name__)


def run_update(config) -> bool:
    try:
        logger.info("Starting IP check")

        current_ip = get_public_ip(config.record_type)
        logger.info("Current IP: %s", current_ip)

        record_id, existing_ip = get_dns_record(config)
        logger.info("Existing IP: %s", existing_ip)

        if current_ip != existing_ip:
            update_dns_record(config, record_id, current_ip)
            logger.info("IP updated from %s to %s", existing_ip, current_ip)
        else:
            logger.info("No IP change detected")

        return True

    except requests.RequestException as exc:
        logger.error("Request failed: %s", exc)
        return False

    except (RuntimeError, ValueError) as exc:
        logger.error("Update failed: %s", exc)
        return False
