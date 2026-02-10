"""TTS client wrapper for Vertex AI with retry logic."""

import logging
import time

from google import genai
from google.genai import types

from audio_generation.domain.constants import MAX_RETRIES


class TTSClient:
    """Wrapper for Vertex AI TTS API with retry logic.

    Handles API calls to Vertex AI Gemini TTS with automatic retry on failure,
    exponential backoff, and proper error handling.
    """

    def __init__(
        self,
        project: str,
        location: str,
        model: str,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize TTS client using Vertex AI.

        Args:
            project: Google Cloud project ID
            location: Google Cloud region (e.g., 'us-central1')
            model: TTS model name
            max_retries: Maximum retry attempts per request
        """
        self._client = genai.Client(vertexai=True, project=project, location=location)
        self._model = model
        self._max_retries = max_retries

    def generate(
        self, prompt: str, speech_config: types.SpeechConfig, batch_num: int = 0
    ) -> bytes:
        """Generate audio from prompt with retry handling.

        Args:
            prompt: Text prompt for TTS
            speech_config: Speech configuration from SpeechConfigBuilder
            batch_num: Batch number for logging (1-indexed)

        Returns:
            Raw PCM audio data

        Raises:
            RuntimeError: If generation fails after all retries
        """
        logging.debug(
            f"Batch {batch_num} prompt ({len(prompt)} chars):\n{prompt[:500]}..."
        )

        for attempt in range(self._max_retries):
            try:
                return self._make_request(prompt, speech_config)
            except Exception as e:
                if attempt < self._max_retries - 1:
                    logging.warning(
                        f"Batch {batch_num} generation failed "
                        f"(attempt {attempt + 1}/{self._max_retries}): {e}"
                    )
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logging.error(
                        f"Batch {batch_num} failed after {self._max_retries} attempts: {e}"
                    )
                    raise RuntimeError(
                        f"Batch {batch_num} failed after {self._max_retries} attempts: {e}"
                    ) from e

        raise RuntimeError(f"Batch {batch_num} failed: max retries exceeded")

    def _make_request(self, prompt: str, speech_config: types.SpeechConfig) -> bytes:
        """Make a single TTS API request.

        Args:
            prompt: Text prompt for TTS
            speech_config: Speech configuration

        Returns:
            Raw PCM audio data

        Raises:
            RuntimeError: If no audio data in response
        """
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
            ),
        )

        # Extract audio data from response
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            if parts:
                for part in parts:
                    if (
                        part.inline_data is not None
                        and part.inline_data.data is not None
                    ):
                        return part.inline_data.data

        # Diagnostic logging for empty audio responses
        self._log_response_diagnostics(response, prompt)
        raise RuntimeError("No audio data in TTS response")

    def _log_response_diagnostics(self, response, prompt: str) -> None:
        """Log detailed diagnostics when no audio data is found in response.

        Helps identify safety filters, content blocks, or unexpected
        response structures that cause empty audio responses.

        Args:
            response: The raw API response object
            prompt: The prompt that was sent (for context)
        """
        logging.warning("--- TTS Response Diagnostics ---")
        logging.warning(f"Prompt length: {len(prompt)} chars")
        logging.warning(f"Full prompt sent to model:\n{prompt}")

        if not response.candidates:
            logging.warning("No candidates in response")
            # Check for prompt_feedback (blocked before generation)
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                logging.warning(f"Prompt feedback: {response.prompt_feedback}")
            return

        candidate = response.candidates[0]

        # Check finish reason (STOP = normal, SAFETY = blocked, OTHER = unknown)
        if hasattr(candidate, "finish_reason") and candidate.finish_reason:
            logging.warning(f"Finish reason: {candidate.finish_reason}")

        # Check safety ratings
        if hasattr(candidate, "safety_ratings") and candidate.safety_ratings:
            for rating in candidate.safety_ratings:
                logging.warning(
                    f"Safety rating: category={rating.category}, "
                    f"probability={rating.probability}, "
                    f"blocked={getattr(rating, 'blocked', 'N/A')}"
                )

        # Check content structure
        if candidate.content:
            parts = candidate.content.parts
            if parts:
                logging.warning(f"Response has {len(parts)} part(s):")
                for i, part in enumerate(parts):
                    has_text = hasattr(part, "text") and part.text
                    has_inline = (
                        part.inline_data is not None
                        if hasattr(part, "inline_data")
                        else False
                    )
                    inline_size = (
                        len(part.inline_data.data)
                        if has_inline and part.inline_data.data
                        else 0
                    )
                    logging.warning(
                        f"  Part {i}: text={has_text}, "
                        f"inline_data={has_inline}, "
                        f"data_size={inline_size}"
                    )
                    if has_text:
                        logging.warning(f"  Text content: {part.text[:200]}")
            else:
                logging.warning("Content has no parts")
        else:
            logging.warning("Candidate has no content")

        logging.warning("--- End Diagnostics ---")

    @property
    def model(self) -> str:
        """Get the TTS model name."""
        return self._model
