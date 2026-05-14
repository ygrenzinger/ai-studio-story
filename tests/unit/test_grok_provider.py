"""Tests for Grok provider REST behavior."""

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from audio_generation.domain.models import AudioScript, Segment, SegmentBatch, SpeakerConfig
from audio_generation.emotion.normalizer import normalize_performance_direction
from audio_generation.cli import print_voice_dry_run
from audio_generation.providers.base import (
    AudioFormat,
    SynthesisRequest,
    TTSAuthError,
    TTSProviderError,
    TTSRateLimitError,
    TTSValidationError,
)
from audio_generation.providers.grok import GrokProvider
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


def make_request(segment=None, voice="ara"):
    if segment is None:
        segment = Segment("Narrator", "Hello from KidStory.")
    speaker = SpeakerConfig(name="Narrator", voice=voice)
    batch = SegmentBatch([segment], ["Narrator"])
    return SynthesisRequest(
        script=AudioScript(stage_uuid="test", locale="en-US", speaker_configs=[speaker], segments=[segment]),
        batch=batch,
        speaker_configs={"Narrator": speaker},
        character_profiles={},
        locale="en-US",
        output_format=AudioFormat(codec="mp3", sample_rate=44100, bit_rate=192000),
    )


def test_registry_returns_grok_provider():
    provider = create_provider("grok")

    assert isinstance(provider, GrokProvider)


def test_missing_xai_key_fails_on_synthesize_only():
    provider = GrokProvider(api_key="")

    with pytest.raises(TTSAuthError, match="XAI_API_KEY"):
        provider.synthesize(make_request())


def test_dry_run_voices_works_without_xai_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
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

    print_voice_dry_run(script_path, "grok", None)

    output = capsys.readouterr().out
    assert "Selected provider: grok" in output
    assert "voice: ara" in output


def test_fake_http_success_returns_synthesis_result_and_payload():
    captured = {}

    def opener(request, timeout):
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    provider = GrokProvider(api_key="test-key", opener=opener)
    result = provider.synthesize(make_request())

    assert result.audio_bytes == b"mp3-data"
    assert result.codec == "mp3"
    assert result.sample_rate == 44100
    assert captured["payload"] == {
        "text": "Hello from KidStory.",
        "voice_id": "ara",
        "language": "auto",
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 192000},
    }
    assert captured["headers"]["Authorization"] == "Bearer test-key"


def test_request_payload_uses_compiled_grok_tags():
    captured = {}
    segment = Segment("Narrator", "We did it!", emotion="laughing, excited")
    segment.direction = normalize_performance_direction(segment.emotion)

    def opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    GrokProvider(api_key="test-key", opener=opener).synthesize(make_request(segment))

    assert captured["payload"]["text"] == "[laugh] We did it!"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [(401, TTSAuthError), (429, TTSRateLimitError), (400, TTSValidationError), (500, TTSProviderError)],
)
def test_http_errors_map_to_normalized_errors(status, error_type):
    def opener(request, timeout):
        raise HTTPError(
            url="https://api.x.ai/v1/tts",
            code=status,
            msg="error",
            hdrs=None,
            fp=BytesIO(b"provider said no"),
        )

    provider = GrokProvider(api_key="test-key", opener=opener)

    with pytest.raises(error_type, match="provider said no"):
        provider.synthesize(make_request())
