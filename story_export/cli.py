"""Command-line interface for Lunii story export."""

from __future__ import annotations

import sys
from pathlib import Path

from story_export.loader import collect_asset_manifest, load_story_data, load_story_title
from story_export.service import export_story, validate_story


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <story-directory>")
        print(f"Example: {sys.argv[0]} stories/victor-pays-du-sommeil")
        sys.exit(1)

    story_dir = Path(sys.argv[1])
    issues = validate_story(story_dir)
    errors = [issue for issue in issues if issue.is_error]

    if errors:
        print("ERROR: Story validation failed:")
        for issue in errors:
            print(f"  - {issue.path}: {issue.message}")
        sys.exit(1)

    story_data = load_story_data(story_dir)
    title = load_story_title(story_dir, story_data)
    manifest = collect_asset_manifest(story_data)

    print("=" * 60)
    print(f"  Lunii Story Export: {title}")
    print("=" * 60)
    print()
    print("[1/4] Loading story.json...")
    print(f"  Stages: {len(story_data['stageNodes'])}, Actions: {len(story_data['actionNodes'])}")
    print()
    print("[2/4] Verifying assets...")
    print(f"  Images: {len(manifest.images)} verified")
    print(f"  Audio:  {len(manifest.audios)} verified")
    if issues:
        print(f"  Warnings: {len(issues)}")
        for issue in issues:
            print(f"    - {issue.message}")
    print()
    print("[3/4] Transforming IDs to UUIDs...")

    result = export_story(story_dir)
    print(f"  Pack UUID: {result.pack_uuid}")
    print()
    print("[4/4] Creating archive...")
    print()
    print("=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)
    print()
    print(f"  Archive:    {result.zip_path}")
    print(f"  Pack UUID:  {result.pack_uuid}")
    print(
        f"  Size:       {result.archive_size:,} bytes "
        f"({result.archive_size / 1024:.1f} KB)"
    )
    print()
    print("  story.json  (1 file, UUIDs converted)")
    thumbnail_label = "300x300 PNG" if result.has_thumbnail else "cover.bmp fallback"
    print(f"  thumbnail   (1 file, {thumbnail_label})")
    print(f"  Images:     {len(result.manifest.images)} BMP files")
    print(f"  Audio:      {len(result.manifest.audios)} MP3 files")
    print(f"  Total:      {result.total_files} files in archive")
    print()
    print(f"  Stage nodes:  {result.stage_count}")
    print(f"  Action nodes: {result.action_count}")
    print()
    print("  Next steps:")
    print("    1. Open Lunii STUdio")
    print("    2. Go to Library > Import")
    print(f"    3. Select: {result.zip_path}")
    print("    4. Transfer to Lunii device")
    print()


if __name__ == "__main__":
    main()
