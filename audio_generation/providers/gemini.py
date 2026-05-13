"""Gemini TTS provider wrapper."""

from audio_generation.domain.constants import GEMINI_TTS_SAMPLE_RATE, TTS_SYSTEM_INSTRUCTION
from audio_generation.providers.base import (
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
)
from audio_generation.tts.client import TTSClient
from audio_generation.tts.config_builder import SpeechConfigBuilder
from audio_generation.tts.prompt_builder import TTSPromptBuilder


class GeminiProvider:
    """Provider adapter around the existing Gemini TTS components."""

    name = "gemini"
    capabilities = ProviderCapabilities(
        supports_prompt_director_notes=True,
        supports_inline_tags=False,
        supports_wrapping_tags=False,
        supports_voice_settings=False,
        supports_direct_mp3_44100=False,
    )

    def __init__(
        self,
        tts_client: TTSClient,
        config_builder: SpeechConfigBuilder | None = None,
        prompt_builder: TTSPromptBuilder | None = None,
    ):
        self._tts_client = tts_client
        self._config_builder = config_builder or SpeechConfigBuilder()
        self._prompt_builder = prompt_builder or TTSPromptBuilder()

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        prompt = self._prompt_builder.build(
            request.batch,
            request.speaker_configs,
            request.character_profiles,
        )
        speech_config = self._config_builder.build_for_batch(
            request.batch,
            request.speaker_configs,
        )
        audio_bytes = self._tts_client.generate(
            prompt,
            speech_config,
            system_instruction=TTS_SYSTEM_INSTRUCTION,
            batch_num=request.batch_num,
        )
        return SynthesisResult(
            audio_bytes=audio_bytes,
            codec="pcm",
            sample_rate=GEMINI_TTS_SAMPLE_RATE,
            channels=1,
        )
