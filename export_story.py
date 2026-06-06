#!/usr/bin/env python3
"""Backward-compatible wrapper for Lunii story export."""

from story_export.cli import main
from story_export.ids import KIDSTORY_NAMESPACE, is_valid_uuid, slug_to_uuid
from story_export.service import export_story, validate_story
from story_export.transformer import transform_story_for_device
from story_export.utils import slugify


if __name__ == "__main__":
    main()
