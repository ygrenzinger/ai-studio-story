"""Unit tests for CharacterLoader."""

import json

import pytest

from audio_generation.domain.character_loader import CharacterLoader


class TestCharacterLoader:
    """Tests for CharacterLoader class."""

    @pytest.fixture
    def loader(self):
        """Create loader instance."""
        return CharacterLoader()

    def _create_character_json(self, dir_path, data: dict) -> None:
        """Helper to write a character JSON file."""
        filename = data.get("name", "character").lower().replace(" ", "-") + ".json"
        filepath = dir_path / filename
        filepath.write_text(json.dumps(data), encoding="utf-8")

    # ---- Discovery tests ----

    def test_load_from_valid_story_structure(self, loader, tmp_path):
        """Loads all JSON files from characters/ directory."""
        # Create story structure:
        # tmp_path/src/chapters/01-test/audio-script.md
        # tmp_path/src/characters/emma.json
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("---\n---\n**Narrator:** Hello")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(
            characters_dir,
            {
                "name": "Emma",
                "role": "Protagonist",
                "age": 8,
                "personality": ["Curious", "Brave"],
                "description": "A curious girl who loves adventure.",
            },
        )

        profiles = loader.load_for_script(script)

        assert "Emma" in profiles
        assert profiles["Emma"].role == "Protagonist"
        assert profiles["Emma"].age == 8
        assert profiles["Emma"].personality == ["Curious", "Brave"]

    def test_load_multiple_characters(self, loader, tmp_path):
        """Loads multiple character files."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(
            characters_dir,
            {"name": "Emma", "role": "Protagonist"},
        )
        self._create_character_json(
            characters_dir,
            {"name": "Narrator", "role": "Narrator"},
        )

        profiles = loader.load_for_script(script)

        assert len(profiles) == 2
        assert "Emma" in profiles
        assert "Narrator" in profiles

    def test_src_discovery_from_nested_chapter(self, loader, tmp_path):
        """Correctly resolves src/ from src/chapters/01-foo/audio-script.md."""
        # Deep nesting
        chapters_dir = tmp_path / "src" / "chapters" / "01-adventure"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(characters_dir, {"name": "Hero", "role": "Main"})

        profiles = loader.load_for_script(script)
        assert "Hero" in profiles

    def test_src_discovery_from_nested_story(self, loader, tmp_path):
        """Correctly resolves from src/stories/01-foo/audio-script.md."""
        # Pack structure
        stories_dir = tmp_path / "src" / "stories" / "01-myth"
        stories_dir.mkdir(parents=True)
        script = stories_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(characters_dir, {"name": "Leo", "role": "Explorer"})

        profiles = loader.load_for_script(script)
        assert "Leo" in profiles

    # ---- Missing/error cases ----

    def test_load_missing_characters_dir(self, loader, tmp_path):
        """Returns empty dict when no characters/ directory exists."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")
        # No characters/ directory created

        profiles = loader.load_for_script(script)
        assert profiles == {}

    def test_load_no_src_directory(self, loader, tmp_path):
        """Returns empty dict when no src/ ancestor exists."""
        script = tmp_path / "audio-script.md"
        script.write_text("test")

        profiles = loader.load_for_script(script)
        assert profiles == {}

    def test_load_malformed_json(self, loader, tmp_path):
        """Skips malformed JSON files, loads valid ones."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)

        # Valid file
        self._create_character_json(
            characters_dir, {"name": "Emma", "role": "Protagonist"}
        )

        # Malformed file
        bad_file = characters_dir / "broken.json"
        bad_file.write_text("{invalid json content", encoding="utf-8")

        profiles = loader.load_for_script(script)

        assert "Emma" in profiles
        assert len(profiles) == 1

    def test_load_missing_name_field(self, loader, tmp_path):
        """Skips JSON files without 'name' field."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)

        # File without name
        no_name_file = characters_dir / "noname.json"
        no_name_file.write_text(json.dumps({"role": "Unknown"}), encoding="utf-8")

        profiles = loader.load_for_script(script)
        assert profiles == {}

    def test_load_missing_optional_fields(self, loader, tmp_path):
        """Handles JSON missing personality, typical_lines, etc."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(
            characters_dir,
            {"name": "MinimalChar"},  # Only required field
        )

        profiles = loader.load_for_script(script)

        assert "MinimalChar" in profiles
        profile = profiles["MinimalChar"]
        assert profile.role == ""
        assert profile.age is None
        assert profile.personality == []
        assert profile.description == ""
        assert profile.typical_lines == []

    # ---- Description truncation ----

    def test_description_truncated_to_two_sentences(self, loader, tmp_path):
        """Long descriptions are truncated to first two sentences."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)
        self._create_character_json(
            characters_dir,
            {
                "name": "Verbose",
                "description": (
                    "First sentence about the character. "
                    "Second sentence with more detail. "
                    "Third sentence that should be cut. "
                    "Fourth sentence also cut."
                ),
            },
        )

        profiles = loader.load_for_script(script)
        desc = profiles["Verbose"].description

        assert "First sentence" in desc
        assert "Second sentence" in desc
        assert "Third sentence" not in desc

    # ---- Non-dict JSON ----

    def test_load_array_json_file(self, loader, tmp_path):
        """Skips JSON files that are arrays, not objects."""
        chapters_dir = tmp_path / "src" / "chapters" / "01-test"
        chapters_dir.mkdir(parents=True)
        script = chapters_dir / "audio-script.md"
        script.write_text("test")

        characters_dir = tmp_path / "src" / "characters"
        characters_dir.mkdir(parents=True)

        array_file = characters_dir / "array.json"
        array_file.write_text(json.dumps([{"name": "Test"}]), encoding="utf-8")

        profiles = loader.load_for_script(script)
        assert profiles == {}
