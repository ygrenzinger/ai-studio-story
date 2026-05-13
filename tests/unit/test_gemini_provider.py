"""Tests for Gemini provider wrapper."""

from audio_generation.domain.models import AudioScript, Segment, SegmentBatch, SpeakerConfig
from audio_generation.domain.models import VerificationResult
from audio_generation.orchestrator import AudioGenerationPipeline
from audio_generation.providers.base import AudioFormat, ProviderCapabilities, SynthesisRequest, SynthesisResult
from audio_generation.providers.gemini import GeminiProvider


class FakeTTSClient:
    def __init__(self):
        self.calls = []

    def generate(self, prompt, speech_config, system_instruction="", batch_num=0):
        self.calls.append((prompt, speech_config, system_instruction, batch_num))
        return b"pcm-data"


def test_gemini_provider_receives_batch_and_returns_result():
    client = FakeTTSClient()
    provider = GeminiProvider(client)
    speaker = SpeakerConfig(name="Narrator", voice="Sulafat")
    batch = SegmentBatch([Segment("Narrator", "Hello.")], ["Narrator"])

    result = provider.synthesize(
        SynthesisRequest(
            script=AudioScript(stage_uuid="test", speaker_configs=[speaker], segments=batch.segments),
            batch=batch,
            speaker_configs={"Narrator": speaker},
            character_profiles={},
            locale="en-US",
            output_format=AudioFormat(),
            batch_num=1,
        )
    )

    assert result.audio_bytes == b"pcm-data"
    assert result.codec == "pcm"
    assert client.calls[0][3] == 1


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(False, True, True, True, True)

    def __init__(self):
        self.requests = []

    def synthesize(self, request):
        self.requests.append(request)
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


def test_pipeline_executes_with_fake_provider(tmp_path):
    script_path = tmp_path / "script.md"
    script_path.write_text(
        """---
stageUuid: test
speakers:
  - name: Narrator
    voice: Sulafat
---

**Narrator:** Hello world.
"""
    )
    provider = FakeProvider()
    pipeline = AudioGenerationPipeline(
        provider=provider,
        concatenator=FakeConcatenator(),
        exporter=FakeExporter(),
        verifier=FakeVerifier(),
    )

    result = pipeline.execute(script_path, tmp_path / "out.mp3", delay_seconds=0)

    assert result == b"mp3"
    assert len(provider.requests) == 1
