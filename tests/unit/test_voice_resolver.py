"""Tests for voice registry and resolver."""

import pytest

from audio_generation.domain.models import SpeakerConfig
from audio_generation.voices.models import ProviderVoiceConfig, VoiceRole
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


def test_gemini_voice_map_uses_allowed_voices():
    registry = VoiceRegistry.load()

    gemini_voices = {
        role.providers["gemini"].voice
        for role in registry.roles.values()
        if "gemini" in role.providers
    }

    assert gemini_voices <= PROVIDER_VOICE_ALLOWLISTS["gemini"]
    assert len(gemini_voices) == 30


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


def test_elevenlabs_voice_map_uses_real_voice_ids():
    registry = VoiceRegistry.load()
    expected_roles = {
        "warm_narrator": "JBFqnCBsd6RMkjVDRZzb",
        "clear_narrator": "nPczCjzI2devNBz1zQrb",
        "playful_child": "Xb7hH8MSUJpSbSDYk0k2",
        "gentle_child": "XrExE9yKIg1WjnnlVkGX",
        "wise_mentor": "onwK4e9ZLuTAKqWW03F9",
        "mysterious_guide": "XB0fDUnXU5powFXDhCwa",
        "gruff_creature": "N2lVS1w4EtoT3dr4eOWO",
        "energetic_adventurer": "TX3LPaxmHKxFdv7VOQHJ",
        "calm_teacher": "nPczCjzI2devNBz1zQrb",
        "soft_bedtime": "pFZP5JQG7iQjIQuC4Bku",
    }

    actual_roles = {
        role: registry.roles[role].providers["elevenlabs"].voice
        for role in expected_roles
    }

    assert actual_roles == expected_roles
    assert not any(voice.startswith("placeholder_") for voice in actual_roles.values())


def test_elevenlabs_placeholder_registry_voice_fails_in_strict_mode():
    registry = VoiceRegistry(
        {
            "bad_role": VoiceRole(
                name="bad_role",
                providers={
                    "elevenlabs": ProviderVoiceConfig(voice="placeholder_bad_role")
                },
            )
        }
    )
    speaker = SpeakerConfig(name="Narrator", voice_role="bad_role")

    with pytest.raises(ValueError, match="placeholder voice"):
        resolve_voice(speaker, "elevenlabs", registry, strict=True)


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


def test_permissive_missing_elevenlabs_role_falls_back_to_documented_voice():
    registry = VoiceRegistry.load()
    speaker = SpeakerConfig(name="Narrator", voice="", voice_role="missing")

    resolved = resolve_voice(speaker, "elevenlabs", registry, strict=False)

    assert resolved.voice_id == "JBFqnCBsd6RMkjVDRZzb"
    assert resolved.source == "providers.elevenlabs.default_voice"
