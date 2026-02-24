#!/usr/bin/env python3
"""
Generic export script for Lunii stories and packs.

Transforms source story.json (with human-readable slug IDs) into a
device-ready ZIP archive with valid UUIDs. Asset filenames are kept
human-readable.

Usage:
    uv run python export_story.py stories/victor-pays-du-sommeil
    uv run python export_story.py stories/aventure-spatiale
    uv run python export_story.py stories/explorateur-croyances
"""

import copy
import json
import sys
import unicodedata
import uuid
import re
import zipfile
from pathlib import Path

# Namespace UUID for deterministic slug-to-UUID conversion (UUID v5).
# This MUST remain stable — changing it changes all derived UUIDs.
KIDSTORY_NAMESPACE = uuid.UUID("d4e8c2f1-7a3b-4e5d-9c1f-2b8a6d4e0f3c")


def is_valid_uuid(s: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


def slug_to_uuid(slug: str) -> str:
    """Convert a slug ID to a deterministic UUID v5.

    If the slug is already a valid UUID, return it unchanged.
    Otherwise, derive a UUID v5 from the project namespace + slug.
    """
    if is_valid_uuid(slug):
        return slug
    return str(uuid.uuid5(KIDSTORY_NAMESPACE, slug))


def transform_story_for_device(story_data: dict) -> dict:
    """Transform source story.json into device-ready format.

    Replaces all slug IDs with deterministic UUIDs (v5) while
    keeping asset filenames unchanged (human-readable).

    The source story_data is NOT modified — a deep copy is used.
    """
    data = copy.deepcopy(story_data)

    # Phase 1: Build slug -> UUID mapping
    id_map: dict[str, str] = {}

    for stage in data["stageNodes"]:
        old_id = stage["uuid"]
        id_map[old_id] = slug_to_uuid(old_id)
        # Also map groupId if present and not already a UUID
        gid = stage.get("groupId")
        if gid and gid not in id_map:
            id_map[gid] = slug_to_uuid(gid)

    for action in data["actionNodes"]:
        old_id = action["id"]
        id_map[old_id] = slug_to_uuid(old_id)
        gid = action.get("groupId")
        if gid and gid not in id_map:
            id_map[gid] = slug_to_uuid(gid)

    # Phase 2: Apply ID mapping to stage nodes
    for stage in data["stageNodes"]:
        stage["uuid"] = id_map[stage["uuid"]]

        if stage.get("groupId") and stage["groupId"] in id_map:
            stage["groupId"] = id_map[stage["groupId"]]

        for trans_key in ("okTransition", "homeTransition"):
            trans = stage.get(trans_key)
            if trans and trans.get("actionNode") in id_map:
                trans["actionNode"] = id_map[trans["actionNode"]]

    # Phase 3: Apply ID mapping to action nodes
    for action in data["actionNodes"]:
        action["id"] = id_map[action["id"]]
        action["options"] = [id_map.get(opt, opt) for opt in action["options"]]
        if action.get("groupId") and action["groupId"] in id_map:
            action["groupId"] = id_map[action["groupId"]]

    return data


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Lowercase, strip accents/diacritics, replace spaces and special
    characters with hyphens, collapse consecutive hyphens, trim
    leading/trailing hyphens.
    """
    # Normalize unicode and strip diacritics
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Collapse consecutive hyphens and trim
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <story-directory>")
        print(f"Example: {sys.argv[0]} stories/victor-pays-du-sommeil")
        sys.exit(1)

    story_dir = Path(sys.argv[1])
    if not story_dir.is_dir():
        print(f"ERROR: Directory not found: {story_dir}")
        sys.exit(1)

    story_json_path = story_dir / "story.json"
    if not story_json_path.exists():
        print(f"ERROR: story.json not found in {story_dir}")
        sys.exit(1)

    assets_dir = story_dir / "assets"
    if not assets_dir.is_dir():
        print(f"ERROR: assets/ directory not found in {story_dir}")
        sys.exit(1)

    # Load metadata for title
    metadata_path = story_dir / "src" / "metadata.json"
    if not metadata_path.exists():
        # Fallback to root-level metadata
        metadata_path = story_dir / "metadata.json"

    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        title = metadata.get("title", story_dir.name)
    else:
        title = story_dir.name

    print("=" * 60)
    print(f"  Lunii Story Export: {title}")
    print("=" * 60)
    print()

    # Load story.json
    print("[1/4] Loading story.json...")
    with open(story_json_path) as f:
        story_data = json.load(f)

    stage_count = len(story_data["stageNodes"])
    action_count = len(story_data["actionNodes"])
    print(f"  Stages: {stage_count}, Actions: {action_count}")
    print()

    # Collect required assets
    images_needed = set()
    audios_needed = set()
    for stage in story_data["stageNodes"]:
        if stage.get("image"):
            images_needed.add(stage["image"])
        if stage.get("audio"):
            audios_needed.add(stage["audio"])

    # Verify all assets exist
    print("[2/4] Verifying assets...")
    missing = []
    for filename in sorted(images_needed | audios_needed):
        path = assets_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            missing.append(filename)

    if missing:
        print("  ERROR: Missing assets:")
        for f in missing:
            print(f"    - {f}")
        sys.exit(1)

    print(f"  Images: {len(images_needed)} verified")
    print(f"  Audio:  {len(audios_needed)} verified")
    print()

    # Transform for device
    print("[3/4] Transforming IDs to UUIDs...")
    device_story = transform_story_for_device(story_data)

    converted_count = 0
    for stage in story_data["stageNodes"]:
        if not is_valid_uuid(stage["uuid"]):
            converted_count += 1
    for action in story_data["actionNodes"]:
        if not is_valid_uuid(action["id"]):
            converted_count += 1

    pack_uuid = device_story["stageNodes"][0]["uuid"]
    print(f"  Converted {converted_count} slug IDs to UUIDs")
    print(f"  Pack UUID: {pack_uuid}")
    print()

    # Create ZIP
    print("[4/4] Creating archive...")
    zip_name = f"{slugify(title)}.zip"
    zip_path = story_dir / zip_name

    # Remove previous archive if it exists
    if zip_path.exists():
        zip_path.unlink()
    # Also remove any other .zip files in the directory
    for old_zip in story_dir.glob("*.zip"):
        old_zip.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # story.json (transformed)
        story_json_str = json.dumps(device_story, indent=2, ensure_ascii=False)
        zf.writestr("story.json", story_json_str)

        # thumbnail.bmp (copy of cover image)
        cover_path = assets_dir / "cover.bmp"
        if cover_path.exists():
            zf.write(cover_path, "thumbnail.bmp")

        # All assets
        for filename in sorted(images_needed | audios_needed):
            asset_path = assets_dir / filename
            zf.write(asset_path, f"assets/{filename}")

    archive_size = zip_path.stat().st_size
    total_files = 1 + 1 + len(images_needed) + len(audios_needed)

    print()
    print("=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)
    print()
    print(f"  Archive:    {zip_path}")
    print(f"  Pack UUID:  {pack_uuid}")
    print(f"  Size:       {archive_size:,} bytes ({archive_size / 1024:.1f} KB)")
    print()
    print(f"  story.json  (1 file, UUIDs converted)")
    print(f"  thumbnail   (1 file)")
    print(f"  Images:     {len(images_needed)} BMP files")
    print(f"  Audio:      {len(audios_needed)} MP3 files")
    print(f"  Total:      {total_files} files in archive")
    print()
    print(f"  Stage nodes:  {stage_count}")
    print(f"  Action nodes: {action_count}")
    print()
    print("  Next steps:")
    print("    1. Open Lunii STUdio")
    print("    2. Go to Library > Import")
    print(f"    3. Select: {zip_path}")
    print("    4. Transfer to Lunii device")
    print()


if __name__ == "__main__":
    main()
