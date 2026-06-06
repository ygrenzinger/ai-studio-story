"""High-level story validation and export services."""

from __future__ import annotations

from pathlib import Path

from story_export.archive import write_archive
from story_export.loader import collect_asset_manifest, load_story_data, load_story_title
from story_export.models import ExportResult, ValidationIssue
from story_export.transformer import transform_story_for_device
from story_export.validator import validate_story_dir


def validate_story(story_dir: Path) -> list[ValidationIssue]:
    """Validate a story directory."""

    return validate_story_dir(story_dir)


def export_story(story_dir: Path, *, overwrite: bool = True) -> ExportResult:
    """Validate, transform, and export a story directory as a Lunii ZIP."""

    issues = validate_story(story_dir)
    errors = [issue for issue in issues if issue.is_error]
    if errors:
        detail = "\n".join(f"- {issue.path}: {issue.message}" for issue in errors)
        raise ValueError(f"Story validation failed:\n{detail}")

    story_data = load_story_data(story_dir)
    title = load_story_title(story_dir, story_data)
    manifest = collect_asset_manifest(story_data)
    device_story = transform_story_for_device(story_data)
    pack_uuid = device_story["stageNodes"][0]["uuid"]
    zip_path, has_thumbnail, used_thumbnail_fallback = write_archive(
        story_dir,
        title,
        device_story,
        manifest,
        overwrite=overwrite,
    )

    return ExportResult(
        zip_path=zip_path,
        pack_uuid=pack_uuid,
        archive_size=zip_path.stat().st_size,
        title=title,
        stage_count=len(story_data["stageNodes"]),
        action_count=len(story_data["actionNodes"]),
        manifest=manifest,
        has_thumbnail=has_thumbnail,
        used_thumbnail_fallback=used_thumbnail_fallback,
    )
