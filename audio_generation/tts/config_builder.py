"""Speech configuration builder for Gemini TTS API."""

from google.genai import types

from audio_generation.domain.models import SegmentBatch, SpeakerConfig


class SpeechConfigBuilder:
    """Builds Gemini TTS speech configurations.

    Supports both single-speaker and multi-speaker (max 2) configurations
    for the Gemini TTS API.
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

    def build_multi_speaker(self, speakers: list[SpeakerConfig]) -> types.SpeechConfig:
        """Build TTS config for multiple speakers (max 2).

        Args:
            speakers: List of speaker configurations

        Returns:
            SpeechConfig for Gemini TTS API with multi-speaker support
        """
        speaker_voice_configs = []
        for cfg in speakers:
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=cfg.name,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=cfg.voice
                        )
                    ),
                )
            )

        return types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
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
        else:
            configs = [speaker_configs_map[s] for s in batch.speakers]
            return self.build_multi_speaker(configs)
