# Part 1: Generic Provider Foundation With Gemini

## Goal

Refactor the current Gemini-specific audio generation path into a generic provider pipeline while keeping Gemini usable as the first provider. This part also introduces structured performance directions and voice mapping because later providers depend on both.

Part 1 is allowed to improve the current Gemini implementation, not just preserve it. Improvements must remain compatible with existing audio scripts and must be covered by tests.

## Target Code Layout

```text
audio_generation/
  providers/
    __init__.py
    base.py
    registry.py
    gemini.py
  emotion/
    __init__.py
    taxonomy.py
    normalizer.py
  voices/
    __init__.py
    models.py
    registry.py
    resolver.py
config/
  voice-map.yaml
tests/unit/
  test_provider_registry.py
  test_performance_direction_normalizer.py
  test_voice_resolver.py
  test_gemini_provider.py
```

## Slice 1.1: Provider Protocol And Gemini Wrapper

### User Value

The CLI still generates audio with Gemini, but the implementation now calls a generic provider interface. This unlocks later providers without rewriting the orchestration again.

### Changes

Add `audio_generation/providers/base.py`:

```python
@dataclass
class AudioFormat:
    codec: str = "mp3"
    sample_rate: int = 44100
    channels: int = 1
    bit_rate: int | None = None

@dataclass
class ProviderCapabilities:
    max_speakers_per_request: int
    supports_prompt_director_notes: bool
    supports_inline_tags: bool
    supports_wrapping_tags: bool
    supports_voice_settings: bool
    supports_direct_mp3_44100: bool

@dataclass
class SynthesisRequest:
    script: AudioScript
    batch: SegmentBatch
    speaker_configs: dict[str, SpeakerConfig]
    character_profiles: dict[str, CharacterProfile]
    locale: str
    output_format: AudioFormat

@dataclass
class SynthesisResult:
    audio_bytes: bytes
    codec: str
    sample_rate: int | None = None
    channels: int | None = None
    request_id: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)

class TTSProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...
```

Add `audio_generation/providers/gemini.py`:

```text
GeminiProvider wraps the current TTSClient, SpeechConfigBuilder, and TTSPromptBuilder.
```

Update `AudioGenerationPipeline`:

```text
Replace direct TTSClient usage with a TTSProvider dependency.
Keep the current Gemini code path available through GeminiProvider.
```

### Tests

Add unit tests proving:

```text
GeminiProvider receives a batch and returns SynthesisResult.
Pipeline can execute with a fake provider.
Existing parser and batcher tests still pass.
```

### Acceptance Criteria

```text
uv run pytest passes.
generate_audio.py still works for existing Gemini scripts.
No Grok or ElevenLabs code exists yet.
Provider abstractions are used by the pipeline.
```

## Slice 1.2: CLI Provider Selection For Gemini

### User Value

Users can explicitly select the current provider:

```bash
uv run python generate_audio.py script.md -o output.mp3 --provider gemini
```

### Changes

Add `audio_generation/providers/registry.py`:

```python
def create_provider(name: str, *, model: str | None = None) -> TTSProvider:
    ...
```

Update `audio_generation/cli.py`:

```text
Add --provider with choices initially limited to gemini.
Keep default provider gemini.
Keep existing --model behavior for Gemini.
```

### Tests

```text
Provider registry returns GeminiProvider for gemini.
Unknown provider fails with a clear error.
CLI parser accepts --provider gemini.
```

### Acceptance Criteria

```text
Existing command without --provider still works.
Command with --provider gemini works.
Unknown provider does not fail late during generation; it fails during argument/config setup.
```

## Slice 1.3: Structured Performance Direction Foundation

### User Value

Writers can keep using `<emotion: ...>`, but the pipeline now stores structured direction data that can later compile into Gemini notes, Grok tags, or ElevenLabs v3 tags.

### Changes

Add `audio_generation/emotion/taxonomy.py`:

```text
Canonical emotion, delivery, vocal event, pace, volume, pitch, and intensity values.
Synonym maps for common script descriptors.
```

Add `audio_generation/emotion/normalizer.py`:

```python
def normalize_performance_direction(raw: str) -> PerformanceDirection:
    ...
```

Update `audio_generation/domain/models.py`:

```python
@dataclass
class PerformanceDirection:
    raw: str = ""
    emotion: list[str] = field(default_factory=list)
    delivery: list[str] = field(default_factory=list)
    vocal_events: list[str] = field(default_factory=list)
    pace: str | None = None
    volume: str | None = None
    pitch: str | None = None
    intensity: str | None = None
    pause_before_ms: int | None = None
    pause_after_ms: int | None = None
```

Update `Segment`:

```python
direction: PerformanceDirection = field(default_factory=PerformanceDirection)
```

Update parser:

```text
Continue filling Segment.emotion for compatibility.
Also fill Segment.direction from the normalized raw marker.
```

### Tests

```text
"whispered, nervous" -> delivery whispering, emotion nervous.
"laughing, excited" -> vocal event laugh, emotion excited.
"slow, soft" -> pace slow, volume soft.
Parser preserves Segment.emotion and adds Segment.direction.
```

### Acceptance Criteria

```text
Existing scripts parse unchanged.
Existing tests that inspect Segment.emotion still pass.
New direction object is available to provider compilers.
```

## Slice 1.4: Gemini Prompt Compiler Uses Structured Directions

### User Value

Gemini output gets more consistent because performance directions are normalized before being written into Director's Notes.

### Changes

Update `audio_generation/tts/prompt_builder.py` or move Gemini-specific prompt code into `audio_generation/providers/gemini.py`.

Recommended path:

```text
Keep TTSPromptBuilder for now, but make it consume Segment.direction where available.
Later providers should not use TTSPromptBuilder directly.
```

Rules:

```text
Transcript remains clean.
Director's Notes use canonical direction wording.
Unknown raw descriptors may be included only in Gemini Director's Notes.
Pause metadata is not written as text if it will be handled by post-processing.
```

Example:

```text
Make Leo sound nervous and whispering, with a slow pace.
```

### Tests

```text
Prompt transcript has no <emotion: ...> marker.
Prompt transcript has no provider tags.
Director's Notes include canonical direction terms.
Unknown descriptor fallback is Gemini-only.
```

### Acceptance Criteria

```text
Gemini prompt generation still works.
Gemini prompt output is cleaner and deterministic for normalized directions.
```

## Slice 1.5: Voice Mapping Models And Global Registry

### User Value

Scripts can use portable voice roles instead of provider-specific voice names. This is required before Grok and ElevenLabs can use the same scripts.

### Changes

Add `audio_generation/voices/models.py`:

```python
@dataclass
class ProviderVoiceConfig:
    voice: str
    model: str | None = None
    voice_settings: dict[str, Any] = field(default_factory=dict)

@dataclass
class VoiceRole:
    name: str
    description: str = ""
    age: str = ""
    tone: str = ""
    gender: str = ""
    providers: dict[str, ProviderVoiceConfig] = field(default_factory=dict)

@dataclass
class ResolvedVoice:
    speaker: str
    role: str | None
    provider: str
    voice_id: str
    model: str | None = None
    voice_settings: dict[str, Any] = field(default_factory=dict)
    source: str = ""
```

Add `config/voice-map.yaml` with initial roles:

```text
warm_narrator
clear_narrator
playful_child
gentle_child
wise_mentor
mysterious_guide
gruff_creature
energetic_adventurer
calm_teacher
soft_bedtime
```

Use real Gemini and Grok built-in candidates where known. Use placeholder ElevenLabs IDs until account-specific IDs are provided.

### Tests

```text
Registry loads config/voice-map.yaml.
Known roles resolve for Gemini.
Unknown roles produce clear errors in strict mode.
Placeholder ElevenLabs voices do not affect Gemini tests.
```

### Acceptance Criteria

```text
Global voice map loads without requiring external API calls.
Gemini can resolve voices from voiceRole.
Legacy speakers[].voice still works.
```

## Slice 1.6: Story-Level Voice Overrides

### User Value

Individual stories can override voice roles per provider without changing the global voice registry.

### Changes

Extend `SpeakerConfig`:

```python
@dataclass
class SpeakerConfig:
    name: str
    voice: str = DEFAULT_VOICE
    voice_role: str | None = None
    provider_voices: dict[str, str] = field(default_factory=dict)
    provider_settings: dict[str, dict[str, Any]] = field(default_factory=dict)
```

Parser supports:

```yaml
speakers:
  - name: Narrator
    voiceRole: warm_narrator
    voices:
      gemini: Sulafat
      grok: ara
    providerSettings:
      elevenlabs:
        voice_settings:
          stability: 0.6
```

Add `audio_generation/voices/resolver.py`:

```python
def resolve_voice(speaker: SpeakerConfig, provider: str, registry: VoiceRegistry, *, strict: bool) -> ResolvedVoice:
    ...
```

Resolution order:

```text
1. speakers[].voices[provider]
2. speakers[].voice if valid for provider or legacy Gemini mode
3. voice-map.yaml role provider voice
4. provider default voice in permissive mode
5. fail in strict mode
```

### Tests

```text
Story provider override wins over registry.
Legacy voice wins when no voiceRole exists.
voiceRole resolves from registry.
Strict mode fails on missing role.
Permissive mode falls back to provider default.
ResolvedVoice.source reports where the voice came from.
```

### Acceptance Criteria

```text
Existing scripts with voice still work.
New scripts with voiceRole work for Gemini.
Provider override format is parsed and tested.
```

## Slice 1.7: Dry-Run Voice Resolution

### User Value

Users can inspect speaker-to-provider voice mapping before spending API calls.

### Changes

Add CLI:

```bash
uv run python generate_audio.py script.md --provider gemini --dry-run-voices
```

Output:

```text
Selected provider: gemini

Speaker resolution:
  Narrator
    role: warm_narrator
    voice: Sulafat
    source: registry.roles.warm_narrator.providers.gemini.voice
```

### Tests

```text
Dry-run voice command parses script but does not call provider.
Output contains speaker, role, voice, and source.
Missing voices show warning or error according to validation mode.
```

### Acceptance Criteria

```text
Dry-run command exits successfully without generating audio.
No network calls are made.
```

## Slice 1.8: Provider-Aware Batching Foundation

### User Value

The pipeline can batch differently per provider. Gemini keeps max-2-speaker batching, while later providers can force one speaker per request.

### Changes

Update or replace `SegmentBatcher`:

```python
class ProviderAwareSegmentBatcher:
    def batch(self, segments: list[Segment], capabilities: ProviderCapabilities) -> list[SegmentBatch]:
        ...
```

For Gemini:

```text
Keep current narrator plus character batching behavior.
Respect capabilities.max_speakers_per_request = 2.
```

### Tests

```text
Gemini batching matches current expected behavior.
One-speaker capability splits on speaker changes.
No batch exceeds provider max speakers.
```

### Acceptance Criteria

```text
Gemini generation still works.
Provider-aware batching can support Grok and ElevenLabs without changing the pipeline again.
```

## Part 1 Final Acceptance

```text
uv run pytest passes.
uv run python generate_audio.py script.md -o output.mp3 still defaults to Gemini.
uv run python generate_audio.py script.md -o output.mp3 --provider gemini works.
uv run python generate_audio.py script.md --provider gemini --dry-run-voices works without API calls.
Existing audio scripts are backward-compatible.
New voiceRole scripts work for Gemini.
```
