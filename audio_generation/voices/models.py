"""Voice mapping domain models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderVoiceConfig:
    voice: str
    model: str | None = None
    voice_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceRole:
    name: str
    description: str = ""
    age: str = ""
    tone: str = ""
    gender: str = ""
    providers: dict[str, ProviderVoiceConfig] = field(default_factory=dict)


@dataclass
class ResolvedVoice:
    speaker: str
    role: str | None
    provider: str
    voice_id: str
    model: str | None = None
    voice_settings: dict[str, Any] = field(default_factory=dict)
    source: str = ""
