Agent for creating interactive audio stories for Lunii devices.

Always use `uv` to run Python scripts. Use `context7` MCP for library docs.

## Key CLI tools

- `uv run python generate_audio.py` - generate MP3 audio from audio-scripts
- `uv run python generate_cover.py` - generate pixel art BMP covers
- `uv run python generate_thumbnail.py` - generate 300x300 PNG story thumbnails
- `uv run python build_story.py stories/{name}` - validate, generate missing assets, and export
- `uv run python export_story.py stories/{name}` - export to Lunii-ready ZIP
- `uv run pytest` - run tests

## Package architecture

- `audio_generation/` - audio parsing, provider selection, TTS synthesis, processing, and MP3 verification
- `image_generation/` - Gemini image generation plus cover BMP and thumbnail PNG processing
- `story_export/` - story graph validation, deterministic UUID conversion, asset manifests, and ZIP export

Root scripts are backward-compatible wrappers around these packages.

## Story structure

Each story lives in `stories/{name}/` with:
- `story.json` - Lunii device story graph (the only required file)
- `thumbnail.png` - Pack thumbnail for library display
- `assets/` - generated `.bmp` covers and `.mp3` audio
- `src/` - source files (for editing/regeneration):
  - `metadata.json`, `outline.md`
  - `chapters/{nn-slug}/chapter.md` and `audio-script.md`
  - `characters/{name}.json`
  - For packs: `hub/` and `stories/` subdirectories


## Commands

Use Pi-compatible `/kidstory` commands for story workflows:
- `/kidstory-new` - create a new story
- `/kidstory-edit` - edit an existing story or pack
- `/kidstory-continue` - continue incomplete work
- `/kidstory-pack` - create a pack of related stories
- `/kidstory-export` - export to Lunii-ready ZIP

The Pi prompt templates live in `.pi/prompts/`. Shared agent instructions live in
`docs/agents/kidstory-skill.md`.

OpenCode command and subagent prompts are also available in `.opencode/` for
backward compatibility with the previous workflow.

## Asset generation by agent environment

Agents may write story source files directly. Do not delegate cover, thumbnail,
or audio generation to subagents by default in Pi/generic agent workflows. Use
`uv run python build_story.py stories/{name}` so validation, resumable asset
generation, verification, and ZIP export stay deterministic and testable.

When running the legacy OpenCode `.opencode/commands/kidstory-export.md`
workflow, follow its restored subagent instructions for `audio-generator`,
`cover-generator`, and `thumbnail-generator`.
