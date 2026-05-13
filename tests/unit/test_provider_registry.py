"""Tests for provider registry."""

import pytest

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


def test_provider_registry_unknown_provider_errors():
    with pytest.raises(ValueError, match="Unknown TTS provider"):
        registry.create_provider("unknown", project="test-project")
