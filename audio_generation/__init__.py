"""Audio Generation Pipeline - Domain-oriented TTS audio generation."""

__all__ = ["AudioGenerationPipeline"]
__version__ = "1.0.0"


def __getattr__(name: str):
    if name == "AudioGenerationPipeline":
        from audio_generation.orchestrator import AudioGenerationPipeline

        return AudioGenerationPipeline
    raise AttributeError(name)
