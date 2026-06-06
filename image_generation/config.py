"""Configuration helpers for image generation providers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VertexImageConfig:
    """Vertex AI image generation configuration."""

    project: str
    location: str = "europe-west1"
    model: str = "gemini-2.5-flash-image"

    @classmethod
    def from_env(cls) -> "VertexImageConfig":
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable is not set. "
                "Set it to your Google Cloud project ID."
            )
        return cls(
            project=project,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1"),
        )
