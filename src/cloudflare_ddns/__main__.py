"""CLI entry point."""

import logging
import sys

from cloudflare_ddns.config import load_config
from cloudflare_ddns.updater import run_update


def main() -> None:
    config = load_config()

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if config.log_file:
        try:
            handlers.append(logging.FileHandler(config.log_file))
        except OSError as exc:
            sys.exit(f"Cannot open log file '{config.log_file}': {exc}")

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=getattr(logging, config.log_level),
        handlers=handlers,
    )

    if not run_update(config):
        sys.exit(1)


if __name__ == "__main__":
    main()
