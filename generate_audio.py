#!/usr/bin/env python3
"""
Generate audio files from story chapters using Gemini TTS via Google AI Studio.

Converts audio-script markdown files to MP3 format with specific requirements:
- Format: MP3 (MPEG Audio Layer III)
- Channels: Mono (1 channel)
- Sample Rate: 44100 Hz
- ID3 Tags: NOT ALLOWED (must be stripped)

This version uses per-segment TTS generation with sequential batch processing,
supporting unlimited speakers by batching narrator + character pairs.

Usage:
    python generate_audio.py audio-scripts/stage-uuid.md -o output.mp3
    python generate_audio.py script.md -o output.mp3 --voice Puck
    python generate_audio.py script.md -o output.mp3 --debug --no-verify

Prerequisites:
    - Google AI Studio API key (supports multi-speaker TTS)
    - Get an API key at: https://aistudio.google.com/apikey
    - Environment variables: GOOGLE_API_KEY or GEMINI_API_KEY
    - FFmpeg installed on system (required by pydub)

NOTE: This is a backward-compatible wrapper. The implementation has been
refactored into the audio_generation package for better maintainability.
"""

from audio_generation.cli import main

if __name__ == "__main__":
    main()
