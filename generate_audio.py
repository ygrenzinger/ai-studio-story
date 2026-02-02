#!/usr/bin/env python3
"""
Generate audio files from story chapters using Gemini TTS via Vertex AI.

Converts audio-script markdown files to MP3 format with specific requirements:
- Format: MP3 (MPEG Audio Layer III)
- Channels: Mono (1 channel)
- Sample Rate: 44100 Hz
- ID3 Tags: NOT ALLOWED (must be stripped)

Usage:
    python generate_audio.py audio-scripts/stage-uuid.md -o output.mp3
    python generate_audio.py script.md -o output.mp3 --voice Puck
    python generate_audio.py script.md -o output.mp3 --debug --no-verify

Prerequisites:
    - Google Cloud project with Vertex AI API enabled
    - Authentication via: gcloud auth application-default login
    - Environment variables: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION (optional)
    - FFmpeg installed on system (required by pydub)
"""

import argparse
import io
import json
import logging
import os
import re
import struct
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from google import genai
from google.genai import types
from pydub import AudioSegment

# Constants
GEMINI_TTS_SAMPLE_RATE = 24000  # Gemini TTS outputs 24kHz
TARGET_SAMPLE_RATE = 44100  # Required output sample rate
TARGET_CHANNELS = 1  # Mono
DEFAULT_VOICE = "Sulafat"  # Warm voice for narrators
DEFAULT_TTS_MODEL = "gemini-2.5-flash-tts"

# Available voices (from voice-guide.md)
AVAILABLE_VOICES = {
    # Female voices
    "Zephyr",
    "Kore",
    "Leda",
    "Aoede",
    "Callirrhoe",
    "Autonoe",
    "Despina",
    "Erinome",
    "Gacrux",
    "Pulcherrima",
    "Achernar",
    "Vindemiatrix",
    "Laomedeia",
    "Sulafat",
    # Male voices
    "Puck",
    "Charon",
    "Fenrir",
    "Orus",
    "Enceladus",
    "Iapetus",
    "Umbriel",
    "Algieba",
    "Algenib",
    "Rasalgethi",
    "Alnilam",
    "Schedar",
    "Achird",
    "Zubenelgenubi",
    "Sadachbia",
    "Sadaltager",
}


@dataclass
class SpeakerConfig:
    """Configuration for a single speaker."""

    speaker: str
    voice_name: str = DEFAULT_VOICE


@dataclass
class AudioScript:
    """Parsed audio script from markdown file."""

    stage_uuid: str
    chapter_ref: str = ""
    speakers: list[str] = field(default_factory=list)
    tts_model: str = DEFAULT_TTS_MODEL
    speaker_configs: list[SpeakerConfig] = field(default_factory=list)

    # Raw content for TTS prompt
    full_prompt: str = ""


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


def parse_audio_script(file_path: Path) -> AudioScript:
    """Parse audio-script markdown file into AudioScript dataclass.

    Expected format:
    ---
    stageUuid: "stage-uuid"
    chapterRef: "chapter-ref"
    speakers: ["Narrator", "Character"]
    locale: "en-US"
    ---

    # AUDIO PROFILE: ...
    ## THE SCENE: ...
    ### DIRECTOR'S NOTES
    ...
    ## TRANSCRIPT
    **Speaker:** Dialogue
    ...
    ## TTS CONFIGURATION
    ```json
    {"speakerConfigs": [...]}
    ```

    Args:
        file_path: Path to the markdown file

    Returns:
        Parsed AudioScript dataclass

    Raises:
        ValueError: If file format is invalid
    """
    content = file_path.read_text(encoding="utf-8")

    # Split frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]
        else:
            raise ValueError("Invalid frontmatter format")
    else:
        raise ValueError("Missing YAML frontmatter (must start with ---)")

    # Parse frontmatter
    script = AudioScript(
        stage_uuid=frontmatter.get("stageUuid", ""),
        chapter_ref=frontmatter.get("chapterRef", ""),
        speakers=frontmatter.get("speakers", []),
    )

    # Extract TTS CONFIGURATION JSON block
    json_match = re.search(
        r"## TTS CONFIGURATION\s*```json\s*(\{.*?\})\s*```", body, re.DOTALL
    )
    if json_match:
        tts_config = json.loads(json_match.group(1))
        for cfg in tts_config.get("speakerConfigs", []):
            script.speaker_configs.append(
                SpeakerConfig(
                    speaker=cfg["speaker"],
                    voice_name=cfg.get("voiceName", DEFAULT_VOICE),
                )
            )

    # If no speaker configs, create defaults from speakers list
    if not script.speaker_configs and script.speakers:
        for speaker in script.speakers:
            script.speaker_configs.append(SpeakerConfig(speaker=speaker))

    # If still no configs, use default narrator
    if not script.speaker_configs:
        script.speaker_configs.append(
            SpeakerConfig(speaker="Narrator", voice_name=DEFAULT_VOICE)
        )

    # Extract content sections for prompt
    # Everything before ## TTS CONFIGURATION is the prompt
    tts_config_pos = body.find("## TTS CONFIGURATION")
    if tts_config_pos > 0:
        script.full_prompt = body[:tts_config_pos].strip()
    else:
        script.full_prompt = body.strip()

    return script


def build_tts_config(script: AudioScript) -> types.SpeechConfig:
    """Build Gemini TTS configuration from AudioScript.

    Args:
        script: Parsed audio script

    Returns:
        SpeechConfig for Gemini TTS API
    """
    if len(script.speaker_configs) == 1:
        # Single speaker mode
        voice_name = script.speaker_configs[0].voice_name
        logging.info(f"Single-speaker mode: {voice_name}")

        return types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        )
    else:
        # Multi-speaker mode (max 2 speakers supported by Gemini TTS)
        speaker_voice_configs = []
        for cfg in script.speaker_configs[:2]:  # Max 2 speakers
            logging.info(f"Speaker: {cfg.speaker} -> Voice: {cfg.voice_name}")
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=cfg.speaker,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=cfg.voice_name
                        )
                    ),
                )
            )

        if len(script.speaker_configs) > 2:
            logging.warning(
                f"Only first 2 speakers used (Gemini TTS limit). "
                f"Ignored: {[c.speaker for c in script.speaker_configs[2:]]}"
            )

        return types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
            )
        )


def generate_tts_audio(
    client: genai.Client, script: AudioScript, speech_config: types.SpeechConfig
) -> bytes:
    """Generate audio using Gemini TTS API.

    Args:
        client: Gemini API client
        script: Parsed audio script
        speech_config: TTS configuration

    Returns:
        Raw PCM audio data (24kHz, 16-bit, mono)

    Raises:
        RuntimeError: If no audio data in response
    """
    logging.info(f"Generating TTS audio with model: {script.tts_model}")
    logging.debug(f"Prompt length: {len(script.full_prompt)} characters")

    response = client.models.generate_content(
        model=script.tts_model,
        contents=script.full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )

    # Extract audio data from response
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            logging.info("TTS audio generated successfully")
            return part.inline_data.data

    raise RuntimeError("No audio data in TTS response")


def strip_id3_tags(mp3_data: bytes) -> bytes:
    """Remove ID3v1 and ID3v2 tags from MP3 data.

    ID3v2: Variable size at start, starts with "ID3"
    ID3v1: 128 bytes at end, starts with "TAG"

    Args:
        mp3_data: MP3 file bytes

    Returns:
        MP3 data with all ID3 tags removed
    """
    data = bytearray(mp3_data)

    # Strip ID3v2 (at beginning)
    while data[:3] == b"ID3":
        # ID3v2 header: "ID3" + 2 version bytes + 1 flags byte + 4 size bytes
        if len(data) < 10:
            break

        # Size is stored as syncsafe integer (7 bits per byte)
        size_bytes = data[6:10]
        size = (
            (size_bytes[0] & 0x7F) << 21
            | (size_bytes[1] & 0x7F) << 14
            | (size_bytes[2] & 0x7F) << 7
            | (size_bytes[3] & 0x7F)
        )

        # Total header size = 10 (header) + size (tag data)
        total_size = 10 + size
        logging.debug(f"Stripping ID3v2 tag: {total_size} bytes")
        data = data[total_size:]

    # Strip ID3v1 (at end) - always 128 bytes starting with "TAG"
    if len(data) >= 128 and data[-128:-125] == b"TAG":
        logging.debug("Stripping ID3v1 tag: 128 bytes")
        data = data[:-128]

    return bytes(data)


def convert_to_mp3(
    pcm_data: bytes, input_sample_rate: int = GEMINI_TTS_SAMPLE_RATE
) -> bytes:
    """Convert PCM audio to MP3 with required specifications.

    Conversion process:
    1. Load PCM data as WAV
    2. Resample to 44100 Hz
    3. Convert to mono
    4. Encode to MP3
    5. Strip ID3 tags

    Args:
        pcm_data: Raw PCM audio (16-bit signed)
        input_sample_rate: Source sample rate (default: 24000 Hz)

    Returns:
        MP3 data without ID3 tags
    """
    logging.info("Converting audio to MP3...")

    # Create WAV file in memory from PCM data
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(input_sample_rate)
        wf.writeframes(pcm_data)

    wav_buffer.seek(0)

    # Load with pydub
    audio = AudioSegment.from_wav(wav_buffer)
    logging.debug(
        f"Loaded audio: {audio.frame_rate}Hz, {audio.channels} channels, {len(audio)}ms"
    )

    # Resample to target sample rate
    if audio.frame_rate != TARGET_SAMPLE_RATE:
        logging.info(f"Resampling: {audio.frame_rate}Hz -> {TARGET_SAMPLE_RATE}Hz")
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

    # Convert to mono if needed
    if audio.channels != TARGET_CHANNELS:
        logging.info(
            f"Converting to mono: {audio.channels} -> {TARGET_CHANNELS} channels"
        )
        audio = audio.set_channels(TARGET_CHANNELS)

    # Export to MP3 (without ID3 tags)
    mp3_buffer = io.BytesIO()
    audio.export(
        mp3_buffer,
        format="mp3",
        parameters=["-id3v2_version", "0"],  # Disable ID3v2
    )

    mp3_data = mp3_buffer.getvalue()

    # Strip any remaining ID3 tags
    mp3_data = strip_id3_tags(mp3_data)

    logging.info(f"MP3 conversion complete: {len(mp3_data):,} bytes")
    return mp3_data


def verify_mp3_format(mp3_data: bytes) -> tuple[bool, list[str]]:
    """Verify MP3 meets required format specifications.

    Required:
    - Format: MP3 (MPEG Audio Layer III)
    - Channels: Mono (1 channel)
    - Sample Rate: 44100 Hz
    - ID3v1: NOT present
    - ID3v2: NOT present

    Args:
        mp3_data: MP3 file bytes

    Returns:
        Tuple of (passed: bool, issues: list[str])
    """
    issues = []

    # Check for ID3v2 tag at start
    if mp3_data[:3] == b"ID3":
        issues.append("ID3v2 tag present at start of file")

    # Check for ID3v1 tag at end
    if len(mp3_data) >= 128 and mp3_data[-128:-125] == b"TAG":
        issues.append("ID3v1 tag present at end of file")

    # Find first MP3 frame to verify format
    # MP3 frame sync: 11 bits set (0xFF followed by 0xE0 or higher)
    frame_start = -1
    for i in range(len(mp3_data) - 4):
        if mp3_data[i] == 0xFF and (mp3_data[i + 1] & 0xE0) == 0xE0:
            frame_start = i
            break

    if frame_start == -1:
        issues.append("No valid MP3 frame sync found")
        return False, issues

    # Parse MP3 frame header (4 bytes)
    header = struct.unpack(">I", mp3_data[frame_start : frame_start + 4])[0]

    # Extract fields from header
    # Bits 19-20: MPEG version (11 = MPEG1, 10 = MPEG2, 00 = MPEG2.5)
    version_bits = (header >> 19) & 0x03
    # Bits 17-18: Layer (01 = Layer III)
    layer_bits = (header >> 17) & 0x03
    # Bits 10-11: Sample rate index
    sample_rate_index = (header >> 10) & 0x03
    # Bit 6: Channel mode (00-10 = stereo variants, 11 = mono)
    channel_mode = (header >> 6) & 0x03

    # Verify Layer III
    if layer_bits != 0x01:
        issues.append(f"Not MP3 Layer III (layer bits: {layer_bits})")

    # Sample rate lookup table
    sample_rates = {
        0x03: {0: 44100, 1: 48000, 2: 32000},  # MPEG1
        0x02: {0: 22050, 1: 24000, 2: 16000},  # MPEG2
        0x00: {0: 11025, 1: 12000, 2: 8000},  # MPEG2.5
    }

    if version_bits in sample_rates and sample_rate_index in sample_rates[version_bits]:
        actual_rate = sample_rates[version_bits][sample_rate_index]
        if actual_rate != TARGET_SAMPLE_RATE:
            issues.append(
                f"Sample rate is {actual_rate}Hz, expected {TARGET_SAMPLE_RATE}Hz"
            )
    else:
        issues.append(
            f"Unable to determine sample rate (version: {version_bits}, index: {sample_rate_index})"
        )

    # Verify mono (channel mode 11 = single channel)
    if channel_mode != 0x03:
        mode_names = {0: "stereo", 1: "joint stereo", 2: "dual channel", 3: "mono"}
        issues.append(
            f"Channel mode is {mode_names.get(channel_mode, 'unknown')}, expected mono"
        )

    passed = len(issues) == 0

    if passed:
        logging.info("MP3 format verification: PASSED")
    else:
        logging.warning(f"MP3 format verification: FAILED ({len(issues)} issues)")
        for issue in issues:
            logging.warning(f"  - {issue}")

    return passed, issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate audio from story chapters using Gemini TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_audio.py audio-scripts/stage-forest.md -o forest.mp3
  python generate_audio.py script.md -o output.mp3 --voice Puck
  python generate_audio.py script.md -o output.mp3 --debug --no-verify

Prerequisites:
  1. Google Cloud project with Vertex AI API enabled
  2. Authentication: gcloud auth application-default login
  3. FFmpeg installed (required by pydub)

Environment Variables:
  GOOGLE_CLOUD_PROJECT   Required. Your Google Cloud project ID.
  GOOGLE_CLOUD_LOCATION  Optional. Region for Vertex AI (default: europe-west1).

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
        help="Enable debug logging",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip output format verification",
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
        # Parse audio script
        logging.info(f"Parsing audio script: {args.input}")
        script = parse_audio_script(args.input)
        logging.info(f"Stage UUID: {script.stage_uuid}")
        logging.info(f"Speakers: {[cfg.speaker for cfg in script.speaker_configs]}")

        # Override voice if specified
        if args.voice:
            if args.voice not in AVAILABLE_VOICES:
                logging.warning(
                    f"Voice '{args.voice}' not in known voices, using anyway"
                )
            script.speaker_configs = [
                SpeakerConfig(speaker="Narrator", voice_name=args.voice)
            ]
            logging.info(f"Voice override: {args.voice}")

        # Build TTS configuration
        speech_config = build_tts_config(script)

        # Get Vertex AI config
        project, location = get_vertex_ai_config()
        logging.info(
            f"Connecting to Vertex AI (project={project}, location={location})"
        )

        # Create client
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

        # Generate TTS audio
        pcm_data = generate_tts_audio(client, script, speech_config)
        logging.info(f"Received {len(pcm_data):,} bytes of PCM audio")

        # Convert to MP3
        mp3_data = convert_to_mp3(pcm_data)

        # Verify format (default: on)
        if not args.no_verify:
            passed, issues = verify_mp3_format(mp3_data)
            if not passed:
                logging.error("Output does not meet format requirements:")
                for issue in issues:
                    logging.error(f"  - {issue}")
                sys.exit(1)

        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(mp3_data)

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
