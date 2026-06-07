---
description: Create a new KidStory pack
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Role and Tone
- Pack Creation
- Audio Script Requirements
- Lunii Graph Requirements
- Final Validation Checklist

Arguments: $ARGUMENTS

Create a related story pack with a hub menu. Generate `src/metadata.json`,
`src/outline.md`, `src/hub/*.md`, `src/stories/*/{chapter.md,audio-script.md}`,
character files, and `story.json`.

The hub scripts are mandatory: `cover-welcome.md`, `menu.md`,
`option-{name}.md` for every selectable story, and `welcome-back.md`.

Before final export or after structural changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
