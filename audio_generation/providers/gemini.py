"""Gemini TTS provider wrapper."""

import logging

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
        supports_inline_tags=True,
        supports_wrapping_tags=False,
        supports_voice_settings=False,
        supports_direct_mp3_44100=False,
        max_speakers_per_request=1,
        max_segments_per_request=12,
        supported_inline_tags=frozenset(
            {
                "[excitedly]",
                "[bored]",
                "[reluctantly]",
                "[very fast]",
                "[very slow]",
                "[sarcastically]",
                "[whispers]",
                "[shouting]",
                "[amazed]",
                "[crying]",
                "[curious]",
                "[excited]",
                "[sighs]",
                "[gasp]",
                "[giggles]",
                "[laughs]",
                "[mischievously]",
                "[panicked]",
                "[serious]",
                "[tired]",
                "[trembling]",
                "[softly]",
            }
        ),
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
        self._fallback_prompt_builder = TTSPromptBuilder(enable_inline_tags=False)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        prompt = self._prompt_builder.build(
            request.batch,
            request.speaker_configs,
            request.character_profiles,
            locale=request.locale,
        )
        speech_config = self._config_builder.build_for_batch(
            request.batch,
            request.speaker_configs,
        )
        try:
            audio_bytes = self._tts_client.generate(
                prompt,
                speech_config,
                system_instruction=TTS_SYSTEM_INSTRUCTION,
                batch_num=request.batch_num,
            )
        except RuntimeError as e:
            if "No audio data in TTS response" not in str(e):
                raise
            fallback_prompt = self._fallback_prompt_builder.build(
                request.batch,
                request.speaker_configs,
                request.character_profiles,
                locale=request.locale,
            )
            if fallback_prompt == prompt:
                raise
            logging.warning(
                "Batch %s returned no Gemini audio; retrying without inline tags",
                request.batch_num,
            )
            audio_bytes = self._tts_client.generate(
                fallback_prompt,
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
