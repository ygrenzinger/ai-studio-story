---
description: Continue an incomplete KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Continue Workflow
- Story Layout
- Pack Creation when resuming packs
- Final Validation Checklist

Arguments: $ARGUMENTS

Start in plan/interview mode. Resolve the target story or pack, but do not read
existing story content by default. Before explicit inspection approval, only list
paths and read minimal metadata such as `src/metadata.json`. Ask permission
before reading `story.json`, outlines, chapters, hub scripts, audio scripts, or
character files. After approval, inspect only the necessary files, summarize
title, status, completed work, gaps, and the proposed resume plan. Ask only the
missing or high-impact questions; do not re-ask answered interview questions
unless the user wants to change direction. Stop and wait for explicit user
approval before writing files.

After approval, continue from the first incomplete source, graph, or validation
gap.

After source or graph changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
