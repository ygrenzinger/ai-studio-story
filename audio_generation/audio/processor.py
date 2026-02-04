"""Audio processor for PCM conversion and normalization."""

import io
import logging
import wave

from pydub import AudioSegment
from pydub.silence import detect_leading_silence as pydub_detect_silence

from audio_generation.domain.constants import (
    COMFORT_NOISE_LEVEL_DB,
    GEMINI_TTS_SAMPLE_RATE,
    SEGMENT_FADE_IN_MS,
    SEGMENT_FADE_OUT_MS,
    SILENCE_BUFFER_MS,
)
from audio_generation.domain.models import PauseConfig
from audio_generation.audio.effects import AudioEffects


class AudioProcessor:
    """Handles PCM to AudioSegment conversion and normalization.

    Provides methods for converting raw PCM data from TTS API
    to AudioSegment objects, and normalizing audio with fades
    and comfort noise buffers.
    """

    def __init__(self, effects: AudioEffects | None = None):
        """Initialize audio processor.

        Args:
            effects: AudioEffects instance for noise generation (created if None)
        """
        self._effects = effects or AudioEffects()

    def pcm_to_segment(
        self, pcm_data: bytes, sample_rate: int = GEMINI_TTS_SAMPLE_RATE
    ) -> AudioSegment:
        """Convert raw PCM data to AudioSegment.

        Args:
            pcm_data: Raw PCM audio (16-bit signed, mono)
            sample_rate: Source sample rate

        Returns:
            AudioSegment object
        """
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_data)

        wav_buffer.seek(0)
        return AudioSegment.from_wav(wav_buffer)

    def normalize(
        self,
        audio: AudioSegment,
        buffer_ms: int = SILENCE_BUFFER_MS,
        fade_in_ms: int = SEGMENT_FADE_IN_MS,
        fade_out_ms: int = SEGMENT_FADE_OUT_MS,
        use_comfort_noise: bool = True,
        comfort_noise_db: float = COMFORT_NOISE_LEVEL_DB,
    ) -> AudioSegment:
        """Normalize segment with fades and comfort noise buffers.

        Processing pipeline:
        1. Trim existing silence from edges
        2. Apply fade in/out to speech content to prevent clicks
        3. Add comfort noise buffer at both ends (or digital silence if disabled)

        Args:
            audio: Input audio segment
            buffer_ms: Target buffer duration in milliseconds
            fade_in_ms: Fade in duration for speech start
            fade_out_ms: Fade out duration for speech end
            use_comfort_noise: Use comfort noise instead of digital silence
            comfort_noise_db: Target noise level for comfort noise

        Returns:
            Normalized audio segment with smooth edges
        """
        # Detect and trim leading/trailing silence
        silence_threshold = audio.dBFS - 16 if audio.dBFS > -float("inf") else -50

        # Use pydub's silence detection
        start_trim = pydub_detect_silence(audio, silence_threshold=silence_threshold)
        end_trim = pydub_detect_silence(
            audio.reverse(), silence_threshold=silence_threshold
        )

        # Trim silence (with safety bounds)
        duration = len(audio)
        start_trim = min(start_trim, duration // 2)
        end_trim = min(end_trim, duration // 2)

        if start_trim + end_trim < duration:
            trimmed = audio[start_trim : duration - end_trim]
        else:
            trimmed = audio  # Don't trim if it would remove everything

        # Apply fades to the speech content to prevent clicks
        trimmed_len = len(trimmed)
        if trimmed_len > fade_in_ms + fade_out_ms:
            trimmed = trimmed.fade_in(fade_in_ms).fade_out(fade_out_ms)
        elif trimmed_len > 20:  # Minimum viable fade
            mini_fade = max(5, trimmed_len // 4)
            trimmed = trimmed.fade_in(mini_fade).fade_out(mini_fade)

        # Add buffer with comfort noise or digital silence
        if use_comfort_noise and buffer_ms > 0:
            buffer = self._effects.generate_comfort_noise(
                buffer_ms,
                target_db=comfort_noise_db,
                sample_rate=audio.frame_rate,
                reference_audio=audio,
            )
        else:
            buffer = AudioSegment.silent(
                duration=buffer_ms, frame_rate=audio.frame_rate
            )

        return buffer + trimmed + buffer

    def normalize_with_config(
        self, audio: AudioSegment, config: PauseConfig
    ) -> AudioSegment:
        """Normalize segment using PauseConfig settings.

        Args:
            audio: Input audio segment
            config: Pause configuration with normalization settings

        Returns:
            Normalized audio segment
        """
        return self.normalize(
            audio,
            buffer_ms=config.segment_edge_buffer_ms,
            fade_in_ms=config.segment_fade_in_ms,
            fade_out_ms=config.segment_fade_out_ms,
            use_comfort_noise=config.use_comfort_noise,
            comfort_noise_db=config.comfort_noise_db,
        )
