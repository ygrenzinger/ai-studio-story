"""Deterministic KidStory build pipeline."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from story_export.loader import collect_asset_manifest, load_story_data, load_story_title
from story_export.models import ExportResult, ValidationIssue
from story_export.service import export_story, validate_story
from story_export.utils import slugify
from story_export.validator import validate_story_data


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ImageTask:
    """A pending or skippable BMP generation task."""

    filename: str
    output_path: Path
    description: str


@dataclass(frozen=True)
class AudioTask:
    """A pending or skippable MP3 generation task."""

    filename: str
    source_path: Path
    output_path: Path


@dataclass(frozen=True)
class ThumbnailTask:
    """A pending or skippable thumbnail generation task."""

    output_path: Path
    description: str


@dataclass(frozen=True)
class BuildPlan:
    """Asset generation plan for a story directory."""

    story_dir: Path
    title: str
    image_tasks: list[ImageTask]
    audio_tasks: list[AudioTask]
    thumbnail_task: ThumbnailTask
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass(frozen=True)
class BuildSummary:
    """Result of a build pipeline run."""

    plan: BuildPlan
    generated_images: int = 0
    skipped_images: int = 0
    generated_audio: int = 0
    skipped_audio: int = 0
    generated_thumbnail: bool = False
    skipped_thumbnail: bool = False
    export_result: ExportResult | None = None
    dry_run: bool = False


class BuildPipelineError(RuntimeError):
    """Raised when a build phase cannot continue."""


def create_build_plan(story_dir: Path) -> BuildPlan:
    """Create a deterministic build plan without generating assets."""

    story_dir = story_dir.resolve()
    issues: list[ValidationIssue] = []
    if not story_dir.is_dir():
        return BuildPlan(
            story_dir=story_dir,
            title=story_dir.name,
            image_tasks=[],
            audio_tasks=[],
            thumbnail_task=ThumbnailTask(story_dir / "thumbnail.png", story_dir.name),
            issues=[
                ValidationIssue(
                    "ERROR",
                    f"Directory not found: {story_dir}",
                    str(story_dir),
                )
            ],
        )

    metadata = _load_metadata(story_dir, issues)
    try:
        story_data = load_story_data(story_dir)
    except FileNotFoundError:
        story_data = {}
        issues.append(
            ValidationIssue(
                "ERROR",
                "story.json not found",
                str(story_dir / "story.json"),
            )
        )
    except json.JSONDecodeError as exc:
        story_data = {}
        issues.append(
            ValidationIssue(
                "ERROR",
                f"story.json is not valid JSON: {exc}",
                str(story_dir / "story.json"),
            )
        )

    if story_data:
        issues.extend(validate_story_data(story_data))

    title = _metadata_text(metadata, "title") or (
        load_story_title(story_dir, story_data) if story_data else story_dir.name
    )
    manifest = collect_asset_manifest(story_data) if story_data else None
    assets_dir = story_dir / "assets"
    stages = story_data.get("stageNodes", []) if story_data else []

    image_tasks: list[ImageTask] = []
    audio_tasks: list[AudioTask] = []
    if manifest:
        for filename in sorted(manifest.images):
            stage = _find_stage_for_asset(stages, "image", filename)
            image_tasks.append(
                ImageTask(
                    filename=filename,
                    output_path=assets_dir / filename,
                    description=_image_description(story_dir, metadata, stage, filename),
                )
            )

        for filename in sorted(manifest.audios):
            stage = _find_stage_for_asset(stages, "audio", filename)
            source_path = _resolve_audio_source(story_dir, metadata, stage, filename)
            if source_path is None:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        f"No source audio script found for {filename}",
                        str(story_dir / "story.json"),
                    )
                )
                continue
            audio_tasks.append(
                AudioTask(
                    filename=filename,
                    source_path=source_path,
                    output_path=assets_dir / filename,
                )
            )

    thumbnail_task = ThumbnailTask(
        output_path=story_dir / "thumbnail.png",
        description=_thumbnail_description(metadata, title),
    )
    return BuildPlan(
        story_dir=story_dir,
        title=title,
        image_tasks=image_tasks,
        audio_tasks=audio_tasks,
        thumbnail_task=thumbnail_task,
        issues=issues,
    )


def build_story(
    story_dir: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_export: bool = False,
    runner: CommandRunner | None = None,
) -> BuildSummary:
    """Run the full build pipeline for a story directory."""

    plan = create_build_plan(story_dir)
    errors = [issue for issue in plan.issues if issue.is_error]
    if errors:
        detail = "\n".join(f"- {issue.path}: {issue.message}" for issue in errors)
        raise BuildPipelineError(f"Source validation failed:\n{detail}")

    if dry_run:
        return BuildSummary(plan=plan, dry_run=True)

    command_runner = runner or _run_command
    assets_dir = plan.story_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    generated_images = skipped_images = 0
    for task in plan.image_tasks:
        if task.output_path.exists() and task.output_path.stat().st_size > 0 and not force:
            skipped_images += 1
            continue
        command_runner(
            [
                "uv",
                "run",
                "python",
                "generate_cover.py",
                task.description,
                "-o",
                str(task.output_path),
            ]
        )
        generated_images += 1

    thumbnail = plan.thumbnail_task
    generated_thumbnail = False
    skipped_thumbnail = False
    if thumbnail.output_path.exists() and thumbnail.output_path.stat().st_size > 0 and not force:
        skipped_thumbnail = True
    else:
        command_runner(
            [
                "uv",
                "run",
                "python",
                "generate_thumbnail.py",
                thumbnail.description,
                "-o",
                str(thumbnail.output_path),
            ]
        )
        generated_thumbnail = True

    generated_audio = skipped_audio = 0
    for task in plan.audio_tasks:
        if task.output_path.exists() and task.output_path.stat().st_size > 0 and not force:
            skipped_audio += 1
            continue
        command_runner(
            [
                "uv",
                "run",
                "python",
                "generate_audio.py",
                str(task.source_path),
                "-o",
                str(task.output_path),
            ]
        )
        generated_audio += 1

    issues = validate_story(plan.story_dir)
    errors = [issue for issue in issues if issue.is_error]
    if errors:
        detail = "\n".join(f"- {issue.path}: {issue.message}" for issue in errors)
        raise BuildPipelineError(f"Final asset verification failed:\n{detail}")

    result = None if skip_export else export_story(plan.story_dir)
    return BuildSummary(
        plan=plan,
        generated_images=generated_images,
        skipped_images=skipped_images,
        generated_audio=generated_audio,
        skipped_audio=skipped_audio,
        generated_thumbnail=generated_thumbnail,
        skipped_thumbnail=skipped_thumbnail,
        export_result=result,
    )


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, text=True)
    if result.returncode != 0:
        raise BuildPipelineError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}"
        )
    return result


def _load_metadata(story_dir: Path, issues: list[ValidationIssue]) -> dict[str, Any]:
    metadata_path = story_dir / "src" / "metadata.json"
    if not metadata_path.exists():
        metadata_path = story_dir / "metadata.json"
    if not metadata_path.exists():
        issues.append(
            ValidationIssue(
                "ERROR",
                "metadata.json not found under src/ or story root",
                str(story_dir / "src" / "metadata.json"),
            )
        )
        return {}
    try:
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)
    except json.JSONDecodeError as exc:
        issues.append(
            ValidationIssue(
                "ERROR",
                f"metadata.json is not valid JSON: {exc}",
                str(metadata_path),
            )
        )
        return {}
    if not metadata.get("title"):
        issues.append(ValidationIssue("ERROR", "metadata.json must contain title", str(metadata_path)))
    if not metadata.get("type"):
        issues.append(ValidationIssue("ERROR", "metadata.json must contain type", str(metadata_path)))
    return metadata


def _find_stage_for_asset(
    stages: list[Any],
    field_name: str,
    filename: str,
) -> dict[str, Any]:
    for stage in stages:
        if isinstance(stage, dict) and stage.get(field_name) == filename:
            return stage
    return {}


def _resolve_audio_source(
    story_dir: Path,
    metadata: dict[str, Any],
    stage: dict[str, Any],
    filename: str,
) -> Path | None:
    src_dir = story_dir / "src"
    stem = Path(filename).stem
    hub_candidates = {
        stem,
        stem.removeprefix("hub-"),
    }
    for candidate in sorted(hub_candidates):
        path = src_dir / "hub" / f"{candidate}.md"
        if path.exists():
            return path

    script_dirs = [
        *(src_dir / "chapters").glob("*"),
        *(src_dir / "stories").glob("*"),
    ]
    script_dirs = sorted((path for path in script_dirs if path.is_dir()), key=lambda path: path.name)
    tokens = _asset_tokens(filename, stage)
    matched_story = _matching_metadata_item(metadata, tokens)
    if matched_story:
        story_id = matched_story.get("id")
        if isinstance(story_id, str):
            tokens.add(story_id)
        title = matched_story.get("title")
        if isinstance(title, str):
            tokens.add(slugify(title))

    for story in _metadata_stories(metadata):
        story_id = story.get("id")
        if isinstance(story_id, str) and _matches_any_token(story_id, tokens):
            tokens.add(story_id)
        title = story.get("title")
        if isinstance(title, str) and _matches_any_token(title, tokens):
            tokens.add(slugify(title))

    for directory in script_dirs:
        audio_script = directory / "audio-script.md"
        if audio_script.exists() and _matches_any_token(directory.name, tokens):
            return audio_script
    return None


def _image_description(
    story_dir: Path,
    metadata: dict[str, Any],
    stage: dict[str, Any],
    filename: str,
) -> str:
    title = _metadata_text(metadata, "title") or story_dir.name
    description = _metadata_text(metadata, "description")
    stem = Path(filename).stem
    stage_name = str(stage.get("name") or "")

    if stem == "cover":
        return _join_prompt(
            title,
            description,
            "Main Lunii cover image. Pixel art, high contrast, no text.",
        )
    if stem.startswith("hub-"):
        return _join_prompt(
            title,
            description,
            f"Hub menu scene for {stage_name or stem}. Pixel art, no text.",
        )

    story_source = _resolve_story_text_source(story_dir, metadata, stage, filename)
    if story_source:
        excerpt = _first_text_excerpt(story_source)
        return _join_prompt(stage_name, excerpt, "Pixel art cover image, no text.")

    matched = _matching_metadata_item(metadata, _asset_tokens(filename, stage))
    if matched:
        return _join_prompt(
            str(matched.get("title") or stage_name or stem),
            str(matched.get("description") or matched.get("theme") or matched.get("country") or ""),
            "Pixel art cover image, no text.",
        )

    return _join_prompt(title, stage_name or stem, "Pixel art cover image, no text.")


def _resolve_story_text_source(
    story_dir: Path,
    metadata: dict[str, Any],
    stage: dict[str, Any],
    filename: str,
) -> Path | None:
    src_dir = story_dir / "src"
    tokens = _asset_tokens(filename, stage)
    matched_story = _matching_metadata_item(metadata, tokens)
    if matched_story:
        story_id = matched_story.get("id")
        if isinstance(story_id, str):
            tokens.add(story_id)
        title = matched_story.get("title")
        if isinstance(title, str):
            tokens.add(slugify(title))

    for root in (src_dir / "chapters", src_dir / "stories"):
        for directory in sorted(root.glob("*"), key=lambda path: path.name):
            if not directory.is_dir() or not _matches_any_token(directory.name, tokens):
                continue
            chapter = directory / "chapter.md"
            if chapter.exists():
                return chapter
    return None


def _thumbnail_description(metadata: dict[str, Any], title: str) -> str:
    pieces = [title]
    for key in ("description", "tone", "language"):
        value = _metadata_text(metadata, key)
        if value:
            pieces.append(value)
    themes = metadata.get("themes")
    if isinstance(themes, list):
        pieces.append(", ".join(str(theme) for theme in themes[:5]))
    pieces.append("Colorful child-friendly story thumbnail, no text.")
    return _join_prompt(*pieces)


def _metadata_stories(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    stories = metadata.get("stories")
    if isinstance(stories, list):
        return [story for story in stories if isinstance(story, dict)]
    return []


def _matching_metadata_item(
    metadata: dict[str, Any],
    tokens: set[str],
) -> dict[str, Any] | None:
    for item in _metadata_stories(metadata):
        item_tokens = set()
        for key in ("id", "title", "country", "continent", "tradition"):
            value = item.get(key)
            if isinstance(value, str):
                item_tokens.add(value)
        if _matches_any_token(" ".join(item_tokens), tokens):
            return item
    return None


def _metadata_text(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) else ""


def _asset_tokens(filename: str, stage: dict[str, Any]) -> set[str]:
    raw = {
        Path(filename).stem,
        str(stage.get("uuid") or ""),
        str(stage.get("name") or ""),
    }
    tokens: set[str] = set()
    for value in raw:
        slug = slugify(value)
        if not slug:
            continue
        tokens.add(slug)
        tokens.add(slug.removeprefix("stage-"))
        tokens.add(slug.removeprefix("stage-story-"))
        tokens.add(slug.removeprefix("story-"))
        tokens.add(re.sub(r"^(story-)?\d+-", "", slug))
        tokens.add(re.sub(r"^(\d+-)+", "", slug))
    return {token for token in tokens if len(token) > 2}


def _matches_any_token(value: str, tokens: set[str]) -> bool:
    normalized = slugify(value)
    normalized_tail = re.sub(r"^(\d+-)+", "", normalized)
    for token in tokens:
        token = slugify(token)
        token_tail = re.sub(r"^(\d+-)+", "", token)
        if token == normalized or token_tail == normalized_tail:
            return True
        if len(token_tail) > 3 and token_tail in normalized:
            return True
        if len(normalized_tail) > 3 and normalized_tail in token:
            return True
    return False


def _first_text_excerpt(path: Path, *, max_chars: int = 500) -> str:
    text = path.read_text(encoding="utf-8")
    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip() and not paragraph.strip().startswith("---")
    ]
    if not paragraphs:
        return text.strip()[:max_chars]
    return paragraphs[0][:max_chars]


def _join_prompt(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())
