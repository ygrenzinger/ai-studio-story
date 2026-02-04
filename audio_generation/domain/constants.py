"""Audio generation constants and configuration values."""

# =============================================================================
# Audio Format Constants
# =============================================================================

GEMINI_TTS_SAMPLE_RATE = 24000  # Gemini TTS outputs 24kHz
TARGET_SAMPLE_RATE = 44100  # Required output sample rate
TARGET_CHANNELS = 1  # Mono

# =============================================================================
# Default Values
# =============================================================================

DEFAULT_VOICE = "Sulafat"  # Warm voice for narrators
DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"  # Gemini TTS model

# =============================================================================
# Segment Processing Constants
# =============================================================================

SILENCE_BUFFER_MS = 200  # Normalized silence at segment edges (industry: 200-500ms)
INTER_SEGMENT_PAUSE_MS = 500  # Default pause between segments (fallback)
API_CALL_DELAY_SEC = 6  # 6 seconds between calls (10 RPM limit)
MAX_RETRIES = 3  # Retry count per segment

# =============================================================================
# Advanced Pause Configuration
# =============================================================================

FILE_LEADING_SILENCE_MS = 500  # Silence at start of audio file
FILE_TRAILING_SILENCE_MS = 1500  # Silence at end of audio file
CROSSFADE_MS = 75  # Crossfade duration (increased from 25ms for smoother transitions)

# =============================================================================
# Audio Smoothing Constants
# =============================================================================

SEGMENT_FADE_IN_MS = 15  # Fade in at segment start to prevent clicks
SEGMENT_FADE_OUT_MS = 25  # Fade out at segment end (slightly longer for natural decay)
COMFORT_NOISE_LEVEL_DB = -55.0  # Target noise floor for comfort noise
NOISE_FADE_MS = 10  # Micro-fade on noise edges to prevent clicks

# =============================================================================
# Context-Aware Pause Durations (milliseconds)
# =============================================================================

PAUSE_NARRATOR_TO_NARRATOR_MS = 750  # Paragraph transition
PAUSE_NARRATOR_TO_CHARACTER_MS = 500  # Setup to dialogue
PAUSE_CHARACTER_TO_NARRATOR_MS = 500  # Return to narration
PAUSE_CHARACTER_TO_CHARACTER_MS = 400  # Quick dialogue exchange
PAUSE_SCENE_BREAK_MS = 2000  # Major scene/section change
PAUSE_DRAMATIC_MS = 1500  # Emotional moment

# =============================================================================
# Emotion-Based Pause Modifiers
# =============================================================================

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

# =============================================================================
# Available Voices
# =============================================================================

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
# Progress File Management
# =============================================================================

PROGRESS_FILE_NAME = ".progress.json"
