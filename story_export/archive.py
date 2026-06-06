"""ZIP archive creation for Lunii exports."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from story_export.models import AssetManifest
from story_export.utils import slugify


def write_archive(
    story_dir: Path,
    title: str,
    device_story: dict[str, Any],
    manifest: AssetManifest,
    *,
    overwrite: bool = True,
) -> tuple[Path, bool, bool]:
    """Write a device-ready ZIP archive.

    Returns:
        Tuple of zip path, has thumbnail, used thumbnail fallback.
    """

    zip_path = story_dir / f"{slugify(title)}.zip"
    if overwrite:
        for old_zip in story_dir.glob("*.zip"):
            old_zip.unlink()
    elif zip_path.exists():
        raise FileExistsError(f"Archive already exists: {zip_path}")

    assets_dir = story_dir / "assets"
    thumbnail_path = story_dir / "thumbnail.png"
    fallback_cover_path = assets_dir / "cover.bmp"
    has_thumbnail = thumbnail_path.exists()
    used_thumbnail_fallback = not has_thumbnail and fallback_cover_path.exists()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        story_json_str = json.dumps(device_story, indent=2, ensure_ascii=False)
        zf.writestr("story.json", story_json_str)

        if has_thumbnail:
            zf.write(thumbnail_path, "thumbnail.png")
        elif used_thumbnail_fallback:
            zf.write(fallback_cover_path, "thumbnail.bmp")

        for filename in sorted(manifest.all_assets):
            zf.write(assets_dir / filename, f"assets/{filename}")

    return zip_path, has_thumbnail, used_thumbnail_fallback
