"""Load the global portable voice registry."""

from pathlib import Path

import yaml

from audio_generation.voices.models import ProviderVoiceConfig, VoiceRole


class VoiceRegistry:
    """In-memory voice role registry."""

    def __init__(self, roles: dict[str, VoiceRole]):
        self.roles = roles

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceRegistry":
        if path is None:
            path = Path(__file__).resolve().parents[2] / "config" / "voice-map.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        roles: dict[str, VoiceRole] = {}
        for name, role_data in (data.get("roles") or {}).items():
            providers = {
                provider_name: ProviderVoiceConfig(
                    voice=provider_data["voice"],
                    model=provider_data.get("model"),
                    voice_settings=provider_data.get("voice_settings", {}) or {},
                )
                for provider_name, provider_data in (role_data.get("providers") or {}).items()
            }
            roles[name] = VoiceRole(
                name=name,
                description=role_data.get("description", ""),
                age=role_data.get("age", ""),
                tone=role_data.get("tone", ""),
                gender=role_data.get("gender", ""),
                providers=providers,
            )
        return cls(roles)

    def get(self, role: str) -> VoiceRole | None:
        return self.roles.get(role)
