"""ElevenLabs v3 TTS provider using the standard REST endpoint."""

from __future__ import annotations

import json
import os
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from audio_generation.emotion.elevenlabs_v3_tags import (
    compile_elevenlabs_v3_segment_text,
)
from audio_generation.providers.base import (
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
    TTSAuthError,
    TTSProviderError,
    TTSRateLimitError,
    TTSValidationError,
)

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_V3_MODEL = "eleven_v3"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"

DEFAULT_VOICE_SETTINGS = {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.35,
    "speed": 1.0,
    "use_speaker_boost": True,
}


class ElevenLabsProvider:
    """ElevenLabs v3 REST TTS provider."""

    name = "elevenlabs"
    capabilities = ProviderCapabilities(
        supports_prompt_director_notes=False,
        supports_inline_tags=True,
        supports_wrapping_tags=False,
        supports_voice_settings=True,
        supports_direct_mp3_44100=True,
    )

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = ELEVENLABS_V3_MODEL,
        opener: Callable | None = None,
        endpoint: str = ELEVENLABS_TTS_URL,
    ):
        validate_elevenlabs_model(model)
        self._api_key = (
            api_key if api_key is not None else os.environ.get("ELEVENLABS_API_KEY")
        )
        self._model = model
        self._opener = opener or urlopen
        self._endpoint = endpoint.rstrip("/")

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if not self._api_key:
            raise TTSAuthError(
                "ELEVENLABS_API_KEY is required for ElevenLabs TTS generation"
            )
        if len(request.batch.speakers) != 1:
            raise TTSValidationError(
                "ElevenLabs TTS requests must contain exactly one speaker"
            )

        speaker_name = request.batch.speakers[0]
        speaker = request.speaker_configs[speaker_name]
        voice_settings = resolve_elevenlabs_voice_settings(
            speaker.provider_settings.get("elevenlabs", {}).get("voice_settings", {})
        )
        payload = {
            "text": self._compile_text(request),
            "model_id": self._model,
            "voice_settings": voice_settings,
        }
        response_bytes = self._post(speaker.voice, payload)
        return SynthesisResult(
            audio_bytes=response_bytes,
            codec="mp3",
            sample_rate=44100,
            channels=1,
            provider_metadata={
                "voice_id": speaker.voice,
                "model_id": self._model,
                "voice_settings": voice_settings,
            },
        )

    def _compile_text(self, request: SynthesisRequest) -> str:
        return "\n".join(
            compile_elevenlabs_v3_segment_text(segment)
            for segment in request.batch.segments
        )

    def _post(self, voice_id: str, payload: dict) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        url = (
            f"{self._endpoint}/{quote(voice_id)}"
            f"?output_format={ELEVENLABS_OUTPUT_FORMAT}"
        )
        request = Request(
            url,
            data=body,
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=120) as response:
                return response.read()
        except HTTPError as exc:
            self._raise_http_error(exc)

    def _raise_http_error(self, exc: HTTPError) -> None:
        message = _read_error_message(exc)
        if exc.code in {401, 403}:
            raise TTSAuthError(
                f"ElevenLabs authentication failed: {message}"
            ) from exc
        if exc.code == 429:
            raise TTSRateLimitError(
                f"ElevenLabs rate limit exceeded: {message}"
            ) from exc
        if exc.code == 422:
            raise TTSValidationError(
                f"ElevenLabs request rejected: {message}"
            ) from exc
        if exc.code >= 500:
            raise TTSProviderError(
                f"ElevenLabs provider error {exc.code}: {message}"
            ) from exc
        raise TTSProviderError(
            f"ElevenLabs request failed with HTTP {exc.code}: {message}"
        ) from exc


def validate_elevenlabs_model(model: str | None) -> str:
    """Validate ElevenLabs provider model selection."""

    selected = model or ELEVENLABS_V3_MODEL
    if selected != ELEVENLABS_V3_MODEL:
        raise ValueError("ElevenLabs provider currently supports only model eleven_v3")
    return selected


def resolve_elevenlabs_voice_settings(overrides: dict | None = None) -> dict:
    """Merge and validate ElevenLabs voice settings."""

    settings = {**DEFAULT_VOICE_SETTINGS, **(overrides or {})}
    _validate_range(settings, "stability", 0.0, 1.0)
    _validate_range(settings, "similarity_boost", 0.0, 1.0)
    _validate_range(settings, "style", 0.0, 1.0)
    _validate_range(settings, "speed", 0.7, 1.2)
    if not isinstance(settings.get("use_speaker_boost"), bool):
        raise TTSValidationError("ElevenLabs use_speaker_boost must be a boolean")
    return settings


def _validate_range(settings: dict, key: str, minimum: float, maximum: float) -> None:
    value = settings.get(key)
    if not isinstance(value, int | float) or not minimum <= value <= maximum:
        raise TTSValidationError(
            f"ElevenLabs {key} must be between {minimum} and {maximum}"
        )


def _read_error_message(exc: HTTPError) -> str:
    try:
        data = exc.read()
    except Exception:
        data = b""
    if not data:
        return exc.reason or "no response body"
    return data.decode("utf-8", errors="replace")
