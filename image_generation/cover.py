"""Cover image generation and Lunii BMP encoding."""

from __future__ import annotations

import logging
import struct
from pathlib import Path

from PIL import Image

from image_generation.config import VertexImageConfig
from image_generation.prompts import COVER_SYSTEM_PROMPT
from image_generation.provider import GeminiImageProvider, ImageProvider

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
COLOR_DEPTH_BITS = 4
NUM_COLORS = 16

BMP_HEADER_SIZE = 14
DIB_HEADER_SIZE = 40
PALETTE_SIZE = NUM_COLORS * 4
BI_RLE4 = 2


def build_cover_prompt(description: str) -> str:
    """Build the complete cover-generation prompt."""

    return (
        f"{COVER_SYSTEM_PROMPT}\n\n"
        f"CHAPTER DESCRIPTION TO ILLUSTRATE:\n{description}"
    )


def process_cover_image(image: Image.Image) -> Image.Image:
    """Resize and quantize an image into a 16-shade grayscale palette image."""

    logging.info("Processing image: original size %s, mode %s", image.size, image.mode)
    if image.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
        logging.info("Resizing to %sx%s...", IMAGE_WIDTH, IMAGE_HEIGHT)
        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)

    if image.mode != "L":
        logging.info("Converting to grayscale...")
        image = image.convert("L")

    logging.info("Quantizing to 16 shades...")
    pixels = list(image.tobytes())
    width, height = image.size
    float_pixels = [
        [float(pixels[y * width + x]) for x in range(width)] for y in range(height)
    ]

    quantized_pixels: list[int] = []
    for y in range(height):
        for x in range(width):
            old_pixel = float_pixels[y][x]
            new_index = min(15, max(0, int(old_pixel * 15 / 255 + 0.5)))
            new_pixel = new_index * 255 / 15
            quantized_pixels.append(new_index)

            quant_error = old_pixel - new_pixel
            if x + 1 < width:
                float_pixels[y][x + 1] += quant_error * 7 / 16
            if y + 1 < height:
                if x > 0:
                    float_pixels[y + 1][x - 1] += quant_error * 3 / 16
                float_pixels[y + 1][x] += quant_error * 5 / 16
                if x + 1 < width:
                    float_pixels[y + 1][x + 1] += quant_error * 1 / 16

    quantized_image = Image.new("P", (width, height))
    quantized_image.putdata(quantized_pixels)
    grayscale_palette: list[int] = []
    for i in range(NUM_COLORS):
        gray_value = int(i * 255 / (NUM_COLORS - 1))
        grayscale_palette.extend([gray_value, gray_value, gray_value])
    grayscale_palette.extend([0] * (768 - len(grayscale_palette)))
    quantized_image.putpalette(grayscale_palette)

    logging.info(
        "Processed image: size %s, mode %s",
        quantized_image.size,
        quantized_image.mode,
    )
    return quantized_image


def encode_rle4(pixel_data: bytes, width: int, height: int) -> bytes:
    """Encode 4-bit indexed pixels using BMP RLE4 compression."""

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
                encoded.append(run_length)
                encoded.append((current << 4) | current)
                x += run_length
                continue

            abs_pixels = []
            while x < width and len(abs_pixels) < 255:
                if x + 2 < width and row_data[x] == row_data[x + 1] == row_data[x + 2]:
                    break
                abs_pixels.append(row_data[x])
                x += 1

            if len(abs_pixels) == 1:
                encoded.append(1)
                encoded.append((abs_pixels[0] << 4) | abs_pixels[0])
            elif len(abs_pixels) == 2:
                encoded.append(2)
                encoded.append((abs_pixels[0] << 4) | abs_pixels[1])
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

        encoded.append(0)
        encoded.append(0)

    encoded.append(0)
    encoded.append(1)
    return bytes(encoded)


def create_bmp_rle4(image: Image.Image) -> bytes:
    """Create a complete 4-bit RLE4-compressed BMP file."""

    width, height = image.size
    pixel_data = image.tobytes()
    palette = image.getpalette()[: NUM_COLORS * 3]

    logging.debug("Creating BMP: %sx%s, %s pixels", width, height, len(pixel_data))
    rle_data = encode_rle4(pixel_data, width, height)
    data_offset = BMP_HEADER_SIZE + DIB_HEADER_SIZE + PALETTE_SIZE
    file_size = data_offset + len(rle_data)

    bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, data_offset)
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        DIB_HEADER_SIZE,
        width,
        height,
        1,
        COLOR_DEPTH_BITS,
        BI_RLE4,
        len(rle_data),
        2835,
        2835,
        NUM_COLORS,
        NUM_COLORS,
    )

    palette_data = bytearray()
    for i in range(NUM_COLORS):
        r = palette[i * 3] if i * 3 < len(palette) else 0
        g = palette[i * 3 + 1] if i * 3 + 1 < len(palette) else 0
        b = palette[i * 3 + 2] if i * 3 + 2 < len(palette) else 0
        palette_data.extend([b, g, r, 0])

    bmp_data = bmp_header + dib_header + bytes(palette_data) + rle_data
    logging.info("BMP file created: %s bytes", len(bmp_data))
    return bmp_data


def verify_bmp_format(data: bytes) -> bool:
    """Verify Lunii cover BMP header requirements."""

    if len(data) < BMP_HEADER_SIZE + DIB_HEADER_SIZE:
        logging.error("BMP data is too short")
        return False
    if data[0:2] != b"BM":
        logging.error("Invalid BMP signature")
        return False

    bit_depth = struct.unpack_from("<H", data, 28)[0]
    if bit_depth != 4:
        logging.error("Invalid bit depth: %s, expected 4", bit_depth)
        return False

    compression = struct.unpack_from("<I", data, 30)[0]
    if compression != BI_RLE4:
        logging.error("Invalid compression: %s, expected %s", compression, BI_RLE4)
        return False

    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    if width != IMAGE_WIDTH or height != IMAGE_HEIGHT:
        logging.error(
            "Invalid dimensions: %sx%s, expected %sx%s",
            width,
            height,
            IMAGE_WIDTH,
            IMAGE_HEIGHT,
        )
        return False

    logging.info("BMP format verification passed")
    return True


def generate_cover(
    description: str,
    output_path: Path,
    *,
    config: VertexImageConfig | None = None,
    provider: ImageProvider | None = None,
) -> bytes:
    """Generate and save a Lunii-compatible cover BMP."""

    if provider is None:
        config = config or VertexImageConfig.from_env()
        provider = GeminiImageProvider(config)
    logging.info("Generating cover for: %s...", description[:50])
    raw_image = provider.generate_image(build_cover_prompt(description))
    processed_image = process_cover_image(raw_image)
    bmp_data = create_bmp_rle4(processed_image)

    if not verify_bmp_format(bmp_data):
        raise RuntimeError("Generated BMP does not meet format requirements")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bmp_data)
    return bmp_data
