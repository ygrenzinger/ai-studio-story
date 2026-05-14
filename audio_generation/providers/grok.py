"""xAI Grok TTS provider using minimal REST support."""

from __future__ import annotations

import json
import os
from typing import Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from audio_generation.emotion.grok_tags import compile_grok_segment_text
from audio_generation.providers.base import (
    ProviderCapabilities,
    SynthesisRequest,
    SynthesisResult,
    TTSAuthError,
    TTSProviderError,
    TTSRateLimitError,
    TTSValidationError,
)

GROK_TTS_URL = "https://api.x.ai/v1/tts"
GROK_VOICES = {"ara", "eve", "rex", "sal", "leo"}


class GrokProvider:
    """xAI Grok REST TTS provider."""

    name = "grok"
    capabilities = ProviderCapabilities(
        supports_prompt_director_notes=False,
        supports_inline_tags=True,
        supports_wrapping_tags=True,
        supports_voice_settings=False,
        supports_direct_mp3_44100=True,
    )

    def __init__(
        self,
        api_key: str | None = None,
        *,
        opener: Callable | None = None,
        endpoint: str = GROK_TTS_URL,
    ):
        self._api_key = api_key if api_key is not None else os.environ.get("XAI_API_KEY")
        self._opener = opener or urlopen
        self._endpoint = endpoint

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if not self._api_key:
            raise TTSAuthError("XAI_API_KEY is required for Grok TTS generation")
        if len(request.batch.speakers) != 1:
            raise TTSValidationError("Grok TTS requests must contain exactly one speaker")

        speaker_name = request.batch.speakers[0]
        speaker = request.speaker_configs[speaker_name]
        text = self._compile_text(request)
        payload = {
            "text": text,
            "voice_id": speaker.voice,
            "language": self._language_for_locale(request.locale),
            "output_format": {
                "codec": "mp3",
                "sample_rate": request.output_format.sample_rate,
                "bit_rate": request.output_format.bit_rate or 192000,
            },
        }
        response_bytes = self._post(payload)
        return SynthesisResult(
            audio_bytes=response_bytes,
            codec="mp3",
            sample_rate=request.output_format.sample_rate,
            channels=request.output_format.channels,
            provider_metadata={"voice_id": speaker.voice},
        )

    def _compile_text(self, request: SynthesisRequest) -> str:
        return "\n".join(compile_grok_segment_text(segment) for segment in request.batch.segments)

    def _post(self, payload: dict) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self._endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
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
        if exc.code == 401:
            raise TTSAuthError(f"Grok authentication failed: {message}") from exc
        if exc.code == 429:
            raise TTSRateLimitError(f"Grok rate limit exceeded: {message}") from exc
        if exc.code == 400:
            raise TTSValidationError(f"Grok request rejected: {message}") from exc
        if exc.code >= 500:
            raise TTSProviderError(f"Grok provider error {exc.code}: {message}") from exc
        raise TTSProviderError(f"Grok request failed with HTTP {exc.code}: {message}") from exc

    def _language_for_locale(self, locale: str) -> str:
        return "auto"


def _read_error_message(exc: HTTPError) -> str:
    try:
        data = exc.read()
    except Exception:
        data = b""
    if not data:
        return exc.reason or "no response body"
    return data.decode("utf-8", errors="replace")
