# Gemini TTS CLI

A command-line application that converts text to speech using Google's Gemini 2.5 TTS API and outputs MP3 or WAV audio files.

## Features

- Convert text to natural-sounding speech using 30 different voices
- Support for style prompts to control tone and delivery
- Output in MP3 or WAV format
- Configurable MP3 bitrate (64-320 kbps)
- Read text from command line, file, or stdin

## Prerequisites

- **Python 3.11** or later
- **uv** - Python package manager ([install instructions](https://docs.astral.sh/uv/getting-started/installation/))
- **FFmpeg** - Required for MP3 encoding ([install instructions](https://ffmpeg.org/download.html))
- **Gemini API Key** - Get yours at [Google AI Studio](https://aistudio.google.com/apikey)

### Installing FFmpeg

**macOS (Homebrew):**

```bash
brew install ffmpeg
```

**Linux (apt):**

```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**

Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd ai-studio-story
   ```

2. Set your API key:

   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Run the application:
   ```bash
   uv run gemini-tts --help
   ```

## Usage

### Basic Usage

```bash
# Simple text-to-speech
uv run gemini-tts --text "Hello, welcome to Gemini TTS!"

# Or after installing globally
gemini-tts --text "Hello, world!"
```

### Command-Line Options

| Option          | Short | Description                          | Default    |
| --------------- | ----- | ------------------------------------ | ---------- |
| `--text`        | `-t`  | Text to convert (use `-` for stdin)  | -          |
| `--file`        | `-f`  | Input text file path                 | -          |
| `--output`      | `-o`  | Output audio file path               | output.mp3 |
| `--voice`       | `-v`  | Voice name to use                    | Kore       |
| `--style`       | `-s`  | Style prompt for tone control        | -          |
| `--format`      | `-F`  | Output format: mp3 or wav            | mp3        |
| `--bitrate`     | `-b`  | MP3 bitrate (64, 128, 192, 256, 320) | 128        |
| `--list-voices` | `-l`  | List all available voices            | -          |
| `--quiet`       | `-q`  | Suppress progress output             | -          |
| `--debug`       |       | Enable debug logging                 | -          |
| `--help`        | `-h`  | Show help message                    | -          |
| `--version`     |       | Show version                         | -          |

### Examples

```bash
# With voice selection
uv run gemini-tts --text "Breaking news from around the world" --voice Charon

# With style prompt
uv run gemini-tts --text "Your order has been shipped!" --style "excited and friendly"

# Custom output file and bitrate
uv run gemini-tts --text "Premium quality audio" --output premium.mp3 --bitrate 320

# WAV output
uv run gemini-tts --text "Uncompressed audio" --format wav --output raw.wav

# From file
uv run gemini-tts --file script.txt --voice Puck --output podcast.mp3

# From stdin
cat article.txt | uv run gemini-tts --text - --output article.mp3

# List available voices
uv run gemini-tts --list-voices
```

## Available Voices

| Voice         | Characteristic |
| ------------- | -------------- |
| Zephyr        | Bright         |
| Puck          | Upbeat         |
| Charon        | Informative    |
| Kore          | Firm           |
| Fenrir        | Excitable      |
| Leda          | Youthful       |
| Orus          | Firm           |
| Aoede         | Breezy         |
| Callirrhoe    | Easy-going     |
| Autonoe       | Bright         |
| Enceladus     | Breathy        |
| Iapetus       | Clear          |
| Umbriel       | Easy-going     |
| Algieba       | Smooth         |
| Despina       | Smooth         |
| Erinome       | Clear          |
| Algenib       | Gravelly       |
| Rasalgethi    | Informative    |
| Laomedeia     | Upbeat         |
| Achernar      | Soft           |
| Alnilam       | Firm           |
| Schedar       | Even           |
| Gacrux        | Mature         |
| Pulcherrima   | Forward        |
| Achird        | Friendly       |
| Zubenelgenubi | Casual         |
| Vindemiatrix  | Gentle         |
| Sadachbia     | Lively         |
| Sadaltager    | Knowledgeable  |
| Sulafat       | Warm           |

## Environment Variables

| Variable         | Description         | Required |
| ---------------- | ------------------- | -------- |
| `GOOGLE_API_KEY` | Your Gemini API key | Yes      |

## Style Prompts

You can control the speech style using natural language prompts:

```bash
# Emotional styles
uv run gemini-tts --text "I have amazing news!" --style "excited and energetic"
uv run gemini-tts --text "I'm sorry for your loss" --style "soft and sympathetic"

# Professional styles
uv run gemini-tts --text "Welcome to our webinar" --style "professional and confident"
uv run gemini-tts --text "The earnings report shows..." --style "formal and measured"

# Character styles
uv run gemini-tts --text "Once upon a time..." --style "storytelling, slow and dramatic"
uv run gemini-tts --text "Breaking news!" --style "urgent news anchor"
```

## Troubleshooting

### API Key Not Set

```
TTS Error: No API key provided. Set GOOGLE_API_KEY environment variable or pass api_key parameter.
```

**Solution:** Set the environment variable:

```bash
export GOOGLE_API_KEY=your_api_key_here
```

### Invalid Voice

```
Error: Invalid value for '-v' / '--voice': Invalid voice: InvalidVoice. Use --list-voices to see available voices.
```

**Solution:** Use `--list-voices` to see valid voice names.

### Text Too Long

```
TTS Error: Text exceeds maximum length of 8000 characters.
```

**Solution:** Split your text into smaller chunks.

### Rate Limit Exceeded

```
TTS Error: Rate limit exceeded. Please try again later.
```

**Solution:** Wait a few seconds before retrying.

### FFmpeg Not Found

```
Conversion Error: Failed to convert to MP3: ...
```

**Solution:** Install FFmpeg and ensure it's in your PATH.

## Project Structure

```
ai-studio-story/
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── gemini_tts/
│   ├── __init__.py             # Package init
│   ├── cli.py                  # CLI entry point (Click)
│   ├── models.py               # Voice, AudioFormat, Bitrate, ExitCode
│   ├── voices.py               # Voice definitions
│   ├── exceptions.py           # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tts_service.py      # Gemini TTS implementation
│   │   └── audio_converter.py  # MP3/WAV conversion
│   └── utils/
│       ├── __init__.py
│       └── wav_utils.py        # WAV file utilities
└── docs/                       # Documentation
```

## Technical Details

- **Audio Format:** 24kHz, 16-bit, mono PCM (converted to MP3/WAV)
- **Maximum Text Length:** 8000 characters
- **Model:** gemini-2.5-flash-preview-tts

## Exit Codes

| Code | Description                            |
| ---- | -------------------------------------- |
| 0    | Success                                |
| 1    | Invalid arguments or user error        |
| 2    | API error (authentication, rate limit) |
| 3    | File I/O error                         |
| 4    | Audio conversion error                 |

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
