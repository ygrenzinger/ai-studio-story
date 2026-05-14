"""Provider factory registry."""

from audio_generation.domain.constants import DEFAULT_TTS_MODEL
from audio_generation.providers.base import TTSProvider
from audio_generation.providers.gemini import GeminiProvider
from audio_generation.providers.grok import GrokProvider
from audio_generation.tts.client import TTSClient


def create_provider(
    name: str,
    *,
    model: str | None = None,
    project: str | None = None,
    location: str | None = None,
) -> TTSProvider:
    """Create a configured TTS provider by name."""

    provider_name = name.lower()
    if provider_name == "grok":
        return GrokProvider()
    if provider_name != "gemini":
        raise ValueError(f"Unknown TTS provider: {name}")
    if not project:
        raise ValueError("Gemini provider requires a Google Cloud project")
    client = TTSClient(
        model=model or DEFAULT_TTS_MODEL,
        project=project,
        location=location,
    )
    return GeminiProvider(client)
