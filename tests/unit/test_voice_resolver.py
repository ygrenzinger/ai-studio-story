"""Tests for voice registry and resolver."""

import pytest

from audio_generation.domain.models import SpeakerConfig
from audio_generation.voices.registry import VoiceRegistry
from audio_generation.voices.resolver import PROVIDER_VOICE_ALLOWLISTS, resolve_voice


def test_registry_loads_global_voice_map():
    registry = VoiceRegistry.load()

    assert "warm_narrator" in registry.roles


def test_known_role_resolves_for_gemini():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice_role="warm_narrator")

    resolved = resolve_voice(speaker, "gemini", registry, strict=True)

    assert resolved.voice_id == "Sulafat"
    assert resolved.source == "registry.roles.warm_narrator.providers.gemini.voice"


def test_grok_voice_map_uses_known_current_voices():
    registry = VoiceRegistry.load()
    expected_roles = {
        "warm_narrator": "ara",
        "clear_narrator": "rex",
        "playful_child": "eve",
        "gentle_child": "ara",
        "wise_mentor": "leo",
        "mysterious_guide": "sal",
        "gruff_creature": "leo",
        "energetic_adventurer": "eve",
        "calm_teacher": "leo",
        "soft_bedtime": "ara",
    }

    actual_roles = {
        role: registry.roles[role].providers["grok"].voice
        for role in expected_roles
    }

    assert actual_roles == expected_roles
    assert set(actual_roles.values()) <= PROVIDER_VOICE_ALLOWLISTS["grok"]


def test_story_provider_override_wins():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(
        name="Narrator",
        voice_role="warm_narrator",
        provider_voices={"gemini": "Puck"},
    )

    resolved = resolve_voice(speaker, "gemini", registry, strict=True)

    assert resolved.voice_id == "Puck"
    assert resolved.source == "speakers.Narrator.voices.gemini"


def test_legacy_voice_wins_without_role():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice="Leda")

    resolved = resolve_voice(speaker, "gemini", registry, strict=True)

    assert resolved.voice_id == "Leda"
    assert resolved.source == "speakers.Narrator.voice"


def test_strict_missing_role_fails():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice_role="missing")

    with pytest.raises(ValueError, match="No gemini voice configured"):
        resolve_voice(speaker, "gemini", registry, strict=True)


def test_permissive_missing_role_falls_back():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice="", voice_role="missing")

    resolved = resolve_voice(speaker, "gemini", registry, strict=False)

    assert resolved.voice_id == "Sulafat"
    assert resolved.source == "providers.gemini.default_voice"


def test_permissive_missing_grok_role_falls_back_to_eve():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice="", voice_role="missing")

    resolved = resolve_voice(speaker, "grok", registry, strict=False)

    assert resolved.voice_id == "eve"
    assert resolved.source == "providers.grok.default_voice"
