"""CLI for thumbnail image generation."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from image_generation.cli_common import setup_logging
from image_generation.thumbnail import generate_thumbnail


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate story thumbnail images using Gemini Flash 2.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("description", help="Description of the story thumbnail")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output file path for the PNG image",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    output_path: Path = args.output
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")
        logging.warning("Output path changed to: %s", output_path)

    try:
        saved_path = generate_thumbnail(args.description, output_path)
        file_size = saved_path.stat().st_size
        logging.info("Thumbnail saved to: %s", saved_path)
        logging.info("File size: %s bytes", f"{file_size:,}")
    except Exception as e:
        logging.error("Failed to generate thumbnail: %s", e)
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
