#!/usr/bin/env python3
"""
Generate pixel art cover images for story chapters using Gemini Flash 2.5 via Vertex AI.

Outputs 4-bit BMP files with RLE4 compression at 320x240 pixels in black and white.

Usage:
    python generate_cover.py "A knight facing a dragon" -o chapter1.bmp
    python generate_cover.py "Mysterious forest with glowing mushrooms" --output cover.bmp

Prerequisites:
    - Google Cloud project with Vertex AI API enabled
    - Authentication via: gcloud auth application-default login
    - Environment variables: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION (optional)
"""

import argparse
import io
import logging
import os
import struct
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Constants
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
COLOR_DEPTH_BITS = 4
NUM_COLORS = 16  # 2^4 = 16 colors for 4-bit

# BMP format constants
BMP_HEADER_SIZE = 14
DIB_HEADER_SIZE = 40  # BITMAPINFOHEADER
PALETTE_SIZE = NUM_COLORS * 4  # 4 bytes per color (BGRA)
BI_RLE4 = 2  # RLE4 compression type

# System prompt for pixel art generation
SYSTEM_PROMPT = """You are an expert pixel art artist creating retro-style cover images for story chapters.

STRICT REQUIREMENTS:
- Style: Classic pixel art with clearly visible, blocky pixels
- Color: STRICTLY BLACK AND WHITE / GRAYSCALE ONLY - no colors whatsoever
- Composition: Simple, iconic imagery suitable for a small 320x240 pixel display
- Theme: Create an evocative scene that captures the essence of the chapter description
- NO TEXT: NEVER include any text, titles, labels, captions, or written words in the image - the image must be purely visual artwork

PIXEL ART BEST PRACTICES TO FOLLOW:
- Use deliberate, hand-placed pixel aesthetic with visible individual pixels
- AVOID anti-aliasing and smooth gradients - use hard edges
- Employ classic dithering patterns (checkerboard, ordered dithering) for shading and gradients
- Keep details minimal but impactful - simplify complex shapes
- Ensure strong silhouettes and high contrast for readability at small size
- Use limited shading - think Game Boy or early Macintosh style
- Prioritize clarity and recognizability over detail

OUTPUT: A striking black and white pixel art illustration with NO text or titles."""


def setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def get_vertex_ai_config() -> tuple[str, str]:
    """Get Vertex AI configuration from environment.

    Returns:
        Tuple of (project_id, location)
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        logging.error(
            "GOOGLE_CLOUD_PROJECT environment variable is not set.\n"
            "Please set it to your Google Cloud project ID.\n"
            "Example: export GOOGLE_CLOUD_PROJECT=my-project-id"
        )
        sys.exit(1)

    # Default to europe-west1 (Belgium) for EU users
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

    return project, location


def generate_image_with_gemini(
    description: str, project: str, location: str
) -> Image.Image:
    """Generate an image using Gemini Flash 2.5 image model via Vertex AI.

    Args:
        description: The chapter description to visualize
        project: Google Cloud project ID
        location: Google Cloud region (e.g., europe-west1)

    Returns:
        PIL Image object
    """
    logging.info(f"Connecting to Vertex AI (project={project}, location={location})...")
    client = genai.Client(
        vertexai=True,
        project=project,
        location=location,
    )

    # Combine system prompt with user description
    full_prompt = (
        f"{SYSTEM_PROMPT}\n\nCHAPTER DESCRIPTION TO ILLUSTRATE:\n{description}"
    )

    logging.info("Generating pixel art image...")
    logging.debug(f"Prompt: {full_prompt[:200]}...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    # Extract image from response
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            logging.info("Image generated successfully")
            # Decode the image data
            image_data = part.inline_data.data
            image = Image.open(io.BytesIO(image_data))
            return image

    raise RuntimeError("No image was generated in the response")


def process_image(image: Image.Image) -> Image.Image:
    """Process image to 320x240 grayscale with 16 shades.

    Args:
        image: Input PIL Image

    Returns:
        Processed PIL Image in 'P' mode with 16-color grayscale palette
    """
    logging.info(f"Processing image: original size {image.size}, mode {image.mode}")

    # Resize to exact dimensions (320x240)
    if image.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
        logging.info(f"Resizing to {IMAGE_WIDTH}x{IMAGE_HEIGHT}...")
        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)

    # Convert to grayscale
    if image.mode != "L":
        logging.info("Converting to grayscale...")
        image = image.convert("L")

    # Quantize to 16 shades of gray using manual mapping
    # PIL's quantize() with custom palette doesn't guarantee indices in 0-15 range
    logging.info("Quantizing to 16 shades...")

    # Apply Floyd-Steinberg dithering manually and map to 16 levels
    # First, get pixel data as a list for manipulation
    pixels = list(image.tobytes())
    width, height = image.size

    # Floyd-Steinberg dithering with quantization to 16 levels
    # Work on a copy with floats for error diffusion
    float_pixels = [
        [float(pixels[y * width + x]) for x in range(width)] for y in range(height)
    ]

    quantized_pixels = []
    for y in range(height):
        for x in range(width):
            old_pixel = float_pixels[y][x]
            # Quantize to 16 levels (0-15), then map back to find nearest level
            # Each level represents a range of ~17 values (256/15 ≈ 17)
            new_index = min(15, max(0, int(old_pixel * 15 / 255 + 0.5)))
            new_pixel = new_index * 255 / 15
            quantized_pixels.append(new_index)

            # Calculate quantization error
            quant_error = old_pixel - new_pixel

            # Distribute error to neighboring pixels (Floyd-Steinberg)
            if x + 1 < width:
                float_pixels[y][x + 1] += quant_error * 7 / 16
            if y + 1 < height:
                if x > 0:
                    float_pixels[y + 1][x - 1] += quant_error * 3 / 16
                float_pixels[y + 1][x] += quant_error * 5 / 16
                if x + 1 < width:
                    float_pixels[y + 1][x + 1] += quant_error * 1 / 16

    # Create a new palette image with the quantized data
    quantized_image = Image.new("P", (width, height))
    quantized_image.putdata(quantized_pixels)

    # Create and set the 16-color grayscale palette
    grayscale_palette = []
    for i in range(NUM_COLORS):
        gray_value = int(i * 255 / (NUM_COLORS - 1))
        grayscale_palette.extend([gray_value, gray_value, gray_value])
    # Pad palette to 256 colors (required by PIL)
    grayscale_palette.extend([0] * (768 - len(grayscale_palette)))
    quantized_image.putpalette(grayscale_palette)

    logging.info(
        f"Processed image: size {quantized_image.size}, mode {quantized_image.mode}"
    )
    return quantized_image


def encode_rle4(pixel_data: bytes, width: int, height: int) -> bytes:
    """Encode pixel data using RLE4 compression.

    BMP stores rows bottom-to-top, so we need to flip the data.
    Each byte in RLE4 contains two 4-bit pixel values.

    Args:
        pixel_data: Raw pixel indices (one byte per pixel, values 0-15)
        width: Image width
        height: Image height

    Returns:
        RLE4 encoded data
    """
    encoded = bytearray()

    # Process rows from bottom to top (BMP format)
    for y in range(height - 1, -1, -1):
        row_start = y * width
        row_data = pixel_data[row_start : row_start + width]

        # Encode the row
        x = 0
        while x < width:
            # Find run of same pixel pairs
            run_start = x

            # Get current pixel
            current = row_data[x]
            run_length = 1

            # Count consecutive identical pixels (max 255)
            while x + run_length < width and run_length < 255:
                if row_data[x + run_length] == current:
                    run_length += 1
                else:
                    break

            if run_length >= 3:
                # Use encoded mode for runs of 3 or more
                # Pack the pixel value into both nibbles
                packed = (current << 4) | current
                encoded.append(run_length)
                encoded.append(packed)
                x += run_length
            else:
                # Use absolute mode for short runs or varied pixels
                # Collect pixels until we hit a run
                abs_start = x
                abs_pixels = []

                while x < width and len(abs_pixels) < 255:
                    # Check if there's a run ahead worth encoding
                    if x + 2 < width:
                        if row_data[x] == row_data[x + 1] == row_data[x + 2]:
                            break
                    abs_pixels.append(row_data[x])
                    x += 1

                if len(abs_pixels) == 1:
                    # Single pixel - encode as run of 1
                    packed = (abs_pixels[0] << 4) | abs_pixels[0]
                    encoded.append(1)
                    encoded.append(packed)
                elif len(abs_pixels) == 2:
                    # Two pixels - encode as run of 2
                    packed = (abs_pixels[0] << 4) | abs_pixels[1]
                    encoded.append(2)
                    encoded.append(packed)
                else:
                    # Absolute mode: 0, count, pixels...
                    encoded.append(0)
                    encoded.append(len(abs_pixels))

                    # Pack pixels into bytes (2 pixels per byte)
                    for i in range(0, len(abs_pixels), 2):
                        high = abs_pixels[i]
                        low = abs_pixels[i + 1] if i + 1 < len(abs_pixels) else 0
                        encoded.append((high << 4) | low)

                    # Absolute mode data must be word-aligned
                    # Number of bytes = ceil(count / 2)
                    data_bytes = (len(abs_pixels) + 1) // 2
                    if data_bytes % 2 == 1:
                        encoded.append(0)  # Padding byte

        # End of line marker
        encoded.append(0)
        encoded.append(0)

    # End of bitmap marker
    encoded.append(0)
    encoded.append(1)

    return bytes(encoded)


def create_bmp_rle4(image: Image.Image) -> bytes:
    """Create a 4-bit BMP file with RLE4 compression.

    Args:
        image: PIL Image in 'P' mode with 16-color palette

    Returns:
        Complete BMP file as bytes
    """
    width, height = image.size

    # Get pixel data and palette
    pixel_data = image.tobytes()
    palette = image.getpalette()[: NUM_COLORS * 3]  # RGB values for 16 colors

    logging.debug(f"Creating BMP: {width}x{height}, {len(pixel_data)} pixels")

    # Encode pixel data with RLE4
    rle_data = encode_rle4(pixel_data, width, height)
    logging.debug(f"RLE4 encoded size: {len(rle_data)} bytes")

    # Calculate sizes
    data_offset = BMP_HEADER_SIZE + DIB_HEADER_SIZE + PALETTE_SIZE
    file_size = data_offset + len(rle_data)

    # Build BMP header (14 bytes)
    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",  # Signature
        file_size,  # File size
        0,  # Reserved1
        0,  # Reserved2
        data_offset,  # Offset to pixel data
    )

    # Build DIB header - BITMAPINFOHEADER (40 bytes)
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        DIB_HEADER_SIZE,  # Header size
        width,  # Width
        height,  # Height (positive = bottom-up)
        1,  # Color planes
        COLOR_DEPTH_BITS,  # Bits per pixel (4-bit) - at byte offset 28
        BI_RLE4,  # Compression (RLE4) - at byte offset 30
        len(rle_data),  # Image size
        2835,  # Horizontal resolution (72 DPI)
        2835,  # Vertical resolution (72 DPI)
        NUM_COLORS,  # Colors used
        NUM_COLORS,  # Important colors
    )

    # Build color palette (16 colors, 4 bytes each: BGRA)
    palette_data = bytearray()
    for i in range(NUM_COLORS):
        r = palette[i * 3] if i * 3 < len(palette) else 0
        g = palette[i * 3 + 1] if i * 3 + 1 < len(palette) else 0
        b = palette[i * 3 + 2] if i * 3 + 2 < len(palette) else 0
        # BMP uses BGRA order
        palette_data.extend([b, g, r, 0])

    # Combine all parts
    bmp_data = bmp_header + dib_header + bytes(palette_data) + rle_data

    logging.info(f"BMP file created: {len(bmp_data)} bytes")
    return bmp_data


def verify_bmp_format(data: bytes) -> bool:
    """Verify the BMP file meets the required format specifications.

    Args:
        data: BMP file bytes

    Returns:
        True if format is correct
    """
    # Check signature
    if data[0:2] != b"BM":
        logging.error("Invalid BMP signature")
        return False

    # Check bit depth at offset 28 (2 bytes, little-endian)
    bit_depth = struct.unpack_from("<H", data, 28)[0]
    if bit_depth != 4:
        logging.error(f"Invalid bit depth: {bit_depth}, expected 4")
        return False

    # Check compression at offset 30 (4 bytes, little-endian)
    compression = struct.unpack_from("<I", data, 30)[0]
    if compression != BI_RLE4:
        logging.error(f"Invalid compression: {compression}, expected {BI_RLE4}")
        return False

    # Check dimensions
    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    if width != IMAGE_WIDTH or height != IMAGE_HEIGHT:
        logging.error(
            f"Invalid dimensions: {width}x{height}, expected {IMAGE_WIDTH}x{IMAGE_HEIGHT}"
        )
        return False

    logging.info("BMP format verification passed")
    logging.debug(f"  Bit depth: {bit_depth} (offset 28)")
    logging.debug(f"  Compression: {compression} (offset 30, BI_RLE4)")
    logging.debug(f"  Dimensions: {width}x{height}")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate pixel art cover images for story chapters using Gemini Flash 2.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_cover.py "A knight facing a dragon" -o chapter1.bmp
  python generate_cover.py "Mysterious forest with glowing mushrooms" --output cover.bmp
  python generate_cover.py "A ship sailing through a storm" -o storm.bmp --debug

Prerequisites:
  1. Google Cloud project with Vertex AI API enabled
  2. Authentication: gcloud auth application-default login

Environment Variables:
  GOOGLE_CLOUD_PROJECT   Required. Your Google Cloud project ID.
  GOOGLE_CLOUD_LOCATION  Optional. Region for Vertex AI (default: europe-west1).
                         Supported EU regions: europe-west1, europe-west4, 
                         europe-central2, europe-north1, europe-southwest1, europe-west8

Output Format:
  - 320x240 pixels, black and white
  - 4-bit BMP with RLE4 compression
  - 16-color grayscale palette
        """,
    )

    parser.add_argument(
        "description",
        help="Description of the chapter to generate a cover image for",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output file path for the BMP image (required)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Validate output path
    output_path: Path = args.output
    if output_path.suffix.lower() != ".bmp":
        output_path = output_path.with_suffix(".bmp")
        logging.warning(f"Output path changed to: {output_path}")

    # Get Vertex AI configuration
    project, location = get_vertex_ai_config()

    try:
        # Generate image with Gemini via Vertex AI
        logging.info(f"Generating cover for: {args.description[:50]}...")
        raw_image = generate_image_with_gemini(args.description, project, location)

        # Process image (resize, grayscale, quantize)
        processed_image = process_image(raw_image)

        # Create BMP with RLE4 compression
        bmp_data = create_bmp_rle4(processed_image)

        # Verify format
        if not verify_bmp_format(bmp_data):
            logging.error("Generated BMP does not meet format requirements")
            sys.exit(1)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(bmp_data)

        logging.info(f"Cover image saved to: {output_path}")
        logging.info(f"File size: {len(bmp_data):,} bytes")

    except Exception as e:
        logging.error(f"Failed to generate cover: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
