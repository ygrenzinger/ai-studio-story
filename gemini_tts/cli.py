"""Command-line interface for Gemini TTS."""

import logging
import sys
from pathlib import Path

import click

from gemini_tts import __version__
from gemini_tts.exceptions import AudioConversionException, TtsException
from gemini_tts.models import AudioFormat, Bitrate, ExitCode
from gemini_tts.services.audio_converter import AudioConverterService
from gemini_tts.services.tts_service import GeminiTextToSpeechService
from gemini_tts.utils.wav_utils import calculate_duration, format_duration
from gemini_tts.voices import DEFAULT_VOICE, is_valid_voice, list_voices


def validate_bitrate(ctx, param, value):
    """Validate bitrate value."""
    if value is None:
        return Bitrate.DEFAULT
    try:
        Bitrate(value)
        return value
    except ValueError as e:
        raise click.BadParameter(str(e))


def validate_format(ctx, param, value):
    """Validate and convert format value."""
    if value is None:
        return AudioFormat.MP3
    try:
        return AudioFormat(value.lower())
    except ValueError:
        raise click.BadParameter(f"Invalid format: {value}. Use 'mp3' or 'wav'.")


def validate_voice(ctx, param, value):
    """Validate voice name."""
    if not is_valid_voice(value):
        raise click.BadParameter(
            f"Invalid voice: {value}. Use --list-voices to see available voices."
        )
    return value


@click.command()
@click.option(
    "-t", "--text",
    help="Input text to convert to speech. Use '-' to read from stdin.",
)
@click.option(
    "-f", "--file",
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Read text from file.",
)
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=Path("output.mp3"),
    help="Output audio file path.",
)
@click.option(
    "-v", "--voice",
    default=DEFAULT_VOICE,
    callback=validate_voice,
    help=f"Voice name (default: {DEFAULT_VOICE}).",
)
@click.option(
    "-s", "--style",
    help="Style prompt (e.g., 'excited', 'calm', 'professional').",
)
@click.option(
    "-F", "--format",
    "audio_format",
    callback=validate_format,
    help="Output format: mp3 or wav (default: mp3).",
)
@click.option(
    "-b", "--bitrate",
    type=int,
    callback=validate_bitrate,
    help=f"MP3 bitrate in kbps: {', '.join(map(str, Bitrate.VALID_VALUES))} (default: {Bitrate.DEFAULT}).",
)
@click.option(
    "-l", "--list-voices",
    is_flag=True,
    help="List all available voices and exit.",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress progress output.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging.",
)
@click.version_option(version=__version__, prog_name="gemini-tts")
def main(
    text: str | None,
    file: Path | None,
    output: Path,
    voice: str,
    style: str | None,
    audio_format: AudioFormat,
    bitrate: int,
    list_voices: bool,
    quiet: bool,
    debug: bool,
):
    """Convert text to speech using Google's Gemini 2.5 TTS API.

    Examples:

    \b
      gemini-tts -t "Hello, world!" -o hello.mp3
      gemini-tts -f story.txt -v Puck -s excited
      echo "Hello" | gemini-tts -t - -o hello.wav -F wav
      gemini-tts --list-voices
    """
    # Configure logging
    log_level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Handle list-voices
    if list_voices:
        click.echo(list_voices_text())
        sys.exit(ExitCode.SUCCESS.value)

    # Validate input source
    if text is None and file is None:
        raise click.UsageError("Either --text or --file must be specified.")

    if text is not None and file is not None:
        raise click.UsageError("Cannot use both --text and --file.")

    # Read input text
    try:
        if text == "-":
            input_text = sys.stdin.read()
        elif text is not None:
            input_text = text
        else:
            input_text = file.read_text(encoding="utf-8")
    except IOError as e:
        click.echo(f"Error reading input: {e}", err=True)
        sys.exit(ExitCode.IO_ERROR.value)

    # Validate text
    if not input_text or not input_text.strip():
        click.echo("Error: Input text is empty.", err=True)
        sys.exit(ExitCode.USER_ERROR.value)

    # Ensure correct file extension
    if not output.suffix.lower() == audio_format.extension:
        output = output.with_suffix(audio_format.extension)

    # Generate and save
    exit_code = generate_and_save(
        text=input_text,
        voice=voice,
        style=style,
        audio_format=audio_format,
        bitrate=bitrate,
        output_path=output,
        quiet=quiet,
    )
    sys.exit(exit_code.value)


def list_voices_text() -> str:
    """Get the formatted list of voices."""
    from gemini_tts.voices import list_voices as get_voices_list
    return get_voices_list()


def generate_and_save(
    text: str,
    voice: str,
    style: str | None,
    audio_format: AudioFormat,
    bitrate: int,
    output_path: Path,
    quiet: bool,
) -> ExitCode:
    """Generate speech and save to file.

    Returns:
        Exit code indicating success or failure type.
    """
    def log(message: str):
        if not quiet:
            click.echo(message)

    try:
        # Initialize services
        tts_service = GeminiTextToSpeechService()
        audio_converter = AudioConverterService(bitrate=bitrate)

        # Generate speech
        log(f"Generating speech with voice '{voice}'...")
        if style:
            log(f"Using style: {style}")

        audio_data = tts_service.generate_speech(text, voice, style)
        log(f"Received audio format: {audio_data.mime_type}")

        # Convert to target format
        log(f"Converting to {audio_format.value.upper()}...")
        converted_audio = audio_converter.convert(audio_data, audio_format)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(converted_audio)

        # Print summary
        sample_rate = audio_data.sample_rate or 24000
        duration = calculate_duration(audio_data.data, sample_rate)
        file_size = len(converted_audio)
        log("")
        log("Success!")
        log(f"  Characters: {len(text)}")
        log(f"  Voice: {voice}")
        if style:
            log(f"  Style: {style}")
        log(f"  Output: {output_path}")
        log(f"  Size: {file_size:,} bytes")
        log(f"  Duration: {format_duration(duration)}")

        return ExitCode.SUCCESS

    except TtsException as e:
        click.echo(f"TTS Error: {e}", err=True)
        return ExitCode.API_ERROR

    except AudioConversionException as e:
        click.echo(f"Conversion Error: {e}", err=True)
        return ExitCode.CONVERSION_ERROR

    except IOError as e:
        click.echo(f"IO Error: {e}", err=True)
        return ExitCode.IO_ERROR

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            import traceback
            traceback.print_exc()
        return ExitCode.USER_ERROR


if __name__ == "__main__":
    main()
