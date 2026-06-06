"""Tests for story validation and export."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from story_export import (
    export_story,
    is_valid_uuid,
    slug_to_uuid,
    transform_story_for_device,
    validate_story,
)
from story_export.validator import validate_story_data


def _valid_story_data() -> dict:
    return {
        "format": "v1",
        "title": "Test Story",
        "stageNodes": [
            {
                "uuid": "stage-cover",
                "squareOne": True,
                "image": "cover.bmp",
                "audio": "cover.mp3",
                "okTransition": {"actionNode": "action-start", "optionIndex": 0},
                "homeTransition": None,
            },
            {
                "uuid": "stage-ending",
                "image": "ending.bmp",
                "audio": "ending.mp3",
                "okTransition": None,
                "homeTransition": None,
            },
        ],
        "actionNodes": [
            {
                "id": "action-start",
                "options": ["stage-ending"],
            }
        ],
    }


def _write_story_dir(tmp_path: Path, story_data: dict | None = None) -> Path:
    story_dir = tmp_path / "story"
    assets_dir = story_dir / "assets"
    src_dir = story_dir / "src"
    assets_dir.mkdir(parents=True)
    src_dir.mkdir()
    data = story_data or _valid_story_data()
    (story_dir / "story.json").write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )
    (src_dir / "metadata.json").write_text(
        json.dumps({"title": "Le Test Étoilé"}, ensure_ascii=False),
        encoding="utf-8",
    )
    for filename in ("cover.bmp", "ending.bmp", "cover.mp3", "ending.mp3"):
        (assets_dir / filename).write_bytes(b"asset")
    (story_dir / "thumbnail.png").write_bytes(b"thumbnail")
    return story_dir


def test_slug_to_uuid_is_deterministic_and_preserves_uuid():
    converted = slug_to_uuid("stage-cover")

    assert is_valid_uuid(converted)
    assert slug_to_uuid("stage-cover") == converted
    assert slug_to_uuid(converted) == converted


def test_transform_story_for_device_converts_ids_without_mutating_source():
    story_data = _valid_story_data()

    transformed = transform_story_for_device(story_data)

    assert story_data["stageNodes"][0]["uuid"] == "stage-cover"
    assert is_valid_uuid(transformed["stageNodes"][0]["uuid"])
    assert is_valid_uuid(transformed["actionNodes"][0]["id"])
    assert transformed["stageNodes"][0]["okTransition"]["actionNode"] == transformed[
        "actionNodes"
    ][0]["id"]
    assert transformed["actionNodes"][0]["options"][0] == transformed["stageNodes"][1][
        "uuid"
    ]


def test_validate_story_data_reports_missing_action_reference():
    story_data = _valid_story_data()
    story_data["stageNodes"][0]["okTransition"]["actionNode"] = "missing-action"

    issues = validate_story_data(story_data)

    assert any(issue.is_error for issue in issues)
    assert any("missing action" in issue.message for issue in issues)


def test_validate_story_reports_missing_asset(tmp_path: Path):
    story_dir = _write_story_dir(tmp_path)
    (story_dir / "assets" / "ending.mp3").unlink()

    issues = validate_story(story_dir)

    assert any(issue.is_error for issue in issues)
    assert any("ending.mp3" in issue.message for issue in issues)


def test_export_story_writes_device_archive(tmp_path: Path):
    story_dir = _write_story_dir(tmp_path)

    result = export_story(story_dir)

    assert result.zip_path.name == "le-test-etoile.zip"
    assert result.pack_uuid == slug_to_uuid("stage-cover")
    assert result.has_thumbnail
    with zipfile.ZipFile(result.zip_path) as archive:
        names = set(archive.namelist())
        assert "story.json" in names
        assert "thumbnail.png" in names
        assert "assets/cover.bmp" in names
        assert "assets/ending.mp3" in names
        device_story = json.loads(archive.read("story.json"))
    assert is_valid_uuid(device_story["stageNodes"][0]["uuid"])
    assert is_valid_uuid(device_story["actionNodes"][0]["id"])
