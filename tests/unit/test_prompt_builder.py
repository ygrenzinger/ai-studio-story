"""Unit tests for TTSPromptBuilder."""

import pytest

from audio_generation.tts.prompt_builder import TTSPromptBuilder
from audio_generation.domain.models import (
    CharacterProfile,
    Segment,
    SegmentBatch,
    SpeakerConfig,
)


class TestTTSPromptBuilder:
    """Tests for TTSPromptBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create builder instance."""
        return TTSPromptBuilder()

    @pytest.fixture
    def speaker_configs_map(self):
        """Create speaker configs map."""
        return {
            "Narrator": SpeakerConfig(
                name="Narrator",
                voice="Sulafat",
            ),
            "Emma": SpeakerConfig(
                name="Emma",
                voice="Leda",
            ),
        }

    @pytest.fixture
    def character_profiles(self):
        """Create character profiles map."""
        return {
            "Narrator": CharacterProfile(
                name="Narrator",
                role="Narrateur",
                description="A warm storytelling narrator.",
                personality=["Warm", "Engaging", "Playful"],
                typical_lines=["Once upon a time..."],
            ),
            "Emma": CharacterProfile(
                name="Emma",
                role="Protagonist",
                age=8,
                gender="female",
                description="A curious 8-year-old girl.",
                personality=["Curious", "Brave", "Enthusiastic"],
                typical_lines=["Wow! Look at that!"],
            ),
        }

    # ---- Transcript section tests ----

    def test_transcript_section_is_clean(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Transcript section must contain no emotion markers."""
        batch = SegmentBatch(
            segments=[
                Segment(
                    speaker="Narrator",
                    text="The room fell silent.",
                    emotion="tense, mysterious",
                ),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        # Emotion must NOT appear in the transcript section
        assert "[tense" not in prompt.split("=== TRANSCRIPT ===")[1]
        assert "<emotion:" not in prompt
        # Clean text must be present
        assert "Narrator: The room fell silent." in prompt

    def test_transcript_has_no_bold_formatting(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Transcript section must not have **bold** speaker labels."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello world.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)
        transcript_section = prompt.split("=== TRANSCRIPT ===")[1]

        assert "**Narrator:**" not in transcript_section
        assert "Narrator: Hello world." in transcript_section

    def test_single_speaker_prompt(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Test building prompt for single speaker batch."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello world.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "=== TRANSCRIPT ===" in prompt
        assert "Narrator: Hello world." in prompt

    def test_multi_speaker_prompt(self, builder: TTSPromptBuilder, speaker_configs_map):
        """Test building prompt for multi-speaker batch."""
        batch = SegmentBatch(
            segments=[
                Segment(speaker="Narrator", text="She spoke."),
                Segment(speaker="Emma", text="Hello!"),
            ],
            speakers=["Narrator", "Emma"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "Narrator: She spoke." in prompt
        assert "Emma: Hello!" in prompt

    # ---- Director's Notes tests ----

    def test_directors_notes_from_emotions(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Emotion values appear in Director's Notes section."""
        batch = SegmentBatch(
            segments=[
                Segment(
                    speaker="Narrator",
                    text="The room fell silent.",
                    emotion="tense, mysterious",
                ),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "=== DIRECTOR'S NOTES ===" in prompt
        assert "Make Narrator sound tense, mysterious." in prompt

    def test_no_emotions_omits_directors_notes(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """When no emotions, Director's Notes section is omitted."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello world.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "DIRECTOR'S NOTES" not in prompt

    def test_multi_emotion_same_speaker(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Multiple Director's Notes lines for different emotions on same speaker."""
        batch = SegmentBatch(
            segments=[
                Segment(
                    speaker="Narrator",
                    text="It was dark.",
                    emotion="mysterious, hushed",
                ),
                Segment(
                    speaker="Narrator",
                    text="Suddenly, light!",
                    emotion="excited, bright",
                ),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "Make Narrator sound mysterious, hushed." in prompt
        assert "Make Narrator sound excited, bright." in prompt

    def test_duplicate_emotions_deduplicated(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Same speaker+emotion combo should appear only once in notes."""
        batch = SegmentBatch(
            segments=[
                Segment(speaker="Narrator", text="Part one.", emotion="warm"),
                Segment(speaker="Narrator", text="Part two.", emotion="warm"),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)
        notes_section = prompt.split("=== DIRECTOR'S NOTES ===")[1].split("===")[0]

        assert notes_section.count("Make Narrator sound warm.") == 1

    def test_french_emotions_in_directors_notes(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """French emotion descriptors should appear in Director's Notes."""
        batch = SegmentBatch(
            segments=[
                Segment(
                    speaker="Narrator",
                    text="Victor se retourna.",
                    emotion="boudeur, fatigué",
                ),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "Make Narrator sound boudeur, fatigué." in prompt
        # Crucially: the French emotion must NOT be in the transcript
        transcript = prompt.split("=== TRANSCRIPT ===")[1]
        assert "boudeur" not in transcript
        assert "fatigué" not in transcript

    # ---- Audio Profile tests ----

    def test_audio_profile_from_character_profiles(
        self, builder: TTSPromptBuilder, speaker_configs_map, character_profiles
    ):
        """Audio Profile section includes character data when profiles provided."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Emma", text="Hello!")],
            speakers=["Emma"],
        )

        prompt = builder.build(batch, speaker_configs_map, character_profiles)

        assert "=== AUDIO PROFILE ===" in prompt
        assert "Emma: Protagonist." in prompt
        assert "Curious" in prompt
        assert "Age: 8." in prompt
        assert 'Typical speech: "Wow! Look at that!"' in prompt

    def test_no_profiles_omits_audio_profile(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """When no character profiles, Audio Profile section is omitted."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map, character_profiles=None)

        assert "AUDIO PROFILE" not in prompt

    def test_empty_profiles_omits_audio_profile(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """When profiles dict is empty, Audio Profile section is omitted."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map, character_profiles={})

        assert "AUDIO PROFILE" not in prompt

    def test_profile_for_unmatched_speaker_is_skipped(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Speakers without matching profiles don't appear in Audio Profile."""
        profiles = {
            "Emma": CharacterProfile(
                name="Emma", role="Protagonist", description="A girl."
            ),
        }
        batch = SegmentBatch(
            segments=[
                Segment(speaker="Narrator", text="She spoke."),
                Segment(speaker="Emma", text="Hello!"),
            ],
            speakers=["Narrator", "Emma"],
        )

        prompt = builder.build(batch, speaker_configs_map, profiles)

        profile_section = prompt.split("=== AUDIO PROFILE ===")[1].split("===")[0]
        assert "Emma:" in profile_section
        assert "Narrator:" not in profile_section

    # ---- Full structured prompt tests ----

    def test_full_structured_prompt_order(
        self, builder: TTSPromptBuilder, speaker_configs_map, character_profiles
    ):
        """Sections appear in correct order: Profile, Notes, Transcript."""
        batch = SegmentBatch(
            segments=[
                Segment(speaker="Emma", text="Look!", emotion="excited, curious"),
            ],
            speakers=["Emma"],
        )

        prompt = builder.build(batch, speaker_configs_map, character_profiles)

        profile_pos = prompt.index("=== AUDIO PROFILE ===")
        notes_pos = prompt.index("=== DIRECTOR'S NOTES ===")
        transcript_pos = prompt.index("=== TRANSCRIPT ===")

        assert profile_pos < notes_pos < transcript_pos

    def test_minimal_prompt_transcript_only(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """With no profiles and no emotions, prompt is just transcript."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Once upon a time.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "=== TRANSCRIPT ===" in prompt
        assert "AUDIO PROFILE" not in prompt
        assert "DIRECTOR'S NOTES" not in prompt
        assert "Narrator: Once upon a time." in prompt

    def test_backward_compatible_no_profiles_arg(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Calling build() without character_profiles works (backward compat)."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello.")],
            speakers=["Narrator"],
        )

        # Should not raise
        prompt = builder.build(batch, speaker_configs_map)
        assert "Narrator: Hello." in prompt
