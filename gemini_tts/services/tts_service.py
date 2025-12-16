"""Text-to-Speech service using Google Gemini API."""

import os
from google import genai
from google.genai import types

from gemini_tts.exceptions import TtsException
from gemini_tts.models import AudioData
from gemini_tts.voices import is_valid_voice


MAX_TEXT_LENGTH = 8000
MODEL_NAME = "gemini-2.5-flash-preview-tts"


class GeminiTextToSpeechService:
    """Service for generating speech using Google Gemini TTS API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the TTS service.

        Args:
            api_key: Google API key. If not provided, reads from GOOGLE_API_KEY env var.

        Raises:
            TtsException: If no API key is provided or found.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise TtsException(
                "No API key provided. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = genai.Client(api_key=self.api_key)

    def generate_speech(
        self,
        text: str,
        voice: str,
        style: str | None = None,
    ) -> AudioData:
        """Generate speech from text.

        Args:
            text: The text to convert to speech.
            voice: The voice name to use.
            style: Optional style prompt (e.g., "excited", "calm").

        Returns:
            AudioData containing raw audio bytes and mime_type from the API.

        Raises:
            TtsException: If text validation fails or API call fails.
        """
        # Validate input
        if not text or not text.strip():
            raise TtsException("Text cannot be empty")

        if len(text) > MAX_TEXT_LENGTH:
            raise TtsException(
                f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters "
                f"(got {len(text)})"
            )

        if not is_valid_voice(voice):
            raise TtsException(f"Invalid voice: {voice}")

        # Build the prompt with optional style
        if style:
            prompt = f"Say in a {style} tone: {text}"
        else:
            prompt = text

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice,
                            )
                        )
                    ),
                ),
            )

            # Extract audio data from response using SDK's parts accessor
            # The SDK returns inline_data.data as bytes (already decoded)
            for part in response.parts:
                if part.inline_data and part.inline_data.data:
                    mime_type = part.inline_data.mime_type or "audio/L16;rate=24000"
                    return AudioData(data=part.inline_data.data, mime_type=mime_type)

            raise TtsException("No audio data found in response")

        except TtsException:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg or "401" in error_msg:
                raise TtsException("Authentication failed. Check your API key.", e)
            elif "rate limit" in error_msg or "429" in error_msg:
                raise TtsException("Rate limit exceeded. Please try again later.", e)
            elif "quota" in error_msg:
                raise TtsException("API quota exceeded.", e)
            elif "network" in error_msg or "connection" in error_msg:
                raise TtsException("Network error. Check your internet connection.", e)
            else:
                raise TtsException(f"API error: {e}", e)
