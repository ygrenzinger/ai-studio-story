---
description: Build and export a KidStory to a Lunii-ready ZIP
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Build and Export Workflow
- Final Validation Checklist

Arguments: $ARGUMENTS

Resolve the target slug under `stories/`, then run:

```bash
uv run python build_story.py stories/{slug}
```

Report the phase summary, generated/skipped counts, and generated ZIP path. If
the build fails, stop and report the recovery instruction from the command
output.
