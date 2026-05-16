"""Speech configuration builder for Gemini TTS API."""

try:
    from google.genai import types
except (ImportError, ModuleNotFoundError):  # pragma: no cover - without optional SDK
    class _SimpleType:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class _Types:
        SpeechConfig = _SimpleType
        VoiceConfig = _SimpleType
        PrebuiltVoiceConfig = _SimpleType

    types = _Types()

from audio_generation.domain.models import SegmentBatch, SpeakerConfig


class SpeechConfigBuilder:
    """Builds Gemini TTS speech configurations.

    Uses single-speaker configurations for Vertex AI-compatible Gemini TTS.
    """

    def build_single_speaker(self, speaker: SpeakerConfig) -> types.SpeechConfig:
        """Build TTS config for single speaker.

        Args:
            speaker: Speaker configuration

        Returns:
            SpeechConfig for Gemini TTS API
        """
        return types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=speaker.voice
                )
            )
        )

    def build_for_batch(
        self, batch: SegmentBatch, speaker_configs_map: dict[str, SpeakerConfig]
    ) -> types.SpeechConfig:
        """Build speech config for a batch.

        Args:
            batch: The segment batch
            speaker_configs_map: Mapping of speaker name to config

        Returns:
            SpeechConfig appropriate for the batch
        """
        if len(batch.speakers) == 1:
            return self.build_single_speaker(speaker_configs_map[batch.speakers[0]])
        raise ValueError(
            "Gemini TTS is configured for Vertex AI-compatible single-speaker "
            "requests; split multi-speaker dialogue before synthesis"
        )
