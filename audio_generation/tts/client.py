"""TTS client wrapper for Gemini TTS with retry logic."""

import logging
import time

try:
    from google import genai
    from google.genai import types
except (ImportError, ModuleNotFoundError):  # pragma: no cover - without optional SDK
    genai = None

    class _Types:
        class SpeechConfig:
            pass

    types = _Types()

from audio_generation.domain.constants import MAX_RETRIES


class TTSClient:
    """Wrapper for Gemini TTS API with retry logic.

    Uses Vertex AI or Gemini Developer API authentication. Handles API calls
    with automatic retry on failure, exponential backoff, and proper error
    handling.
    """

    def __init__(
        self,
        model: str,
        max_retries: int = MAX_RETRIES,
        *,
        project: str | None = None,
        location: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize TTS client.

        Args:
            model: TTS model name
            max_retries: Maximum retry attempts per request
            project: Google Cloud project ID for Vertex AI
            location: Google Cloud region (default: us-central1)
            api_key: Gemini Developer API key
        """
        if genai is None:
            raise RuntimeError("Google GenAI SDK is not installed")
        if project:
            self._client = genai.Client(
                vertexai=True, project=project, location=location
            )
            self._backend = "Vertex AI"
        elif api_key:
            self._client = genai.Client(api_key=api_key)
            self._backend = "Gemini API"
        else:
            raise ValueError(
                "Gemini TTS requires GOOGLE_CLOUD_PROJECT or GEMINI_API_KEY"
            )
        self._model = model
        self._max_retries = max_retries

    def generate(
        self,
        prompt: str,
        speech_config: types.SpeechConfig,
        system_instruction: str = "",
        batch_num: int = 0,
    ) -> bytes:
        """Generate audio from prompt with retry handling.

        Args:
            prompt: Text prompt for TTS (structured with sections)
            speech_config: Speech configuration from SpeechConfigBuilder
            system_instruction: Optional system instruction for the model
                (e.g., rules about not reading stage directions aloud)
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
                return self._make_request(prompt, speech_config, system_instruction)
            except Exception as e:
                if attempt < self._max_retries - 1:
                    error_str = str(e)
                    # Rate limit: wait longer (parse retry delay or default 20s)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = 20
                        # Try to extract suggested retry delay
                        import re

                        match = re.search(
                            r"retry in (\d+(?:\.\d+)?)s", error_str, re.IGNORECASE
                        )
                        if match:
                            wait_time = max(int(float(match.group(1))) + 2, 20)
                        logging.warning(
                            f"Batch {batch_num} rate limited "
                            f"(attempt {attempt + 1}/{self._max_retries}), "
                            f"waiting {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logging.warning(
                            f"Batch {batch_num} generation failed "
                            f"(attempt {attempt + 1}/{self._max_retries}): {e}"
                        )
                        time.sleep(2 * (attempt + 1))  # Exponential backoff
                else:
                    logging.error(
                        f"Batch {batch_num} failed after {self._max_retries} attempts: {e}"
                    )
                    raise RuntimeError(
                        f"Batch {batch_num} failed after {self._max_retries} attempts: {e}"
                    ) from e

        raise RuntimeError(f"Batch {batch_num} failed: max retries exceeded")

    def _make_request(
        self,
        prompt: str,
        speech_config: types.SpeechConfig,
        system_instruction: str = "",
    ) -> bytes:
        """Make a single TTS API request.

        Args:
            prompt: Text prompt for TTS
            speech_config: Speech configuration
            system_instruction: Optional system instruction

        Returns:
            Raw PCM audio data

        Raises:
            RuntimeError: If no audio data in response
        """
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        )

        # TTS-specific models (e.g. gemini-2.5-flash-preview-tts) don't support
        # system_instruction — it causes 500 INTERNAL errors. Fold it into the
        # prompt instead.
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        else:
            full_prompt = prompt

        response = self._client.models.generate_content(
            model=self._model,
            contents=full_prompt,
            config=config,
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
