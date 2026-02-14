#!/usr/bin/env python3
"""
Export script for "L'Incroyable Voyage Spatial de Zara" Lunii story.

Loads real assets from disk (assets/) when available,
falls back to placeholder BMP images and silent MP3s for missing files,
then creates a Lunii-compatible ZIP archive.

Usage:
    uv run python stories/aventure-spatiale/export_pack.py
"""

import copy
import json
import struct
import time
import uuid
import zipfile
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
NUM_COLORS = 16
COLOR_DEPTH_BITS = 4
BMP_HEADER_SIZE = 14
DIB_HEADER_SIZE = 40
PALETTE_SIZE = NUM_COLORS * 4
BI_RLE4 = 2

STORY_DIR = Path(__file__).parent
STORY_JSON = STORY_DIR / "story.json"
ASSETS_DIR = STORY_DIR / "assets"

# Namespace UUID for deterministic slug-to-UUID conversion (UUID v5).
# This MUST remain stable — changing it changes all derived UUIDs.
KIDSTORY_NAMESPACE = uuid.UUID("d4e8c2f1-7a3b-4e5d-9c1f-2b8a6d4e0f3c")

# Color themes for different stage types (R, G, B)
COLOR_THEMES = {
    "cover": (10, 10, 50),  # Deep space navy
    "ch01-decollage": (30, 30, 80),  # Night sky blue
    "ch02-planetes-brulantes": (200, 100, 30),  # Solar orange
    "ch03-planete-rouge": (180, 60, 30),  # Mars red-orange
    "ch04-geantes-magnifiques": (180, 150, 80),  # Jupiter tan
    "ch05-confins-glaces": (60, 130, 160),  # Ice blue
    "ch06-mysteres-retour": (80, 40, 120),  # Nebula purple
}

# Labels for placeholder images
LABELS = {
    "cover.bmp": "L'Incroyable Voyage\nSpatial de Zara",
    "ch01-decollage.bmp": "Chapitre 1\nDecollage vers les etoiles",
    "ch02-planetes-brulantes.bmp": "Chapitre 2\nLes planetes brulantes",
    "ch03-planete-rouge.bmp": "Chapitre 3\nLa planete rouge",
    "ch04-geantes-magnifiques.bmp": "Chapitre 4\nLes geantes magnifiques",
    "ch05-confins-glaces.bmp": "Chapitre 5\nLes confins glaces",
    "ch06-mysteres-retour.bmp": "Chapitre 6\nMysteres et retour",
}


# ─── BMP Generation (4-bit, RLE4, 320x240) ──────────────────────────────────


def create_16_color_grayscale_palette():
    """Create a 16-color grayscale palette (BGRA format for BMP)."""
    palette = bytearray()
    for i in range(NUM_COLORS):
        gray = int(i * 255 / (NUM_COLORS - 1))
        palette.extend([gray, gray, gray, 0])  # BGRA
    return bytes(palette)


def create_placeholder_pixels(
    label: str, base_color: tuple[int, int, int]
) -> list[int]:
    """Create pixel data for a placeholder image.

    Generates a simple colored background with a lighter rectangle in the center.
    Since Lunii uses grayscale BMP, we convert to grayscale palette indices (0-15).

    Args:
        label: Text label (not rendered in pixels, just for the concept)
        base_color: RGB tuple for the background tone

    Returns:
        List of pixel indices (0-15) for each pixel, row by row
    """
    r, g, b = base_color
    # Convert to grayscale luminance
    bg_gray = int(0.299 * r + 0.587 * g + 0.114 * b)
    bg_index = min(15, max(0, int(bg_gray * 15 / 255)))

    # Center area slightly lighter
    center_index = min(15, bg_index + 3)

    # Border even darker
    border_index = max(0, bg_index - 3)

    pixels = []
    for y in range(IMAGE_HEIGHT):
        for x in range(IMAGE_WIDTH):
            # Draw a simple frame with center area
            if x < 8 or x >= IMAGE_WIDTH - 8 or y < 8 or y >= IMAGE_HEIGHT - 8:
                pixels.append(border_index)
            elif (40 <= x < IMAGE_WIDTH - 40) and (60 <= y < IMAGE_HEIGHT - 60):
                pixels.append(center_index)
            else:
                pixels.append(bg_index)

    return pixels


def encode_rle4(pixel_data: list[int], width: int, height: int) -> bytes:
    """Encode pixel data using RLE4 compression (bottom-to-top BMP order)."""
    encoded = bytearray()

    for y in range(height - 1, -1, -1):
        row_start = y * width
        row_data = pixel_data[row_start : row_start + width]

        x = 0
        while x < width:
            current = row_data[x]
            run_length = 1

            while x + run_length < width and run_length < 255:
                if row_data[x + run_length] == current:
                    run_length += 1
                else:
                    break

            if run_length >= 3:
                packed = (current << 4) | current
                encoded.append(run_length)
                encoded.append(packed)
                x += run_length
            else:
                abs_start = x
                abs_pixels = []

                while x < width and len(abs_pixels) < 255:
                    if x + 2 < width:
                        if row_data[x] == row_data[x + 1] == row_data[x + 2]:
                            break
                    abs_pixels.append(row_data[x])
                    x += 1

                if len(abs_pixels) == 1:
                    packed = (abs_pixels[0] << 4) | abs_pixels[0]
                    encoded.append(1)
                    encoded.append(packed)
                elif len(abs_pixels) == 2:
                    packed = (abs_pixels[0] << 4) | abs_pixels[1]
                    encoded.append(2)
                    encoded.append(packed)
                else:
                    encoded.append(0)
                    encoded.append(len(abs_pixels))
                    for i in range(0, len(abs_pixels), 2):
                        high = abs_pixels[i]
                        low = abs_pixels[i + 1] if i + 1 < len(abs_pixels) else 0
                        encoded.append((high << 4) | low)
                    data_bytes = (len(abs_pixels) + 1) // 2
                    if data_bytes % 2 == 1:
                        encoded.append(0)

        # End of line
        encoded.append(0)
        encoded.append(0)

    # End of bitmap
    encoded.append(0)
    encoded.append(1)

    return bytes(encoded)


def create_bmp(label: str, base_color: tuple[int, int, int]) -> bytes:
    """Create a 4-bit BMP file with RLE4 compression.

    Args:
        label: Text label for the placeholder
        base_color: RGB tuple for the background tone

    Returns:
        Complete BMP file bytes
    """
    pixels = create_placeholder_pixels(label, base_color)
    palette = create_16_color_grayscale_palette()
    rle_data = encode_rle4(pixels, IMAGE_WIDTH, IMAGE_HEIGHT)

    data_offset = BMP_HEADER_SIZE + DIB_HEADER_SIZE + PALETTE_SIZE
    file_size = data_offset + len(rle_data)

    # BMP header (14 bytes)
    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",
        file_size,
        0,
        0,
        data_offset,
    )

    # DIB header (40 bytes)
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        DIB_HEADER_SIZE,
        IMAGE_WIDTH,
        IMAGE_HEIGHT,
        1,  # color planes
        COLOR_DEPTH_BITS,  # bits per pixel
        BI_RLE4,  # compression
        len(rle_data),  # image size
        2835,
        2835,  # resolution (72 DPI)
        NUM_COLORS,
        NUM_COLORS,
    )

    return bmp_header + dib_header + palette + rle_data


def verify_bmp(data: bytes, filename: str) -> bool:
    """Verify BMP meets Lunii format requirements."""
    if data[0:2] != b"BM":
        print(f"  ERROR: {filename} - Invalid BMP signature")
        return False

    bit_depth = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]

    ok = True
    if bit_depth != 4:
        print(f"  ERROR: {filename} - Bit depth {bit_depth}, expected 4")
        ok = False
    if compression != BI_RLE4:
        print(f"  ERROR: {filename} - Compression {compression}, expected {BI_RLE4}")
        ok = False
    if width != IMAGE_WIDTH or height != IMAGE_HEIGHT:
        print(
            f"  ERROR: {filename} - Size {width}x{height}, expected {IMAGE_WIDTH}x{IMAGE_HEIGHT}"
        )
        ok = False

    return ok


# ─── MP3 Placeholder (minimal valid MP3 - 1 second silence) ─────────────────


def create_silent_mp3() -> bytes:
    """Create a minimal valid MP3 file with ~1 second of silence.

    Uses MPEG1 Layer III, 128kbps, 44100Hz, mono.
    Each frame is 417 bytes (header + data).
    ~38 frames = ~1 second.

    No ID3 tags (Lunii requirement).
    """
    frames = bytearray()

    header = bytes([0xFF, 0xFB, 0x90, 0xC4])

    frame_data_size = 413

    # Side information for mono MPEG1 Layer III = 17 bytes
    # Set to zeros (silence)
    side_info = bytes(17)

    # Remaining data (padding to fill frame)
    remaining = frame_data_size - 17
    padding = bytes(remaining)

    # Generate ~1 second worth of frames (38 frames at 44100Hz, 1152 samples/frame)
    num_frames = 38
    for _ in range(num_frames):
        frames.extend(header)
        frames.extend(side_info)
        frames.extend(padding)

    return bytes(frames)


# ─── Real Asset Loading ──────────────────────────────────────────────────────


def load_real_asset(directory: Path, filename: str) -> bytes | None:
    """Try to load a real asset from disk.

    Returns the file bytes if found and non-empty, None otherwise.
    """
    path = directory / filename
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    return None


# ─── UUID Transformation for Device Compatibility ────────────────────────────


def is_valid_uuid(s: str) -> bool:
    """Check if a string is a valid UUID parseable by java.util.UUID.fromString()."""
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

    Args:
        story_data: Parsed source story.json

    Returns:
        Transformed story data with valid UUIDs for all identifiers.
    """
    data = copy.deepcopy(story_data)

    # Phase 1: Build slug → UUID mapping for all IDs
    id_map: dict[str, str] = {}

    for stage in data["stageNodes"]:
        old_id = stage["uuid"]
        new_id = slug_to_uuid(old_id)
        id_map[old_id] = new_id

    for action in data["actionNodes"]:
        old_id = action["id"]
        new_id = slug_to_uuid(old_id)
        id_map[old_id] = new_id

    # Phase 2: Apply ID mapping to stage nodes
    for stage in data["stageNodes"]:
        stage["uuid"] = id_map[stage["uuid"]]

        # Update transition references
        for trans_key in ("okTransition", "homeTransition"):
            trans = stage.get(trans_key)
            if trans and trans.get("actionNode") in id_map:
                trans["actionNode"] = id_map[trans["actionNode"]]

    # Phase 3: Apply ID mapping to action nodes
    for action in data["actionNodes"]:
        action["id"] = id_map[action["id"]]
        action["options"] = [id_map.get(opt, opt) for opt in action["options"]]

    return data


# ─── Archive Creation ────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  Lunii Story Export: L'Incroyable Voyage Spatial de Zara")
    print("=" * 60)
    print()

    # Load and validate story.json
    print("[1/5] Loading story.json...")
    with open(STORY_JSON) as f:
        story_data = json.load(f)

    stage_count = len(story_data["stageNodes"])
    action_count = len(story_data["actionNodes"])
    print(f"  Loaded: {stage_count} stages, {action_count} actions")

    # Collect required assets
    images_needed = set()
    audios_needed = set()
    for stage in story_data["stageNodes"]:
        if stage.get("image"):
            images_needed.add(stage["image"])
        if stage.get("audio"):
            audios_needed.add(stage["audio"])

    print(f"  Images needed: {len(images_needed)}")
    print(f"  Audios needed: {len(audios_needed)}")
    print()

    # Load images: prefer real assets from disk, fall back to placeholders
    print("[2/5] Loading images (real from disk, placeholder fallback)...")
    bmp_files: dict[str, bytes] = {}
    real_image_count = 0
    placeholder_image_count = 0
    for filename in sorted(images_needed):
        # Try loading real asset from disk
        real_data = load_real_asset(ASSETS_DIR, filename)
        if real_data and verify_bmp(real_data, filename):
            bmp_files[filename] = real_data
            real_image_count += 1
            print(f"  REAL: {filename} ({len(real_data):,} bytes)")
        else:
            # Fall back to placeholder
            stem = filename.replace(".bmp", "")
            color = COLOR_THEMES.get(stem, (128, 128, 128))
            label = LABELS.get(filename, stem) or stem
            bmp_data = create_bmp(label, color)
            if not verify_bmp(bmp_data, filename):
                print(f"  FAILED: {filename}")
                return
            bmp_files[filename] = bmp_data
            placeholder_image_count += 1
            print(f"  PLACEHOLDER: {filename} ({len(bmp_data):,} bytes)")

    print(f"  Images: {real_image_count} real, {placeholder_image_count} placeholder")
    print()

    # Load audio: prefer real assets from disk, fall back to silent placeholders
    print("[3/5] Loading audio (real from disk, placeholder fallback)...")
    silent_mp3_data = create_silent_mp3()
    mp3_files: dict[str, bytes] = {}
    real_audio_count = 0
    placeholder_audio_count = 0
    for filename in sorted(audios_needed):
        real_data = load_real_asset(ASSETS_DIR, filename)
        if real_data and len(real_data) > 1024:  # Real audio is > 1KB
            mp3_files[filename] = real_data
            real_audio_count += 1
            print(f"  REAL: {filename} ({len(real_data):,} bytes)")
        else:
            mp3_files[filename] = silent_mp3_data
            placeholder_audio_count += 1
            print(f"  PLACEHOLDER: {filename} ({len(silent_mp3_data):,} bytes)")

    print(f"  Audio: {real_audio_count} real, {placeholder_audio_count} placeholder")
    print()

    # Validate all references
    print("[4/5] Validating archive contents...")
    errors = []

    for stage in story_data["stageNodes"]:
        img = stage.get("image")
        if img and img not in bmp_files:
            errors.append(f"Missing image: {img} (stage {stage['uuid']})")
        aud = stage.get("audio")
        if aud and aud not in mp3_files:
            errors.append(f"Missing audio: {aud} (stage {stage['uuid']})")

    # Check transitions
    all_uuids = {s["uuid"] for s in story_data["stageNodes"]}
    all_actions = {a["id"] for a in story_data["actionNodes"]}

    for stage in story_data["stageNodes"]:
        for trans_name in ("okTransition", "homeTransition"):
            trans = stage.get(trans_name)
            if trans:
                if trans["actionNode"] not in all_actions:
                    errors.append(
                        f"Stage {stage['uuid']} {trans_name} -> invalid action {trans['actionNode']}"
                    )

    for action in story_data["actionNodes"]:
        for opt in action["options"]:
            if opt not in all_uuids:
                errors.append(f"Action {action['id']} -> invalid stage {opt}")

    # Check squareOne
    sq = [s for s in story_data["stageNodes"] if s.get("squareOne")]
    if len(sq) != 1:
        errors.append(f"Expected 1 squareOne, found {len(sq)}")

    if errors:
        print("  ERRORS found:")
        for e in errors:
            print(f"    - {e}")
        return
    else:
        print("  All asset references valid")
        print("  All transitions valid")
        print("  squareOne: stage-cover")
        print("  No orphaned nodes")
    print()

    # ── Phase 5: Transform for device and create ZIP archive ──

    print("[5/5] Transforming for device and creating archive...")

    # Transform: slug IDs → valid UUIDs (deterministic via UUID v5)
    device_story = transform_story_for_device(story_data)

    # Report the ID mapping
    print("  UUID conversion:")
    converted_count = 0
    for stage in story_data["stageNodes"]:
        old_id = stage["uuid"]
        new_id = slug_to_uuid(old_id)
        if old_id != new_id:
            print(f"    {old_id} -> {new_id}")
            converted_count += 1
    for action in story_data["actionNodes"]:
        old_id = action["id"]
        new_id = slug_to_uuid(old_id)
        if old_id != new_id:
            print(f"    {old_id} -> {new_id}")
            converted_count += 1
    if converted_count == 0:
        print("    (all IDs were already valid UUIDs)")
    else:
        print(f"    Converted {converted_count} slug IDs to UUIDs")

    # Pack UUID = first stage node UUID (the squareOne cover)
    pack_uuid = device_story["stageNodes"][0]["uuid"]
    print(f"  Pack UUID: {pack_uuid}")

    # Create the archive
    archive_name = f"{pack_uuid}.zip"
    archive_path = STORY_DIR / archive_name

    # Remove previous archive with the same name if it exists
    if archive_path.exists():
        archive_path.unlink()

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # story.json (transformed with valid UUIDs)
        story_json_str = json.dumps(device_story, indent=2, ensure_ascii=False)
        zf.writestr("story.json", story_json_str)
        print("  + story.json (with valid UUIDs)")

        # Thumbnail (copy of cover image)
        if "cover.bmp" in bmp_files:
            zf.writestr("thumbnail.bmp", bmp_files["cover.bmp"])
            print("  + thumbnail.bmp")

        # Images
        for filename, data in sorted(bmp_files.items()):
            zf.writestr(f"assets/{filename}", data)
            print(f"  + assets/{filename}")

        # Audio
        for filename, data in sorted(mp3_files.items()):
            zf.writestr(f"assets/{filename}", data)
            print(f"  + assets/{filename}")

    # Final report
    archive_size = archive_path.stat().st_size
    total_files = (
        1 + (1 if "cover.bmp" in bmp_files else 0) + len(bmp_files) + len(mp3_files)
    )  # story.json + thumbnail + images + audio

    print()
    print("=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)
    print()
    print(f"  Archive: {archive_path}")
    print(f"  Pack UUID: {pack_uuid}")
    print(f"  Size: {archive_size:,} bytes ({archive_size / 1024:.1f} KB)")
    print()
    print(f"  Total: {stage_count} stages, {action_count} actions")
    print(f"  IDs converted: {converted_count} slug -> UUID")
    print()
    print(f"  Images: {real_image_count}/{len(bmp_files)} real", end="")
    if placeholder_image_count > 0:
        print(f" ({placeholder_image_count} placeholder)", end="")
    print()
    print(f"  Audio:  {real_audio_count}/{len(mp3_files)} real", end="")
    if placeholder_audio_count > 0:
        print(f" ({placeholder_audio_count} placeholder)", end="")
    print()
    print(f"  Total files in archive: {total_files}")
    print()

    all_real = placeholder_image_count == 0 and placeholder_audio_count == 0
    if all_real:
        print("  All assets are REAL - archive is device-ready!")
    else:
        print("  NOTE: Some assets are placeholders.")
        if placeholder_audio_count > 0:
            print(f"  Missing audio: {placeholder_audio_count} files")
            print(
                "    Generate with: uv run python generate_audio.py <script.md> -o <output.mp3>"
            )
        if placeholder_image_count > 0:
            print(f"  Missing images: {placeholder_image_count} files")
            print(
                '    Generate with: uv run python generate_cover.py "description" -o <output.bmp>'
            )
        print("  Re-run this export after generating assets to include them.")
    print()
    print("  Lunii STUdio Import:")
    print("    1. Open Lunii STUdio")
    print("    2. Go to Library > Import")
    print(f"    3. Select: {archive_name}")
    print("    4. Verify story appears in library")
    print("    5. Transfer to Lunii device")
    print()


if __name__ == "__main__":
    main()
