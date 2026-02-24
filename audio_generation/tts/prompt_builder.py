"""TTS prompt builder for Gemini TTS API.

Constructs structured prompts following Google's recommended format:
Audio Profile + Director's Notes + Transcript. Emotion markers are
placed in Director's Notes (acting directions) rather than inline in
the transcript, preventing the TTS model from reading them aloud.
"""

from __future__ import annotations

from audio_generation.domain.models import (
    CharacterProfile,
    SegmentBatch,
    SpeakerConfig,
)


class TTSPromptBuilder:
    """Constructs structured prompts for TTS generation.

    Builds prompts with three clearly separated sections:

    1. **Audio Profile** - Character identity and personality (from
       character JSON files). Omitted if no profiles are available.
    2. **Director's Notes** - Emotional performance guidance extracted
       from segment emotion markers. Omitted if no emotions present.
    3. **Transcript** - Clean spoken text only. No emotion markers,
       no formatting marks, no stage directions.

    Voice identity is handled separately by SpeechConfig voice selection.
    """

    def build(
        self,
        batch: SegmentBatch,
        speaker_configs_map: dict[str, SpeakerConfig],
        character_profiles: dict[str, CharacterProfile] | None = None,
    ) -> str:
        """Build structured TTS prompt for a segment batch.

        Args:
            batch: The segment batch to generate audio for.
            speaker_configs_map: Mapping of speaker name to voice config.
            character_profiles: Optional mapping of speaker name to
                character profile loaded from story JSON files.

        Returns:
            Formatted prompt with Audio Profile, Director's Notes,
            and Transcript sections.
        """
        sections: list[str] = []

        # Section 1: Audio Profile (if character profiles available)
        audio_profile = self._build_audio_profile(batch, character_profiles or {})
        if audio_profile:
            sections.append(audio_profile)

        # Section 2: Director's Notes (if any emotions present)
        directors_notes = self._build_directors_notes(batch)
        if directors_notes:
            sections.append(directors_notes)

        # Section 3: Transcript (always present, always clean)
        transcript = self._build_transcript(batch)
        sections.append(transcript)

        return "\n\n".join(sections)

    def _build_audio_profile(
        self,
        batch: SegmentBatch,
        character_profiles: dict[str, CharacterProfile],
    ) -> str:
        """Build Audio Profile section from character profiles.

        Describes each speaker's identity, personality, and speech
        patterns so the TTS model can embody the character.

        Args:
            batch: The segment batch.
            character_profiles: Speaker name to profile mapping.

        Returns:
            Formatted Audio Profile section, or empty string if no
            profiles match batch speakers.
        """
        if not character_profiles:
            return ""

        lines: list[str] = []

        for speaker in batch.speakers:
            profile = character_profiles.get(speaker)
            if profile is None:
                continue

            parts: list[str] = []

            # Role and description
            if profile.role:
                parts.append(f"{speaker}: {profile.role}.")
            else:
                parts.append(f"{speaker}.")

            if profile.description:
                parts.append(profile.description)

            # Age hint
            if profile.age is not None:
                parts.append(f"Age: {profile.age}.")

            # Personality traits
            if profile.personality:
                traits = ", ".join(profile.personality)
                parts.append(f"Personality: {traits}.")

            # Typical speech pattern
            if profile.typical_lines:
                example = profile.typical_lines[0]
                parts.append(f'Typical speech: "{example}"')

            lines.append(" ".join(parts))

        if not lines:
            return ""

        header = "=== AUDIO PROFILE ==="
        return header + "\n" + "\n".join(lines)

    def _build_directors_notes(self, batch: SegmentBatch) -> str:
        """Build Director's Notes section from segment emotions.

        Aggregates emotion markers per speaker and formats them as
        acting directions that the TTS model should interpret but
        never read aloud.

        Args:
            batch: The segment batch.

        Returns:
            Formatted Director's Notes section, or empty string if
            no segments have emotion markers.
        """
        notes: list[str] = []
        seen: set[tuple[str, str]] = set()

        for segment in batch.segments:
            if not segment.emotion:
                continue

            key = (segment.speaker, segment.emotion)
            if key in seen:
                continue
            seen.add(key)

            notes.append(f"Make {segment.speaker} sound {segment.emotion}.")

        if not notes:
            return ""

        header = "=== DIRECTOR'S NOTES ==="
        return header + "\n" + "\n".join(notes)

    def _build_transcript(self, batch: SegmentBatch) -> str:
        """Build clean Transcript section with only spoken text.

        The transcript contains ONLY the text that should be spoken
        aloud. No emotion markers, no formatting, no stage directions.

        Args:
            batch: The segment batch.

        Returns:
            Formatted Transcript section.
        """
        lines: list[str] = []

        for segment in batch.segments:
            lines.append(f"{segment.speaker}: {segment.text}")

        header = "=== TRANSCRIPT ==="
        return header + "\n" + "\n".join(lines)
