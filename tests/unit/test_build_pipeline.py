"""Tests for the deterministic KidStory build pipeline."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from story_export.pipeline import build_story, create_build_plan


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _story_data() -> dict:
    return {
        "format": "v1",
        "title": "Test Pack",
        "stageNodes": [
            {
                "uuid": "stage-cover-test-pack",
                "squareOne": True,
                "image": "cover.bmp",
                "audio": "cover-welcome.mp3",
                "okTransition": {"actionNode": "action-menu", "optionIndex": 0},
                "homeTransition": None,
            },
            {
                "uuid": "stage-hub-menu",
                "image": "hub-menu.bmp",
                "audio": "hub-menu.mp3",
                "okTransition": {"actionNode": "action-story", "optionIndex": 0},
                "homeTransition": None,
            },
            {
                "uuid": "stage-story-01-egypte",
                "name": "Histoire 1 - Egypte",
                "image": "story-01-egypte.bmp",
                "audio": "story-01-egypte.mp3",
                "okTransition": {"actionNode": "action-story-two", "optionIndex": 0},
                "homeTransition": None,
            },
            {
                "uuid": "stage-story-02-maroc",
                "name": "Histoire 2 - Maroc",
                "image": "story-02-maroc.bmp",
                "audio": "story-02-maroc.mp3",
                "okTransition": None,
                "homeTransition": None,
            },
        ],
        "actionNodes": [
            {"id": "action-menu", "options": ["stage-hub-menu"]},
            {"id": "action-story", "options": ["stage-story-01-egypte"]},
            {"id": "action-story-two", "options": ["stage-story-02-maroc"]},
        ],
    }


def _write_pack_sources(story_dir: Path) -> None:
    _write_json(
        story_dir / "src" / "metadata.json",
        {
            "type": "pack",
            "title": "Test Pack",
            "description": "A geography pack",
            "stories": [
                {"id": "01-01-egypte", "title": "L Egypte"},
                {"id": "01-02-maroc", "title": "Le Maroc"},
            ],
            "themes": ["geography"],
        },
    )
    (story_dir / "src" / "hub").mkdir(parents=True, exist_ok=True)
    (story_dir / "src" / "hub" / "cover-welcome.md").write_text("Welcome", encoding="utf-8")
    (story_dir / "src" / "hub" / "menu.md").write_text("Menu", encoding="utf-8")
    story_source = story_dir / "src" / "stories" / "01-01-egypte"
    story_source.mkdir(parents=True, exist_ok=True)
    (story_source / "chapter.md").write_text("The Nile shines.", encoding="utf-8")
    (story_source / "audio-script.md").write_text("Narrator: The Nile shines.", encoding="utf-8")
    story_source = story_dir / "src" / "stories" / "01-02-maroc"
    story_source.mkdir(parents=True, exist_ok=True)
    (story_source / "chapter.md").write_text("The atlas opens.", encoding="utf-8")
    (story_source / "audio-script.md").write_text("Narrator: The atlas opens.", encoding="utf-8")
    _write_json(story_dir / "story.json", _story_data())


def test_create_build_plan_maps_pack_sources(tmp_path: Path) -> None:
    story_dir = tmp_path / "test-pack"
    _write_pack_sources(story_dir)

    plan = create_build_plan(story_dir)

    assert not [issue for issue in plan.issues if issue.is_error]
    assert {task.filename for task in plan.image_tasks} == {
        "cover.bmp",
        "hub-menu.bmp",
        "story-01-egypte.bmp",
        "story-02-maroc.bmp",
    }
    assert {
        task.filename: task.source_path.relative_to(story_dir).as_posix()
        for task in plan.audio_tasks
    } == {
        "cover-welcome.mp3": "src/hub/cover-welcome.md",
        "hub-menu.mp3": "src/hub/menu.md",
        "story-01-egypte.mp3": "src/stories/01-01-egypte/audio-script.md",
        "story-02-maroc.mp3": "src/stories/01-02-maroc/audio-script.md",
    }


def test_create_build_plan_reports_missing_audio_source(tmp_path: Path) -> None:
    story_dir = tmp_path / "test-pack"
    _write_pack_sources(story_dir)
    (story_dir / "src" / "stories" / "01-01-egypte" / "audio-script.md").unlink()

    plan = create_build_plan(story_dir)

    errors = [issue.message for issue in plan.issues if issue.is_error]
    assert any("story-01-egypte.mp3" in message for message in errors)


def test_build_story_generates_missing_assets_with_runner(tmp_path: Path) -> None:
    story_dir = tmp_path / "test-pack"
    _write_pack_sources(story_dir)
    commands: list[list[str]] = []

    def runner(command):
        commands.append(list(command))
        output = Path(command[command.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"generated")
        return subprocess.CompletedProcess(command, 0)

    summary = build_story(story_dir, runner=runner, skip_export=True)

    assert summary.generated_images == 4
    assert summary.generated_audio == 4
    assert summary.generated_thumbnail
    assert len(commands) == 9
    assert all((story_dir / "assets" / name).exists() for name in [
        "cover.bmp",
        "hub-menu.bmp",
        "story-01-egypte.bmp",
        "story-02-maroc.bmp",
        "cover-welcome.mp3",
        "hub-menu.mp3",
        "story-01-egypte.mp3",
        "story-02-maroc.mp3",
    ])
