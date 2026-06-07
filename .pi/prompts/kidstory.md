---
description: Route KidStory creation, editing, continuation, and export tasks
---

Read and follow `docs/agents/kidstory-skill.md`.

Arguments: $ARGUMENTS

Route the request, but every route starts in plan/interview mode. Arguments are
hints for a draft brief, not approval to act. To preserve context, do not read
existing story content by default; only list paths and read minimal metadata
until the user explicitly asks for content inspection. Ask focused questions,
present a concise plan, and wait for explicit approval before reading existing
story content, writing files, changing `story.json`, generating assets, or
exporting.

- `new [topic]`: plan a new single story through an interview before creating.
- `pack [theme]`: plan a story pack with a hub menu through an interview before creating.
- `continue [slug]`: use metadata only, ask to inspect content, then propose a resume plan before continuing.
- `edit [slug]`: use metadata only, ask to inspect content, then propose an edit plan before modifying.
- `export [slug]`: use metadata only, ask for approval, then run `uv run python build_story.py stories/{slug}`.
- no arguments: list available entries in `stories/` and ask what to do next.

Prefer the repository's `stories/{slug}/src/` layout. Asset generation and ZIP
creation must go through `build_story.py`.

When routing to a workflow, follow the corresponding detailed section in
`docs/agents/kidstory-skill.md`; do not rely only on this router summary.
