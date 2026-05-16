"""Tests for provider registry."""

import pytest

from audio_generation.domain.constants import GEMINI_3_1_FLASH_TTS_MODEL
from audio_generation.providers import registry
from audio_generation.providers.gemini import GeminiProvider


class FakeTTSClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_provider_registry_returns_gemini_provider(monkeypatch):
    monkeypatch.setattr(registry, "TTSClient", FakeTTSClient)

    provider = registry.create_provider("gemini", project="test-project")

    assert isinstance(provider, GeminiProvider)
    assert provider.name == "gemini"


def test_provider_registry_passes_gemini_31_model_with_api_key(monkeypatch):
    monkeypatch.setattr(registry, "TTSClient", FakeTTSClient)

    provider = registry.create_provider(
        "gemini",
        model=GEMINI_3_1_FLASH_TTS_MODEL,
        api_key="test-key",
    )

    assert provider._tts_client.kwargs["model"] == GEMINI_3_1_FLASH_TTS_MODEL
    assert provider._tts_client.kwargs["api_key"] == "test-key"
    assert provider._tts_client.kwargs["project"] is None


def test_provider_registry_gemini_requires_auth():
    with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT or GEMINI_API_KEY"):
        registry.create_provider("gemini")


def test_provider_registry_unknown_provider_errors():
    with pytest.raises(ValueError, match="Unknown TTS provider"):
        registry.create_provider("unknown", project="test-project")
