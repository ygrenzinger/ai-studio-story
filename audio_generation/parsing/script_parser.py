"""Audio script parser for markdown files with YAML frontmatter."""

import logging
import re
from pathlib import Path

import yaml

from audio_generation.domain.models import (
    AudioScript,
    Segment,
    SpeakerConfig,
)
from audio_generation.domain.constants import DEFAULT_TTS_MODEL, DEFAULT_VOICE


class AudioScriptParser:
    """Parses audio-script markdown files into domain objects.

    Expected format:
    ---
    stageUuid: "stage-uuid"
    chapterRef: "chapter-ref"
    locale: "en-US"
    speakers:
      - name: Narrator
        voice: Sulafat
        profile: "Warm storyteller..."
      - name: Emma
        voice: Leda
        profile: "8-year-old girl..."
    ---

    **Narrator:** <emotion: warm> Text with emotion marker inline...
    **Emma:** <emotion: curious> Character dialogue...
    """

    def parse(self, file_path: Path) -> AudioScript:
        """Parse audio-script markdown file into AudioScript dataclass.

        Args:
            file_path: Path to the markdown file

        Returns:
            Parsed AudioScript dataclass

        Raises:
            ValueError: If file format is invalid
        """
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(content)
        speaker_configs = self._parse_speaker_configs(frontmatter)
        segments = self._parse_transcript(body, speaker_configs)

        return AudioScript(
            stage_uuid=frontmatter.get("stageUuid", ""),
            chapter_ref=frontmatter.get("chapterRef", ""),
            locale=frontmatter.get("locale", "en-US"),
            speaker_configs=speaker_configs,
            segments=segments,
            tts_model=frontmatter.get("model", DEFAULT_TTS_MODEL),
        )

    def _split_frontmatter(self, content: str) -> tuple[dict, str]:
        """Split content into frontmatter and body.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter dict, body string)

        Raises:
            ValueError: If frontmatter format is invalid
        """
        if not content.startswith("---"):
            raise ValueError("Missing YAML frontmatter (must start with ---)")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")

        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]

        return frontmatter, body

    def _parse_speaker_configs(self, frontmatter: dict) -> list[SpeakerConfig]:
        """Parse speaker configurations from frontmatter.

        Args:
            frontmatter: Parsed YAML frontmatter

        Returns:
            List of SpeakerConfig objects
        """
        speaker_configs = []
        for speaker_data in frontmatter.get("speakers", []):
            if isinstance(speaker_data, dict):
                speaker_configs.append(
                    SpeakerConfig(
                        name=speaker_data.get("name", "Narrator"),
                        voice=speaker_data.get("voice", DEFAULT_VOICE),
                        profile=speaker_data.get("profile", ""),
                    )
                )

        # If no speakers defined, use default narrator
        if not speaker_configs:
            speaker_configs.append(
                SpeakerConfig(name="Narrator", voice=DEFAULT_VOICE, profile="")
            )

        return speaker_configs

    def _parse_transcript(
        self, content: str, speaker_configs: list[SpeakerConfig]
    ) -> list[Segment]:
        """Parse transcript content into ordered segments.

        Handles:
        - Speaker labels: **Speaker:** text
        - Emotion markers: <emotion: descriptor1, descriptor2>
        - Multiple emotions in one block (splits into multiple segments)

        Args:
            content: The transcript content (body after frontmatter)
            speaker_configs: List of configured speakers for validation

        Returns:
            List of Segment objects in order
        """
        segments = []
        valid_speakers = {cfg.name for cfg in speaker_configs}

        # Pattern: **Speaker:** followed by content until next **Speaker:** or end
        speaker_pattern = r"\*\*(\w+):\*\*"
        matches = list(re.finditer(speaker_pattern, content))

        for i, match in enumerate(matches):
            speaker = match.group(1)

            # Warn about undefined speakers
            if speaker not in valid_speakers:
                logging.warning(
                    f"Speaker '{speaker}' found in transcript but not defined in frontmatter"
                )

            # Extract text until next speaker or end
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            text = content[start:end].strip()

            # Skip empty segments
            if not text:
                continue

            # Check for multiple <emotion:> markers -> split
            emotion_splits = self._split_by_emotions(text)

            for emotion, segment_text in emotion_splits:
                # Clean up the segment text (remove trailing dashes/separators)
                segment_text = re.sub(r"\n---\s*$", "", segment_text).strip()
                if not segment_text:
                    continue

                segments.append(
                    Segment(speaker=speaker, text=segment_text, emotion=emotion)
                )

        return segments

    def _split_by_emotions(self, text: str) -> list[tuple[str, str]]:
        """Split text by <emotion:> markers into (emotion, text) pairs.

        Args:
            text: Text that may contain <emotion:> markers

        Returns:
            List of (emotion, text) tuples. Empty emotion string if no marker.
        """
        # Pattern: <emotion: ...> followed by text
        pattern = r"<emotion:\s*([^>]+)>\s*"

        parts = re.split(pattern, text)
        # parts = [pre_text, emotion1, text1, emotion2, text2, ...]

        results = []

        # Text before first emotion marker (if any)
        if parts[0].strip():
            results.append(("", parts[0].strip()))

        # Process emotion + text pairs
        for i in range(1, len(parts), 2):
            emotion = parts[i].strip()
            segment_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if segment_text:
                results.append((emotion, segment_text))

        return results if results else [("", text.strip())]
