"""WAV file utilities."""

import struct

# Audio format constants (matching Gemini TTS output)
SAMPLE_RATE = 24000  # 24 kHz
BITS_PER_SAMPLE = 16
NUM_CHANNELS = 1  # Mono
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8


def create_wav_header(data_size: int, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Create a 44-byte WAV header for PCM audio data.

    Args:
        data_size: Size of the PCM audio data in bytes.
        sample_rate: Audio sample rate in Hz (default: 24000).

    Returns:
        44-byte WAV header.
    """
    byte_rate = sample_rate * NUM_CHANNELS * BYTES_PER_SAMPLE
    block_align = NUM_CHANNELS * BYTES_PER_SAMPLE
    file_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",           # ChunkID
        file_size,         # ChunkSize
        b"WAVE",           # Format
        b"fmt ",           # Subchunk1ID
        16,                # Subchunk1Size (16 for PCM)
        1,                 # AudioFormat (1 for PCM)
        NUM_CHANNELS,      # NumChannels
        sample_rate,       # SampleRate
        byte_rate,         # ByteRate
        block_align,       # BlockAlign
        BITS_PER_SAMPLE,   # BitsPerSample
        b"data",           # Subchunk2ID
        data_size,         # Subchunk2Size
    )
    return header


def calculate_duration(pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> float:
    """Calculate the duration of PCM audio data in seconds.

    Args:
        pcm_data: Raw PCM audio bytes.
        sample_rate: Audio sample rate in Hz (default: 24000).

    Returns:
        Duration in seconds.
    """
    num_samples = len(pcm_data) // BYTES_PER_SAMPLE
    return num_samples / sample_rate


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "1m 23s" or "45s".
    """
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60

    if minutes > 0:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"
