"""Segment concatenator with context-aware pauses."""

import logging

import numpy as np
from pydub import AudioSegment

from audio_generation.domain.models import PauseConfig, Segment
from audio_generation.domain.constants import (
    INTER_SEGMENT_PAUSE_MS,
    TARGET_SAMPLE_RATE,
)
from audio_generation.audio.effects import AudioEffects
from audio_generation.audio.processor import AudioProcessor


class SegmentConcatenator:
    """Concatenates audio segments with context-aware pauses.

    Joins audio segments with professional-grade transitions including:
    - Context-aware pause durations based on speaker transitions
    - Punctuation-based pause adjustments
    - Comfort noise in pauses
    - Non-linear crossfades
    """

    def __init__(
        self,
        processor: AudioProcessor | None = None,
        effects: AudioEffects | None = None,
        pause_config: PauseConfig | None = None,
    ):
        """Initialize concatenator.

        Args:
            processor: AudioProcessor instance (created if None)
            effects: AudioEffects instance (created if None)
            pause_config: Pause configuration (uses defaults if None)
        """
        self._effects = effects or AudioEffects()
        self._processor = processor or AudioProcessor(self._effects)
        self._config = pause_config or PauseConfig()

    def concatenate(
        self,
        audio_segments: list[bytes],
        segment_metadata: list[Segment] | None = None,
        pause_ms: int = INTER_SEGMENT_PAUSE_MS,
    ) -> AudioSegment:
        """Concatenate segment audio with professional-grade transitions.

        Enhanced pipeline for smooth audio transitions:
        1. Convert PCM to AudioSegment
        2. Analyze overall noise floor for consistency
        3. Normalize each segment with comfort noise buffers and fades
        4. Calculate context-aware pause durations
        5. Join with comfort noise pauses and non-linear crossfades
        6. Add file-level leading/trailing with comfort noise

        Args:
            audio_segments: List of raw PCM audio data
            segment_metadata: Optional list of Segment objects for context-aware pausing
            pause_ms: Default pause duration between segments (fallback)

        Returns:
            Combined AudioSegment

        Raises:
            ValueError: If no audio segments provided
        """
        if not audio_segments:
            raise ValueError("No audio segments to concatenate")

        config = self._config

        # Determine if we can use context-aware pausing
        use_context_aware = segment_metadata is not None and len(
            segment_metadata
        ) == len(audio_segments)

        smoothing_mode = (
            "comfort noise" if config.use_comfort_noise else "digital silence"
        )
        if use_context_aware:
            logging.info(
                f"Concatenating {len(audio_segments)} segments with context-aware pausing "
                f"({smoothing_mode}, {config.crossfade_curve} crossfade)"
            )
        else:
            logging.info(
                f"Concatenating {len(audio_segments)} segments with {pause_ms}ms pauses "
                f"({smoothing_mode})"
            )

        # Step 1: Convert all PCM to AudioSegment
        raw_segments: list[AudioSegment] = []
        for pcm_data in audio_segments:
            audio = self._processor.pcm_to_segment(pcm_data)
            raw_segments.append(audio)

        # Step 2: Analyze overall noise floor for consistency (if using comfort noise)
        target_noise_db = config.comfort_noise_db
        if config.use_comfort_noise and raw_segments:
            noise_floors = [
                self._effects.analyze_noise_floor(seg)
                for seg in raw_segments
                if seg.dBFS > -float("inf")
            ]
            if noise_floors:
                avg_noise_floor = float(np.mean(noise_floors))
                # Use slightly below average to be subtle
                target_noise_db = min(config.comfort_noise_db, avg_noise_floor - 5)
                logging.debug(f"Target comfort noise level: {target_noise_db:.1f} dBFS")

        # Step 3: Normalize each segment with fades and comfort noise
        processed_segments: list[AudioSegment] = []
        for i, audio in enumerate(raw_segments):
            normalized = self._processor.normalize(
                audio,
                buffer_ms=config.segment_edge_buffer_ms,
                fade_in_ms=config.segment_fade_in_ms,
                fade_out_ms=config.segment_fade_out_ms,
                use_comfort_noise=config.use_comfort_noise,
                comfort_noise_db=target_noise_db,
            )
            processed_segments.append(normalized)
            logging.debug(
                f"Segment {i + 1}: {len(audio)}ms -> {len(normalized)}ms (normalized)"
            )

        # Step 4 & 5: Combine with context-aware pauses and non-linear crossfades
        # Generate leading buffer (comfort noise or silence)
        if config.use_comfort_noise:
            combined = self._effects.generate_comfort_noise(
                config.file_leading_ms,
                target_db=target_noise_db,
                sample_rate=TARGET_SAMPLE_RATE,
            )
        else:
            combined = AudioSegment.silent(duration=config.file_leading_ms)

        for i, segment_audio in enumerate(processed_segments):
            if i == 0:
                # First segment - join with leading buffer
                combined = self._effects.apply_crossfade(
                    combined,
                    segment_audio,
                    config.crossfade_ms,
                    config.crossfade_curve,
                )
            else:
                # Calculate pause duration
                if use_context_aware and segment_metadata:
                    prev_seg = segment_metadata[i - 1]
                    curr_seg = segment_metadata[i]
                    pause_duration = self._calculate_pause(prev_seg, curr_seg)
                else:
                    pause_duration = pause_ms

                # Create pause with comfort noise or digital silence
                if config.use_comfort_noise:
                    pause = self._effects.generate_comfort_noise(
                        pause_duration,
                        target_db=target_noise_db,
                        sample_rate=TARGET_SAMPLE_RATE,
                    )
                else:
                    pause = AudioSegment.silent(duration=pause_duration)

                # Apply crossfade through the pause to the next segment
                combined = self._effects.apply_crossfade(
                    combined,
                    pause,
                    config.crossfade_ms,
                    config.crossfade_curve,
                )
                combined = self._effects.apply_crossfade(
                    combined,
                    segment_audio,
                    config.crossfade_ms,
                    config.crossfade_curve,
                )

        # Step 6: Add trailing buffer
        if config.use_comfort_noise:
            trailing = self._effects.generate_comfort_noise(
                config.file_trailing_ms,
                target_db=target_noise_db,
                sample_rate=TARGET_SAMPLE_RATE,
            )
        else:
            trailing = AudioSegment.silent(duration=config.file_trailing_ms)

        combined = self._effects.apply_crossfade(
            combined,
            trailing,
            config.crossfade_ms,
            config.crossfade_curve,
        )

        return combined

    def _calculate_pause(
        self,
        prev_segment: Segment | None,
        next_segment: Segment | None,
    ) -> int:
        """Calculate context-appropriate pause between segments.

        Considers:
        - Speaker transition type (narrator<->character, character<->character)
        - Punctuation-based pauses (ellipsis, em-dash, question mark)

        Args:
            prev_segment: Previous segment (None for file start)
            next_segment: Next segment (None for file end)

        Returns:
            Calculated pause duration in milliseconds
        """
        config = self._config

        if prev_segment is None or next_segment is None:
            return config.narrator_to_narrator_ms

        # Determine base pause from speaker transition type
        prev_is_narrator = prev_segment.speaker == "Narrator"
        next_is_narrator = next_segment.speaker == "Narrator"

        if prev_is_narrator and next_is_narrator:
            base_pause = config.narrator_to_narrator_ms
        elif prev_is_narrator:
            base_pause = config.narrator_to_character_ms
        elif next_is_narrator:
            base_pause = config.character_to_narrator_ms
        else:
            # Character to different character - check if same speaker
            if prev_segment.speaker == next_segment.speaker:
                base_pause = config.character_to_character_ms
            else:
                # Different characters talking - slightly longer
                base_pause = int(config.character_to_character_ms * 1.25)

        # Add punctuation-based pause
        punctuation_pause = self._detect_natural_pauses(prev_segment.text)

        # Calculate final pause
        final_pause = base_pause + punctuation_pause

        logging.debug(
            f"Pause: {prev_segment.speaker}->{next_segment.speaker} = "
            f"{base_pause}ms + {punctuation_pause}ms = {final_pause}ms"
        )

        return final_pause

    def _detect_natural_pauses(self, text: str) -> int:
        """Detect if text ends with pause-indicating punctuation.

        Analyzes the ending punctuation to determine if additional pause
        is needed beyond the base pause duration.

        Args:
            text: Text content to analyze

        Returns:
            Additional pause duration in milliseconds
        """
        stripped = text.rstrip()

        # Ellipsis indicates trailing thought - needs longer pause
        if stripped.endswith("..."):
            return 750

        # Em-dash indicates abrupt cut/interruption - shorter pause
        if stripped.endswith("—") or stripped.endswith("--"):
            return 200

        # Question mark - slight pause for implied response
        if stripped.endswith("?"):
            return 300

        # Exclamation - slight pause for emphasis to land
        if stripped.endswith("!"):
            return 200

        return 0
