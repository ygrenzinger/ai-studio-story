"""Resolve speaker configs to provider-specific voices."""

from audio_generation.domain.constants import AVAILABLE_VOICES, DEFAULT_VOICE
from audio_generation.domain.models import SpeakerConfig
from audio_generation.voices.models import ResolvedVoice
from audio_generation.voices.registry import VoiceRegistry

PROVIDER_DEFAULT_VOICES = {
    "gemini": DEFAULT_VOICE,
    "grok": "eve",
    "elevenlabs": "placeholder_elevenlabs_default",
}

PROVIDER_VOICE_ALLOWLISTS = {
    "gemini": AVAILABLE_VOICES,
    "grok": {"ara", "eve", "rex", "sal", "leo"},
}


def resolve_voice(
    speaker: SpeakerConfig,
    provider: str,
    registry: VoiceRegistry,
    *,
    strict: bool,
) -> ResolvedVoice:
    """Resolve a speaker voice using story overrides, legacy voice, then role registry."""

    provider_name = provider.lower()
    settings = speaker.provider_settings.get(provider_name, {})
    if provider_name in speaker.provider_voices:
        return ResolvedVoice(
            speaker=speaker.name,
            role=speaker.voice_role,
            provider=provider_name,
            voice_id=speaker.provider_voices[provider_name],
            voice_settings=settings.get("voice_settings", {}) or {},
            source=f"speakers.{speaker.name}.voices.{provider_name}",
        )

    if (
        speaker.voice_role is None
        and speaker.voice
        and speaker.voice in PROVIDER_VOICE_ALLOWLISTS.get(provider_name, set())
    ):
        return ResolvedVoice(
            speaker=speaker.name,
            role=None,
            provider=provider_name,
            voice_id=speaker.voice,
            source=f"speakers.{speaker.name}.voice",
        )

    if speaker.voice_role:
        role = registry.get(speaker.voice_role)
        provider_config = role.providers.get(provider_name) if role else None
        if provider_config:
            if strict and provider_name == "elevenlabs" and provider_config.voice.startswith("placeholder_"):
                raise ValueError(
                    f"ElevenLabs role '{speaker.voice_role}' uses placeholder voice "
                    f"'{provider_config.voice}' for speaker '{speaker.name}'"
                )
            return ResolvedVoice(
                speaker=speaker.name,
                role=speaker.voice_role,
                provider=provider_name,
                voice_id=provider_config.voice,
                model=provider_config.model,
                voice_settings={**provider_config.voice_settings, **(settings.get("voice_settings", {}) or {})},
                source=f"registry.roles.{speaker.voice_role}.providers.{provider_name}.voice",
            )
        if strict:
            raise ValueError(
                f"No {provider_name} voice configured for role '{speaker.voice_role}' "
                f"on speaker '{speaker.name}'"
            )

    if speaker.voice in PROVIDER_VOICE_ALLOWLISTS.get(provider_name, set()):
        return ResolvedVoice(
            speaker=speaker.name,
            role=speaker.voice_role,
            provider=provider_name,
            voice_id=speaker.voice,
            source=f"speakers.{speaker.name}.voice",
        )

    if strict:
        raise ValueError(f"No {provider_name} voice configured for speaker '{speaker.name}'")

    return ResolvedVoice(
        speaker=speaker.name,
        role=speaker.voice_role,
        provider=provider_name,
        voice_id=PROVIDER_DEFAULT_VOICES.get(provider_name, DEFAULT_VOICE),
        source=f"providers.{provider_name}.default_voice",
    )
