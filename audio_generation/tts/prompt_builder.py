"""TTS prompt builder for Gemini TTS API."""

from audio_generation.domain.models import SegmentBatch, SpeakerConfig


class TTSPromptBuilder:
    """Constructs prompts for TTS generation.

    Builds prompts containing only transcript content with emotion markers
    for natural speech. Voice identity is handled by SpeechConfig voice
    selection, and tone by inline emotion markers.
    """

    def build(
        self, batch: SegmentBatch, speaker_configs_map: dict[str, SpeakerConfig]
    ) -> str:
        """Build TTS prompt for a segment batch.

        Only includes the transcript text with emotion markers. Voice
        identity is handled separately by SpeechConfig voice selection.

        Args:
            batch: The segment batch
            speaker_configs_map: Mapping of speaker name to config

        Returns:
            Formatted prompt for TTS generation
        """
        prompt_parts = []

        for segment in batch.segments:
            if segment.emotion:
                prompt_parts.append(
                    f"**{segment.speaker}:** [{segment.emotion}] {segment.text}"
                )
            else:
                prompt_parts.append(f"**{segment.speaker}:** {segment.text}")

        return "\n".join(prompt_parts)
