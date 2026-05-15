"""Tests for ElevenLabs voice settings resolution and validation."""

import pytest

from audio_generation.domain.models import Segment, VerificationResult
from audio_generation.orchestrator import AudioGenerationPipeline
from audio_generation.providers.base import SynthesisResult, TTSValidationError
from audio_generation.providers.elevenlabs import resolve_elevenlabs_voice_settings


def test_story_settings_override_provider_defaults():
    settings = resolve_elevenlabs_voice_settings({"stability": 0.8, "speed": 1.1})

    assert settings["stability"] == 0.8
    assert settings["speed"] == 1.1
    assert settings["similarity_boost"] == 0.75


def test_invalid_speed_fails_validation():
    with pytest.raises(TTSValidationError, match="speed"):
        resolve_elevenlabs_voice_settings({"speed": 1.3})


def test_invalid_stability_fails_validation():
    with pytest.raises(TTSValidationError, match="stability"):
        resolve_elevenlabs_voice_settings({"stability": -0.1})


class RecordingElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self):
        self.requests = []

    def synthesize(self, request):
        self.requests.append(request)
        assert len(request.batch.speakers) == 1
        return SynthesisResult(audio_bytes=b"pcm", codec="pcm")


class FakeConcatenator:
    def concatenate(self, audio_segments, batch_metadata):
        return b"combined"


class FakeExporter:
    def export(self, combined, output_path):
        output_path.write_bytes(b"mp3")
        return b"mp3"


class FakeVerifier:
    def verify(self, mp3_data):
        return VerificationResult(passed=True)


def test_story_settings_override_registry_settings(tmp_path):
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voiceRole: warm_narrator
    voices:
      elevenlabs: account_voice_123
    providerSettings:
      elevenlabs:
        voice_settings:
          stability: 0.9
---

**Narrator:** Hello.
"""
    )
    provider = RecordingElevenLabsProvider()

    _pipeline(provider).execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    speaker = provider.requests[0].speaker_configs["Narrator"]
    assert speaker.voice == "account_voice_123"
    assert speaker.provider_settings["elevenlabs"]["voice_settings"]["stability"] == 0.9


def test_registry_settings_override_provider_defaults(tmp_path):
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
    provider = RecordingElevenLabsProvider()

    _pipeline(provider).execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    settings = provider.requests[0].speaker_configs["Narrator"].provider_settings[
        "elevenlabs"
    ]["voice_settings"]
    assert settings["stability"] == 0.4
    assert settings["style"] == 0.3


def test_missing_elevenlabs_voice_fails_in_strict_mode(tmp_path):
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voiceRole: missing_role
---

**Narrator:** Hello.
"""
    )

    with pytest.raises(ValueError, match="No elevenlabs voice configured"):
        _pipeline(RecordingElevenLabsProvider()).execute(
            script_path, tmp_path / "out.mp3", delay_seconds=0, strict_voices=True
        )


def test_registry_voice_resolves_in_strict_mode(tmp_path):
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
    provider = RecordingElevenLabsProvider()

    _pipeline(provider).execute(
        script_path, tmp_path / "out.mp3", delay_seconds=0, strict_voices=True
    )

    assert (
        provider.requests[0].speaker_configs["Narrator"].voice
        == "JBFqnCBsd6RMkjVDRZzb"
    )


def test_alternating_script_sends_one_speaker_batches(tmp_path):
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voices:
      elevenlabs: narrator_voice
  - name: Leo
    voices:
      elevenlabs: leo_voice
---

**Narrator:** Setup.

**Leo:** Hello.

**Narrator:** Back.
"""
    )
    provider = RecordingElevenLabsProvider()

    _pipeline(provider).execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    assert [request.batch.speakers for request in provider.requests] == [
        ["Narrator"],
        ["Leo"],
        ["Narrator"],
    ]


def _pipeline(provider):
    return AudioGenerationPipeline(
        provider=provider,
        concatenator=FakeConcatenator(),
        exporter=FakeExporter(),
        verifier=FakeVerifier(),
    )
