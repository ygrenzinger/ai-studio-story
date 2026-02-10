"""Command-line interface for audio generation."""

import argparse
import logging
import os
import sys
from pathlib import Path

from audio_generation.domain.constants import AVAILABLE_VOICES
from audio_generation.orchestrator import AudioGenerationPipeline
from audio_generation.progress.progress_manager import ProgressManager
from audio_generation.tts.client import TTSClient
from audio_generation.utils.logging import setup_logging


def get_vertex_config() -> tuple[str, str]:
    """Get Vertex AI configuration from environment.

    Returns:
        Tuple of (project_id, location)

    Raises:
        SystemExit: If required environment variables are missing
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

    if not project:
        logging.error(
            "GOOGLE_CLOUD_PROJECT environment variable is not set.\n"
            "Please set it to your Google Cloud project ID.\n"
            "Example: export GOOGLE_CLOUD_PROJECT=my-project-id\n"
            "Also ensure you are authenticated via: gcloud auth application-default login"
        )
        sys.exit(1)
    return project, location


def print_progress(current: int, total: int) -> None:
    """Print progress bar for segment generation.

    Args:
        current: Current progress count
        total: Total items to process
    """
    bar_width = 40
    progress = current / total
    filled = int(bar_width * progress)
    bar = "=" * filled + "-" * (bar_width - filled)
    print(f"\rGenerating segments: [{bar}] {current}/{total}", end="", flush=True)
    if current == total:
        print()  # Newline at completion


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate audio from story chapters using Vertex AI Gemini TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m audio_generation.cli audio-scripts/stage-forest.md -o forest.mp3
  python -m audio_generation.cli script.md -o output.mp3 --voice Puck
  python -m audio_generation.cli script.md -o output.mp3 --debug --no-verify
  python -m audio_generation.cli script.md -o output.mp3 --resume

Prerequisites:
   1. Google Cloud project with Vertex AI API enabled
   2. Authenticated via: gcloud auth application-default login
   3. FFmpeg installed (required by pydub)

Environment Variables:
   GOOGLE_CLOUD_PROJECT  Required. Your Google Cloud project ID.
   GOOGLE_CLOUD_REGION   Optional. Region (default: us-central1).

Output Format:
  - MP3 (MPEG Audio Layer III)
  - Mono (1 channel)
  - 44100 Hz sample rate
  - No ID3 tags (ID3v1 and ID3v2 stripped)
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to audio-script markdown file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Output MP3 file path (required)",
    )
    parser.add_argument(
        "--voice",
        help="Override voice for single-speaker mode (e.g., Sulafat, Puck, Leda)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and save intermediate files",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip output format verification",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar output",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from saved progress (use after rate limit or other failure)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Validate input file
    if not args.input.exists():
        logging.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Ensure output has .mp3 extension
    output_path: Path = args.output
    if output_path.suffix.lower() != ".mp3":
        output_path = output_path.with_suffix(".mp3")
        logging.warning(f"Output path changed to: {output_path}")

    try:
        # Get Vertex AI configuration
        project, location = get_vertex_config()
        logging.info(
            f"Connecting to Vertex AI (project={project}, location={location})"
        )

        # Create pipeline with dependencies
        pipeline = AudioGenerationPipeline()

        # Parse script first to get model
        script = pipeline.parse_script(args.input)

        # Override voice if specified
        if args.voice:
            if args.voice not in AVAILABLE_VOICES:
                logging.warning(
                    f"Voice '{args.voice}' not in known voices, using anyway"
                )
            for cfg in script.speaker_configs:
                cfg.voice = args.voice
            logging.info(f"Voice override: {args.voice}")

        # Configure TTS client
        tts_client = TTSClient(
            project=project, location=location, model=script.tts_model
        )
        pipeline.set_tts_client(tts_client)

        # Configure progress manager
        progress_manager = ProgressManager(output_path.parent)
        pipeline.set_progress_manager(progress_manager)

        # Execute pipeline
        progress_callback = None if args.no_progress else print_progress

        mp3_data = pipeline.execute(
            input_file=args.input,
            output_path=output_path,
            resume=args.resume,
            verify=not args.no_verify,
            progress_callback=progress_callback,
        )

        logging.info(f"Audio saved to: {output_path}")
        logging.info(f"File size: {len(mp3_data):,} bytes")

    except Exception as e:
        logging.error(f"Failed to generate audio: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
