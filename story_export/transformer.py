"""Source story to device story transformations."""

from __future__ import annotations

import copy
from typing import Any

from story_export.ids import slug_to_uuid


def transform_story_for_device(story_data: dict[str, Any]) -> dict[str, Any]:
    """Convert source slug IDs to deterministic UUIDs for Lunii devices."""

    data = copy.deepcopy(story_data)
    id_map: dict[str, str] = {}

    for stage in data["stageNodes"]:
        old_id = stage["uuid"]
        id_map[old_id] = slug_to_uuid(old_id)
        group_id = stage.get("groupId")
        if group_id and group_id not in id_map:
            id_map[group_id] = slug_to_uuid(group_id)

    for action in data["actionNodes"]:
        old_id = action["id"]
        id_map[old_id] = slug_to_uuid(old_id)
        group_id = action.get("groupId")
        if group_id and group_id not in id_map:
            id_map[group_id] = slug_to_uuid(group_id)

    for stage in data["stageNodes"]:
        stage["uuid"] = id_map[stage["uuid"]]
        if stage.get("groupId") and stage["groupId"] in id_map:
            stage["groupId"] = id_map[stage["groupId"]]

        for transition_key in ("okTransition", "homeTransition"):
            transition = stage.get(transition_key)
            if transition and transition.get("actionNode") in id_map:
                transition["actionNode"] = id_map[transition["actionNode"]]

    for action in data["actionNodes"]:
        action["id"] = id_map[action["id"]]
        action["options"] = [id_map.get(option, option) for option in action["options"]]
        if action.get("groupId") and action["groupId"] in id_map:
            action["groupId"] = id_map[action["groupId"]]

    return data
