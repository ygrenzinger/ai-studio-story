"""Unit tests for SegmentBatcher."""

import pytest

from audio_generation.batching.segment_batcher import SegmentBatcher
from audio_generation.domain.models import Segment


class TestSegmentBatcher:
    """Tests for SegmentBatcher class."""

    @pytest.fixture
    def batcher(self):
        """Create batcher instance."""
        return SegmentBatcher()

    def test_batch_empty_segments(self, batcher: SegmentBatcher):
        """Test batching empty segment list."""
        batches = batcher.batch([])
        assert batches == []

    def test_batch_single_narrator(self, batcher: SegmentBatcher):
        """Test batching single narrator segment."""
        segments = [Segment(speaker="Narrator", text="Hello world.")]
        batches = batcher.batch(segments)

        assert len(batches) == 1
        assert batches[0].speakers == ["Narrator"]
        assert len(batches[0].segments) == 1

    def test_batch_narrator_then_character(self, batcher: SegmentBatcher):
        """Test batching narrator followed by character."""
        segments = [
            Segment(speaker="Narrator", text="Introduction."),
            Segment(speaker="Emma", text="Hello!"),
        ]
        batches = batcher.batch(segments)

        assert len(batches) == 1
        assert batches[0].speakers == ["Narrator", "Emma"]
        assert len(batches[0].segments) == 2

    def test_batch_multiple_narrator_then_character(self, batcher: SegmentBatcher):
        """Test batching multiple narrator segments before character."""
        segments = [
            Segment(speaker="Narrator", text="First narrator."),
            Segment(speaker="Narrator", text="Second narrator."),
            Segment(speaker="Emma", text="Character speaks."),
        ]
        batches = batcher.batch(segments)

        assert len(batches) == 1
        assert batches[0].speakers == ["Narrator", "Emma"]
        assert len(batches[0].segments) == 3

    def test_batch_character_without_narrator(self, batcher: SegmentBatcher):
        """Test batching character segment without preceding narrator."""
        segments = [Segment(speaker="Emma", text="Direct speech.")]
        batches = batcher.batch(segments)

        assert len(batches) == 1
        assert batches[0].speakers == ["Emma"]
        assert len(batches[0].segments) == 1

    def test_batch_alternating_speakers(self, batcher: SegmentBatcher):
        """Test batching alternating narrator and character."""
        segments = [
            Segment(speaker="Narrator", text="Setup."),
            Segment(speaker="Emma", text="Line 1."),
            Segment(speaker="Narrator", text="Description."),
            Segment(speaker="Emma", text="Line 2."),
        ]
        batches = batcher.batch(segments)

        # Should create 2 batches: [Narrator, Emma], [Narrator, Emma]
        assert len(batches) == 2
        assert all(b.speakers == ["Narrator", "Emma"] for b in batches)

    def test_batch_trailing_narrator(self, batcher: SegmentBatcher):
        """Test batching with trailing narrator segments."""
        segments = [
            Segment(speaker="Emma", text="Dialogue."),
            Segment(speaker="Narrator", text="Closing narration."),
        ]
        batches = batcher.batch(segments)

        # Should create 2 batches: [Emma], [Narrator]
        assert len(batches) == 2
        assert batches[0].speakers == ["Emma"]
        assert batches[1].speakers == ["Narrator"]

    def test_batch_multiple_characters(self, batcher: SegmentBatcher):
        """Test batching dialogue between multiple characters."""
        segments = [
            Segment(speaker="Narrator", text="Setup."),
            Segment(speaker="Emma", text="Hi Bob!"),
            Segment(speaker="Bob", text="Hi Emma!"),
        ]
        batches = batcher.batch(segments)

        # Should create 2 batches: [Narrator, Emma], [Bob]
        assert len(batches) == 2
        assert batches[0].speakers == ["Narrator", "Emma"]
        assert batches[1].speakers == ["Bob"]

    def test_batch_preserves_segment_order(self, batcher: SegmentBatcher):
        """Test that batching preserves segment order."""
        segments = [
            Segment(speaker="Narrator", text="First."),
            Segment(speaker="Narrator", text="Second."),
            Segment(speaker="Emma", text="Third."),
        ]
        batches = batcher.batch(segments)

        assert len(batches) == 1
        assert batches[0].segments[0].text == "First."
        assert batches[0].segments[1].text == "Second."
        assert batches[0].segments[2].text == "Third."
