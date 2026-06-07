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

Start in plan/interview mode. Treat arguments as a draft topic only, not as
approval to generate files. Ask the guided interview questions in short batches,
then present a concise creation plan with proposed slug, outline, files to
create, graph pattern, and dry-run command. Stop and wait for explicit user
approval before writing files.

After approval, create a new single story. Generate `src/metadata.json`,
`src/outline.md`, chapter files, character files, audio scripts, and `story.json`
using the canonical `stories/{slug}/src/` layout. Present the outline for
approval before generating final content unless it was already approved in plan
mode or the user explicitly asks for quick mode.

Before final export or after structural changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
