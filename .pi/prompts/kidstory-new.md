---
description: Create a new single KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Role and Tone
- Single Story Creation
- Audio Script Requirements
- Lunii Graph Requirements
- Final Validation Checklist

Arguments: $ARGUMENTS

Create a new single story through the guided interview. Generate
`src/metadata.json`, `src/outline.md`, chapter files, character files,
audio scripts, and `story.json` using the canonical `stories/{slug}/src/`
layout. Present the outline for approval before generating final content unless
the user explicitly asks for quick mode.

Before final export or after structural changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
