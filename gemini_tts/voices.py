"""Voice registry for available TTS voices."""

from gemini_tts.models import Voice


# All available voices with their descriptions
VOICES: list[Voice] = [
    Voice("Zephyr", "Bright"),
    Voice("Puck", "Upbeat"),
    Voice("Charon", "Informative"),
    Voice("Kore", "Firm"),
    Voice("Fenrir", "Excitable"),
    Voice("Leda", "Youthful"),
    Voice("Orus", "Firm"),
    Voice("Aoede", "Breezy"),
    Voice("Callirrhoe", "Easy-going"),
    Voice("Autonoe", "Bright"),
    Voice("Enceladus", "Breathy"),
    Voice("Iapetus", "Clear"),
    Voice("Umbriel", "Easy-going"),
    Voice("Algieba", "Smooth"),
    Voice("Despina", "Smooth"),
    Voice("Erinome", "Clear"),
    Voice("Algenib", "Gravelly"),
    Voice("Rasalgethi", "Informative"),
    Voice("Laomedeia", "Upbeat"),
    Voice("Achernar", "Soft"),
    Voice("Alnilam", "Firm"),
    Voice("Schedar", "Even"),
    Voice("Gacrux", "Mature"),
    Voice("Pulcherrima", "Forward"),
    Voice("Achird", "Friendly"),
    Voice("Zubenelgenubi", "Casual"),
    Voice("Vindemiatrix", "Gentle"),
    Voice("Sadachbia", "Lively"),
    Voice("Sadaltager", "Knowledgeable"),
    Voice("Sulafat", "Warm"),
]

# Build a case-insensitive lookup map
_VOICE_MAP: dict[str, Voice] = {v.name.lower(): v for v in VOICES}

DEFAULT_VOICE = "Kore"


def get_voice(name: str) -> Voice | None:
    """Get a voice by name (case-insensitive).

    Args:
        name: The voice name to look up.

    Returns:
        The Voice if found, None otherwise.
    """
    return _VOICE_MAP.get(name.lower())


def is_valid_voice(name: str) -> bool:
    """Check if a voice name is valid (case-insensitive).

    Args:
        name: The voice name to check.

    Returns:
        True if the voice exists, False otherwise.
    """
    return name.lower() in _VOICE_MAP


def list_voices() -> str:
    """Get a formatted list of all available voices.

    Returns:
        A formatted string with all voices and descriptions.
    """
    lines = ["Available voices:"]
    for voice in VOICES:
        lines.append(f"  {voice.name:20} - {voice.description}")
    return "\n".join(lines)


def get_all_voice_names() -> list[str]:
    """Get all voice names.

    Returns:
        A list of all voice names.
    """
    return [v.name for v in VOICES]
