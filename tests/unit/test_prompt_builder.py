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
            ),
            "Emma": SpeakerConfig(
                name="Emma",
                voice="Leda",
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

        assert "**Narrator:** Hello world." in prompt
        assert "VOICE PROFILES" not in prompt

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
