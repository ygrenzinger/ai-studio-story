# AI Studio Story

A Python toolkit for creating interactive audio stories for [Lunii](https://lunii.com/) storyteller devices. It covers the full production pipeline: AI-guided story writing, pixel art cover generation, multi-speaker audio synthesis, and packaging into device-ready archives.

## How It Works

The pipeline has four stages:

1. **Story Design** -- An AI-guided conversation (via OpenCode `/kidstory` commands) walks you through choosing age range, language, theme, characters, and story structure. It generates an outline, chapters, character profiles, and audio scripts. Supports linear narratives, branching (choose-your-own-adventure), and hub-and-spoke story packs.

2. **Cover Image Generation** -- `generate_cover.py` takes a text description and produces a retro pixel art illustration using Gemini Flash 2.5 via Vertex AI. The image is automatically resized to 320x240, converted to 16-shade grayscale with Floyd-Steinberg dithering, and saved as a 4-bit BMP with RLE4 compression (the exact format the Lunii device expects).

3. **Audio Generation** -- `generate_audio.py` converts markdown audio scripts into MP3 files using Gemini TTS via Vertex AI. It supports multi-speaker scripts with per-character voice and emotion control, context-aware pauses, comfort noise, crossfades, and segment fade-in/out. Output is mono 44100 Hz MP3 with no ID3 tags (Lunii requirement). Includes resume capability for recovering from rate limits.

4. **Export** -- `export_pack.py` (per story) assembles all assets into a Lunii-compatible ZIP archive. It builds the story graph (`story.json`), maps human-readable IDs to UUID v5 identifiers, validates all references, and bundles BMP and MP3 assets.

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
| AI workflow | [OpenCode](https://opencode.ai/) commands and subagents |

## Prerequisites

- **Python 3.11** or later
- **uv** -- [install instructions](https://docs.astral.sh/uv/getting-started/installation/)
- **FFmpeg** -- required by pydub for MP3 encoding
- **Google Cloud project** with Vertex AI API enabled
- **gcloud CLI** authenticated via `gcloud auth application-default login`

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

# Copy the env template and fill in your project ID
cp .env.example .env
# Edit .env:
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GOOGLE_CLOUD_REGION=us-central1

# Authenticate with Google Cloud
gcloud auth application-default login
```

## Usage

### Generate audio from a script

```bash
uv run python generate_audio.py audio-scripts/chapter1.md -o chapter1.mp3
```

Options:

| Flag | Description |
| --- | --- |
| `-o, --output` | Output MP3 path (required) |
| `--voice` | Override voice for all speakers (e.g. `Puck`, `Leda`) |
| `--resume` | Resume from saved progress after a failure |
| `--no-verify` | Skip MP3 format verification |
| `--no-progress` | Disable progress bar |
| `--debug` | Enable debug logging |

### Generate a cover image

```bash
uv run python generate_cover.py "A knight facing a dragon in a dark cave" -o cover.bmp
```

Options:

| Flag | Description |
| --- | --- |
| `-o, --output` | Output BMP path (required) |
| `--debug` | Enable debug logging |

### AI-assisted story creation (OpenCode)

If you use [OpenCode](https://opencode.ai/), the project ships with `/kidstory` commands:

| Command | Description |
| --- | --- |
| `/kidstory new [topic]` | Create a new story through a guided interview |
| `/kidstory pack [theme]` | Create a story pack (hub menu + multiple stories) |
| `/kidstory continue [name]` | Resume work on an incomplete story |
| `/kidstory edit [name]` | Edit an existing story |
| `/kidstory export [name]` | Full export pipeline: validate, generate covers and audio, build ZIP |

### Export a story to Lunii archive

Each story under `stories/` has its own `export_pack.py`:

```bash
uv run python stories/aventure-spatiale/export_pack.py
```

This produces a ZIP archive ready to be loaded onto a Lunii device.

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
├── pyproject.toml                 # Project metadata and dependencies
├── .env.example                   # Environment variable template
├── audio_generation/              # Core audio generation package
│   ├── cli.py                     #   CLI argument parsing
│   ├── orchestrator.py            #   8-stage pipeline coordinator
│   ├── domain/                    #   Models and constants
│   ├── parsing/                   #   Markdown + YAML script parser
│   ├── batching/                  #   Segment batcher (max 2 speakers/batch)
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
└── .opencode/                     # AI agent commands and subagents
    ├── commands/                   #   /kidstory command definitions
    └── agents/                    #   audio-generator, cover-generator subagents
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
