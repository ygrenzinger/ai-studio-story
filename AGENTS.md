Agent for creating interactive audio stories for Lunii devices.

Always use `uv` to run Python scripts. Use `context7` MCP for library docs.

## Key CLI tools

- `uv run python generate_audio.py` - generate MP3 audio from audio-scripts
- `uv run python generate_cover.py` - generate pixel art BMP covers
- `uv run python generate_thumbnail.py` - generate 300x300 PNG story thumbnails
- `uv run pytest` - run tests

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

Use `/kidstory` commands for story workflows:
- `/kidstory-new` - create a new story
- `/kidstory-edit` - edit an existing story or pack
- `/kidstory-continue` - continue incomplete work
- `/kidstory-pack` - create a pack of related stories
- `/kidstory-export` - export to Lunii-ready ZIP

## Subagents

When generating audio, cover, or thumbnail assets, delegate to the appropriate subagent via the Task tool:
- audio-generator: converts audio-script .md files into MP3 audio files
- cover-generator: converts chapter descriptions into pixel art BMP cover images
- thumbnail-generator: generates 300x300 PNG thumbnails for stories and packs