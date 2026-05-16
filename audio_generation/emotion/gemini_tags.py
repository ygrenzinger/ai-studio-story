"""Compile structured performance directions into Gemini TTS audio tags."""

from audio_generation.domain.models import PerformanceDirection, Segment

EMOTION_TAGS = {
    "curious": "[curious]",
    "excited": "[excited]",
    "nervous": "[trembling]",
    "playful": "[mischievously]",
    "sad": "[tired]",
    "sarcastic": "[sarcastically]",
    "scared": "[panicked]",
    "surprised": "[amazed]",
    "tense": "[serious]",
}

DELIVERY_TAGS = {
    "hushed": "[whispers]",
    "whispering": "[whispers]",
}

VOCAL_EVENT_TAGS = {
    "laugh": "[laughs]",
    "giggle": "[giggles]",
    "sigh": "[sighs]",
}

PACE_TAGS = {
    "fast": "[very fast]",
    "slow": "[very slow]",
}

VOLUME_TAGS = {
    "loud": "[shouting]",
    "soft": "[softly]",
}


def compile_gemini_segment_text(segment: Segment) -> str:
    """Compile supported directions for one segment into safe Gemini tags."""

    return compile_gemini_tags(segment.text, segment.direction)


def compile_gemini_tags(text: str, direction: PerformanceDirection) -> str:
    """Prefix spoken text with allowlisted Gemini audio tags."""

    tags: list[str] = []
    for delivery in direction.delivery:
        if delivery in DELIVERY_TAGS:
            tags.append(DELIVERY_TAGS[delivery])
    for emotion in direction.emotion:
        if emotion in EMOTION_TAGS:
            tags.append(EMOTION_TAGS[emotion])
    for event in direction.vocal_events:
        if event in VOCAL_EVENT_TAGS:
            tags.append(VOCAL_EVENT_TAGS[event])
    if direction.pace in PACE_TAGS:
        tags.append(PACE_TAGS[direction.pace])
    if direction.volume in VOLUME_TAGS:
        tags.append(VOLUME_TAGS[direction.volume])

    tags = _dedupe(tags)
    if not tags:
        return text
    return f"{' '.join(tags)} {text}"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
