"""Story loading and asset manifest helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_export.models import AssetManifest


def load_story_data(story_dir: Path) -> dict[str, Any]:
    """Load a story.json file from a story directory."""

    story_json_path = story_dir / "story.json"
    with story_json_path.open(encoding="utf-8") as f:
        return json.load(f)


def load_story_title(story_dir: Path, story_data: dict[str, Any] | None = None) -> str:
    """Load the best available story title."""

    metadata_path = story_dir / "src" / "metadata.json"
    if not metadata_path.exists():
        metadata_path = story_dir / "metadata.json"

    if metadata_path.exists():
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata.get("title", story_dir.name)

    if story_data:
        return story_data.get("title", story_dir.name)
    return story_dir.name


def collect_asset_manifest(story_data: dict[str, Any]) -> AssetManifest:
    """Collect image and audio filenames referenced by stage nodes."""

    images: set[str] = set()
    audios: set[str] = set()
    for stage in story_data.get("stageNodes", []):
        if stage.get("image"):
            images.add(stage["image"])
        if stage.get("audio"):
            audios.add(stage["audio"])
    return AssetManifest(images=images, audios=audios)
