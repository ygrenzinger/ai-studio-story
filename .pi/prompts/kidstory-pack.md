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

Start in plan/interview mode. Treat arguments as a draft theme only, not as
approval to generate files. Ask the pack-level and per-story interview questions
in short batches, then present a concise pack plan with proposed slug, story
list, hub/menu behavior, characters, files to create, graph pattern, and dry-run
command. Stop and wait for explicit user approval before writing files.

After approval, create a related story pack with a hub menu. Generate
`src/metadata.json`, `src/outline.md`, `src/hub/*.md`,
`src/stories/*/{chapter.md,audio-script.md}`, character files, and `story.json`.

The hub scripts are mandatory: `cover-welcome.md`, `menu.md`,
`option-{name}.md` for every selectable story, and `welcome-back.md`.

Before final export or after structural changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
