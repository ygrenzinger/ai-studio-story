---
description: Edit an existing KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Edit Workflow
- Lunii Graph Requirements
- Build and Export Workflow
- Final Validation Checklist

Arguments: $ARGUMENTS

Start in plan/interview mode. Find the target story or pack under `stories/`,
but do not read existing story content by default. Before explicit inspection
approval, only list paths and read minimal metadata such as `src/metadata.json`.
Ask permission before reading `story.json`, outlines, chapters, hub scripts,
audio scripts, or character files. Then ask focused clarification questions and
present a concise edit plan with files to change, graph impact, validation
command, and risks. Stop and wait for explicit user approval before writing
files.

After approval, make only the requested edits. Preview impact before destructive
or cascading changes.

Run a dry build when edits affect story graph, audio scripts, images, or
exportability:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
