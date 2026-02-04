"""Audio effects: crossfade, comfort noise, analysis."""

import array
import logging

import numpy as np
from pydub import AudioSegment

from audio_generation.domain.constants import (
    COMFORT_NOISE_LEVEL_DB,
    CROSSFADE_MS,
    NOISE_FADE_MS,
    TARGET_SAMPLE_RATE,
)


class AudioEffects:
    """Audio effects for professional-grade transitions.

    Provides crossfades, comfort noise generation, and audio analysis
    for smooth segment transitions.
    """

    def generate_comfort_noise(
        self,
        duration_ms: int,
        target_db: float = COMFORT_NOISE_LEVEL_DB,
        sample_rate: int = TARGET_SAMPLE_RATE,
        reference_audio: AudioSegment | None = None,
    ) -> AudioSegment:
        """Generate low-level pink noise to replace digital silence.

        Uses pink noise (1/f spectrum) which sounds more natural than white noise
        and better matches room tone. If reference_audio is provided, the noise
        level is adjusted to match the reference's noise floor.

        Args:
            duration_ms: Duration in milliseconds
            target_db: Target noise level in dBFS (default -55 dB)
            sample_rate: Output sample rate
            reference_audio: Optional audio to match noise floor from

        Returns:
            AudioSegment containing comfort noise
        """
        if duration_ms <= 0:
            return AudioSegment.silent(duration=0, frame_rate=sample_rate)

        num_samples = int(sample_rate * duration_ms / 1000)

        # Generate white noise as base
        white = np.random.randn(num_samples)

        # Apply simple pink noise approximation using a cumulative filter
        # This gives 1/f characteristics (equal energy per octave)
        pink = np.zeros(num_samples)
        b0, b1, b2 = 0.0, 0.0, 0.0
        for i in range(num_samples):
            white_sample = white[i]
            b0 = 0.99886 * b0 + white_sample * 0.0555179
            b1 = 0.99332 * b1 + white_sample * 0.0750759
            b2 = 0.96900 * b2 + white_sample * 0.1538520
            pink[i] = b0 + b1 + b2 + white_sample * 0.5362
        pink = pink / np.max(np.abs(pink)) if np.max(np.abs(pink)) > 0 else pink

        # Adjust target level if reference audio provided
        if reference_audio is not None and reference_audio.dBFS > -float("inf"):
            # Match slightly below the reference's quiet portions
            ref_noise_floor = self.analyze_noise_floor(reference_audio)
            target_db = min(target_db, ref_noise_floor - 3)

        # Convert dB to linear amplitude (16-bit range)
        target_amplitude = 10 ** (target_db / 20) * 32767

        # Scale noise to target level
        pink = (pink * target_amplitude).astype(np.int16)

        # Convert to AudioSegment
        noise_segment = AudioSegment(
            data=pink.tobytes(),
            sample_width=2,
            frame_rate=sample_rate,
            channels=1,
        )

        # Apply micro-fades to prevent clicks at edges
        if duration_ms > NOISE_FADE_MS * 2:
            noise_segment = noise_segment.fade_in(NOISE_FADE_MS).fade_out(NOISE_FADE_MS)

        return noise_segment

    def analyze_noise_floor(self, audio: AudioSegment, percentile: int = 10) -> float:
        """Analyze the noise floor of an audio segment.

        Examines the quietest portions of the audio to determine
        the inherent noise floor level.

        Args:
            audio: Audio segment to analyze
            percentile: Lower percentile to consider as noise floor (default 10)

        Returns:
            Noise floor level in dBFS
        """
        # Get samples as numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float64)

        # Calculate RMS in small windows (10ms windows)
        window_size = int(audio.frame_rate * 0.010)
        num_windows = len(samples) // window_size

        if num_windows < 10:
            # Not enough data, return conservative estimate
            return audio.dBFS - 20 if audio.dBFS > -float("inf") else -60

        rms_values = []
        for i in range(num_windows):
            window = samples[i * window_size : (i + 1) * window_size]
            rms = np.sqrt(np.mean(window**2))
            if rms > 0:
                rms_values.append(rms)

        if not rms_values:
            return -60  # Default quiet level

        # Get the percentile (quietest non-silent portions)
        noise_floor_rms = np.percentile(rms_values, percentile)

        # Convert to dBFS (relative to 16-bit max)
        if noise_floor_rms > 0:
            noise_floor_db = 20 * np.log10(noise_floor_rms / 32767)
        else:
            noise_floor_db = -60

        return float(noise_floor_db)

    def apply_crossfade(
        self,
        audio1: AudioSegment,
        audio2: AudioSegment,
        crossfade_ms: int = CROSSFADE_MS,
        curve_type: str = "logarithmic",
    ) -> AudioSegment:
        """Apply crossfade between two audio segments with configurable curve.

        Crossfading prevents clicks and pops at edit points by smoothly
        transitioning between segments. Non-linear curves provide more
        natural-sounding transitions than linear crossfades.

        Curve types:
        - "linear": Standard linear fade (pydub default)
        - "logarithmic": Slower start, faster end - natural decay
        - "exponential": Faster start, slower end - natural attack
        - "s_curve": Slow start/end, fast middle - smoothest perceived transition

        Args:
            audio1: First audio segment
            audio2: Second audio segment
            crossfade_ms: Duration of crossfade overlap in milliseconds
            curve_type: Type of fade curve to apply

        Returns:
            Combined audio with crossfade applied
        """
        if crossfade_ms <= 0:
            return audio1 + audio2

        # Ensure crossfade doesn't exceed segment lengths
        max_crossfade = min(len(audio1), len(audio2), crossfade_ms)

        if max_crossfade < 10:  # Too short for meaningful crossfade
            return audio1 + audio2

        if max_crossfade < crossfade_ms:
            logging.debug(
                f"Reducing crossfade from {crossfade_ms}ms to {max_crossfade}ms "
                f"(segment too short)"
            )

        # For linear curves, use pydub's built-in (more efficient)
        if curve_type == "linear":
            return audio1.append(audio2, crossfade=max_crossfade)

        # For non-linear curves, we need manual implementation
        # Extract crossfade regions
        fade_out_region = audio1[-max_crossfade:]
        fade_in_region = audio2[:max_crossfade]

        # Get samples as numpy arrays
        samples1 = np.array(fade_out_region.get_array_of_samples(), dtype=np.float64)
        samples2 = np.array(fade_in_region.get_array_of_samples(), dtype=np.float64)

        # Ensure same length (may differ slightly due to sample rate rounding)
        min_len = min(len(samples1), len(samples2))
        samples1 = samples1[:min_len]
        samples2 = samples2[:min_len]

        num_samples = min_len
        t = np.linspace(0, 1, num_samples)

        # Generate fade curves based on type
        if curve_type == "logarithmic":
            # Logarithmic: slow decay, natural for audio fade-outs
            fade_out = 1 - np.log1p(t * (np.e - 1)) / np.log(np.e)
            fade_in = np.log1p(t * (np.e - 1)) / np.log(np.e)
        elif curve_type == "exponential":
            # Exponential: quick start, slow finish
            fade_out = 1 - t**2
            fade_in = t**2
        elif curve_type == "s_curve":
            # S-curve (smoothstep): slow-fast-slow, very smooth
            fade_in = t * t * (3 - 2 * t)  # smoothstep function
            fade_out = 1 - fade_in
        else:
            # Fallback to linear
            fade_out = 1 - t
            fade_in = t

        # Apply fades and mix
        mixed = (samples1 * fade_out + samples2 * fade_in).astype(np.int16)

        # Create mixed segment with same properties as original
        mixed_segment = fade_out_region._spawn(
            array.array(fade_out_region.array_type, mixed)
        )

        # Combine: audio1 (without overlap) + mixed + audio2 (without overlap)
        result = audio1[:-max_crossfade] + mixed_segment + audio2[max_crossfade:]

        return result
