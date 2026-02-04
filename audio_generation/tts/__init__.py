"""TTS generation module."""

from audio_generation.tts.client import TTSClient
from audio_generation.tts.config_builder import SpeechConfigBuilder
from audio_generation.tts.prompt_builder import TTSPromptBuilder

__all__ = ["TTSClient", "SpeechConfigBuilder", "TTSPromptBuilder"]
