---
description: Continue an incomplete KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Continue Workflow
- Story Layout
- Pack Creation when resuming packs
- Final Validation Checklist

Arguments: $ARGUMENTS

Start in plan/interview mode. Resume an incomplete story or pack by inspecting
`src/metadata.json`, `src/outline.md`, existing chapters, audio scripts, and
`story.json`. Summarize title, status, completed work, gaps, and the proposed
resume plan. Ask only the missing or high-impact questions; do not re-ask
answered interview questions unless the user wants to change direction. Stop and
wait for explicit user approval before writing files.

After approval, continue from the first incomplete source, graph, or validation
gap.

After source or graph changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
