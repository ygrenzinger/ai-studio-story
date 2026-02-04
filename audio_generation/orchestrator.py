"""Audio generation pipeline orchestrator."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from google.genai import errors as genai_errors

from audio_generation.audio.concatenator import SegmentConcatenator
from audio_generation.audio.effects import AudioEffects
from audio_generation.audio.exporter import MP3Exporter
from audio_generation.audio.processor import AudioProcessor
from audio_generation.batching.segment_batcher import SegmentBatcher
from audio_generation.domain.constants import API_CALL_DELAY_SEC
from audio_generation.domain.models import (
    AudioScript,
    PauseConfig,
    Segment,
    SegmentBatch,
    SpeakerConfig,
    VerificationResult,
)
from audio_generation.parsing.script_parser import AudioScriptParser
from audio_generation.progress.progress_manager import ProgressManager
from audio_generation.tts.client import TTSClient
from audio_generation.tts.config_builder import SpeechConfigBuilder
from audio_generation.tts.prompt_builder import TTSPromptBuilder
from audio_generation.verification.mp3_verifier import MP3Verifier


class AudioGenerationPipeline:
    """Domain-oriented orchestrator for audio generation.

    Coordinates all components to execute the full audio generation
    pipeline from script parsing to MP3 output.
    """

    def __init__(
        self,
        parser: AudioScriptParser | None = None,
        batcher: SegmentBatcher | None = None,
        tts_client: TTSClient | None = None,
        config_builder: SpeechConfigBuilder | None = None,
        prompt_builder: TTSPromptBuilder | None = None,
        concatenator: SegmentConcatenator | None = None,
        exporter: MP3Exporter | None = None,
        verifier: MP3Verifier | None = None,
        progress_manager: ProgressManager | None = None,
        pause_config: PauseConfig | None = None,
    ):
        """Initialize pipeline with optional dependency injection.

        Components are created with defaults if not provided,
        enabling easy testing with mocks.

        Args:
            parser: Script parser instance
            batcher: Segment batcher instance
            tts_client: TTS client instance (must be provided for generation)
            config_builder: Speech config builder instance
            prompt_builder: Prompt builder instance
            concatenator: Segment concatenator instance
            exporter: MP3 exporter instance
            verifier: MP3 verifier instance
            progress_manager: Progress manager instance
            pause_config: Pause configuration
        """
        self._parser = parser or AudioScriptParser()
        self._batcher = batcher or SegmentBatcher()
        self._tts_client = tts_client  # Must be set before execute()
        self._config_builder = config_builder or SpeechConfigBuilder()
        self._prompt_builder = prompt_builder or TTSPromptBuilder()

        # Audio processing chain
        effects = AudioEffects()
        processor = AudioProcessor(effects)
        self._pause_config = pause_config or PauseConfig()
        self._concatenator = concatenator or SegmentConcatenator(
            processor, effects, self._pause_config
        )
        self._exporter = exporter or MP3Exporter()
        self._verifier = verifier or MP3Verifier()
        self._progress_manager = progress_manager

    def set_tts_client(self, client: TTSClient) -> None:
        """Set TTS client (required before execute).

        Args:
            client: Configured TTS client
        """
        self._tts_client = client

    def set_progress_manager(self, manager: ProgressManager) -> None:
        """Set progress manager for resume capability.

        Args:
            manager: Progress manager instance
        """
        self._progress_manager = manager

    def execute(
        self,
        input_file: Path,
        output_path: Path,
        resume: bool = False,
        verify: bool = True,
        progress_callback: Callable[[int, int], None] | None = None,
        delay_seconds: float = API_CALL_DELAY_SEC,
    ) -> bytes:
        """Execute the full audio generation pipeline.

        Pipeline stages:
        1. Parse script from markdown file
        2. Batch segments for TTS API
        3. Load/initialize progress tracking
        4. Generate audio for each batch (with resume support)
        5. Concatenate segments with context-aware pauses
        6. Export to MP3 format
        7. Verify output format
        8. Clean up progress files

        Args:
            input_file: Path to input markdown file
            output_path: Output MP3 file path
            resume: If True, attempt to resume from saved progress
            verify: If True, verify output format after generation
            progress_callback: Optional callback for progress updates (current, total)
            delay_seconds: Delay between API calls (default: 6s for <10 RPM)

        Returns:
            Final MP3 data bytes

        Raises:
            ValueError: If TTS client not configured
            RuntimeError: If generation fails
        """
        if self._tts_client is None:
            raise ValueError("TTS client must be configured before execute()")

        # Ensure progress manager is set
        if self._progress_manager is None:
            self._progress_manager = ProgressManager(output_path.parent)

        # Stage 1: Parse script
        logging.info(f"Parsing audio script: {input_file}")
        script = self._parser.parse(input_file)
        logging.info(f"Stage UUID: {script.stage_uuid}")
        logging.info(f"Speakers: {[cfg.name for cfg in script.speaker_configs]}")
        logging.info(f"Segments: {len(script.segments)}")

        # Stage 2: Batch segments
        batches = self._batcher.batch(script.segments)
        logging.info(
            f"Processing {len(script.segments)} segments in {len(batches)} batches"
        )

        # Stage 3: Handle progress/resume
        speaker_configs_map = {cfg.name: cfg for cfg in script.speaker_configs}

        # Stage 4: Generate audio for all batches
        audio_segments = self._generate_batches(
            batches=batches,
            speaker_configs_map=speaker_configs_map,
            input_file=input_file,
            output_dir=output_path.parent,
            resume=resume,
            progress_callback=progress_callback,
            delay_seconds=delay_seconds,
        )

        # Stage 5: Create batch metadata for context-aware pausing
        batch_metadata: list[Segment] = []
        for batch in batches:
            if batch.segments:
                batch_metadata.append(batch.segments[-1])

        # Concatenate with context-aware pauses
        combined = self._concatenator.concatenate(audio_segments, batch_metadata)

        # Stage 6: Export to MP3
        mp3_data = self._exporter.export(combined, output_path)

        # Stage 7: Verify format
        if verify:
            result = self._verifier.verify(mp3_data)
            if not result.passed:
                logging.error("Output does not meet format requirements:")
                for issue in result.issues:
                    logging.error(f"  - {issue}")
                raise RuntimeError(
                    f"MP3 verification failed: {', '.join(result.issues)}"
                )

        # Stage 8: Clean up progress files
        self._progress_manager.clear()

        return mp3_data

    def _generate_batches(
        self,
        batches: list[SegmentBatch],
        speaker_configs_map: dict[str, SpeakerConfig],
        input_file: Path,
        output_dir: Path,
        resume: bool,
        progress_callback: Callable[[int, int], None] | None,
        delay_seconds: float,
    ) -> list[bytes]:
        """Generate audio for all batches with resume capability.

        Args:
            batches: List of segment batches
            speaker_configs_map: Speaker name to config mapping
            input_file: Input file for hash validation
            output_dir: Directory for progress files
            resume: Whether to resume from saved progress
            progress_callback: Optional progress callback
            delay_seconds: Delay between API calls

        Returns:
            List of raw PCM audio data in batch order

        Raises:
            RuntimeError: If generation fails
        """
        if self._tts_client is None:
            raise ValueError("TTS client not configured")

        total_batches = len(batches)

        # Try to load existing progress if resuming
        progress = None
        if resume and self._progress_manager:
            progress = self._progress_manager.load()
            if progress and self._progress_manager.validate(
                progress, input_file, total_batches
            ):
                logging.info(
                    f"Resuming: {len(progress.completed_batches)}/{total_batches} "
                    "batches already complete"
                )
                if progress.last_error:
                    logging.info(
                        f"Previous error on batch {(progress.last_error_batch or 0) + 1}: "
                        f"{progress.last_error}"
                    )
            else:
                progress = None
                logging.info("Starting fresh (no valid progress found)")

        # Initialize new progress if needed
        if progress is None and self._progress_manager:
            progress = self._progress_manager.create_initial_progress(
                input_file, total_batches
            )
            self._progress_manager.save(progress)

        results: list[bytes | None] = [None] * total_batches

        # Load already-completed batches from disk
        if progress and self._progress_manager:
            for batch_idx in progress.completed_batches:
                filename = progress.audio_files.get(batch_idx)
                if filename:
                    results[batch_idx] = self._progress_manager.load_batch_audio(
                        filename
                    )
                    logging.debug(f"Loaded cached batch {batch_idx + 1}")

        # Report initial progress for resumed batches
        if progress and progress.completed_batches and progress_callback:
            progress_callback(len(progress.completed_batches), total_batches)

        # Track if we need delay
        need_delay = bool(progress and progress.completed_batches)

        # Process remaining batches
        for i, batch in enumerate(batches):
            if progress and i in progress.completed_batches:
                continue  # Skip already completed

            # Rate limiting delay
            if need_delay:
                logging.debug(f"Rate limit delay: {delay_seconds}s")
                time.sleep(delay_seconds)
            need_delay = True

            batch_num = i + 1

            try:
                # Build prompt and config
                prompt = self._prompt_builder.build(batch, speaker_configs_map)
                speech_config = self._config_builder.build_for_batch(
                    batch, speaker_configs_map
                )

                # Generate audio
                audio_data = self._tts_client.generate(prompt, speech_config, batch_num)

                # Save immediately to disk
                if self._progress_manager and progress:
                    filename = self._progress_manager.save_batch_audio(i, audio_data)
                    results[i] = audio_data

                    # Update progress
                    progress.completed_batches.append(i)
                    progress.audio_files[i] = filename
                    progress.last_error = None
                    progress.last_error_batch = None
                    progress.last_error_time = None
                    self._progress_manager.save(progress)
                else:
                    results[i] = audio_data

                if progress_callback:
                    completed = (
                        len(progress.completed_batches) if progress else batch_num
                    )
                    progress_callback(completed, total_batches)

            except genai_errors.APIError as e:
                # Save error state and exit
                if self._progress_manager and progress:
                    progress.last_error = f"API Error {e.code}: {e.message}"
                    progress.last_error_batch = i
                    progress.last_error_time = datetime.now().isoformat()
                    self._progress_manager.save(progress)

                logging.error(
                    f"Batch {batch_num} failed with API error: {e.code} - {e.message}"
                )
                logging.error("Progress saved. Resume with --resume flag.")
                completed = len(progress.completed_batches) if progress else 0
                raise RuntimeError(
                    f"Batch {batch_num} failed: API Error {e.code}. "
                    f"Progress saved ({completed}/{total_batches} complete). "
                    "Resume with --resume flag."
                ) from e

            except Exception as e:
                # Save error state for any other exception
                if self._progress_manager and progress:
                    progress.last_error = str(e)
                    progress.last_error_batch = i
                    progress.last_error_time = datetime.now().isoformat()
                    self._progress_manager.save(progress)

                logging.error(f"Batch {batch_num} failed: {e}")
                logging.error("Progress saved. Resume with --resume flag.")
                completed = len(progress.completed_batches) if progress else 0
                raise RuntimeError(
                    f"Batch {batch_num} failed: {e}. "
                    f"Progress saved ({completed}/{total_batches} complete). "
                    "Resume with --resume flag."
                ) from e

        # All batches complete - return results
        return [r for r in results if r is not None]

    def parse_script(self, file_path: Path) -> AudioScript:
        """Parse script without executing full pipeline.

        Useful for validation and inspection.

        Args:
            file_path: Path to markdown file

        Returns:
            Parsed AudioScript
        """
        return self._parser.parse(file_path)

    def verify_mp3(self, mp3_data: bytes) -> VerificationResult:
        """Verify MP3 format meets requirements.

        Args:
            mp3_data: MP3 file bytes

        Returns:
            VerificationResult with status and issues
        """
        return self._verifier.verify(mp3_data)
