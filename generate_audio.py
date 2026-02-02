#!/usr/bin/env python3
"""
Generate audio files from story chapters using Gemini TTS via Google AI Studio.

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
    - Google AI Studio API key (supports multi-speaker TTS)
    - Get an API key at: https://aistudio.google.com/apikey
    - Environment variables: GOOGLE_API_KEY or GEMINI_API_KEY
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
DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# Chunking constants (for long transcripts)
MAX_CHUNK_SIZE = 6000  # Characters - safety margin below 8000 Gemini limit
CHUNK_PAUSE_MS = 300  # Milliseconds of silence between chunks

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

    # Content fields (separated for deterministic TTS output)
    transcript: str = ""  # Only the ## TRANSCRIPTION content (to be read aloud)
    style_context: str = ""  # Scene + Director's notes (style guidance, not read)
    full_prompt: str = ""  # Built from above fields


@dataclass
class ChunkInfo:
    """Metadata for a transcript chunk, used for tracking and retry."""

    index: int  # 0-based index
    total: int  # Total number of chunks
    text: str  # The chunk content
    char_count: int  # Length of text
    markdown_path: Path  # Path to saved .md file
    audio_path: Path  # Path to output .mp3 file
    status: str = "pending"  # "pending", "generated", "failed"


def setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


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
    # Separate TRANSCRIPTION (to be read aloud) from style context (guidance only)

    # Find TTS configuration section (supports both "## TTS CONFIGURATION" and "## CONFIGURATION TTS")
    tts_config_match = re.search(
        r"##\s*(?:TTS\s+CONFIGURATION|CONFIGURATION\s+TTS)", body, re.IGNORECASE
    )
    tts_config_pos = tts_config_match.start() if tts_config_match else -1
    content_body = body[:tts_config_pos].strip() if tts_config_pos > 0 else body.strip()

    # Try to extract ## TRANSCRIPTION section specifically
    # Match content between ## TRANSCRIPTION (or ## TRANSCRIPT) and the next --- or ## section
    transcript_match = re.search(
        r"##\s*TRANSCRIPT(?:ION)?\s*\n(.*?)(?=\n---|\n##|$)",
        content_body,
        re.DOTALL | re.IGNORECASE,
    )

    if transcript_match:
        script.transcript = transcript_match.group(1).strip()
        # Style context is everything before ## TRANSCRIPTION
        transcript_section_start = re.search(
            r"##\s*TRANSCRIPT(?:ION)?", content_body, re.IGNORECASE
        )
        if transcript_section_start:
            script.style_context = content_body[
                : transcript_section_start.start()
            ].strip()
        else:
            script.style_context = ""
    else:
        # Fallback: use entire content as transcript (backward compatibility)
        script.transcript = content_body
        script.style_context = ""
        logging.warning(
            "No ## TRANSCRIPTION section found, using entire content as transcript"
        )

    # Build full_prompt for backward compatibility
    script.full_prompt = content_body

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


def build_tts_prompt(script: AudioScript, include_context: bool = True) -> str:
    """Build the TTS prompt from script sections.

    Separates style guidance (not to be read aloud) from transcript content
    (to be read aloud) using explicit markers to ensure deterministic output.

    Args:
        script: Parsed audio script with transcript and style_context
        include_context: Whether to include style context as guidance prefix

    Returns:
        Formatted prompt for TTS generation with clear markers
    """
    if include_context and script.style_context:
        return f"""[STYLE GUIDANCE - DO NOT READ ALOUD, USE FOR VOICE TONE AND EMOTION ONLY]
{script.style_context}

[READ THE FOLLOWING TRANSCRIPT ALOUD - THIS IS THE ONLY CONTENT TO VOCALIZE]
{script.transcript}"""
    else:
        return script.transcript


def chunk_transcript(transcript: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Split transcript into chunks at paragraph boundaries.

    Splits long transcripts into smaller chunks that fit within the Gemini TTS
    character limit. Prioritizes splitting at paragraph boundaries for natural
    audio breaks.

    Args:
        transcript: The full transcript text to split
        max_size: Maximum characters per chunk (default: 6000)

    Returns:
        List of transcript chunks, each within max_size limit
    """
    # If transcript fits in one chunk, return as-is
    if len(transcript) <= max_size:
        return [transcript]

    chunks: list[str] = []

    # Split by paragraphs (double newline)
    paragraphs = transcript.split("\n\n")

    current_chunk: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Calculate size including separator
        para_size = len(paragraph)
        separator_size = 2 if current_chunk else 0  # "\n\n" between paragraphs

        # If single paragraph exceeds max_size, split by sentences
        if para_size > max_size:
            # First, save current chunk if any
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            # Split paragraph by sentences
            sentence_chunks = _split_by_sentences(paragraph, max_size)
            chunks.extend(sentence_chunks)
            continue

        # If adding this paragraph would exceed limit, start new chunk
        if current_size + separator_size + para_size > max_size:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_size = para_size
        else:
            current_chunk.append(paragraph)
            current_size += separator_size + para_size

    # Don't forget the last chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def _split_by_sentences(text: str, max_size: int) -> list[str]:
    """Split text by sentence boundaries when paragraphs are too long.

    Args:
        text: Text to split (typically a long paragraph)
        max_size: Maximum characters per chunk

    Returns:
        List of text chunks split at sentence boundaries
    """
    import re

    # Split by sentence endings (. ! ?) followed by space or newline
    sentence_pattern = r"(?<=[.!?])\s+"
    sentences = re.split(sentence_pattern, text)

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sent_size = len(sentence)
        separator_size = 1 if current_chunk else 0  # space between sentences

        # If single sentence exceeds max_size, split by words (last resort)
        if sent_size > max_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

            word_chunks = _split_by_words(sentence, max_size)
            chunks.extend(word_chunks)
            continue

        # If adding this sentence would exceed limit, start new chunk
        if current_size + separator_size + sent_size > max_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_size = sent_size
        else:
            current_chunk.append(sentence)
            current_size += separator_size + sent_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _split_by_words(text: str, max_size: int) -> list[str]:
    """Split text by word boundaries as last resort.

    Args:
        text: Text to split (typically a very long sentence)
        max_size: Maximum characters per chunk

    Returns:
        List of text chunks split at word boundaries
    """
    words = text.split()
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0

    for word in words:
        word_size = len(word)
        separator_size = 1 if current_chunk else 0

        if current_size + separator_size + word_size > max_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += separator_size + word_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def generate_tts_audio(
    client: genai.Client,
    script: AudioScript,
    speech_config: types.SpeechConfig,
    include_context: bool = True,
) -> bytes:
    """Generate audio using Gemini TTS API.

    Uses build_tts_prompt() to construct a prompt with explicit markers
    separating style guidance from transcript content, ensuring deterministic
    output where only the transcript is vocalized.

    Args:
        client: Gemini API client
        script: Parsed audio script
        speech_config: TTS configuration
        include_context: Whether to include style context as guidance prefix

    Returns:
        Raw PCM audio data (24kHz, 16-bit, mono)

    Raises:
        RuntimeError: If no audio data in response
    """
    # Build prompt with explicit markers for deterministic output
    tts_prompt = build_tts_prompt(script, include_context=include_context)

    logging.info(f"Generating TTS audio with model: {script.tts_model}")
    logging.debug(f"Transcript length: {len(script.transcript)} characters")
    logging.debug(f"Style context length: {len(script.style_context)} characters")
    logging.debug(f"Total prompt length: {len(tts_prompt)} characters")
    logging.debug(f"Include context: {include_context}")

    response = client.models.generate_content(
        model=script.tts_model,
        contents=tts_prompt,
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


def save_chunk_markdown(
    chunk_info: ChunkInfo,
    script: AudioScript,
    output_dir: Path,
) -> Path:
    """Save a transcript chunk as a standalone markdown file for debugging/retry.

    Creates a markdown file with the same format as the original audio script,
    but containing only the chunk's portion of the transcript. Includes full
    style context for voice consistency.

    Args:
        chunk_info: Metadata for the chunk
        script: Original AudioScript with full context
        output_dir: Directory to save the markdown file

    Returns:
        Path to the saved markdown file
    """
    import json

    # Build frontmatter
    frontmatter = {
        "stageUuid": script.stage_uuid,
        "chapterRef": script.chapter_ref,
        "chunkIndex": chunk_info.index + 1,  # 1-based for human readability
        "totalChunks": chunk_info.total,
        "speakers": script.speakers,
    }

    # Build TTS configuration JSON
    tts_config = {
        "speakerConfigs": [
            {"speaker": cfg.speaker, "voiceName": cfg.voice_name}
            for cfg in script.speaker_configs
        ]
    }

    # Construct markdown content
    content_parts = [
        "---",
        yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip(),
        "---",
        "",
        script.style_context if script.style_context else "",
        "",
        "## TRANSCRIPT",
        "",
        chunk_info.text,
        "",
        "---",
        "",
        "## TTS CONFIGURATION",
        "",
        "```json",
        json.dumps(tts_config, indent=2),
        "```",
    ]

    markdown_content = "\n".join(content_parts)

    # Save to file
    output_dir.mkdir(parents=True, exist_ok=True)
    chunk_info.markdown_path.write_text(markdown_content, encoding="utf-8")

    return chunk_info.markdown_path


def generate_chunked_audio(
    client: genai.Client,
    script: AudioScript,
    speech_config: types.SpeechConfig,
    output_dir: Path,
    include_context: bool = True,
) -> list[ChunkInfo]:
    """Generate audio for long transcripts by chunking.

    Splits the transcript into chunks, saves each as a markdown file,
    generates audio for each chunk, and tracks progress for retry capability.

    Args:
        client: Gemini API client
        script: Parsed audio script with full transcript
        speech_config: TTS configuration
        output_dir: Directory for chunk files (markdown and audio)
        include_context: Whether to include style context in prompts

    Returns:
        List of ChunkInfo objects with status for each chunk
    """
    # Split transcript into chunks
    chunks = chunk_transcript(script.transcript)
    total_chunks = len(chunks)

    logging.info(f"Splitting transcript into {total_chunks} chunks")

    # Create ChunkInfo for each chunk and save markdown
    chunk_infos: list[ChunkInfo] = []

    for i, chunk_text in enumerate(chunks):
        chunk_num = str(i + 1).zfill(3)  # Zero-padded: 001, 002, etc.

        markdown_path = output_dir / f"{script.stage_uuid}_chunk_{chunk_num}.md"
        audio_path = output_dir / f"{script.stage_uuid}_chunk_{chunk_num}.mp3"

        chunk_info = ChunkInfo(
            index=i,
            total=total_chunks,
            text=chunk_text,
            char_count=len(chunk_text),
            markdown_path=markdown_path,
            audio_path=audio_path,
            status="pending",
        )

        # Save markdown file
        save_chunk_markdown(chunk_info, script, output_dir)
        logging.info(
            f"Chunk {i + 1}/{total_chunks}: {chunk_info.char_count} chars -> "
            f"{markdown_path.name}"
        )

        chunk_infos.append(chunk_info)

    # Generate audio for each chunk
    for chunk_info in chunk_infos:
        logging.info(f"Generating audio {chunk_info.index + 1}/{chunk_info.total}...")

        try:
            # Create a temporary AudioScript for this chunk
            chunk_script = AudioScript(
                stage_uuid=script.stage_uuid,
                chapter_ref=script.chapter_ref,
                speakers=script.speakers,
                tts_model=script.tts_model,
                speaker_configs=script.speaker_configs,
                transcript=chunk_info.text,
                style_context=script.style_context,
            )

            # Generate TTS audio
            pcm_data = generate_tts_audio(
                client, chunk_script, speech_config, include_context=include_context
            )

            # Convert to MP3
            mp3_data = convert_to_mp3(pcm_data)

            # Save chunk audio
            chunk_info.audio_path.write_bytes(mp3_data)
            chunk_info.status = "generated"

            logging.info(
                f"Chunk {chunk_info.index + 1}/{chunk_info.total} complete: "
                f"{chunk_info.audio_path.name}"
            )

        except Exception as e:
            chunk_info.status = "failed"
            logging.error(
                f"Chunk {chunk_info.index + 1}/{chunk_info.total} failed: {e}"
            )
            # Continue to next chunk, don't abort

    return chunk_infos


def concatenate_audio_files(
    chunk_paths: list[Path],
    output_path: Path,
    pause_ms: int = CHUNK_PAUSE_MS,
) -> None:
    """Concatenate multiple MP3 files into a single output file.

    Joins audio chunks with optional silence between them for natural pauses.
    Output meets required specifications: mono, 44100Hz, no ID3 tags.

    Args:
        chunk_paths: List of paths to MP3 chunk files (in order)
        output_path: Path for the final concatenated MP3
        pause_ms: Milliseconds of silence between chunks (default: 300)
    """
    if not chunk_paths:
        raise ValueError("No chunk paths provided for concatenation")

    logging.info(f"Concatenating {len(chunk_paths)} chunks with {pause_ms}ms pauses")

    # Load first chunk
    combined = AudioSegment.from_mp3(chunk_paths[0])

    # Create silence segment
    silence = AudioSegment.silent(duration=pause_ms)

    # Append remaining chunks with silence
    for chunk_path in chunk_paths[1:]:
        combined += silence
        combined += AudioSegment.from_mp3(chunk_path)

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
    logging.info(f"Final file size: {len(mp3_data):,} bytes")


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
        help="Enable debug logging",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip output format verification",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Disable style context (scene, director's notes) in TTS prompt. "
        "Only the transcript will be sent to the TTS model.",
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

        # Get API key for Google AI Studio
        api_key = get_api_key()
        logging.info("Connecting to Google AI Studio API")

        # Create client (using Google AI Studio for multi-speaker TTS support)
        client = genai.Client(api_key=api_key)

        # Generate TTS audio
        include_context = not args.no_context
        output_dir = output_path.parent

        # Check if chunking is needed (transcript exceeds MAX_CHUNK_SIZE)
        if len(script.transcript) > MAX_CHUNK_SIZE:
            logging.info(
                f"Transcript exceeds {MAX_CHUNK_SIZE} chars "
                f"({len(script.transcript)} chars), chunking required"
            )

            # Generate chunked audio (markdown + audio files)
            chunk_infos = generate_chunked_audio(
                client, script, speech_config, output_dir, include_context
            )

            # Check for failures
            failed = [c for c in chunk_infos if c.status == "failed"]
            if failed:
                logging.error(
                    f"{len(failed)} chunk(s) failed. "
                    f"Retry individually with: python generate_audio.py <chunk>.md -o <chunk>.mp3"
                )
                for c in failed:
                    logging.error(f"  - {c.markdown_path.name}")
                sys.exit(1)

            # Concatenate successful chunks
            chunk_paths = [c.audio_path for c in chunk_infos]
            concatenate_audio_files(chunk_paths, output_path, CHUNK_PAUSE_MS)

            # Read final file for verification
            mp3_data = output_path.read_bytes()

        else:
            # Single-call path (transcript fits in one request)
            pcm_data = generate_tts_audio(
                client, script, speech_config, include_context=include_context
            )
            logging.info(f"Received {len(pcm_data):,} bytes of PCM audio")

            # Convert to MP3
            mp3_data = convert_to_mp3(pcm_data)

            # Save output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(mp3_data)

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
