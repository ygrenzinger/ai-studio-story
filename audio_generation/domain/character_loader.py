"""Character profile loader from story character JSON files."""

import json
import logging
from pathlib import Path

from audio_generation.domain.models import CharacterProfile


class CharacterLoader:
    """Loads character profiles from story character JSON files.

    Discovers character JSON files by walking upward from the audio-script
    path to find the nearest ``src/characters/`` directory.
    """

    def load_for_script(self, script_path: Path) -> dict[str, CharacterProfile]:
        """Discover and load character profiles relative to an audio-script.

        Searches upward from script_path for a ``characters/`` directory
        under the nearest ``src/`` ancestor.

        Path resolution examples::

            stories/aventure-spatiale/src/chapters/01-decollage/audio-script.md
            -> stories/aventure-spatiale/src/characters/*.json

            stories/explorateur-croyances/src/stories/01-dieux-olympe/audio-script.md
            -> stories/explorateur-croyances/src/characters/*.json

        Args:
            script_path: Path to the audio-script markdown file.

        Returns:
            Dict mapping speaker name to CharacterProfile. Empty dict if
            no characters directory found or no JSON files exist.
        """
        characters_dir = self._find_characters_dir(script_path)
        if characters_dir is None:
            logging.debug(f"No characters directory found for script: {script_path}")
            return {}

        return self._load_from_directory(characters_dir)

    def _find_characters_dir(self, script_path: Path) -> Path | None:
        """Walk upward from script path to find src/characters/ directory.

        Args:
            script_path: Path to the audio-script file.

        Returns:
            Path to characters directory, or None if not found.
        """
        current = script_path.resolve().parent

        # Walk up to a reasonable depth (max 10 levels)
        for _ in range(10):
            if current.name == "src":
                candidates = current / "characters"
                if candidates.is_dir():
                    return candidates
            # Also check if current dir has a src/ child
            src_child = current / "src"
            if src_child.is_dir():
                candidates = src_child / "characters"
                if candidates.is_dir():
                    return candidates

            parent = current.parent
            if parent == current:
                # Reached filesystem root
                break
            current = parent

        return None

    def _load_from_directory(self, characters_dir: Path) -> dict[str, CharacterProfile]:
        """Load all character JSON files from a directory.

        Args:
            characters_dir: Path to the characters directory.

        Returns:
            Dict mapping character name to CharacterProfile.
        """
        profiles: dict[str, CharacterProfile] = {}

        for json_file in sorted(characters_dir.glob("*.json")):
            try:
                profile = self._load_single(json_file)
                if profile is not None:
                    profiles[profile.name] = profile
            except Exception as e:
                logging.warning(f"Failed to load character file {json_file}: {e}")

        if profiles:
            logging.debug(
                f"Loaded {len(profiles)} character profiles from {characters_dir}"
            )

        return profiles

    def _load_single(self, json_file: Path) -> CharacterProfile | None:
        """Load a single character profile from a JSON file.

        Args:
            json_file: Path to the character JSON file.

        Returns:
            CharacterProfile, or None if the file is not a valid character.
        """
        data = json.loads(json_file.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            logging.warning(f"Character file {json_file} is not a JSON object")
            return None

        name = data.get("name")
        if not name:
            logging.warning(f"Character file {json_file} missing 'name' field")
            return None

        return CharacterProfile(
            name=name,
            role=data.get("role", ""),
            age=data.get("age"),
            gender=data.get("gender", ""),
            personality=data.get("personality", []),
            description=self._truncate_to_first_sentence(data.get("description", "")),
            typical_lines=data.get("typical_lines", []),
        )

    @staticmethod
    def _truncate_to_first_sentence(text: str) -> str:
        """Truncate description to first two sentences to avoid prompt bloat.

        Args:
            text: Full description text.

        Returns:
            First two sentences, or the full text if fewer than 2 sentences.
        """
        if not text:
            return ""

        # Split on sentence-ending punctuation followed by space
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in ".!?" and len(current.strip()) > 5:
                sentences.append(current.strip())
                current = ""
                if len(sentences) >= 2:
                    break

        if sentences:
            return " ".join(sentences)

        # No clear sentence boundary found, return as-is
        return text.strip()
