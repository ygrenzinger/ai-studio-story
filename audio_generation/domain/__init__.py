"""Domain models and constants for audio generation."""

from audio_generation.domain.models import (
    AudioScript,
    GenerationProgress,
    PauseConfig,
    Segment,
    SegmentBatch,
    SpeakerConfig,
)
from audio_generation.domain.constants import (
    AVAILABLE_VOICES,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    GEMINI_TTS_SAMPLE_RATE,
    TARGET_CHANNELS,
    TARGET_SAMPLE_RATE,
)

__all__ = [
    # Models
    "AudioScript",
    "GenerationProgress",
    "PauseConfig",
    "Segment",
    "SegmentBatch",
    "SpeakerConfig",
    # Constants
    "AVAILABLE_VOICES",
    "DEFAULT_TTS_MODEL",
    "DEFAULT_VOICE",
    "GEMINI_TTS_SAMPLE_RATE",
    "TARGET_CHANNELS",
    "TARGET_SAMPLE_RATE",
]
