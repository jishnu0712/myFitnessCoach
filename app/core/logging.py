"""Configure consistent application-wide logging without sensitive payloads."""

import logging


def configure_logging(level: str) -> None:
    """Set a predictable timestamped log format and the configured root level."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
