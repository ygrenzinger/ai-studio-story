"""Segment batching for TTS API calls."""

from audio_generation.domain.models import Segment, SegmentBatch


class SegmentBatcher:
    """Batches segments into single-speaker TTS requests.

    Consecutive segments from the same speaker are grouped together.
    Speaker changes always create a new request, regardless of provider.
    """

    def batch(self, segments: list[Segment]) -> list[SegmentBatch]:
        """Batch segments for TTS generation.

        Args:
            segments: List of parsed segments in order

        Returns:
            List of SegmentBatch objects ready for TTS generation
        """
        if not segments:
            return []

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
