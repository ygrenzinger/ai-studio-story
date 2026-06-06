"""Tests for image generation pipelines."""

from pathlib import Path

from PIL import Image

from image_generation.cover import (
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    create_bmp_rle4,
    generate_cover,
    process_cover_image,
    verify_bmp_format,
)
from image_generation.thumbnail import IMAGE_SIZE, generate_thumbnail, process_thumbnail_image


class FakeImageProvider:
    def __init__(self, image: Image.Image):
        self.image = image
        self.prompts: list[str] = []

    def generate_image(self, prompt: str) -> Image.Image:
        self.prompts.append(prompt)
        return self.image.copy()


def test_process_cover_image_outputs_lunii_palette_image():
    image = Image.new("RGB", (16, 12), color=(120, 80, 40))

    processed = process_cover_image(image)

    assert processed.size == (IMAGE_WIDTH, IMAGE_HEIGHT)
    assert processed.mode == "P"
    assert len(processed.getpalette()) == 768
    assert set(processed.tobytes()).issubset(set(range(16)))


def test_create_bmp_rle4_outputs_verified_lunii_bmp():
    image = Image.new("L", (IMAGE_WIDTH, IMAGE_HEIGHT), color=127)
    processed = process_cover_image(image)

    bmp_data = create_bmp_rle4(processed)

    assert verify_bmp_format(bmp_data)
    assert bmp_data[:2] == b"BM"


def test_generate_cover_uses_injected_provider(tmp_path: Path):
    provider = FakeImageProvider(Image.new("RGB", (32, 24), color=(200, 200, 200)))
    output_path = tmp_path / "cover.bmp"

    bmp_data = generate_cover(
        "A tiny moon base",
        output_path,
        provider=provider,
    )

    assert output_path.read_bytes() == bmp_data
    assert verify_bmp_format(bmp_data)
    assert "A tiny moon base" in provider.prompts[0]


def test_process_thumbnail_image_outputs_rgba_square():
    image = Image.new("RGB", (120, 80), color=(12, 34, 56))

    processed = process_thumbnail_image(image)

    assert processed.size == (IMAGE_SIZE, IMAGE_SIZE)
    assert processed.mode == "RGBA"


def test_generate_thumbnail_uses_injected_provider(tmp_path: Path):
    provider = FakeImageProvider(Image.new("RGB", (64, 64), color=(200, 100, 50)))
    output_path = tmp_path / "thumbnail.png"

    saved_path = generate_thumbnail(
        "A cheerful space adventure",
        output_path,
        provider=provider,
    )

    assert saved_path == output_path
    assert output_path.exists()
    assert Image.open(output_path).size == (IMAGE_SIZE, IMAGE_SIZE)
    assert "A cheerful space adventure" in provider.prompts[0]
