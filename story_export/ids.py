"""Stable story ID conversion helpers."""

from __future__ import annotations

import uuid

KIDSTORY_NAMESPACE = uuid.UUID("d4e8c2f1-7a3b-4e5d-9c1f-2b8a6d4e0f3c")


def is_valid_uuid(value: str) -> bool:
    """Check whether a string is a valid UUID."""

    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def slug_to_uuid(slug: str) -> str:
    """Convert a slug ID to a deterministic UUID v5."""

    if is_valid_uuid(slug):
        return slug
    return str(uuid.uuid5(KIDSTORY_NAMESPACE, slug))
