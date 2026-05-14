"""Canonical performance direction taxonomy."""

CANONICAL_EMOTIONS = {
    "angry",
    "brave",
    "calm",
    "crying",
    "curious",
    "excited",
    "happy",
    "mysterious",
    "nervous",
    "playful",
    "sad",
    "scared",
    "surprised",
    "sarcastic",
    "tense",
    "warm",
}

CANONICAL_DELIVERY = {
    "bright",
    "gentle",
    "hushed",
    "whispering",
}

CANONICAL_VOCAL_EVENTS = {
    "chuckle",
    "exhale",
    "giggle",
    "inhale",
    "laugh",
    "long_pause",
    "pause",
    "sigh",
}

PACE_VALUES = {"fast", "normal", "slow"}
VOLUME_VALUES = {"loud", "normal", "soft"}
PITCH_VALUES = {"high", "low", "normal"}
INTENSITY_VALUES = {"high", "low", "medium"}

EMOTION_SYNONYMS = {
    "afraid": "scared",
    "anxious": "nervous",
    "cheerful": "happy",
    "frightened": "scared",
    "joyful": "happy",
    "worried": "nervous",
}

DELIVERY_SYNONYMS = {
    "hushed": "hushed",
    "softly spoken": "gentle",
    "whisper": "whispering",
    "whispered": "whispering",
}

VOCAL_EVENT_SYNONYMS = {
    "laughing": "laugh",
    "laughs": "laugh",
    "chuckling": "chuckle",
    "chuckles": "chuckle",
    "giggling": "giggle",
    "giggles": "giggle",
    "inhales": "inhale",
    "inhaling": "inhale",
    "exhales": "exhale",
    "exhaling": "exhale",
    "long pause": "long_pause",
    "long-pause": "long_pause",
    "sighing": "sigh",
    "sighs": "sigh",
}

PACE_SYNONYMS = {
    "quick": "fast",
    "quickly": "fast",
    "rapid": "fast",
    "slowly": "slow",
}

VOLUME_SYNONYMS = {
    "quiet": "soft",
    "quietly": "soft",
    "softly": "soft",
}

PITCH_SYNONYMS = {
    "higher pitch": "high",
    "higher-pitch": "high",
    "lower pitch": "low",
    "lower-pitch": "low",
}
INTENSITY_SYNONYMS = {}
