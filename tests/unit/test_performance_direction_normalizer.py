"""Tests for performance direction normalization."""

from audio_generation.emotion.normalizer import normalize_performance_direction


def test_whispered_nervous_normalizes_delivery_and_emotion():
    direction = normalize_performance_direction("whispered, nervous")

    assert direction.delivery == ["whispering"]
    assert direction.emotion == ["nervous"]


def test_laughing_excited_normalizes_vocal_event_and_emotion():
    direction = normalize_performance_direction("laughing, excited")

    assert direction.vocal_events == ["laugh"]
    assert direction.emotion == ["excited"]


def test_slow_soft_normalizes_pace_and_volume():
    direction = normalize_performance_direction("slow, soft")

    assert direction.pace == "slow"
    assert direction.volume == "soft"
