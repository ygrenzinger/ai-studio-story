---
description: Build and export a KidStory to a Lunii-ready ZIP
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Build and Export Workflow
- Final Validation Checklist

Arguments: $ARGUMENTS

Start in plan mode. Resolve the target slug under `stories/`, inspect export
readiness with read-only checks as needed, summarize what build/export will do,
and stop for explicit user approval before running the full build.

After approval, run:

```bash
uv run python build_story.py stories/{slug}
```

Report the phase summary, generated/skipped counts, and generated ZIP path. If
the build fails, stop and report the recovery instruction from the command
output.
