"""Segment batching for TTS API calls."""

from audio_generation.domain.models import Segment, SegmentBatch
from audio_generation.providers.base import ProviderCapabilities


class SegmentBatcher:
    """Batches segments into single-speaker TTS requests.

    Consecutive segments from the same speaker are grouped together.
    Speaker changes always create a new request, regardless of provider.
    """

    def batch(
        self,
        segments: list[Segment],
        capabilities: ProviderCapabilities | None = None,
    ) -> list[SegmentBatch]:
        """Batch segments for TTS generation.

        Args:
            segments: List of parsed segments in order

        Returns:
            List of SegmentBatch objects ready for TTS generation
        """
        if not segments:
            return []

        max_speakers = capabilities.max_speakers_per_request if capabilities else 1
        max_segments = capabilities.max_segments_per_request if capabilities else 1
        if max_speakers > 1:
            return self._batch_multi_speaker(
                segments,
                max_speakers=max_speakers,
                max_segments=max_segments,
            )

        batches: list[SegmentBatch] = []
        current_segments = [segments[0]]
        current_speaker = segments[0].speaker

        for segment in segments[1:]:
            if segment.speaker == current_speaker:
                current_segments.append(segment)
                continue
            batches.append(SegmentBatch(current_segments, [current_speaker]))
            current_segments = [segment]
            current_speaker = segment.speaker

        batches.append(SegmentBatch(current_segments, [current_speaker]))

        return batches

    def _batch_multi_speaker(
        self,
        segments: list[Segment],
        *,
        max_speakers: int,
        max_segments: int,
    ) -> list[SegmentBatch]:
        batches: list[SegmentBatch] = []
        current_segments: list[Segment] = []
        current_speakers: list[str] = []

        for segment in segments:
            next_speakers = list(current_speakers)
            if segment.speaker not in next_speakers:
                next_speakers.append(segment.speaker)

            too_many_speakers = len(next_speakers) > max_speakers
            too_many_segments = bool(
                max_segments and len(current_segments) >= max_segments
            )
            if current_segments and (too_many_speakers or too_many_segments):
                batches.append(SegmentBatch(current_segments, current_speakers))
                current_segments = []
                current_speakers = []

            current_segments.append(segment)
            if segment.speaker not in current_speakers:
                current_speakers.append(segment.speaker)

        if current_segments:
            batches.append(SegmentBatch(current_segments, current_speakers))
        return batches
