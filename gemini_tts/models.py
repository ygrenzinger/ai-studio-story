"""Data models for Gemini TTS."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Voice:
    """Represents a TTS voice with name and description."""
    name: str
    description: str


@dataclass(frozen=True)
class AudioData:
    """Audio data with format metadata from the API.

    Attributes:
        data: Raw audio bytes (decoded from base64).
        mime_type: The MIME type of the audio data (e.g., "audio/L16;rate=24000").
    """
    data: bytes
    mime_type: str

    @property
    def is_pcm(self) -> bool:
        """Check if the audio is raw PCM format."""
        return self.mime_type.startswith("audio/L16") or self.mime_type.startswith("audio/pcm")

    @property
    def sample_rate(self) -> int | None:
        """Extract sample rate from mime_type if present."""
        if "rate=" in self.mime_type:
            try:
                rate_part = self.mime_type.split("rate=")[1].split(";")[0]
                return int(rate_part)
            except (IndexError, ValueError):
                return None
        return None


class AudioFormat(Enum):
    """Supported audio output formats."""
    MP3 = "mp3"
    WAV = "wav"

    @property
    def extension(self) -> str:
        """Get the file extension for this format."""
        return f".{self.value}"


class Bitrate:
    """MP3 bitrate configuration."""
    VALID_VALUES = (64, 128, 192, 256, 320)
    DEFAULT = 128

    def __init__(self, value: int = DEFAULT):
        if value not in self.VALID_VALUES:
            raise ValueError(
                f"Invalid bitrate: {value}. "
                f"Valid values are: {', '.join(map(str, self.VALID_VALUES))}"
            )
        self.value = value

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"Bitrate({self.value})"


class ExitCode(Enum):
    """CLI exit codes."""
    SUCCESS = 0
    USER_ERROR = 1
    API_ERROR = 2
    IO_ERROR = 3
    CONVERSION_ERROR = 4
