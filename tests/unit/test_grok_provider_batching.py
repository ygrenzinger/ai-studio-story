"""Tests for Grok batching and provider-specific voice resolution."""

from audio_generation.batching.segment_batcher import SegmentBatcher
from audio_generation.domain.models import Segment, VerificationResult
from audio_generation.orchestrator import AudioGenerationPipeline
from audio_generation.providers.base import SynthesisResult
from audio_generation.providers.grok import GrokProvider


def test_alternating_script_becomes_one_speaker_batches():
    segments = [
        Segment("Narrator", "Setup."),
        Segment("Leo", "Hello."),
        Segment("Narrator", "Back."),
    ]

    batches = SegmentBatcher().batch(segments)

    assert [batch.speakers for batch in batches] == [["Narrator"], ["Leo"], ["Narrator"]]


class RecordingGrokProvider:
    name = "grok"
    capabilities = GrokProvider.capabilities

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


def test_grok_story_override_voice_wins(tmp_path):
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voiceRole: warm_narrator
    voices:
      grok: rex
---

**Narrator:** Hello.
"""
    )
    provider = RecordingGrokProvider()
    pipeline = _pipeline(provider)

    pipeline.execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    assert provider.requests[0].speaker_configs["Narrator"].voice == "rex"


def test_grok_voice_role_registry_resolves(tmp_path):
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
    provider = RecordingGrokProvider()
    pipeline = _pipeline(provider)

    pipeline.execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    assert provider.requests[0].speaker_configs["Narrator"].voice == "ara"


def _pipeline(provider):
    return AudioGenerationPipeline(
        provider=provider,
        concatenator=FakeConcatenator(),
        exporter=FakeExporter(),
        verifier=FakeVerifier(),
    )
