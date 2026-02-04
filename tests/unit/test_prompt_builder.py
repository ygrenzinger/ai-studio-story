"""Unit tests for TTSPromptBuilder."""

import pytest

from audio_generation.tts.prompt_builder import TTSPromptBuilder
from audio_generation.domain.models import Segment, SegmentBatch, SpeakerConfig


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
                profile="Warm storyteller voice",
            ),
            "Emma": SpeakerConfig(
                name="Emma",
                voice="Leda",
                profile="Curious young girl",
            ),
        }

    def test_build_single_speaker_prompt(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Test building prompt for single speaker batch."""
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Hello world.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "VOICE PROFILES" in prompt
        assert "Narrator: Warm storyteller voice" in prompt
        assert "TRANSCRIPT" in prompt
        assert "**Narrator:** Hello world." in prompt

    def test_build_multi_speaker_prompt(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Test building prompt for multi-speaker batch."""
        batch = SegmentBatch(
            segments=[
                Segment(speaker="Narrator", text="She spoke."),
                Segment(speaker="Emma", text="Hello!"),
            ],
            speakers=["Narrator", "Emma"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        assert "Narrator: Warm storyteller voice" in prompt
        assert "Emma: Curious young girl" in prompt
        assert "**Narrator:** She spoke." in prompt
        assert "**Emma:** Hello!" in prompt

    def test_build_prompt_with_emotion(
        self, builder: TTSPromptBuilder, speaker_configs_map
    ):
        """Test building prompt with emotion markers."""
        batch = SegmentBatch(
            segments=[
                Segment(
                    speaker="Narrator", text="The room fell silent.", emotion="tense"
                ),
            ],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, speaker_configs_map)

        # Emotion should be included in brackets
        assert "[tense]" in prompt
        assert "**Narrator:** [tense] The room fell silent." in prompt

    def test_build_prompt_without_profile(self, builder: TTSPromptBuilder):
        """Test building prompt when speaker has no profile."""
        configs = {
            "Narrator": SpeakerConfig(name="Narrator", voice="Sulafat", profile=""),
        }
        batch = SegmentBatch(
            segments=[Segment(speaker="Narrator", text="Text.")],
            speakers=["Narrator"],
        )

        prompt = builder.build(batch, configs)

        # Should not include voice profiles section if no profiles
        assert "VOICE PROFILES" not in prompt
        assert "TRANSCRIPT" in prompt
