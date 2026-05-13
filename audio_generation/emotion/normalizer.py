"""Normalize raw script performance descriptors."""

import re

from audio_generation.domain.models import PerformanceDirection
from audio_generation.emotion.taxonomy import (
    CANONICAL_DELIVERY,
    CANONICAL_EMOTIONS,
    CANONICAL_VOCAL_EVENTS,
    DELIVERY_SYNONYMS,
    EMOTION_SYNONYMS,
    INTENSITY_SYNONYMS,
    INTENSITY_VALUES,
    PACE_SYNONYMS,
    PACE_VALUES,
    PITCH_SYNONYMS,
    PITCH_VALUES,
    VOCAL_EVENT_SYNONYMS,
    VOLUME_SYNONYMS,
    VOLUME_VALUES,
)


def normalize_performance_direction(raw: str) -> PerformanceDirection:
    """Normalize a comma-separated performance descriptor string."""

    direction = PerformanceDirection(raw=raw.strip())
    if not raw.strip():
        return direction

    descriptors = [part.strip().lower() for part in re.split(r"[,;]", raw) if part.strip()]
    for descriptor in descriptors:
        value = EMOTION_SYNONYMS.get(descriptor, descriptor)
        if value in CANONICAL_EMOTIONS:
            _append_unique(direction.emotion, value)
            continue

        value = DELIVERY_SYNONYMS.get(descriptor, descriptor)
        if value in CANONICAL_DELIVERY:
            _append_unique(direction.delivery, value)
            continue

        value = VOCAL_EVENT_SYNONYMS.get(descriptor, descriptor)
        if value in CANONICAL_VOCAL_EVENTS:
            _append_unique(direction.vocal_events, value)
            continue

        value = PACE_SYNONYMS.get(descriptor, descriptor)
        if value in PACE_VALUES:
            direction.pace = value
            continue

        value = VOLUME_SYNONYMS.get(descriptor, descriptor)
        if value in VOLUME_VALUES:
            direction.volume = value
            continue

        value = PITCH_SYNONYMS.get(descriptor, descriptor)
        if value in PITCH_VALUES:
            direction.pitch = value
            continue

        value = INTENSITY_SYNONYMS.get(descriptor, descriptor)
        if value in INTENSITY_VALUES:
            direction.intensity = value

    return direction


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
