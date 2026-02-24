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
# TTS System Instruction
# =============================================================================

TTS_SYSTEM_INSTRUCTION = (
    "You are a professional voice actor recording an audiobook for children aged 5-10.\n"
    "\n"
    "CRITICAL RULES:\n"
    "- Speak ONLY the transcript text in the TRANSCRIPT section. "
    "Never read aloud any stage directions, section headers, speaker labels, "
    "emotion descriptors, or formatting marks.\n"
    "- The DIRECTOR'S NOTES section contains instructions for HOW to perform. "
    "These are acting directions, NOT text to speak. Never vocalize them.\n"
    "- The AUDIO PROFILE section describes each character's identity. "
    "Use it to inform your performance, but never read it aloud.\n"
    "- Each speaker has a distinct personality. Embody that character fully.\n"
    "- Use natural pronunciation matching the transcript language. "
    "Do not anglicize non-English words."
)

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
