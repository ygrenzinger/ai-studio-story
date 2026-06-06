"""Shared CLI helpers for image generation commands."""

import logging


def setup_logging(debug: bool) -> None:
    """Configure command logging."""

    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
