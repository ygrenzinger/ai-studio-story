---
description: Continue an incomplete KidStory
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Continue Workflow
- Story Layout
- Pack Creation when resuming packs
- Final Validation Checklist

Arguments: $ARGUMENTS

Resume an incomplete story or pack by inspecting `src/metadata.json`,
`src/outline.md`, existing chapters, audio scripts, and `story.json`. Continue
from the first incomplete source, graph, or validation gap. Do not re-ask
answered interview questions unless the user wants to change direction.

After source or graph changes, run:

```bash
uv run python build_story.py --dry-run stories/{slug}
```
