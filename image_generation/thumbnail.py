"""Thumbnail image generation pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from image_generation.config import VertexImageConfig
from image_generation.prompts import THUMBNAIL_SYSTEM_PROMPT
from image_generation.provider import GeminiImageProvider, ImageProvider

IMAGE_SIZE = 300


def build_thumbnail_prompt(description: str) -> str:
    """Build the complete thumbnail-generation prompt."""

    return (
        f"{THUMBNAIL_SYSTEM_PROMPT}\n\n"
        f"STORY DESCRIPTION TO ILLUSTRATE:\n{description}"
    )


def process_thumbnail_image(image: Image.Image) -> Image.Image:
    """Resize and convert an image to a 300x300 RGBA thumbnail."""

    logging.info("Processing image: original size %s, mode %s", image.size, image.mode)
    if image.size != (IMAGE_SIZE, IMAGE_SIZE):
        logging.info("Resizing to %sx%s...", IMAGE_SIZE, IMAGE_SIZE)
        image = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
    if image.mode != "RGBA":
        logging.info("Converting from %s to RGBA...", image.mode)
        image = image.convert("RGBA")
    logging.info("Processed image: size %s, mode %s", image.size, image.mode)
    return image


def generate_thumbnail(
    description: str,
    output_path: Path,
    *,
    config: VertexImageConfig | None = None,
    provider: ImageProvider | None = None,
) -> Path:
    """Generate and save a 300x300 story thumbnail PNG."""

    if provider is None:
        config = config or VertexImageConfig.from_env()
        provider = GeminiImageProvider(config)
    logging.info("Generating thumbnail for: %s...", description[:80])
    raw_image = provider.generate_image(build_thumbnail_prompt(description))
    processed_image = process_thumbnail_image(raw_image)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_image.save(output_path, format="PNG")
    return output_path
