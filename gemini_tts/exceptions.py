"""Custom exceptions for Gemini TTS."""


class TtsException(Exception):
    """Base exception for TTS operations."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class AudioConversionException(Exception):
    """Exception for audio conversion failures."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause
