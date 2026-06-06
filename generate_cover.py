#!/usr/bin/env python3
"""Backward-compatible wrapper for Lunii cover image generation."""

from image_generation.cli_cover import main
from image_generation.cli_common import setup_logging
from image_generation.config import VertexImageConfig
from image_generation.cover import (
    BI_RLE4,
    BMP_HEADER_SIZE,
    COLOR_DEPTH_BITS,
    DIB_HEADER_SIZE,
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    NUM_COLORS,
    PALETTE_SIZE,
    build_cover_prompt,
    create_bmp_rle4,
    encode_rle4,
    generate_cover,
    process_cover_image as process_image,
    verify_bmp_format,
)
from image_generation.provider import GeminiImageProvider
from image_generation.prompts import COVER_SYSTEM_PROMPT as SYSTEM_PROMPT


def get_vertex_ai_config() -> tuple[str, str]:
    """Return Vertex AI project/location from environment."""

    config = VertexImageConfig.from_env()
    return config.project, config.location


def generate_image_with_gemini(description: str, project: str, location: str):
    """Generate a raw image using Gemini via Vertex AI."""

    provider = GeminiImageProvider(VertexImageConfig(project=project, location=location))
    return provider.generate_image(build_cover_prompt(description))


if __name__ == "__main__":
    main()
