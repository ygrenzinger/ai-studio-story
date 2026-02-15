"""Domain models for audio generation pipeline."""

from dataclasses import dataclass, field

from audio_generation.domain.constants import (
    COMFORT_NOISE_LEVEL_DB,
    CROSSFADE_MS,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    FILE_LEADING_SILENCE_MS,
    FILE_TRAILING_SILENCE_MS,
    PAUSE_CHARACTER_TO_CHARACTER_MS,
    PAUSE_CHARACTER_TO_NARRATOR_MS,
    PAUSE_DRAMATIC_MS,
    PAUSE_NARRATOR_TO_CHARACTER_MS,
    PAUSE_NARRATOR_TO_NARRATOR_MS,
    PAUSE_SCENE_BREAK_MS,
    SEGMENT_FADE_IN_MS,
    SEGMENT_FADE_OUT_MS,
    SILENCE_BUFFER_MS,
)


@dataclass
class SpeakerConfig:
    """Configuration for a single speaker.

    Attributes:
        name: Speaker identifier (e.g., "Narrator", "Emma")
        voice: Gemini TTS voice name (e.g., "Sulafat", "Puck")
    """

    name: str
    voice: str = DEFAULT_VOICE


@dataclass
class Segment:
    """A single speaker segment with optional emotion marker.

    Attributes:
        speaker: Speaker name matching SpeakerConfig.name
        text: The text content to be spoken
        emotion: Emotion descriptor (e.g., "warm", "tense")
    """

    speaker: str
    text: str
    emotion: str = ""


@dataclass
class SegmentBatch:
    """A batch of segments for a single TTS call (max 2 speakers).

    Gemini TTS API supports maximum 2 speakers per call. Batches are
    structured to optimize API usage while maintaining narrative flow.

    Attributes:
        segments: Ordered list of segments in this batch
        speakers: Unique speaker names in this batch (max 2)
    """

    segments: list[Segment]
    speakers: list[str]


@dataclass
class AudioScript:
    """Parsed audio script from markdown file.

    Contains all information needed to generate audio from a script,
    including metadata, speaker configurations, and content segments.

    Attributes:
        stage_uuid: Unique identifier for this audio stage
        chapter_ref: Reference to the source chapter
        locale: Language/locale code (e.g., "en-US")
        speaker_configs: List of speaker voice configurations
        segments: Ordered list of content segments
        tts_model: Gemini TTS model to use
    """

    stage_uuid: str
    chapter_ref: str = ""
    locale: str = "en-US"
    speaker_configs: list[SpeakerConfig] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    tts_model: str = DEFAULT_TTS_MODEL


@dataclass
class GenerationProgress:
    """Tracks batch generation progress for resume capability.

    Enables resuming audio generation after failures (e.g., API rate limits)
    by tracking which batches have been successfully completed.

    Attributes:
        input_file_hash: MD5 hash of input file for invalidation detection
        total_batches: Total number of batches to process
        completed_batches: Indices of completed batches (0-based)
        audio_files: Mapping of batch_index to saved audio filename
        last_error: Error message if processing stopped due to error
        last_error_batch: Which batch failed
        last_error_time: ISO timestamp of error
        started_at: ISO timestamp when processing started
        updated_at: ISO timestamp of last update
    """

    input_file_hash: str
    total_batches: int
    completed_batches: list[int] = field(default_factory=list)
    audio_files: dict[int, str] = field(default_factory=dict)
    last_error: str | None = None
    last_error_batch: int | None = None
    last_error_time: str | None = None
    started_at: str = ""
    updated_at: str = ""


@dataclass
class PauseConfig:
    """Configuration for pause timing and audio smoothing.

    Based on audiobook and podcast production best practices:
    - Sentence end: 500-750ms
    - Paragraph/topic change: 1000-1500ms
    - Speaker change: 400-700ms
    - Scene change: 1500-2500ms
    - Dramatic pause: 1000-2000ms

    Attributes:
        narrator_to_narrator_ms: Pause for paragraph transitions
        narrator_to_character_ms: Pause from setup to dialogue
        character_to_narrator_ms: Pause returning to narration
        character_to_character_ms: Pause for quick dialogue
        scene_break_ms: Pause for major scene changes
        dramatic_pause_ms: Pause for emotional moments
        file_leading_ms: Silence at start of file
        file_trailing_ms: Silence at end of file
        segment_edge_buffer_ms: Buffer at segment edges
        crossfade_ms: Crossfade duration between segments
        use_comfort_noise: Use pink noise instead of digital silence
        comfort_noise_db: Target noise level in dBFS
        crossfade_curve: Curve type (linear, logarithmic, exponential, s_curve)
        segment_fade_in_ms: Fade in duration at segment start
        segment_fade_out_ms: Fade out duration at segment end
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

    # Audio smoothing settings
    use_comfort_noise: bool = True
    comfort_noise_db: float = COMFORT_NOISE_LEVEL_DB
    crossfade_curve: str = "logarithmic"
    segment_fade_in_ms: int = SEGMENT_FADE_IN_MS
    segment_fade_out_ms: int = SEGMENT_FADE_OUT_MS


@dataclass
class VerificationResult:
    """Result of MP3 format verification.

    Attributes:
        passed: Whether all checks passed
        issues: List of issues found (empty if passed)
    """

    passed: bool
    issues: list[str] = field(default_factory=list)
