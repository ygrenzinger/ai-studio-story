"""TTS prompt builder for Gemini TTS API."""

from audio_generation.domain.models import SegmentBatch, SpeakerConfig


class TTSPromptBuilder:
    """Constructs prompts for TTS generation.

    Builds prompts that include voice profiles as guidance and
    transcript content with emotion markers for natural speech.
    """

    def build(
        self, batch: SegmentBatch, speaker_configs_map: dict[str, SpeakerConfig]
    ) -> str:
        """Build TTS prompt for a segment batch.

        Includes voice profiles and emotion markers as style guidance.

        Args:
            batch: The segment batch
            speaker_configs_map: Mapping of speaker name to config

        Returns:
            Formatted prompt for TTS generation
        """
        prompt_parts = []

        # Add style guidance header with profiles
        style_parts = []
        for speaker in batch.speakers:
            config = speaker_configs_map.get(speaker)
            if config and config.profile:
                style_parts.append(f"{speaker}: {config.profile}")

        if style_parts:
            prompt_parts.append(
                "[VOICE PROFILES - Use for tone and character, do not read aloud]\n"
                + "\n".join(style_parts)
            )
            prompt_parts.append("")

        # Add transcript with emotion markers
        prompt_parts.append("[TRANSCRIPT - Read aloud with indicated emotions]")

        for segment in batch.segments:
            if segment.emotion:
                # Include emotion as inline guidance
                prompt_parts.append(
                    f"**{segment.speaker}:** [{segment.emotion}] {segment.text}"
                )
            else:
                prompt_parts.append(f"**{segment.speaker}:** {segment.text}")

        return "\n".join(prompt_parts)
