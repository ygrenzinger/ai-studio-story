"""Compile structured performance directions into ElevenLabs v3 audio tags."""

from audio_generation.domain.models import PerformanceDirection, Segment

VOCAL_EVENT_TAGS = {
    "laugh": "[laughs]",
    "chuckle": "[chuckles]",
    "giggle": "[giggles]",
    "sigh": "[sighs]",
    "inhale": "[inhales]",
    "exhale": "[exhales]",
}

DIRECTION_TAGS = {
    "whispering": "[whispers]",
    "sarcastic": "[sarcastic]",
    "curious": "[curious]",
    "excited": "[excited]",
    "crying": "[crying]",
    "playful": "[mischievously]",
}


def compile_elevenlabs_v3_segment_text(segment: Segment) -> str:
    """Compile supported directions for one segment into Eleven v3 tags."""

    return compile_elevenlabs_v3_tags(segment.text, segment.direction)


def compile_elevenlabs_v3_tags(text: str, direction: PerformanceDirection) -> str:
    """Prefix text with allowlisted Eleven v3 audio tags."""

    tags: list[str] = []
    for delivery in direction.delivery:
        if delivery in DIRECTION_TAGS:
            tags.append(DIRECTION_TAGS[delivery])
    for emotion in direction.emotion:
        if emotion in DIRECTION_TAGS:
            tags.append(DIRECTION_TAGS[emotion])
    for event in direction.vocal_events:
        if event in VOCAL_EVENT_TAGS:
            tags.append(VOCAL_EVENT_TAGS[event])

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
