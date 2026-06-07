---
description: Route KidStory creation, editing, continuation, and export tasks
---

Read and follow `docs/agents/kidstory-skill.md`.

Arguments: $ARGUMENTS

Route the request:

- `new [topic]`: create a new single story.
- `pack [theme]`: create a story pack with a hub menu.
- `continue [slug]`: resume incomplete work.
- `edit [slug]`: modify an existing story or pack.
- `export [slug]`: run `uv run python build_story.py stories/{slug}`.
- no arguments: list available entries in `stories/` and ask what to do next.

Prefer the repository's `stories/{slug}/src/` layout. Asset generation and ZIP
creation must go through `build_story.py`.

When routing to a workflow, follow the corresponding detailed section in
`docs/agents/kidstory-skill.md`; do not rely only on this router summary.
