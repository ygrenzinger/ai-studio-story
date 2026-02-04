"""Progress management for resume capability."""

import hashlib
import json
import logging
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from audio_generation.domain.models import GenerationProgress
from audio_generation.domain.constants import PROGRESS_FILE_NAME


class ProgressManager:
    """Manages generation progress for resume capability.

    Enables resuming audio generation after failures (e.g., API rate limits)
    by persisting progress to disk and tracking which batches are complete.
    """

    def __init__(self, output_dir: Path):
        """Initialize progress manager.

        Args:
            output_dir: Directory to store progress files and batch audio
        """
        self._output_dir = output_dir
        self._progress_path = output_dir / PROGRESS_FILE_NAME
        self._batch_dir = output_dir / "batches"

    def load(self) -> GenerationProgress | None:
        """Load existing progress from disk.

        Returns:
            GenerationProgress if valid progress exists, None otherwise
        """
        if not self._progress_path.exists():
            return None

        try:
            data = json.loads(self._progress_path.read_text())
            return GenerationProgress(
                input_file_hash=data["input_file_hash"],
                total_batches=data["total_batches"],
                completed_batches=data.get("completed_batches", []),
                audio_files={int(k): v for k, v in data.get("audio_files", {}).items()},
                last_error=data.get("last_error"),
                last_error_batch=data.get("last_error_batch"),
                last_error_time=data.get("last_error_time"),
                started_at=data.get("started_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logging.warning(f"Could not load progress file: {e}")
            return None

    def save(self, progress: GenerationProgress) -> None:
        """Save progress to disk.

        Args:
            progress: Progress state to persist
        """
        progress.updated_at = datetime.now().isoformat()
        # Convert audio_files keys to strings for JSON serialization
        data = asdict(progress)
        data["audio_files"] = {str(k): v for k, v in progress.audio_files.items()}
        self._progress_path.write_text(json.dumps(data, indent=2))

    def save_batch_audio(self, batch_index: int, audio_data: bytes) -> str:
        """Save a single batch's audio data to disk immediately.

        Args:
            batch_index: Index of the batch (0-based)
            audio_data: Raw PCM audio data

        Returns:
            Filename of saved audio file (relative to batches directory)
        """
        self._batch_dir.mkdir(parents=True, exist_ok=True)
        filename = f"batch_{batch_index:04d}.pcm"
        filepath = self._batch_dir / filename
        filepath.write_bytes(audio_data)
        return filename

    def load_batch_audio(self, filename: str) -> bytes:
        """Load a previously saved batch audio file.

        Args:
            filename: Filename from save_batch_audio

        Returns:
            Raw PCM audio data
        """
        filepath = self._batch_dir / filename
        return filepath.read_bytes()

    def clear(self) -> None:
        """Remove progress file and batch directory after successful completion."""
        if self._progress_path.exists():
            self._progress_path.unlink()
            logging.debug("Removed progress file")

        if self._batch_dir.exists():
            shutil.rmtree(self._batch_dir)
            logging.debug("Removed batch directory")

    def validate(
        self, progress: GenerationProgress, input_file: Path, total_batches: int
    ) -> bool:
        """Check if saved progress is still valid for current run.

        Args:
            progress: Previously loaded progress
            input_file: Current input file
            total_batches: Expected batch count

        Returns:
            True if progress is valid for resume, False otherwise
        """
        current_hash = self.calculate_file_hash(input_file)
        if progress.input_file_hash != current_hash:
            logging.warning(
                "Input file has changed since last run - progress invalidated"
            )
            return False
        if progress.total_batches != total_batches:
            logging.warning("Batch count changed - progress invalidated")
            return False
        return True

    def create_initial_progress(
        self, input_file: Path, total_batches: int
    ) -> GenerationProgress:
        """Create a new progress tracking object.

        Args:
            input_file: Input markdown file
            total_batches: Total number of batches

        Returns:
            New GenerationProgress instance
        """
        return GenerationProgress(
            input_file_hash=self.calculate_file_hash(input_file),
            total_batches=total_batches,
            completed_batches=[],
            audio_files={},
            last_error=None,
            last_error_batch=None,
            last_error_time=None,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash string
        """
        return hashlib.md5(file_path.read_bytes()).hexdigest()
