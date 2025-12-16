"""Audio format conversion service."""

import io

from pydub import AudioSegment

from gemini_tts.exceptions import AudioConversionException
from gemini_tts.models import AudioData, AudioFormat, Bitrate
from gemini_tts.utils.wav_utils import (
    SAMPLE_RATE,
    BITS_PER_SAMPLE,
    NUM_CHANNELS,
    create_wav_header,
)


class AudioConverterService:
    """Service for converting PCM audio to various formats."""

    def __init__(self, bitrate: int = Bitrate.DEFAULT, quality: int = 2):
        """Initialize the audio converter.

        Args:
            bitrate: MP3 bitrate in kbps.
            quality: MP3 quality (0-9, lower is better).
        """
        self.bitrate = bitrate
        self.quality = quality

    def convert(self, audio_data: AudioData, format: AudioFormat) -> bytes:
        """Convert audio to the specified format.

        Args:
            audio_data: AudioData containing raw audio bytes and mime_type.
            format: Target audio format.

        Returns:
            Converted audio data.

        Raises:
            AudioConversionException: If conversion fails.
        """
        # Use sample rate from mime_type if available, otherwise default
        sample_rate = audio_data.sample_rate or SAMPLE_RATE

        if format == AudioFormat.MP3:
            return self.convert_to_mp3(audio_data.data, sample_rate)
        elif format == AudioFormat.WAV:
            return self.convert_to_wav(audio_data.data, sample_rate)
        else:
            raise AudioConversionException(f"Unsupported format: {format}")

    def convert_to_mp3(self, pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
        """Convert PCM audio to MP3.

        Args:
            pcm_data: Raw PCM audio data.
            sample_rate: Audio sample rate in Hz.

        Returns:
            MP3 audio data.

        Raises:
            AudioConversionException: If conversion fails.
        """
        try:
            # Create AudioSegment from raw PCM data
            audio = AudioSegment(
                data=pcm_data,
                sample_width=BITS_PER_SAMPLE // 8,
                frame_rate=sample_rate,
                channels=NUM_CHANNELS,
            )

            # Export to MP3
            buffer = io.BytesIO()
            audio.export(
                buffer,
                format="mp3",
                bitrate=f"{self.bitrate}k",
                parameters=["-q:a", str(self.quality)],
            )
            return buffer.getvalue()

        except Exception as e:
            raise AudioConversionException(f"Failed to convert to MP3: {e}", e)

    def convert_to_wav(self, pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
        """Convert PCM audio to WAV.

        Args:
            pcm_data: Raw PCM audio data.
            sample_rate: Audio sample rate in Hz.

        Returns:
            WAV audio data with header.

        Raises:
            AudioConversionException: If conversion fails.
        """
        try:
            header = create_wav_header(len(pcm_data), sample_rate)
            return header + pcm_data
        except Exception as e:
            raise AudioConversionException(f"Failed to convert to WAV: {e}", e)
