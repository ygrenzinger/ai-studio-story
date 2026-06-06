#!/usr/bin/env python3
"""Backward-compatible wrapper for story thumbnail image generation."""

from image_generation.cli_thumbnail import main
from image_generation.cli_common import setup_logging
from image_generation.config import VertexImageConfig
from image_generation.provider import GeminiImageProvider
from image_generation.prompts import THUMBNAIL_SYSTEM_PROMPT as SYSTEM_PROMPT
from image_generation.thumbnail import (
    IMAGE_SIZE,
    build_thumbnail_prompt,
    generate_thumbnail,
    process_thumbnail_image as process_image,
)


def get_vertex_ai_config() -> tuple[str, str]:
    """Return Vertex AI project/location from environment."""

    config = VertexImageConfig.from_env()
    return config.project, config.location


def generate_image_with_gemini(description: str, project: str, location: str):
    """Generate a raw image using Gemini via Vertex AI."""

    provider = GeminiImageProvider(VertexImageConfig(project=project, location=location))
    return provider.generate_image(build_thumbnail_prompt(description))


if __name__ == "__main__":
    main()
