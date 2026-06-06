"""Story graph and asset validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from story_export.loader import collect_asset_manifest
from story_export.models import ValidationIssue


def validate_story_dir(story_dir: Path) -> list[ValidationIssue]:
    """Validate a story directory and its story.json graph."""

    issues: list[ValidationIssue] = []
    if not story_dir.is_dir():
        return [ValidationIssue("ERROR", f"Directory not found: {story_dir}", str(story_dir))]

    story_json_path = story_dir / "story.json"
    if not story_json_path.exists():
        return [
            ValidationIssue(
                "ERROR",
                f"story.json not found in {story_dir}",
                str(story_json_path),
            )
        ]

    try:
        with story_json_path.open(encoding="utf-8") as f:
            story_data = json.load(f)
    except json.JSONDecodeError as e:
        return [
            ValidationIssue(
                "ERROR",
                f"story.json is not valid JSON: {e}",
                str(story_json_path),
            )
        ]

    issues.extend(validate_story_data(story_data))
    issues.extend(validate_assets(story_dir, story_data))
    return issues


def validate_story_data(story_data: dict[str, Any]) -> list[ValidationIssue]:
    """Validate source story graph structure and references."""

    issues: list[ValidationIssue] = []
    if not isinstance(story_data, dict):
        return [ValidationIssue("ERROR", "story.json must contain a JSON object")]

    if story_data.get("format") != "v1":
        issues.append(ValidationIssue("ERROR", 'story.json format must be "v1"'))

    stage_nodes = story_data.get("stageNodes")
    action_nodes = story_data.get("actionNodes")
    if not isinstance(stage_nodes, list) or not stage_nodes:
        issues.append(ValidationIssue("ERROR", "stageNodes must be a non-empty array"))
        stage_nodes = []
    if not isinstance(action_nodes, list):
        issues.append(ValidationIssue("ERROR", "actionNodes must be an array"))
        action_nodes = []

    stage_ids = _collect_ids(stage_nodes, "uuid", "stageNodes", issues)
    action_ids = _collect_ids(action_nodes, "id", "actionNodes", issues)
    action_by_id = {
        action.get("id"): action
        for action in action_nodes
        if isinstance(action, dict) and action.get("id")
    }

    square_one_indexes = [
        idx
        for idx, stage in enumerate(stage_nodes)
        if isinstance(stage, dict) and stage.get("squareOne") is True
    ]
    if len(square_one_indexes) != 1:
        issues.append(
            ValidationIssue(
                "ERROR",
                f"Exactly one stage node must have squareOne=true; found {len(square_one_indexes)}",
            )
        )
    elif square_one_indexes[0] != 0:
        issues.append(ValidationIssue("ERROR", "The squareOne stage must be first"))

    referenced_actions: set[str] = set()
    for stage in stage_nodes:
        if not isinstance(stage, dict):
            continue
        for transition_key in ("okTransition", "homeTransition"):
            transition = stage.get(transition_key)
            if transition is None:
                continue
            if not isinstance(transition, dict):
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        f"{stage.get('uuid', '<unknown>')}.{transition_key} must be null or an object",
                    )
                )
                continue
            _validate_transition(
                stage,
                transition_key,
                transition,
                action_by_id,
                action_ids,
                issues,
                referenced_actions,
            )

    for action in action_nodes:
        if not isinstance(action, dict):
            continue
        action_id = action.get("id", "<unknown>")
        options = action.get("options")
        if not isinstance(options, list) or not options:
            issues.append(
                ValidationIssue("ERROR", f"Action {action_id} must have non-empty options")
            )
            continue
        for option in options:
            if option not in stage_ids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        f"Action {action_id} references missing stage option {option}",
                    )
                )

    for action_id in sorted(action_ids - referenced_actions):
        issues.append(
            ValidationIssue(
                "WARNING",
                f"Action {action_id} is not referenced by any stage transition",
            )
        )

    issues.extend(_validate_reachability(stage_nodes, action_by_id))
    return issues


def validate_assets(story_dir: Path, story_data: dict[str, Any]) -> list[ValidationIssue]:
    """Validate that referenced assets exist and are not empty."""

    assets_dir = story_dir / "assets"
    manifest = collect_asset_manifest(story_data)
    issues: list[ValidationIssue] = []
    if manifest.all_assets and not assets_dir.is_dir():
        return [
            ValidationIssue(
                "ERROR",
                f"assets/ directory not found in {story_dir}",
                str(assets_dir),
            )
        ]

    for filename in sorted(manifest.all_assets):
        path = assets_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    f"Missing or empty referenced asset: {filename}",
                    str(path),
                )
            )
    return issues


def _collect_ids(
    nodes: list[Any],
    key: str,
    collection_name: str,
    issues: list[ValidationIssue],
) -> set[str]:
    ids: set[str] = set()
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(
                ValidationIssue("ERROR", f"{collection_name}[{idx}] must be an object")
            )
            continue
        value = node.get(key)
        if not value:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    f"{collection_name}[{idx}] must contain a non-empty {key}",
                )
            )
            continue
        if value in ids:
            issues.append(
                ValidationIssue("ERROR", f"Duplicate {collection_name} {key}: {value}")
            )
        ids.add(value)
    return ids


def _validate_transition(
    stage: dict[str, Any],
    transition_key: str,
    transition: dict[str, Any],
    action_by_id: dict[str, dict[str, Any]],
    action_ids: set[str],
    issues: list[ValidationIssue],
    referenced_actions: set[str],
) -> None:
    stage_id = stage.get("uuid", "<unknown>")
    action_id = transition.get("actionNode")
    if action_id not in action_ids:
        issues.append(
            ValidationIssue(
                "ERROR",
                f"Stage {stage_id} {transition_key} references missing action {action_id}",
            )
        )
        return

    referenced_actions.add(action_id)
    option_index = transition.get("optionIndex")
    if not isinstance(option_index, int):
        issues.append(
            ValidationIssue(
                "ERROR",
                f"Stage {stage_id} {transition_key} optionIndex must be an integer",
            )
        )
        return
    if option_index == -1:
        return

    options = action_by_id.get(action_id, {}).get("options", [])
    if isinstance(options, list) and not 0 <= option_index < len(options):
        issues.append(
            ValidationIssue(
                "ERROR",
                f"Stage {stage_id} {transition_key} optionIndex {option_index} is out of bounds for {action_id}",
            )
        )


def _validate_reachability(
    stage_nodes: list[Any], action_by_id: dict[str, dict[str, Any]]
) -> list[ValidationIssue]:
    if not stage_nodes:
        return []
    square_one = next(
        (
            stage.get("uuid")
            for stage in stage_nodes
            if isinstance(stage, dict) and stage.get("squareOne") is True
        ),
        None,
    )
    if not square_one:
        return []

    stage_ids = {
        stage.get("uuid")
        for stage in stage_nodes
        if isinstance(stage, dict) and stage.get("uuid")
    }
    by_id = {
        stage.get("uuid"): stage
        for stage in stage_nodes
        if isinstance(stage, dict) and stage.get("uuid")
    }
    reachable: set[str] = set()
    stack = [square_one]
    while stack:
        stage_id = stack.pop()
        if stage_id in reachable or stage_id not in by_id:
            continue
        reachable.add(stage_id)
        stage = by_id[stage_id]
        for transition_key in ("okTransition", "homeTransition"):
            transition = stage.get(transition_key)
            if not isinstance(transition, dict):
                continue
            action = action_by_id.get(transition.get("actionNode"))
            if not action:
                continue
            options = action.get("options", [])
            if isinstance(options, list):
                stack.extend(option for option in options if option in stage_ids)

    return [
        ValidationIssue("WARNING", f"Stage {stage_id} is not reachable from squareOne")
        for stage_id in sorted(stage_ids - reachable)
    ]
