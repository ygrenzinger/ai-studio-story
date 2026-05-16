"""Tests for Gemini TTS client configuration."""

import pytest

from audio_generation.tts import client as tts_client_module
from audio_generation.tts.client import TTSClient


class FakeGenAI:
    def __init__(self):
        self.clients = []

    def Client(self, **kwargs):
        self.clients.append(kwargs)
        return object()


def test_tts_client_uses_vertex_when_project_is_configured(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(tts_client_module, "genai", fake_genai)

    client = TTSClient(
        model="gemini-2.5-flash-preview-tts",
        project="test-project",
        location="us-central1",
    )

    assert client.model == "gemini-2.5-flash-preview-tts"
    assert fake_genai.clients == [
        {"vertexai": True, "project": "test-project", "location": "us-central1"}
    ]


def test_tts_client_uses_gemini_api_key_without_project(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(tts_client_module, "genai", fake_genai)

    client = TTSClient(
        model="gemini-3.1-flash-tts-preview",
        api_key="test-key",
    )

    assert client.model == "gemini-3.1-flash-tts-preview"
    assert fake_genai.clients == [{"api_key": "test-key"}]


def test_tts_client_requires_project_or_api_key(monkeypatch):
    fake_genai = FakeGenAI()
    monkeypatch.setattr(tts_client_module, "genai", fake_genai)

    with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT or GEMINI_API_KEY"):
        TTSClient(model="gemini-3.1-flash-tts-preview")
