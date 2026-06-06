"""Domain models for story export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    """A validation finding for a source story."""

    severity: str
    message: str
    path: str = "story.json"

    @property
    def is_error(self) -> bool:
        return self.severity.upper() == "ERROR"


@dataclass(frozen=True)
class AssetManifest:
    """Assets referenced by a story graph."""

    images: set[str] = field(default_factory=set)
    audios: set[str] = field(default_factory=set)

    @property
    def all_assets(self) -> set[str]:
        return set(self.images) | set(self.audios)


@dataclass(frozen=True)
class ExportResult:
    """Result of a successful Lunii archive export."""

    zip_path: Path
    pack_uuid: str
    archive_size: int
    title: str
    stage_count: int
    action_count: int
    manifest: AssetManifest
    has_thumbnail: bool
    used_thumbnail_fallback: bool = False

    @property
    def total_files(self) -> int:
        thumbnail_count = 1 if self.has_thumbnail or self.used_thumbnail_fallback else 0
        return 1 + thumbnail_count + len(self.manifest.images) + len(self.manifest.audios)
