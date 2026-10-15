"""Logging setup for applications embedding The A Team."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure concise process-wide logging.

    Applications with an existing logging setup can skip this function.
    """

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
