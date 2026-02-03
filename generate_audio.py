#!/usr/bin/env python3
"""
Generate audio files from story chapters using Gemini TTS via Google AI Studio.

Converts audio-script markdown files to MP3 format with specific requirements:
- Format: MP3 (MPEG Audio Layer III)
- Channels: Mono (1 channel)
- Sample Rate: 44100 Hz
- ID3 Tags: NOT ALLOWED (must be stripped)

This version uses per-segment TTS generation with sequential batch processing,
supporting unlimited speakers by batching narrator + character pairs.

Usage:
    python generate_audio.py audio-scripts/stage-uuid.md -o output.mp3
    python generate_audio.py script.md -o output.mp3 --voice Puck
    python generate_audio.py script.md -o output.mp3 --debug --no-verify

Prerequisites:
    - Google AI Studio API key (supports multi-speaker TTS)
    - Get an API key at: https://aistudio.google.com/apikey
    - Environment variables: GOOGLE_API_KEY or GEMINI_API_KEY
    - FFmpeg installed on system (required by pydub)
"""

import argparse
import array
import io
import json
import logging
import os
import re
import shutil
import struct
import sys
import tempfile
import time
import wave

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

import yaml
from google import genai
from google.genai import types
from pydub import AudioSegment
from pydub.silence import detect_leading_silence as pydub_detect_silence

# Constants
GEMINI_TTS_SAMPLE_RATE = 24000  # Gemini TTS outputs 24kHz
TARGET_SAMPLE_RATE = 44100  # Required output sample rate
TARGET_CHANNELS = 1  # Mono
DEFAULT_VOICE = "Sulafat"  # Warm voice for narrators
DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"  # Gemini TTS model

# Segment processing constants (updated based on audio production best practices)
SILENCE_BUFFER_MS = 200  # Normalized silence at segment edges (industry: 200-500ms)
INTER_SEGMENT_PAUSE_MS = 500  # Default pause between segments (fallback)
API_CALL_DELAY_SEC = 2  # 2 seconds between calls
MAX_RETRIES = 3  # Retry count per segment

# Advanced pause configuration (based on audiobook/podcast production standards)
FILE_LEADING_SILENCE_MS = 500  # Silence at start of audio file
FILE_TRAILING_SILENCE_MS = 1500  # Silence at end of audio file
CROSSFADE_MS = 75  # Crossfade duration (increased from 25ms for smoother transitions)

# Audio smoothing constants (for professional-grade transitions)
SEGMENT_FADE_IN_MS = 15  # Fade in at segment start to prevent clicks
SEGMENT_FADE_OUT_MS = 25  # Fade out at segment end (slightly longer for natural decay)
COMFORT_NOISE_LEVEL_DB = -55.0  # Target noise floor for comfort noise
NOISE_FADE_MS = 10  # Micro-fade on noise edges to prevent clicks

# Context-aware pause durations (in milliseconds)
PAUSE_NARRATOR_TO_NARRATOR_MS = 750  # Paragraph transition
PAUSE_NARRATOR_TO_CHARACTER_MS = 500  # Setup to dialogue
PAUSE_CHARACTER_TO_NARRATOR_MS = 500  # Return to narration
PAUSE_CHARACTER_TO_CHARACTER_MS = 400  # Quick dialogue exchange
PAUSE_SCENE_BREAK_MS = 2000  # Major scene/section change
PAUSE_DRAMATIC_MS = 1500  # Emotional moment

# Emotion-based pause modifiers (multiply base pause by this factor)
EMOTION_PAUSE_MODIFIERS: dict[str, float] = {
    # Longer pauses for dramatic effect
    "tense": 1.5,
    "suspense": 1.5,
    "mysterious": 1.3,
    "dramatic": 1.5,
    "sad": 1.4,
    "thoughtful": 1.3,
    "hushed": 1.2,
    "soft": 1.2,
    "gentle": 1.1,
    "warm": 1.1,
    "calm": 1.2,
    "reflective": 1.3,
    # Shorter pauses for energy
    "excited": 0.8,
    "rushed": 0.7,
    "urgent": 0.75,
    "breathless": 0.7,
    "action": 0.8,
    "energetic": 0.8,
    "lively": 0.85,
    "quick": 0.75,
}

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


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SpeakerConfig:
    """Configuration for a single speaker with voice profile."""

    name: str
    voice: str = DEFAULT_VOICE
    profile: str = ""  # Voice profile description for TTS guidance


@dataclass
class Segment:
    """A single speaker segment with optional emotion marker."""

    speaker: str
    text: str
    emotion: str = ""  # From <emotion:> marker or narrator context


@dataclass
class SegmentBatch:
    """A batch of segments for a single TTS call (max 2 speakers)."""

    segments: list[Segment]
    speakers: list[str]  # Unique speakers in this batch (max 2)


@dataclass
class AudioScript:
    """Parsed audio script from markdown file."""

    stage_uuid: str
    chapter_ref: str = ""
    locale: str = "en-US"
    speaker_configs: list[SpeakerConfig] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    tts_model: str = DEFAULT_TTS_MODEL


@dataclass
class PauseConfig:
    """Configuration for pause timing and audio smoothing.

    Based on audiobook and podcast production best practices:
    - Sentence end: 500-750ms
    - Paragraph/topic change: 1000-1500ms
    - Speaker change: 400-700ms
    - Scene change: 1500-2500ms
    - Dramatic pause: 1000-2000ms
    """

    # Pause timing settings
    narrator_to_narrator_ms: int = PAUSE_NARRATOR_TO_NARRATOR_MS
    narrator_to_character_ms: int = PAUSE_NARRATOR_TO_CHARACTER_MS
    character_to_narrator_ms: int = PAUSE_CHARACTER_TO_NARRATOR_MS
    character_to_character_ms: int = PAUSE_CHARACTER_TO_CHARACTER_MS
    scene_break_ms: int = PAUSE_SCENE_BREAK_MS
    dramatic_pause_ms: int = PAUSE_DRAMATIC_MS
    file_leading_ms: int = FILE_LEADING_SILENCE_MS
    file_trailing_ms: int = FILE_TRAILING_SILENCE_MS
    segment_edge_buffer_ms: int = SILENCE_BUFFER_MS
    crossfade_ms: int = CROSSFADE_MS

    # Audio smoothing settings (for professional-grade transitions)
    use_comfort_noise: bool = True  # Use comfort noise instead of digital silence
    comfort_noise_db: float = COMFORT_NOISE_LEVEL_DB  # Target noise level in dBFS
    crossfade_curve: str = "logarithmic"  # linear, logarithmic, exponential, s_curve
    segment_fade_in_ms: int = SEGMENT_FADE_IN_MS  # Fade in at segment start
    segment_fade_out_ms: int = SEGMENT_FADE_OUT_MS  # Fade out at segment end


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


# =============================================================================
# API Key Management
# =============================================================================


def get_api_key() -> str:
    """Get Google AI Studio API key from environment.

    The API key is required for TTS generation, especially for multi-speaker support
    which is only available through Google AI Studio (not Vertex AI).

    Returns:
        API key string

    Raises:
        SystemExit: If no API key is found in environment
    """
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error(
            "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is not set.\n"
            "Please set it to your Google AI Studio API key.\n"
            "Get an API key at: https://aistudio.google.com/apikey\n"
            "Example: export GOOGLE_API_KEY=your-api-key-here"
        )
        sys.exit(1)

    return api_key


# =============================================================================
# Transcript Parsing (New Format)
# =============================================================================


def split_by_emotions(text: str) -> list[tuple[str, str]]:
    """Split text by <emotion:> markers into (emotion, text) pairs.

    Args:
        text: Text that may contain <emotion:> markers

    Returns:
        List of (emotion, text) tuples. Empty emotion string if no marker.
    """
    # Pattern: <emotion: ...> followed by text
    pattern = r"<emotion:\s*([^>]+)>\s*"

    parts = re.split(pattern, text)
    # parts = [pre_text, emotion1, text1, emotion2, text2, ...]

    results = []

    # Text before first emotion marker (if any)
    if parts[0].strip():
        results.append(("", parts[0].strip()))

    # Process emotion + text pairs
    for i in range(1, len(parts), 2):
        emotion = parts[i].strip()
        segment_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if segment_text:
            results.append((emotion, segment_text))

    return results if results else [("", text.strip())]


def parse_transcript(
    content: str, speaker_configs: list[SpeakerConfig]
) -> list[Segment]:
    """Parse transcript content into ordered segments.

    Handles:
    - Speaker labels: **Speaker:** text
    - Emotion markers: <emotion: descriptor1, descriptor2>
    - Multiple emotions in one block (splits into multiple segments)

    Args:
        content: The transcript content (body after frontmatter)
        speaker_configs: List of configured speakers for validation

    Returns:
        List of Segment objects in order
    """
    segments = []
    valid_speakers = {cfg.name for cfg in speaker_configs}

    # Pattern: **Speaker:** followed by content until next **Speaker:** or end
    # Using a more robust approach: find all speaker markers first
    speaker_pattern = r"\*\*(\w+):\*\*"
    matches = list(re.finditer(speaker_pattern, content))

    for i, match in enumerate(matches):
        speaker = match.group(1)

        # Warn about undefined speakers
        if speaker not in valid_speakers:
            logging.warning(
                f"Speaker '{speaker}' found in transcript but not defined in frontmatter"
            )

        # Extract text until next speaker or end
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()

        # Skip empty segments
        if not text:
            continue

        # Check for multiple <emotion:> markers → split
        emotion_splits = split_by_emotions(text)

        for emotion, segment_text in emotion_splits:
            # Clean up the segment text (remove trailing dashes/separators)
            segment_text = re.sub(r"\n---\s*$", "", segment_text).strip()
            if not segment_text:
                continue

            segments.append(
                Segment(speaker=speaker, text=segment_text, emotion=emotion)
            )

    return segments


# =============================================================================
# Audio Script Parsing
# =============================================================================


def parse_audio_script(file_path: Path) -> AudioScript:
    """Parse audio-script markdown file into AudioScript dataclass.

    Expected format:
    ---
    stageUuid: "stage-uuid"
    chapterRef: "chapter-ref"
    locale: "en-US"
    speakers:
      - name: Narrator
        voice: Sulafat
        profile: "Warm storyteller..."
      - name: Emma
        voice: Leda
        profile: "8-year-old girl..."
    ---

    **Narrator:** <emotion: warm> Text with emotion marker inline...
    **Emma:** <emotion: curious> Character dialogue...

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

    # Parse speaker configs from frontmatter
    speaker_configs = []
    for speaker_data in frontmatter.get("speakers", []):
        if isinstance(speaker_data, dict):
            speaker_configs.append(
                SpeakerConfig(
                    name=speaker_data.get("name", "Narrator"),
                    voice=speaker_data.get("voice", DEFAULT_VOICE),
                    profile=speaker_data.get("profile", ""),
                )
            )

    # If no speakers defined, use default narrator
    if not speaker_configs:
        speaker_configs.append(
            SpeakerConfig(name="Narrator", voice=DEFAULT_VOICE, profile="")
        )

    # Parse segments from body
    segments = parse_transcript(body, speaker_configs)

    return AudioScript(
        stage_uuid=frontmatter.get("stageUuid", ""),
        chapter_ref=frontmatter.get("chapterRef", ""),
        locale=frontmatter.get("locale", "en-US"),
        speaker_configs=speaker_configs,
        segments=segments,
        tts_model=frontmatter.get("model", DEFAULT_TTS_MODEL),
    )


# =============================================================================
# Segment Batching
# =============================================================================


def batch_segments(segments: list[Segment]) -> list[SegmentBatch]:
    """Batch segments for TTS generation (max 2 speakers per batch).

    Strategy:
    - Each character segment batches with preceding narrator segments
    - Narrator-only sequences batch with the following character if one exists
    - Character-to-character transitions create separate single-speaker batches

    Args:
        segments: List of parsed segments in order

    Returns:
        List of SegmentBatch objects ready for TTS generation
    """
    if not segments:
        return []

    batches = []
    pending_narrator: list[Segment] = []

    for segment in segments:
        if segment.speaker == "Narrator":
            pending_narrator.append(segment)
        else:
            # Character segment - batch with pending narrator
            if pending_narrator:
                batch = SegmentBatch(
                    segments=pending_narrator + [segment],
                    speakers=["Narrator", segment.speaker],
                )
                pending_narrator = []
            else:
                # No preceding narrator - single speaker batch
                batch = SegmentBatch(
                    segments=[segment],
                    speakers=[segment.speaker],
                )
            batches.append(batch)

    # Handle trailing narrator segments
    if pending_narrator:
        batches.append(
            SegmentBatch(
                segments=pending_narrator,
                speakers=["Narrator"],
            )
        )

    return batches


# =============================================================================
# TTS Configuration Building
# =============================================================================


def build_single_speaker_config(speaker_config: SpeakerConfig) -> types.SpeechConfig:
    """Build TTS config for single speaker.

    Args:
        speaker_config: Speaker configuration

    Returns:
        SpeechConfig for Gemini TTS API
    """
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=speaker_config.voice
            )
        )
    )


def build_multi_speaker_config(
    speaker_configs: list[SpeakerConfig],
) -> types.SpeechConfig:
    """Build TTS config for multiple speakers (max 2).

    Args:
        speaker_configs: List of speaker configurations

    Returns:
        SpeechConfig for Gemini TTS API with multi-speaker support
    """
    speaker_voice_configs = []
    for cfg in speaker_configs:
        speaker_voice_configs.append(
            types.SpeakerVoiceConfig(
                speaker=cfg.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=cfg.voice
                    )
                ),
            )
        )

    return types.SpeechConfig(
        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_voice_configs
        )
    )


def build_batch_speech_config(
    batch: SegmentBatch, speaker_configs_map: dict[str, SpeakerConfig]
) -> types.SpeechConfig:
    """Build speech config for a batch.

    Args:
        batch: The segment batch
        speaker_configs_map: Mapping of speaker name to config

    Returns:
        SpeechConfig appropriate for the batch
    """
    if len(batch.speakers) == 1:
        return build_single_speaker_config(speaker_configs_map[batch.speakers[0]])
    else:
        configs = [speaker_configs_map[s] for s in batch.speakers]
        return build_multi_speaker_config(configs)


# =============================================================================
# TTS Prompt Building
# =============================================================================


def build_batch_prompt(
    batch: SegmentBatch, speaker_configs_map: dict[str, SpeakerConfig]
) -> str:
    """Build TTS prompt for a segment batch.

    Includes voice profiles and emotion markers as style guidance.

    Args:
        batch: The segment batch
        speaker_configs_map: Mapping of speaker name to config

    Returns:
        Formatted prompt for TTS generation
    """
    prompt_parts = []

    # Add style guidance header with profiles
    style_parts = []
    for speaker in batch.speakers:
        config = speaker_configs_map.get(speaker)
        if config and config.profile:
            style_parts.append(f"{speaker}: {config.profile}")

    if style_parts:
        prompt_parts.append(
            "[VOICE PROFILES - Use for tone and character, do not read aloud]\n"
            + "\n".join(style_parts)
        )
        prompt_parts.append("")

    # Add transcript with emotion markers
    prompt_parts.append("[TRANSCRIPT - Read aloud with indicated emotions]")

    for segment in batch.segments:
        if segment.emotion:
            # Include emotion as inline guidance
            prompt_parts.append(
                f"**{segment.speaker}:** [{segment.emotion}] {segment.text}"
            )
        else:
            prompt_parts.append(f"**{segment.speaker}:** {segment.text}")

    return "\n".join(prompt_parts)


# =============================================================================
# TTS Generation
# =============================================================================


def generate_batch_audio(
    client: genai.Client,
    batch: SegmentBatch,
    batch_num: int,
    speaker_configs_map: dict[str, SpeakerConfig],
    tts_model: str,
) -> bytes:
    """Generate audio for a single segment batch.

    Args:
        client: Gemini API client
        batch: The segment batch to generate
        batch_num: Batch number for logging (1-indexed)
        speaker_configs_map: Mapping of speaker name to config
        tts_model: TTS model to use

    Returns:
        Raw PCM audio data

    Raises:
        RuntimeError: If no audio data in response
    """
    # Build prompt and speech config
    prompt = build_batch_prompt(batch, speaker_configs_map)
    speech_config = build_batch_speech_config(batch, speaker_configs_map)

    logging.debug(f"Batch {batch_num} prompt ({len(prompt)} chars):\n{prompt[:500]}...")

    response = client.models.generate_content(
        model=tts_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )

    # Extract audio data from response
    if response.candidates and response.candidates[0].content:
        parts = response.candidates[0].content.parts
        if parts:
            for part in parts:
                if part.inline_data is not None and part.inline_data.data is not None:
                    return part.inline_data.data

    raise RuntimeError("No audio data in TTS response")


def generate_batch_with_retry(
    client: genai.Client,
    batch: SegmentBatch,
    batch_num: int,
    speaker_configs_map: dict[str, SpeakerConfig],
    tts_model: str,
    max_retries: int = MAX_RETRIES,
) -> bytes:
    """Generate audio for a batch with retry logic.

    Args:
        client: Gemini API client
        batch: The segment batch
        batch_num: Batch number for logging (1-indexed)
        speaker_configs_map: Mapping of speaker name to config
        tts_model: TTS model to use
        max_retries: Maximum retry attempts

    Returns:
        Raw PCM audio data

    Raises:
        RuntimeError: If generation fails after all retries
    """
    for attempt in range(max_retries):
        try:
            return generate_batch_audio(
                client, batch, batch_num, speaker_configs_map, tts_model
            )
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(
                    f"Batch {batch_num} generation failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                time.sleep(1 * (attempt + 1))  # Exponential backoff
            else:
                logging.error(
                    f"Batch {batch_num} failed after {max_retries} attempts: {e}"
                )
                raise RuntimeError(
                    f"Batch {batch_num} failed after {max_retries} attempts: {e}"
                ) from e

    raise RuntimeError(f"Batch {batch_num} failed: max retries exceeded")


def generate_all_batches(
    client: genai.Client,
    batches: list[SegmentBatch],
    speaker_configs_map: dict[str, SpeakerConfig],
    tts_model: str,
    progress_callback: Callable[[int, int], None] | None = None,
    delay_seconds: float = API_CALL_DELAY_SEC,
) -> list[bytes]:
    """Generate audio for all batches sequentially with rate limiting.

    Args:
        client: Gemini API client
        batches: List of segment batches
        speaker_configs_map: Mapping of speaker name to config
        tts_model: TTS model to use
        progress_callback: Optional callback for progress updates
        delay_seconds: Delay between API calls (default: 2s)

    Returns:
        List of raw PCM audio data in batch order

    Raises:
        RuntimeError: If any batch fails after retries
    """
    results: list[bytes] = []

    for i, batch in enumerate(batches):
        # Rate limiting delay (skip for first request)
        if i > 0:
            logging.debug(f"Rate limit delay: {delay_seconds}s")
            time.sleep(delay_seconds)

        batch_num = i + 1
        audio_data = generate_batch_with_retry(
            client, batch, batch_num, speaker_configs_map, tts_model
        )
        results.append(audio_data)

        if progress_callback:
            progress_callback(batch_num, len(batches))

    return results


# =============================================================================
# Progress Display
# =============================================================================


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


# =============================================================================
# Audio Processing
# =============================================================================


def pcm_to_audio_segment(
    pcm_data: bytes, sample_rate: int = GEMINI_TTS_SAMPLE_RATE
) -> AudioSegment:
    """Convert raw PCM data to AudioSegment.

    Args:
        pcm_data: Raw PCM audio (16-bit signed, mono)
        sample_rate: Source sample rate

    Returns:
        AudioSegment object
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)

    wav_buffer.seek(0)
    return AudioSegment.from_wav(wav_buffer)


def normalize_segment_audio(
    audio: AudioSegment,
    buffer_ms: int = SILENCE_BUFFER_MS,
    fade_in_ms: int = SEGMENT_FADE_IN_MS,
    fade_out_ms: int = SEGMENT_FADE_OUT_MS,
    use_comfort_noise: bool = True,
    comfort_noise_db: float = COMFORT_NOISE_LEVEL_DB,
) -> AudioSegment:
    """Normalize segment with fades and comfort noise buffers.

    Processing pipeline:
    1. Trim existing silence from edges
    2. Apply fade in/out to speech content to prevent clicks
    3. Add comfort noise buffer at both ends (or digital silence if disabled)

    Args:
        audio: Input audio segment
        buffer_ms: Target buffer duration in milliseconds
        fade_in_ms: Fade in duration for speech start
        fade_out_ms: Fade out duration for speech end
        use_comfort_noise: Use comfort noise instead of digital silence
        comfort_noise_db: Target noise level for comfort noise

    Returns:
        Normalized audio segment with smooth edges
    """
    # Detect and trim leading/trailing silence
    silence_threshold = audio.dBFS - 16 if audio.dBFS > -float("inf") else -50

    # Use pydub's silence detection
    start_trim = pydub_detect_silence(audio, silence_threshold=silence_threshold)
    end_trim = pydub_detect_silence(
        audio.reverse(), silence_threshold=silence_threshold
    )

    # Trim silence (with safety bounds)
    duration = len(audio)
    start_trim = min(start_trim, duration // 2)
    end_trim = min(end_trim, duration // 2)

    if start_trim + end_trim < duration:
        trimmed = audio[start_trim : duration - end_trim]
    else:
        trimmed = audio  # Don't trim if it would remove everything

    # Apply fades to the speech content to prevent clicks
    trimmed_len = len(trimmed)
    if trimmed_len > fade_in_ms + fade_out_ms:
        trimmed = trimmed.fade_in(fade_in_ms).fade_out(fade_out_ms)
    elif trimmed_len > 20:  # Minimum viable fade
        mini_fade = max(5, trimmed_len // 4)
        trimmed = trimmed.fade_in(mini_fade).fade_out(mini_fade)

    # Add buffer with comfort noise or digital silence
    if use_comfort_noise and buffer_ms > 0:
        buffer = generate_comfort_noise(
            buffer_ms,
            target_db=comfort_noise_db,
            sample_rate=audio.frame_rate,
            reference_audio=audio,
        )
    else:
        buffer = AudioSegment.silent(duration=buffer_ms, frame_rate=audio.frame_rate)

    return buffer + trimmed + buffer


def generate_comfort_noise(
    duration_ms: int,
    target_db: float = COMFORT_NOISE_LEVEL_DB,
    sample_rate: int = TARGET_SAMPLE_RATE,
    reference_audio: AudioSegment | None = None,
) -> AudioSegment:
    """Generate low-level pink noise to replace digital silence.

    Uses pink noise (1/f spectrum) which sounds more natural than white noise
    and better matches room tone. If reference_audio is provided, the noise
    level is adjusted to match the reference's noise floor.

    Args:
        duration_ms: Duration in milliseconds
        target_db: Target noise level in dBFS (default -55 dB)
        sample_rate: Output sample rate
        reference_audio: Optional audio to match noise floor from

    Returns:
        AudioSegment containing comfort noise
    """
    if duration_ms <= 0:
        return AudioSegment.silent(duration=0, frame_rate=sample_rate)

    num_samples = int(sample_rate * duration_ms / 1000)

    # Generate white noise as base
    white = np.random.randn(num_samples)

    # Apply simple pink noise approximation using a cumulative filter
    # This gives 1/f characteristics (equal energy per octave)
    pink = np.zeros(num_samples)
    b0, b1, b2 = 0.0, 0.0, 0.0
    for i in range(num_samples):
        white_sample = white[i]
        b0 = 0.99886 * b0 + white_sample * 0.0555179
        b1 = 0.99332 * b1 + white_sample * 0.0750759
        b2 = 0.96900 * b2 + white_sample * 0.1538520
        pink[i] = b0 + b1 + b2 + white_sample * 0.5362
    pink = pink / np.max(np.abs(pink)) if np.max(np.abs(pink)) > 0 else pink

    # Adjust target level if reference audio provided
    if reference_audio is not None and reference_audio.dBFS > -float("inf"):
        # Match slightly below the reference's quiet portions
        ref_noise_floor = analyze_noise_floor(reference_audio)
        target_db = min(target_db, ref_noise_floor - 3)

    # Convert dB to linear amplitude (16-bit range)
    target_amplitude = 10 ** (target_db / 20) * 32767

    # Scale noise to target level
    pink = (pink * target_amplitude).astype(np.int16)

    # Convert to AudioSegment
    noise_segment = AudioSegment(
        data=pink.tobytes(),
        sample_width=2,
        frame_rate=sample_rate,
        channels=1,
    )

    # Apply micro-fades to prevent clicks at edges
    if duration_ms > NOISE_FADE_MS * 2:
        noise_segment = noise_segment.fade_in(NOISE_FADE_MS).fade_out(NOISE_FADE_MS)

    return noise_segment


def analyze_noise_floor(audio: AudioSegment, percentile: int = 10) -> float:
    """Analyze the noise floor of an audio segment.

    Examines the quietest portions of the audio to determine
    the inherent noise floor level.

    Args:
        audio: Audio segment to analyze
        percentile: Lower percentile to consider as noise floor (default 10)

    Returns:
        Noise floor level in dBFS
    """
    # Get samples as numpy array
    samples = np.array(audio.get_array_of_samples(), dtype=np.float64)

    # Calculate RMS in small windows (10ms windows)
    window_size = int(audio.frame_rate * 0.010)
    num_windows = len(samples) // window_size

    if num_windows < 10:
        # Not enough data, return conservative estimate
        return audio.dBFS - 20 if audio.dBFS > -float("inf") else -60

    rms_values = []
    for i in range(num_windows):
        window = samples[i * window_size : (i + 1) * window_size]
        rms = np.sqrt(np.mean(window**2))
        if rms > 0:
            rms_values.append(rms)

    if not rms_values:
        return -60  # Default quiet level

    # Get the percentile (quietest non-silent portions)
    noise_floor_rms = np.percentile(rms_values, percentile)

    # Convert to dBFS (relative to 16-bit max)
    if noise_floor_rms > 0:
        noise_floor_db = 20 * np.log10(noise_floor_rms / 32767)
    else:
        noise_floor_db = -60

    return float(noise_floor_db)


def detect_natural_pauses(text: str) -> int:
    """Detect if text ends with pause-indicating punctuation.

    Analyzes the ending punctuation to determine if additional pause
    is needed beyond the base pause duration.

    Args:
        text: Text content to analyze

    Returns:
        Additional pause duration in milliseconds
    """
    stripped = text.rstrip()

    # Ellipsis indicates trailing thought - needs longer pause
    if stripped.endswith("..."):
        return 750

    # Em-dash indicates abrupt cut/interruption - shorter pause
    if stripped.endswith("—") or stripped.endswith("--"):
        return 200

    # Question mark - slight pause for implied response
    if stripped.endswith("?"):
        return 300

    # Exclamation - slight pause for emphasis to land
    if stripped.endswith("!"):
        return 200

    return 0


def get_emotion_modifier(emotion: str) -> float:
    """Get pause duration modifier based on emotion.

    Emotional content affects pacing - tense moments need longer pauses,
    exciting moments need shorter pauses.

    Args:
        emotion: Emotion string from segment (may contain multiple descriptors)

    Returns:
        Multiplier for base pause duration (default 1.0)
    """
    if not emotion:
        return 1.0

    # Parse emotion string (may be comma-separated: "tense, hushed")
    emotion_lower = emotion.lower()
    modifiers = []

    for emotion_key, modifier in EMOTION_PAUSE_MODIFIERS.items():
        if emotion_key in emotion_lower:
            modifiers.append(modifier)

    if not modifiers:
        return 1.0

    # Average the modifiers if multiple emotions detected
    return sum(modifiers) / len(modifiers)


def calculate_pause_duration(
    prev_segment: Segment | None,
    next_segment: Segment | None,
    pause_config: PauseConfig,
) -> int:
    """Calculate context-appropriate pause between segments.

    Considers:
    - Speaker transition type (narrator↔character, character↔character)
    - Emotion of the previous segment
    - Punctuation-based pauses (ellipsis, em-dash, question mark)

    Args:
        prev_segment: Previous segment (None for file start)
        next_segment: Next segment (None for file end)
        pause_config: Pause configuration settings

    Returns:
        Calculated pause duration in milliseconds
    """
    if prev_segment is None or next_segment is None:
        return pause_config.narrator_to_narrator_ms

    # Determine base pause from speaker transition type
    prev_is_narrator = prev_segment.speaker == "Narrator"
    next_is_narrator = next_segment.speaker == "Narrator"

    if prev_is_narrator and next_is_narrator:
        base_pause = pause_config.narrator_to_narrator_ms
    elif prev_is_narrator:
        base_pause = pause_config.narrator_to_character_ms
    elif next_is_narrator:
        base_pause = pause_config.character_to_narrator_ms
    else:
        # Character to different character - check if same speaker
        if prev_segment.speaker == next_segment.speaker:
            base_pause = pause_config.character_to_character_ms
        else:
            # Different characters talking - slightly longer
            base_pause = int(pause_config.character_to_character_ms * 1.25)

    # Apply emotion modifier from previous segment
    emotion_modifier = get_emotion_modifier(prev_segment.emotion)

    # Add punctuation-based pause
    punctuation_pause = detect_natural_pauses(prev_segment.text)

    # Calculate final pause
    final_pause = int(base_pause * emotion_modifier) + punctuation_pause

    logging.debug(
        f"Pause: {prev_segment.speaker}→{next_segment.speaker} = "
        f"{base_pause}ms × {emotion_modifier:.2f} + {punctuation_pause}ms = {final_pause}ms"
    )

    return final_pause


def apply_crossfade(
    audio1: AudioSegment,
    audio2: AudioSegment,
    crossfade_ms: int = CROSSFADE_MS,
    curve_type: str = "logarithmic",
) -> AudioSegment:
    """Apply crossfade between two audio segments with configurable curve.

    Crossfading prevents clicks and pops at edit points by smoothly
    transitioning between segments. Non-linear curves provide more
    natural-sounding transitions than linear crossfades.

    Curve types:
    - "linear": Standard linear fade (pydub default)
    - "logarithmic": Slower start, faster end - natural decay
    - "exponential": Faster start, slower end - natural attack
    - "s_curve": Slow start/end, fast middle - smoothest perceived transition

    Args:
        audio1: First audio segment
        audio2: Second audio segment
        crossfade_ms: Duration of crossfade overlap in milliseconds
        curve_type: Type of fade curve to apply

    Returns:
        Combined audio with crossfade applied
    """
    if crossfade_ms <= 0:
        return audio1 + audio2

    # Ensure crossfade doesn't exceed segment lengths
    max_crossfade = min(len(audio1), len(audio2), crossfade_ms)

    if max_crossfade < 10:  # Too short for meaningful crossfade
        return audio1 + audio2

    if max_crossfade < crossfade_ms:
        logging.debug(
            f"Reducing crossfade from {crossfade_ms}ms to {max_crossfade}ms "
            f"(segment too short)"
        )

    # For linear curves, use pydub's built-in (more efficient)
    if curve_type == "linear":
        return audio1.append(audio2, crossfade=max_crossfade)

    # For non-linear curves, we need manual implementation
    # Extract crossfade regions
    fade_out_region = audio1[-max_crossfade:]
    fade_in_region = audio2[:max_crossfade]

    # Get samples as numpy arrays
    samples1 = np.array(fade_out_region.get_array_of_samples(), dtype=np.float64)
    samples2 = np.array(fade_in_region.get_array_of_samples(), dtype=np.float64)

    # Ensure same length (may differ slightly due to sample rate rounding)
    min_len = min(len(samples1), len(samples2))
    samples1 = samples1[:min_len]
    samples2 = samples2[:min_len]

    num_samples = min_len
    t = np.linspace(0, 1, num_samples)

    # Generate fade curves based on type
    if curve_type == "logarithmic":
        # Logarithmic: slow decay, natural for audio fade-outs
        fade_out = 1 - np.log1p(t * (np.e - 1)) / np.log(np.e)
        fade_in = np.log1p(t * (np.e - 1)) / np.log(np.e)
    elif curve_type == "exponential":
        # Exponential: quick start, slow finish
        fade_out = 1 - t**2
        fade_in = t**2
    elif curve_type == "s_curve":
        # S-curve (smoothstep): slow-fast-slow, very smooth
        fade_in = t * t * (3 - 2 * t)  # smoothstep function
        fade_out = 1 - fade_in
    else:
        # Fallback to linear
        fade_out = 1 - t
        fade_in = t

    # Apply fades and mix
    mixed = (samples1 * fade_out + samples2 * fade_in).astype(np.int16)

    # Create mixed segment with same properties as original
    mixed_segment = fade_out_region._spawn(
        array.array(fade_out_region.array_type, mixed)
    )

    # Combine: audio1 (without overlap) + mixed + audio2 (without overlap)
    result = audio1[:-max_crossfade] + mixed_segment + audio2[max_crossfade:]

    return result


def concatenate_segment_audio(
    audio_segments: list[bytes],
    output_path: Path,
    pause_ms: int = INTER_SEGMENT_PAUSE_MS,
    buffer_ms: int = SILENCE_BUFFER_MS,
    segment_metadata: list[Segment] | None = None,
    pause_config: PauseConfig | None = None,
) -> None:
    """Concatenate segment audio with professional-grade transitions.

    Enhanced pipeline for smooth audio transitions:
    1. Convert PCM to AudioSegment
    2. Analyze overall noise floor for consistency
    3. Normalize each segment with comfort noise buffers and fades
    4. Calculate context-aware pause durations
    5. Join with comfort noise pauses and non-linear crossfades
    6. Add file-level leading/trailing with comfort noise

    Args:
        audio_segments: List of raw PCM audio data
        output_path: Output MP3 file path
        pause_ms: Default pause duration between segments (fallback)
        buffer_ms: Silence buffer for normalization
        segment_metadata: Optional list of Segment objects for context-aware pausing
        pause_config: Optional PauseConfig for timing customization
    """
    if not audio_segments:
        raise ValueError("No audio segments to concatenate")

    # Use default config if not provided
    config = pause_config or PauseConfig()

    # Determine if we can use context-aware pausing
    use_context_aware = segment_metadata is not None and len(segment_metadata) == len(
        audio_segments
    )

    smoothing_mode = "comfort noise" if config.use_comfort_noise else "digital silence"
    if use_context_aware:
        logging.info(
            f"Concatenating {len(audio_segments)} segments with context-aware pausing "
            f"({smoothing_mode}, {config.crossfade_curve} crossfade)"
        )
    else:
        logging.info(
            f"Concatenating {len(audio_segments)} segments with {pause_ms}ms pauses "
            f"({smoothing_mode})"
        )

    # Step 1: Convert all PCM to AudioSegment
    raw_segments: list[AudioSegment] = []
    for pcm_data in audio_segments:
        audio = pcm_to_audio_segment(pcm_data)
        raw_segments.append(audio)

    # Step 2: Analyze overall noise floor for consistency (if using comfort noise)
    target_noise_db = config.comfort_noise_db
    if config.use_comfort_noise and raw_segments:
        noise_floors = [
            analyze_noise_floor(seg) for seg in raw_segments if seg.dBFS > -float("inf")
        ]
        if noise_floors:
            avg_noise_floor = float(np.mean(noise_floors))
            # Use slightly below average to be subtle
            target_noise_db = min(config.comfort_noise_db, avg_noise_floor - 5)
            logging.debug(f"Target comfort noise level: {target_noise_db:.1f} dBFS")

    # Step 3: Normalize each segment with fades and comfort noise
    processed_segments: list[AudioSegment] = []
    for i, audio in enumerate(raw_segments):
        normalized = normalize_segment_audio(
            audio,
            buffer_ms=config.segment_edge_buffer_ms,
            fade_in_ms=config.segment_fade_in_ms,
            fade_out_ms=config.segment_fade_out_ms,
            use_comfort_noise=config.use_comfort_noise,
            comfort_noise_db=target_noise_db,
        )
        processed_segments.append(normalized)
        logging.debug(
            f"Segment {i + 1}: {len(audio)}ms -> {len(normalized)}ms (normalized)"
        )

    # Step 4 & 5: Combine with context-aware pauses and non-linear crossfades
    # Generate leading buffer (comfort noise or silence)
    if config.use_comfort_noise:
        combined = generate_comfort_noise(
            config.file_leading_ms,
            target_db=target_noise_db,
            sample_rate=TARGET_SAMPLE_RATE,
        )
    else:
        combined = AudioSegment.silent(duration=config.file_leading_ms)

    for i, segment_audio in enumerate(processed_segments):
        if i == 0:
            # First segment - join with leading buffer
            combined = apply_crossfade(
                combined,
                segment_audio,
                config.crossfade_ms,
                config.crossfade_curve,
            )
        else:
            # Calculate pause duration
            if use_context_aware and segment_metadata:
                prev_seg = segment_metadata[i - 1]
                curr_seg = segment_metadata[i]
                pause_duration = calculate_pause_duration(prev_seg, curr_seg, config)
            else:
                pause_duration = pause_ms

            # Create pause with comfort noise or digital silence
            if config.use_comfort_noise:
                pause = generate_comfort_noise(
                    pause_duration,
                    target_db=target_noise_db,
                    sample_rate=TARGET_SAMPLE_RATE,
                )
            else:
                pause = AudioSegment.silent(duration=pause_duration)

            # Apply crossfade through the pause to the next segment
            combined = apply_crossfade(
                combined,
                pause,
                config.crossfade_ms,
                config.crossfade_curve,
            )
            combined = apply_crossfade(
                combined,
                segment_audio,
                config.crossfade_ms,
                config.crossfade_curve,
            )

    # Step 6: Add trailing buffer
    if config.use_comfort_noise:
        trailing = generate_comfort_noise(
            config.file_trailing_ms,
            target_db=target_noise_db,
            sample_rate=TARGET_SAMPLE_RATE,
        )
    else:
        trailing = AudioSegment.silent(duration=config.file_trailing_ms)

    combined = apply_crossfade(
        combined,
        trailing,
        config.crossfade_ms,
        config.crossfade_curve,
    )

    # Ensure correct format (mono, 44100Hz)
    if combined.frame_rate != TARGET_SAMPLE_RATE:
        combined = combined.set_frame_rate(TARGET_SAMPLE_RATE)
    if combined.channels != TARGET_CHANNELS:
        combined = combined.set_channels(TARGET_CHANNELS)

    # Export to MP3 without ID3 tags
    mp3_buffer = io.BytesIO()
    combined.export(
        mp3_buffer,
        format="mp3",
        parameters=["-id3v2_version", "0"],
    )

    mp3_data = mp3_buffer.getvalue()

    # Strip any remaining ID3 tags
    mp3_data = strip_id3_tags(mp3_data)

    # Ensure output directory exists and save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(mp3_data)

    logging.info(f"Concatenated audio saved to: {output_path}")
    logging.info(
        f"Total duration: {len(combined)}ms "
        f"(incl. {config.file_leading_ms}ms lead + {config.file_trailing_ms}ms trail), "
        f"File size: {len(mp3_data):,} bytes"
    )


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


# =============================================================================
# MP3 Verification
# =============================================================================


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


# =============================================================================
# Debug Output
# =============================================================================


def dump_segments_debug(
    segments: list[Segment], batches: list[SegmentBatch], output_dir: Path
) -> None:
    """Dump parsed segments and batches for debugging.

    Args:
        segments: List of parsed segments
        batches: List of segment batches
        output_dir: Directory to save debug files
    """
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    # Print segment summary
    print(f"\nParsed {len(segments)} segments:")
    for i, seg in enumerate(segments):
        emotion_str = (
            f" (emotion: {seg.emotion})" if seg.emotion else " (emotion: none)"
        )
        text_preview = seg.text[:60] + "..." if len(seg.text) > 60 else seg.text
        print(f'  [{i + 1}] {seg.speaker}: "{text_preview}"{emotion_str}')

    print(f"\nBatched into {len(batches)} TTS calls:")
    for i, batch in enumerate(batches):
        speakers_str = " + ".join(batch.speakers)
        seg_count = len(batch.segments)
        print(f"  Batch {i + 1}: {speakers_str} ({seg_count} segments)")

    # Save detailed JSON
    debug_data = {
        "segments": [
            {"speaker": s.speaker, "text": s.text, "emotion": s.emotion}
            for s in segments
        ],
        "batches": [
            {"index": i, "speakers": b.speakers, "segment_count": len(b.segments)}
            for i, b in enumerate(batches)
        ],
    }

    debug_path = debug_dir / "segments.json"
    debug_path.write_text(json.dumps(debug_data, indent=2))
    print(f"\nDebug data saved to: {debug_path}")


def save_batch_audio_debug(audio_segments: list[bytes], output_dir: Path) -> None:
    """Save individual batch audio files for debugging.

    Args:
        audio_segments: List of raw PCM audio data
        output_dir: Directory to save debug files
    """
    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    for i, audio_data in enumerate(audio_segments):
        # Convert to MP3 for easier playback
        mp3_data = convert_to_mp3(audio_data)
        audio_path = debug_dir / f"segment_{i + 1:03d}.mp3"
        audio_path.write_bytes(mp3_data)
        logging.debug(f"Saved debug audio: {audio_path}")

    print(f"Debug audio files saved to: {debug_dir}")


# =============================================================================
# Main Generation Flow
# =============================================================================


def generate_audio_from_script(
    script: AudioScript,
    output_path: Path,
    client: genai.Client,
    debug: bool = False,
    show_progress: bool = True,
) -> bytes:
    """Generate audio from parsed audio script using per-segment TTS.

    Args:
        script: Parsed AudioScript
        output_path: Output MP3 file path
        client: Gemini API client
        debug: Enable debug output
        show_progress: Show progress bar

    Returns:
        Final MP3 data

    Raises:
        RuntimeError: If any batch fails after retries
    """
    # Create speaker configs map for quick lookup
    speaker_configs_map = {cfg.name: cfg for cfg in script.speaker_configs}

    # Batch segments
    batches = batch_segments(script.segments)

    logging.info(
        f"Processing {len(script.segments)} segments in {len(batches)} batches"
    )

    # Debug output
    if debug:
        dump_segments_debug(script.segments, batches, output_path.parent)

    # Generate audio for all batches (raises RuntimeError on failure)
    progress_callback = print_progress if show_progress else None
    audio_segments = generate_all_batches(
        client,
        batches,
        speaker_configs_map,
        script.tts_model,
        progress_callback=progress_callback,
    )

    # Debug: save individual batch audio
    if debug:
        save_batch_audio_debug(audio_segments, output_path.parent)

    # Create batch metadata for context-aware pausing
    # Each batch may contain multiple segments, but we use the last segment
    # of each batch for determining transitions to the next batch
    batch_metadata: list[Segment] = []
    for batch in batches:
        # Use the last segment of each batch for transition context
        # This captures the speaker and emotion that ends the batch
        if batch.segments:
            batch_metadata.append(batch.segments[-1])

    # Concatenate with context-aware pauses
    pause_config = PauseConfig()
    concatenate_segment_audio(
        audio_segments,
        output_path,
        segment_metadata=batch_metadata,
        pause_config=pause_config,
    )

    return output_path.read_bytes()


# =============================================================================
# Main Entry Point
# =============================================================================


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
  1. Google AI Studio API key (supports multi-speaker TTS)
  2. Get an API key at: https://aistudio.google.com/apikey
  3. FFmpeg installed (required by pydub)

Environment Variables:
  GOOGLE_API_KEY   Required. Your Google AI Studio API key.
  GEMINI_API_KEY   Alternative to GOOGLE_API_KEY (either works).

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
        logging.info(f"Speakers: {[cfg.name for cfg in script.speaker_configs]}")
        logging.info(f"Segments: {len(script.segments)}")

        # Override voice if specified (for single speaker mode)
        if args.voice:
            if args.voice not in AVAILABLE_VOICES:
                logging.warning(
                    f"Voice '{args.voice}' not in known voices, using anyway"
                )
            # Override all speakers to use this voice
            for cfg in script.speaker_configs:
                cfg.voice = args.voice
            logging.info(f"Voice override: {args.voice}")

        # Get API key for Google AI Studio
        api_key = get_api_key()
        logging.info("Connecting to Google AI Studio API")

        # Create client
        client = genai.Client(api_key=api_key)

        # Generate audio
        mp3_data = generate_audio_from_script(
            script,
            output_path,
            client,
            debug=args.debug,
            show_progress=not args.no_progress,
        )

        # Verify format (default: on)
        if not args.no_verify:
            passed, issues = verify_mp3_format(mp3_data)
            if not passed:
                logging.error("Output does not meet format requirements:")
                for issue in issues:
                    logging.error(f"  - {issue}")
                sys.exit(1)

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
