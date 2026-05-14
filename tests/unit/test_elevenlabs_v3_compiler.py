"""Tests for ElevenLabs v3 tag compilation."""

from audio_generation.emotion.elevenlabs_v3_tags import compile_elevenlabs_v3_tags
from audio_generation.emotion.normalizer import normalize_performance_direction


def test_whisper_compiles_to_v3_tag():
    direction = normalize_performance_direction("whispering, nervous")

    assert compile_elevenlabs_v3_tags("I hear something.", direction) == "[whispers] I hear something."


def test_laugh_compiles_to_v3_tag():
    direction = normalize_performance_direction("excited, laughing")

    assert compile_elevenlabs_v3_tags("We found it!", direction) == "[excited] [laughs] We found it!"


def test_curious_compiles_to_v3_tag():
    direction = normalize_performance_direction("curious")

    assert compile_elevenlabs_v3_tags("What is this?", direction) == "[curious] What is this?"


def test_unsupported_descriptor_is_dropped():
    direction = normalize_performance_direction("nervous")
    compiled = compile_elevenlabs_v3_tags("I can try.", direction)

    assert compiled == "I can try."
    assert "[nervous]" not in compiled


def test_compiler_does_not_alter_spoken_words():
    direction = normalize_performance_direction("playful")
    spoken = "The same words stay here."

    assert compile_elevenlabs_v3_tags(spoken, direction) == f"[mischievously] {spoken}"
