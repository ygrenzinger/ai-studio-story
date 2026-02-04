"""Unit tests for AudioScriptParser."""

import tempfile
from pathlib import Path

import pytest

from audio_generation.parsing.script_parser import AudioScriptParser
from audio_generation.domain.models import Segment, SpeakerConfig


class TestAudioScriptParser:
    """Tests for AudioScriptParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return AudioScriptParser()

    @pytest.fixture
    def sample_script(self, tmp_path: Path) -> Path:
        """Create a sample script file."""
        content = """---
stageUuid: "test-uuid-123"
chapterRef: "chapter-1"
locale: "en-US"
speakers:
  - name: Narrator
    voice: Sulafat
    profile: "Warm storyteller voice"
  - name: Emma
    voice: Leda
    profile: "Young curious girl"
---

**Narrator:** <emotion: warm> Once upon a time, there was a girl named Emma.

**Emma:** <emotion: curious> What's that sound?

**Narrator:** The wind whispered through the trees.
"""
        script_path = tmp_path / "test_script.md"
        script_path.write_text(content)
        return script_path

    def test_parse_basic_script(self, parser: AudioScriptParser, sample_script: Path):
        """Test parsing a basic script with speakers and segments."""
        script = parser.parse(sample_script)

        assert script.stage_uuid == "test-uuid-123"
        assert script.chapter_ref == "chapter-1"
        assert script.locale == "en-US"
        assert len(script.speaker_configs) == 2
        assert len(script.segments) == 3

    def test_parse_speaker_configs(
        self, parser: AudioScriptParser, sample_script: Path
    ):
        """Test speaker configuration parsing."""
        script = parser.parse(sample_script)

        narrator = script.speaker_configs[0]
        assert narrator.name == "Narrator"
        assert narrator.voice == "Sulafat"
        assert narrator.profile == "Warm storyteller voice"

        emma = script.speaker_configs[1]
        assert emma.name == "Emma"
        assert emma.voice == "Leda"
        assert emma.profile == "Young curious girl"

    def test_parse_segments_with_emotions(
        self, parser: AudioScriptParser, sample_script: Path
    ):
        """Test segment parsing including emotion markers."""
        script = parser.parse(sample_script)

        # First segment: Narrator with warm emotion
        assert script.segments[0].speaker == "Narrator"
        assert script.segments[0].emotion == "warm"
        assert "Once upon a time" in script.segments[0].text

        # Second segment: Emma with curious emotion
        assert script.segments[1].speaker == "Emma"
        assert script.segments[1].emotion == "curious"

        # Third segment: Narrator without emotion
        assert script.segments[2].speaker == "Narrator"
        assert script.segments[2].emotion == ""

    def test_parse_missing_frontmatter(self, parser: AudioScriptParser, tmp_path: Path):
        """Test error handling for missing frontmatter."""
        content = "No frontmatter here"
        script_path = tmp_path / "no_frontmatter.md"
        script_path.write_text(content)

        with pytest.raises(ValueError, match="Missing YAML frontmatter"):
            parser.parse(script_path)

    def test_parse_default_speaker(self, parser: AudioScriptParser, tmp_path: Path):
        """Test default narrator when no speakers defined."""
        content = """---
stageUuid: "test"
---

**Narrator:** Hello world.
"""
        script_path = tmp_path / "default_speaker.md"
        script_path.write_text(content)

        script = parser.parse(script_path)
        assert len(script.speaker_configs) == 1
        assert script.speaker_configs[0].name == "Narrator"

    def test_split_by_emotions(self, parser: AudioScriptParser):
        """Test emotion splitting from text."""
        text = "<emotion: tense> The shadow moved. <emotion: calm> Then all was quiet."
        splits = parser._split_by_emotions(text)

        assert len(splits) == 2
        assert splits[0] == ("tense", "The shadow moved.")
        assert splits[1] == ("calm", "Then all was quiet.")

    def test_split_by_emotions_no_markers(self, parser: AudioScriptParser):
        """Test text without emotion markers."""
        text = "Just plain text here."
        splits = parser._split_by_emotions(text)

        assert len(splits) == 1
        assert splits[0] == ("", "Just plain text here.")

    def test_split_by_emotions_text_before_marker(self, parser: AudioScriptParser):
        """Test text that appears before first emotion marker."""
        text = "Intro text. <emotion: happy> Main content."
        splits = parser._split_by_emotions(text)

        assert len(splits) == 2
        assert splits[0] == ("", "Intro text.")
        assert splits[1] == ("happy", "Main content.")
