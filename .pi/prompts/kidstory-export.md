---
description: Build and export a KidStory to a Lunii-ready ZIP
---

Read and follow `docs/agents/kidstory-skill.md`, especially:
- Build and Export Workflow
- Final Validation Checklist

Arguments: $ARGUMENTS

Start in plan mode. Resolve the target slug under `stories/`, but do not read
existing story content by default. Before explicit inspection/export approval,
only list paths and read minimal metadata such as `src/metadata.json`. Ask
permission before reading `story.json`, source files, generated assets, or ZIP
contents. Summarize what build/export will do from metadata and user-provided
details, then stop for explicit user approval before running the full build.

After approval, run:

```bash
uv run python build_story.py stories/{slug}
```

Report the phase summary, generated/skipped counts, and generated ZIP path. If
the build fails, stop and report the recovery instruction from the command
output.
