"""General story export utilities."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")
