"""Segment batching for TTS API calls."""

from audio_generation.domain.models import Segment, SegmentBatch


class SegmentBatcher:
    """Batches segments for TTS API calls (max 2 speakers per batch).

    Gemini TTS API supports maximum 2 speakers per call. This batcher
    optimizes batching to minimize API calls while maintaining
    narrative flow.

    Strategy:
    - Each character segment batches with preceding narrator segments
    - Narrator-only sequences batch with the following character if one exists
    - Character-to-character transitions create separate single-speaker batches
    """

    def batch(self, segments: list[Segment]) -> list[SegmentBatch]:
        """Batch segments for TTS generation (max 2 speakers per batch).

        Args:
            segments: List of parsed segments in order

        Returns:
            List of SegmentBatch objects ready for TTS generation
        """
        if not segments:
            return []

        batches = []
        pending_narrator: list[Segment] = []

        for segment in segments:
            if segment.speaker == "Narrator":
                pending_narrator.append(segment)
            else:
                # Character segment - batch with pending narrator
                if pending_narrator:
                    batch = SegmentBatch(
                        segments=pending_narrator + [segment],
                        speakers=["Narrator", segment.speaker],
                    )
                    pending_narrator = []
                else:
                    # No preceding narrator - single speaker batch
                    batch = SegmentBatch(
                        segments=[segment],
                        speakers=[segment.speaker],
                    )
                batches.append(batch)

        # Handle trailing narrator segments
        if pending_narrator:
            batches.append(
                SegmentBatch(
                    segments=pending_narrator,
                    speakers=["Narrator"],
                )
            )

        return batches
