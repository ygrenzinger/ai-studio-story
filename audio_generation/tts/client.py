"""TTS client wrapper for Gemini API with retry logic."""

import logging
import time

from google import genai
from google.genai import types

from audio_generation.domain.constants import MAX_RETRIES


class TTSClient:
    """Wrapper for Gemini TTS API with retry logic.

    Handles API calls to Gemini TTS with automatic retry on failure,
    exponential backoff, and proper error handling.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize TTS client.

        Args:
            api_key: Google AI Studio API key
            model: TTS model name
            max_retries: Maximum retry attempts per request
        """
        self._client = genai.Client(api_key=api_key)
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

        raise RuntimeError("No audio data in TTS response")

    @property
    def model(self) -> str:
        """Get the TTS model name."""
        return self._model
