# AI Studio Story

A Python toolkit for creating interactive audio stories for [Lunii](https://lunii.com/) storyteller devices. It covers the full production pipeline: AI-guided story writing, pixel art cover generation, multi-speaker audio synthesis, and packaging into device-ready archives.

## How It Works

The pipeline has four stages:

1. **Story Design** -- An AI-guided conversation (via Pi-compatible `/kidstory` prompts) walks you through choosing age range, language, theme, characters, and story structure. It generates an outline, chapters, character profiles, and audio scripts. Supports linear narratives, branching (choose-your-own-adventure), and hub-and-spoke story packs.

2. **Cover Image Generation** -- `generate_cover.py` takes a text description and produces a retro pixel art illustration using Gemini Flash 2.5 via Vertex AI. The image is automatically resized to 320x240, converted to 16-shade grayscale with Floyd-Steinberg dithering, and saved as a 4-bit BMP with RLE4 compression (the exact format the Lunii device expects).

3. **Audio Generation** -- `generate_audio.py` converts markdown audio scripts into MP3 files using Gemini TTS via Vertex AI. It supports multi-speaker scripts with per-character voice and emotion control, context-aware pauses, comfort noise, crossfades, and segment fade-in/out. Output is mono 44100 Hz MP3 with no ID3 tags (Lunii requirement). Includes resume capability for recovering from rate limits.

4. **Build and Export** -- `build_story.py` validates source files, generates missing covers, thumbnails, and audio assets, verifies every `story.json` asset reference, then assembles a Lunii-compatible ZIP archive. The export maps human-readable IDs to UUID v5 identifiers without modifying the source `story.json`.

## Tech Stack

| Component | Technology |
| --- | --- |
| Language | Python 3.11+ |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| LLM / Image generation | [Google Gemini](https://ai.google.dev/) via Vertex AI (`google-genai`) |
| Text-to-speech | Gemini 2.5 Flash Preview TTS (30 voices, multi-speaker) |
| Image processing | [Pillow](https://pillow.readthedocs.io/) |
| Audio processing | [pydub](https://github.com/jiaaro/pydub) + [FFmpeg](https://ffmpeg.org/) |
| Config parsing | [PyYAML](https://pyyaml.org/) |
| Testing | [pytest](https://docs.pytest.org/) |
| AI workflow | Pi-compatible prompt templates, generic agent instructions, and restored OpenCode prompts |

## Prerequisites

- **Python 3.11** or later
- **uv** -- [install instructions](https://docs.astral.sh/uv/getting-started/installation/)
- **FFmpeg** -- required by pydub for MP3 encoding
- **Google Cloud project** with Vertex AI API enabled
- **gcloud CLI** authenticated via `gcloud auth application-default login`
- **Pi Agent** -- install from the current instructions on [pi.dev](https://pi.dev/) or the [Pi Quickstart](https://pi.dev/docs/latest/quickstart)

### Installing FFmpeg

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt update && sudo apt install ffmpeg
```

On Windows, download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Getting Started

```bash
# Clone and enter the repo
git clone <repository-url>
cd ai-studio-story

# Install dependencies
uv sync
```

Configure Google Cloud for Gemini image and audio generation:

```bash
# Copy the env template and fill in your project ID
cp .env.example .env
# Edit .env:
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_CLOUD_REGION=us-central1

# Authenticate with Google Cloud
gcloud auth application-default login
```

Set up Pi Agent using the install flow documented on [pi.dev](https://pi.dev/)
or the [Pi Quickstart](https://pi.dev/docs/latest/quickstart), then start Pi
from this repository and authenticate it:

```bash
pi
# Inside Pi:
# /login
```

Run the local setup check:

```bash
uv run pytest
```

## Usage

### Create a story with Pi

Start Pi from the repository root:

```bash
cd ai-studio-story
pi
```

This repository provides Pi-compatible prompt templates in `.pi/prompts/`.
Pi loads project templates from `.pi/prompts/*.md` after the project is trusted;
see the [Pi prompt templates docs](https://pi.dev/docs/latest/prompt-templates)
for details.

Available story commands:

| Command | Description |
| --- | --- |
| `/kidstory new [topic]` or `/kidstory-new [topic]` | Create a new story through a guided interview |
| `/kidstory pack [theme]` or `/kidstory-pack [theme]` | Create a story pack (hub menu + multiple stories) |
| `/kidstory continue [name]` or `/kidstory-continue [name]` | Resume work on an incomplete story |
| `/kidstory edit [name]` or `/kidstory-edit [name]` | Edit an existing story |
| `/kidstory export [name]` or `/kidstory-export [name]` | Full build pipeline: validate, generate covers/audio/thumbnail, build ZIP |

Examples:

```text
/kidstory-new une aventure éducative sur le sommeil pour 6-8 ans
/kidstory-pack voyages autour du monde pour 7-8 ans
/kidstory-export grand-voyage-continents
```

The agent writes source files under `stories/{slug}/src/` and the Lunii graph
to `stories/{slug}/story.json`. Shared agent guidance lives in
`docs/agents/kidstory-skill.md`.

The previous OpenCode setup is also restored under `.opencode/commands/` and
`.opencode/agents/` for users who still run the OpenCode workflow. Pi and other
generic agents should prefer `docs/agents/kidstory-skill.md` plus
`build_story.py`.

### Build and export

Use the deterministic build command for final output:

```bash
uv run python build_story.py stories/{slug}
```

The build pipeline:

1. Validates source files and the `story.json` graph.
2. Generates missing BMP cover assets.
3. Generates `thumbnail.png` when missing.
4. Generates missing MP3 audio assets.
5. Verifies every asset referenced by `story.json`.
6. Creates the Lunii-ready ZIP archive.

Existing non-empty assets are skipped by default. Use `--force` only when you
want to regenerate them.

Useful build commands:

| Command | Description |
| --- | --- |
| `uv run python build_story.py --dry-run stories/{slug}` | Validate sources and print the asset plan without API calls |
| `uv run python build_story.py --skip-export stories/{slug}` | Generate and verify assets without writing the ZIP |
| `uv run python build_story.py --force stories/{slug}` | Regenerate assets even when files already exist |
| `uv run python build_story.py stories/{slug}` | Generate missing assets and export the ZIP |

### Story directory anatomy

Each story or pack uses this structure:

```text
stories/{slug}/
├── story.json              # Lunii graph, using source-friendly IDs
├── thumbnail.png           # Library thumbnail
├── assets/                 # Generated BMP and MP3 files
└── src/                    # Editable source material
    ├── metadata.json
    ├── outline.md
    ├── characters/
    ├── chapters/           # Single-story chapters
    ├── hub/                # Pack menu scripts
    └── stories/            # Pack story scripts
```

Single stories usually store chapters as:

```text
src/chapters/{nn-slug}/chapter.md
src/chapters/{nn-slug}/audio-script.md
```

Story packs usually store hub and story source files as:

```text
src/hub/cover-welcome.md
src/hub/menu.md
src/hub/option-{story}.md
src/hub/welcome-back.md
src/stories/{story-id}/chapter.md
src/stories/{story-id}/audio-script.md
```

### Setup verification and troubleshooting

Run these checks before generating paid or quota-backed assets:

```bash
# Python dependencies and tests
uv run pytest

# FFmpeg availability
ffmpeg -version

# Source and asset plan, no API calls
uv run python build_story.py --dry-run stories/grand-voyage-continents
```

To verify Pi prompt discovery, start `pi` from the repo root and type
`/kidstory`. The prompt should appear in autocomplete or expand when selected.

Common issues:

- Missing `GOOGLE_CLOUD_PROJECT`: set it in `.env` or the shell environment.
- Google auth failure: run `gcloud auth application-default login`.
- MP3 generation failure: confirm FFmpeg is installed and visible in `PATH`.
- Build planner reports a missing source script: update `story.json` or add the
  referenced `src/.../audio-script.md`.

### Advanced manual commands

The Pi workflow and `build_story.py` are the recommended path. These lower-level
commands are useful for debugging or regenerating one asset manually.

Generate audio from a script:

```bash
uv run python generate_audio.py stories/{slug}/src/chapters/01-intro/audio-script.md -o stories/{slug}/assets/story-01-intro.mp3
```

Audio options:

| Flag | Description |
| --- | --- |
| `-o, --output` | Output MP3 path (required unless `--dry-run-voices`) |
| `--provider` | TTS provider: `gemini`, `grok`, or `elevenlabs` |
| `--voice` | Override voice for all speakers (e.g. `Puck`, `Leda`) |
| `--resume` | Resume from saved progress after a failure |
| `--no-verify` | Skip MP3 format verification |
| `--no-progress` | Disable progress bar |
| `--dry-run-voices` | Print voice resolution without generating audio |
| `--debug` | Enable debug logging |

Generate a cover image:

```bash
uv run python generate_cover.py "A knight facing a dragon in a dark cave" -o cover.bmp
```

Generate a thumbnail:

```bash
uv run python generate_thumbnail.py "A colorful story thumbnail about a magical forest" -o thumbnail.png
```

Export an already-complete story without generating assets:

```bash
uv run python export_story.py stories/{slug}
```

## Available Voices

| Voice | Characteristic |
| --- | --- |
| Zephyr | Bright |
| Puck | Upbeat |
| Charon | Informative |
| Kore | Firm |
| Fenrir | Excitable |
| Leda | Youthful |
| Orus | Firm |
| Aoede | Breezy |
| Callirrhoe | Easy-going |
| Autonoe | Bright |
| Enceladus | Breathy |
| Iapetus | Clear |
| Umbriel | Easy-going |
| Algieba | Smooth |
| Despina | Smooth |
| Erinome | Clear |
| Algenib | Gravelly |
| Rasalgethi | Informative |
| Laomedeia | Upbeat |
| Achernar | Soft |
| Alnilam | Firm |
| Schedar | Even |
| Gacrux | Mature |
| Pulcherrima | Forward |
| Achird | Friendly |
| Zubenelgenubi | Casual |
| Vindemiatrix | Gentle |
| Sadachbia | Lively |
| Sadaltager | Knowledgeable |
| Sulafat | Warm |

## Project Structure

```
ai-studio-story/
├── generate_audio.py              # CLI: audio generation
├── generate_cover.py              # CLI: cover image generation
├── build_story.py                 # CLI: validate, generate assets, export ZIP
├── pyproject.toml                 # Project metadata and dependencies
├── .env.example                   # Environment variable template
├── audio_generation/              # Core audio generation package
│   ├── cli.py                     #   CLI argument parsing
│   ├── orchestrator.py            #   8-stage pipeline coordinator
│   ├── domain/                    #   Models and constants
│   ├── parsing/                   #   Markdown + YAML script parser
│   ├── batching/                  #   Provider-compatible segment batching
│   ├── tts/                       #   Gemini TTS client, config, prompts
│   ├── audio/                     #   Processing, effects, concatenation, export
│   ├── verification/              #   MP3 format validation
│   └── progress/                  #   Resume capability
├── stories/                       # Generated stories
│   ├── aventure-spatiale/         #   Complete example story
│   └── explorateur-croyances/     #   Story pack (in progress)
├── examples/                      # Example audio script markdown files
├── docs/                          # Architecture docs, format specs, templates
├── tests/                         # Unit, integration, and e2e tests
├── .pi/prompts/                   # Pi-compatible /kidstory prompt templates
├── .opencode/                     # Restored OpenCode commands and subagents
└── docs/agents/                   # Generic agent workflow instructions
```

## Running Tests

```bash
uv run pytest
```

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `GOOGLE_CLOUD_PROJECT` | Yes | Google Cloud project ID |
| `GOOGLE_CLOUD_REGION` | No | Vertex AI region (default: `us-central1`) |
| `GOOGLE_CLOUD_LOCATION` | No | Used by cover generation (default: `europe-west1`) |

## License

MIT
