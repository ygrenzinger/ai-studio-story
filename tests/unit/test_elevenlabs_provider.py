"""Tests for ElevenLabs v3 provider."""

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from audio_generation.cli import print_voice_dry_run, validate_provider_model
from audio_generation.domain.models import AudioScript, Segment, SegmentBatch, SpeakerConfig
from audio_generation.emotion.normalizer import normalize_performance_direction
from audio_generation.providers.base import (
    AudioFormat,
    SynthesisRequest,
    TTSAuthError,
    TTSProviderError,
    TTSRateLimitError,
    TTSValidationError,
)
from audio_generation.providers.elevenlabs import ElevenLabsProvider
from audio_generation.providers.registry import create_provider


class FakeResponse:
    def __init__(self, data=b"mp3-data"):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._data


def make_request(segment=None, voice="voice-123", settings=None):
    if segment is None:
        segment = Segment("Narrator", "Hello from KidStory.")
    speaker = SpeakerConfig(name="Narrator", voice=voice)
    if settings is not None:
        speaker.provider_settings["elevenlabs"] = {"voice_settings": settings}
    batch = SegmentBatch([segment], ["Narrator"])
    return SynthesisRequest(
        script=AudioScript(stage_uuid="test", locale="en-US", speaker_configs=[speaker], segments=[segment]),
        batch=batch,
        speaker_configs={"Narrator": speaker},
        character_profiles={},
        locale="en-US",
        output_format=AudioFormat(codec="mp3", sample_rate=44100, bit_rate=128000),
    )


def test_registry_returns_elevenlabs_provider():
    provider = create_provider("elevenlabs")

    assert isinstance(provider, ElevenLabsProvider)


def test_provider_model_validation_accepts_v3():
    assert validate_provider_model("elevenlabs", "eleven_v3") == "eleven_v3"


def test_provider_model_validation_rejects_non_v3():
    with pytest.raises(ValueError, match="only model eleven_v3"):
        validate_provider_model("elevenlabs", "eleven_multilingual_v2")


def test_dry_run_voices_works_without_api_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voiceRole: warm_narrator
---

**Narrator:** Hello.
"""
    )

    print_voice_dry_run(script_path, "elevenlabs", None)

    output = capsys.readouterr().out
    assert "Selected provider: elevenlabs" in output
    assert "voice: JBFqnCBsd6RMkjVDRZzb" in output


def test_missing_api_key_fails_on_synthesize_only():
    provider = ElevenLabsProvider(api_key="")

    with pytest.raises(TTSAuthError, match="ELEVENLABS_API_KEY"):
        provider.synthesize(make_request())


def test_fake_http_success_returns_result_and_payload():
    captured = {}

    def opener(request, timeout):
        captured["timeout"] = timeout
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    provider = ElevenLabsProvider(api_key="test-key", opener=opener)
    result = provider.synthesize(
        make_request(settings={"stability": 0.5, "style": 0.45})
    )

    assert result.audio_bytes == b"mp3-data"
    assert result.codec == "mp3"
    assert "voice-123?output_format=mp3_44100_128" in captured["url"]
    assert captured["headers"]["Xi-api-key"] == "test-key"
    assert captured["payload"]["model_id"] == "eleven_v3"
    assert captured["payload"]["voice_settings"]["stability"] == 0.5
    assert captured["payload"]["voice_settings"]["style"] == 0.45


def test_payload_uses_compiled_elevenlabs_tags():
    captured = {}
    segment = Segment("Narrator", "We found it!", emotion="excited, laughing")
    segment.direction = normalize_performance_direction(segment.emotion)

    def opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    ElevenLabsProvider(api_key="test-key", opener=opener).synthesize(make_request(segment))

    assert captured["payload"]["text"] == "[excited] [laughs] We found it!"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, TTSAuthError),
        (403, TTSAuthError),
        (422, TTSValidationError),
        (429, TTSRateLimitError),
        (500, TTSProviderError),
    ],
)
def test_http_errors_map_to_normalized_errors(status, error_type):
    def opener(request, timeout):
        raise HTTPError(
            url="https://api.elevenlabs.io/v1/text-to-speech/voice-123",
            code=status,
            msg="error",
            hdrs=None,
            fp=BytesIO(b"provider said no"),
        )

    provider = ElevenLabsProvider(api_key="test-key", opener=opener)

    with pytest.raises(error_type, match="provider said no"):
        provider.synthesize(make_request())
