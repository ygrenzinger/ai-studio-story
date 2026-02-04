"""Logging configuration for audio generation."""

import logging


def setup_logging(debug: bool = False) -> None:
    """Configure logging based on debug flag.

    Args:
        debug: If True, enable DEBUG level logging
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
