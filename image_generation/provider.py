"""Image provider protocol and Gemini implementation."""

from __future__ import annotations

import io
import logging
from typing import Protocol

from PIL import Image

from image_generation.config import VertexImageConfig


class ImageProvider(Protocol):
    """Provider capable of generating a PIL image from a text prompt."""

    def generate_image(self, prompt: str) -> Image.Image:
        """Generate an image from a complete prompt."""


class GeminiImageProvider:
    """Gemini image provider using Vertex AI."""

    def __init__(self, config: VertexImageConfig):
        self._config = config

    def generate_image(self, prompt: str) -> Image.Image:
        from google import genai
        from google.genai import types

        logging.info(
            "Connecting to Vertex AI (project=%s, location=%s)...",
            self._config.project,
            self._config.location,
        )
        client = genai.Client(
            vertexai=True,
            project=self._config.project,
            location=self._config.location,
        )

        logging.debug("Image prompt: %s...", prompt[:200])
        response = client.models.generate_content(
            model=self._config.model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                logging.info("Image generated successfully")
                return Image.open(io.BytesIO(part.inline_data.data))

        raise RuntimeError("No image was generated in the response")
