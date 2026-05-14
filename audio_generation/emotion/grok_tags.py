"""Compile structured performance directions into Grok TTS tags."""

from audio_generation.domain.models import PerformanceDirection, Segment

INLINE_EVENTS = {
    "laugh": "[laugh]",
    "chuckle": "[chuckle]",
    "giggle": "[giggle]",
    "sigh": "[sigh]",
    "pause": "[pause]",
    "long_pause": "[long-pause]",
}

WRAPPING_STYLES = {
    "whispering": "whisper",
    "soft": "soft",
    "loud": "loud",
    "slow": "slow",
    "fast": "fast",
    "higher_pitch": "higher-pitch",
    "lower_pitch": "lower-pitch",
}


def compile_grok_segment_text(segment: Segment) -> str:
    """Compile a segment's supported directions into safe Grok tags."""

    return compile_grok_tags(segment.text, segment.direction)


def compile_grok_tags(text: str, direction: PerformanceDirection) -> str:
    """Compile supported Grok inline and wrapping tags from a direction."""

    compiled = text
    for style in _wrapping_styles(direction):
        tag = WRAPPING_STYLES[style]
        compiled = f"<{tag}>{compiled}</{tag}>"

    prefixes = [INLINE_EVENTS[event] for event in direction.vocal_events if event in INLINE_EVENTS]
    if prefixes:
        compiled = f"{' '.join(prefixes)} {compiled}"
    return compiled


def _wrapping_styles(direction: PerformanceDirection) -> list[str]:
    styles: list[str] = []
    for delivery in direction.delivery:
        if delivery in WRAPPING_STYLES:
            styles.append(delivery)
    if direction.volume in WRAPPING_STYLES:
        styles.append(direction.volume)
    if direction.pace in WRAPPING_STYLES:
        styles.append(direction.pace)
    if direction.pitch == "high":
        styles.append("higher_pitch")
    elif direction.pitch == "low":
        styles.append("lower_pitch")
    return _dedupe(styles)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
