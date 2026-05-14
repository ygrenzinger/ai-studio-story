"""Tests for Grok emotion tag compilation."""

from audio_generation.emotion.grok_tags import compile_grok_tags
from audio_generation.emotion.normalizer import normalize_performance_direction


def test_whisper_compiles_to_wrapper():
    direction = normalize_performance_direction("whispering, nervous")

    assert compile_grok_tags("I hear something.", direction) == "<whisper>I hear something.</whisper>"


def test_slow_plus_soft_nests_deterministically():
    direction = normalize_performance_direction("slow, soft")

    assert compile_grok_tags("Goodnight.", direction) == "<slow><soft>Goodnight.</soft></slow>"


def test_laugh_compiles_to_inline_event():
    direction = normalize_performance_direction("laughing, excited")

    assert compile_grok_tags("We did it!", direction) == "[laugh] We did it!"


def test_unsupported_descriptor_is_dropped():
    direction = normalize_performance_direction("nervous")

    compiled = compile_grok_tags("I can try.", direction)

    assert compiled == "I can try."
    assert "[nervous]" not in compiled
