"""Command-line interface for audio generation."""

import argparse
import logging
import os
import sys
from pathlib import Path

from audio_generation.domain.constants import AVAILABLE_VOICES
from audio_generation.orchestrator import AudioGenerationPipeline
from audio_generation.parsing.script_parser import AudioScriptParser
from audio_generation.progress.progress_manager import ProgressManager
from audio_generation.providers.registry import create_provider
from audio_generation.utils.logging import setup_logging
from audio_generation.voices.registry import VoiceRegistry
from audio_generation.voices.resolver import resolve_voice


def get_tts_config() -> dict:
    """Get TTS configuration from environment.

    Returns:
        Dict with 'project' and 'location' keys for Vertex AI.

    Raises:
        SystemExit: If no authentication is configured.
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

    if project:
        return {"project": project, "location": location}

    logging.error(
        "No TTS authentication configured.\n"
        "Set GOOGLE_CLOUD_PROJECT to your Vertex AI project ID.\n"
        "Example: export GOOGLE_CLOUD_PROJECT=your-project-id"
    )
    sys.exit(1)


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


def print_voice_dry_run(input_path: Path, provider: str, voice_override: str | None) -> None:
    """Print provider voice resolution without making network calls."""

    script = AudioScriptParser().parse(input_path)
    registry = VoiceRegistry.load()

    print(f"Selected provider: {provider}")
    print()
    print("Speaker resolution:")
    for cfg in script.speaker_configs:
        if voice_override:
            cfg.voice = voice_override
            cfg.voice_role = None
            cfg.provider_voices.clear()
        resolved = resolve_voice(cfg, provider, registry, strict=False)
        print(f"  {resolved.speaker}")
        print(f"    role: {resolved.role or '-'}")
        print(f"    voice: {resolved.voice_id}")
        print(f"    source: {resolved.source}")


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate audio from story chapters using a TTS provider",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m audio_generation.cli audio-scripts/stage-forest.md -o forest.mp3
  python -m audio_generation.cli script.md -o output.mp3 --voice Puck
  python -m audio_generation.cli script.md -o output.mp3 --debug --no-verify
  python -m audio_generation.cli script.md -o output.mp3 --resume

Prerequisites:
   1. Google Cloud project with Vertex AI enabled
   2. FFmpeg installed (required by pydub)

Environment Variables:
   GOOGLE_CLOUD_PROJECT  Required. Vertex AI project ID.
   GOOGLE_CLOUD_REGION   Optional. Vertex AI region (default: us-central1).

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
        type=Path,
        help="Output MP3 file path (required unless --dry-run-voices)",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "grok"],
        default="gemini",
        help="TTS provider to use (default: gemini)",
    )
    parser.add_argument(
        "--voice",
        help="Override voice for single-speaker mode (e.g., Sulafat, Puck, Leda)",
    )
    parser.add_argument(
        "--model",
        help="Override TTS model (e.g., gemini-2.5-pro-preview-tts)",
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
    parser.add_argument(
        "--dry-run-voices",
        action="store_true",
        help="Print speaker voice resolution without generating audio",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Validate input file
    if not args.input.exists():
        logging.error(f"Input file not found: {args.input}")
        sys.exit(1)

    if args.dry_run_voices:
        print_voice_dry_run(args.input, args.provider, args.voice)
        return

    if args.output is None:
        logging.error("Output MP3 file path is required unless --dry-run-voices is used")
        sys.exit(1)

    # Ensure output has .mp3 extension
    output_path: Path = args.output
    if output_path.suffix.lower() != ".mp3":
        output_path = output_path.with_suffix(".mp3")
        logging.warning(f"Output path changed to: {output_path}")

    try:
        tts_config = {}
        if args.provider == "gemini":
            tts_config = get_tts_config()
            logging.info(
                f"Using Vertex AI (project={tts_config['project']}, "
                f"location={tts_config['location']})"
            )
        else:
            logging.info("Using Grok TTS")

        pipeline = AudioGenerationPipeline()

        script = pipeline.parse_script(args.input)
        tts_model = args.model or script.tts_model
        if args.model:
            logging.info(f"Model override: {tts_model}")
        if args.voice:
            if args.voice not in AVAILABLE_VOICES:
                logging.warning(f"Voice '{args.voice}' not in known voices, using anyway")
            logging.info(f"Voice override: {args.voice}")

        provider = create_provider(args.provider, model=tts_model, **tts_config)
        pipeline.set_provider(provider)

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
            voice_override=args.voice,
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
