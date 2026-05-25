#!/usr/bin/env python3
"""Export this pack using the repository-level Lunii exporter."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import export_story

if __name__ == "__main__":
    sys.argv = [sys.argv[0], str(Path(__file__).resolve().parent)]
    export_story.main()
