"""Generic TTS provider protocol and request/response models."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from audio_generation.domain.models import (
    AudioScript,
    CharacterProfile,
    SegmentBatch,
    SpeakerConfig,
)


@dataclass
class AudioFormat:
    """Requested synthesis output format."""

    codec: str = "mp3"
    sample_rate: int = 44100
    channels: int = 1
    bit_rate: int | None = None


@dataclass
class ProviderCapabilities:
    """Provider feature capabilities."""

    supports_prompt_director_notes: bool
    supports_inline_tags: bool
    supports_wrapping_tags: bool
    supports_voice_settings: bool
    supports_direct_mp3_44100: bool
    max_speakers_per_request: int = 1
    max_segments_per_request: int = 1
    supported_inline_tags: frozenset[str] = field(default_factory=frozenset)


class TTSError(RuntimeError):
    """Base provider-normalized TTS error."""


class TTSAuthError(TTSError):
    """Authentication or authorization failure."""


class TTSRateLimitError(TTSError):
    """Provider rate limit failure."""


class TTSValidationError(TTSError):
    """Provider rejected the synthesis request."""


class TTSProviderError(TTSError):
    """Generic provider-side failure."""


@dataclass
class SynthesisRequest:
    """A single provider synthesis request."""

    script: AudioScript
    batch: SegmentBatch
    speaker_configs: dict[str, SpeakerConfig]
    character_profiles: dict[str, CharacterProfile]
    locale: str
    output_format: AudioFormat
    batch_num: int = 0


@dataclass
class SynthesisResult:
    """Provider synthesis response."""

    audio_bytes: bytes
    codec: str
    sample_rate: int | None = None
    channels: int | None = None
    request_id: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)


class TTSProvider(Protocol):
    """Protocol implemented by all TTS providers."""

    name: str
    capabilities: ProviderCapabilities

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Generate audio for one segment batch."""
