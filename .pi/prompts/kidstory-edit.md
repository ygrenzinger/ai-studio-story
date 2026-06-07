---
description: Edit an existing KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Edit Workflow
- Lunii Graph Requirements
- Build and Export Workflow
- Final Validation Checklist

Arguments: $ARGUMENTS

Find the target story or pack under `stories/`, inspect its `src/` files and
`story.json`, then make only the requested edits. Preview impact before
destructive or cascading changes.

Run a dry build when edits affect story graph, audio scripts, images, or
exportability:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
