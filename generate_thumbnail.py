#!/usr/bin/env python3
"""
Generate story thumbnail images using Gemini Flash 2.5 via Vertex AI.

Outputs 300x300 PNG files with colorful, child-friendly illustrations.

Usage:
    python generate_thumbnail.py "A magical space adventure with a young astronaut" -o thumbnail.png
    python generate_thumbnail.py "Friendly dragons in an enchanted forest" --output cover.png

Prerequisites:
    - Google Cloud project with Vertex AI API enabled
    - Authentication via: gcloud auth application-default login
    - Environment variables: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION (optional)
"""

import argparse
import io
import logging
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Constants
IMAGE_SIZE = 300  # 300x300 square thumbnail

# System prompt for thumbnail generation
SYSTEM_PROMPT = """You are an expert children's book illustrator creating thumbnail images for story collections.

STRICT REQUIREMENTS:
- Style: Colorful, warm, child-friendly illustration suitable for ages 5-10
- Composition: A single, clear focal image that represents the story theme
- Format: Square composition (will be displayed at 300x300 pixels)
- Colors: Vibrant but not overwhelming, warm palette preferred
- Appeal: Should immediately attract a child's attention and convey the story mood
- NO TEXT: NEVER include any text, titles, labels, captions, or written words in the image

ILLUSTRATION BEST PRACTICES:
- Use a central subject or scene that captures the story essence
- Keep the composition simple and readable at small sizes
- Use soft, rounded shapes appealing to children
- Ensure good contrast so the image reads well as a small thumbnail
- Think "children's picture book cover" aesthetic
- Avoid dark, scary, or overly complex imagery

OUTPUT: A colorful, inviting children's illustration with NO text or titles."""


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
        description: The story description to visualize
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
    full_prompt = f"{SYSTEM_PROMPT}\n\nSTORY DESCRIPTION TO ILLUSTRATE:\n{description}"

    logging.info("Generating thumbnail image...")
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
            image_data = part.inline_data.data
            image = Image.open(io.BytesIO(image_data))
            return image

    raise RuntimeError("No image was generated in the response")


def process_image(image: Image.Image) -> Image.Image:
    """Process image to 300x300 RGBA PNG.

    Args:
        image: Input PIL Image

    Returns:
        Processed PIL Image resized to 300x300
    """
    logging.info(f"Processing image: original size {image.size}, mode {image.mode}")

    # Resize to exact dimensions (300x300)
    if image.size != (IMAGE_SIZE, IMAGE_SIZE):
        logging.info(f"Resizing to {IMAGE_SIZE}x{IMAGE_SIZE}...")
        image = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)

    # Convert to RGBA for PNG output
    if image.mode != "RGBA":
        logging.info(f"Converting from {image.mode} to RGBA...")
        image = image.convert("RGBA")

    logging.info(f"Processed image: size {image.size}, mode {image.mode}")
    return image


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate story thumbnail images using Gemini Flash 2.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_thumbnail.py "A magical space adventure" -o thumbnail.png
  python generate_thumbnail.py "Friendly dragons in an enchanted forest" --output cover.png
  python generate_thumbnail.py "A brave knight's quest" -o thumb.png --debug

Prerequisites:
  1. Google Cloud project with Vertex AI API enabled
  2. Authentication: gcloud auth application-default login

Environment Variables:
  GOOGLE_CLOUD_PROJECT   Required. Your Google Cloud project ID.
  GOOGLE_CLOUD_LOCATION  Optional. Region for Vertex AI (default: europe-west1).

Output Format:
  - 300x300 pixels, colorful child-friendly illustration
  - PNG format with RGBA color
        """,
    )

    parser.add_argument(
        "description",
        help="Description of the story to generate a thumbnail for",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output file path for the PNG image (required)",
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
    if output_path.suffix.lower() != ".png":
        output_path = output_path.with_suffix(".png")
        logging.warning(f"Output path changed to: {output_path}")

    # Get Vertex AI configuration
    project, location = get_vertex_ai_config()

    try:
        # Generate image with Gemini via Vertex AI
        logging.info(f"Generating thumbnail for: {args.description[:80]}...")
        raw_image = generate_image_with_gemini(args.description, project, location)

        # Process image (resize to 300x300, convert to RGBA)
        processed_image = process_image(raw_image)

        # Save as PNG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        processed_image.save(output_path, format="PNG")

        file_size = output_path.stat().st_size
        logging.info(f"Thumbnail saved to: {output_path}")
        logging.info(f"File size: {file_size:,} bytes")

    except Exception as e:
        logging.error(f"Failed to generate thumbnail: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
