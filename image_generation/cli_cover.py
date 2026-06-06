"""CLI for cover image generation."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from image_generation.cli_common import setup_logging
from image_generation.cover import generate_cover


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pixel art cover images for story chapters using Gemini Flash 2.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("description", help="Description of the chapter cover image")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output file path for the BMP image",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    output_path: Path = args.output
    if output_path.suffix.lower() != ".bmp":
        output_path = output_path.with_suffix(".bmp")
        logging.warning("Output path changed to: %s", output_path)

    try:
        bmp_data = generate_cover(args.description, output_path)
        logging.info("Cover image saved to: %s", output_path)
        logging.info("File size: %s bytes", f"{len(bmp_data):,}")
    except Exception as e:
        logging.error("Failed to generate cover: %s", e)
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
