# Part 3: ElevenLabs v3 Provider

## Goal

Add ElevenLabs as the third provider, starting with Eleven v3 only. The first ElevenLabs slice should prioritize expressive v3 audio tags, one speaker per request, environment-variable credentials, voice settings, and final Lunii MP3 normalization.

Non-v3 models, request stitching, and ElevenLabs Text to Dialogue are intentionally deferred.

## Target Code Layout

```text
audio_generation/
  providers/
    elevenlabs.py
  emotion/
    elevenlabs_v3_tags.py
tests/unit/
  test_elevenlabs_provider.py
  test_elevenlabs_v3_compiler.py
  test_elevenlabs_voice_settings.py
```

## Assumptions

| Area | Decision |
| --- | --- |
| API | Use standard ElevenLabs text-to-speech endpoint for v3 model first. |
| Model | First implementation is `eleven_v3` only. |
| Credentials | Read `ELEVENLABS_API_KEY` from the environment. |
| Voices | Use resolved ElevenLabs `voice_id` from story override or voice registry. |
| Output | Request `mp3_44100_128` initially. Still run final export and verification. |
| Speakers | One speaker per request. Split on speaker changes. |
| Emotion | Compile to Eleven v3 audio tags only. |

## Slice 3.1: ElevenLabs v3 Provider Skeleton And Registry

### User Value

`--provider elevenlabs` becomes recognized, but first-generation support is explicitly v3-only.

### Changes

Add `audio_generation/providers/elevenlabs.py`:

```python
class ElevenLabsProvider:
    name = "elevenlabs"
    capabilities = ProviderCapabilities(
        max_speakers_per_request=1,
        supports_prompt_director_notes=False,
        supports_inline_tags=True,
        supports_wrapping_tags=False,
        supports_voice_settings=True,
        supports_direct_mp3_44100=True,
    )
```

Update provider registry:

```text
create_provider("elevenlabs") returns ElevenLabsProvider.
```

Update CLI:

```text
--provider choices include gemini, grok, elevenlabs.
--model eleven_v3 is required or defaulted when provider is elevenlabs.
If provider is elevenlabs and model is not eleven_v3, fail with a clear v3-only message.
```

### Tests

```text
Provider registry returns ElevenLabsProvider.
CLI accepts --provider elevenlabs --model eleven_v3.
CLI rejects --provider elevenlabs --model eleven_multilingual_v2 for now.
Dry-run voices does not require ELEVENLABS_API_KEY.
```

### Acceptance Criteria

```text
ElevenLabs provider is selectable.
v3-only limitation is explicit and tested.
```

## Slice 3.2: ElevenLabs REST Client With Fake HTTP Tests

### User Value

The pipeline can call ElevenLabs v3 and receive audio bytes through the provider interface.

### Changes

Implement request shape:

```text
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128
```

Payload:

```json
{
  "text": "[whispers] I hear something.",
  "model_id": "eleven_v3",
  "voice_settings": {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.45,
    "speed": 1.0,
    "use_speaker_boost": true
  }
}
```

Error mapping:

```text
401/403 -> TTSAuthError
422 -> TTSValidationError
429 -> TTSRateLimitError
5xx -> retryable provider error
```

### Tests

```text
Fake HTTP success returns SynthesisResult.
Payload includes model_id eleven_v3.
Payload includes voice_settings when resolved.
Request URL includes voice_id and output_format.
401/403/422/429/500 map to normalized provider errors.
```

### Acceptance Criteria

```text
ElevenLabsProvider.synthesize is tested without network.
Credentials are read only for real generation.
```

## Slice 3.3: Eleven v3 Emotion Tag Compiler

### User Value

KidStory emotion markers produce expressive Eleven v3 tags while keeping provider-specific syntax out of canonical scripts.

### Changes

Add `audio_generation/emotion/elevenlabs_v3_tags.py`.

Initial allowlist:

```text
Vocal events:
  laugh -> [laughs]
  chuckle -> [chuckles]
  giggle -> [giggles]
  sigh -> [sighs]
  inhale -> [inhales]
  exhale -> [exhales]

Delivery/emotion tags:
  whispering -> [whispers]
  sarcastic -> [sarcastic]
  curious -> [curious]
  excited -> [excited]
  crying -> [crying]
  playful -> [mischievously]
```

Compile examples:

```text
<emotion: whispering, nervous> I hear something.
  -> [whispers] I hear something.

<emotion: excited, laughing> We found it!
  -> [excited] [laughs] We found it!

<emotion: curious> What is this?
  -> [curious] What is this?
```

Unsupported descriptors:

```text
Do not emit unknown bracket tags.
Prefer punctuation or no-op.
Never add prose like "she said sadly" in v3 compiler.
```

### Tests

```text
Whisper compiles to [whispers].
Laugh compiles to [laughs].
Curious compiles to [curious].
Unsupported descriptor is dropped.
Compiler never emits raw unknown bracket tags.
Compiler does not alter spoken words except provider tags and safe punctuation.
```

### Acceptance Criteria

```text
Eleven v3 tags compile safely from PerformanceDirection.
Canonical script syntax remains provider-neutral.
```

## Slice 3.4: Voice Settings Resolution

### User Value

ElevenLabs voices can be tuned per role and per story without hardcoding settings in the provider.

### Changes

Use `ResolvedVoice.voice_settings` from Part 1.

Merge order:

```text
1. Story providerSettings.elevenlabs.voice_settings
2. Voice role provider voice_settings
3. ElevenLabs provider defaults
```

Initial defaults:

```json
{
  "stability": 0.35,
  "similarity_boost": 0.75,
  "style": 0.35,
  "speed": 1.0,
  "use_speaker_boost": true
}
```

Validation:

```text
stability: 0.0 to 1.0
similarity_boost: 0.0 to 1.0
style: 0.0 to 1.0
speed: 0.7 to 1.2
use_speaker_boost: boolean
```

### Tests

```text
Story settings override registry settings.
Registry settings override provider defaults.
Invalid speed fails validation.
Invalid stability fails validation.
Payload contains merged settings.
```

### Acceptance Criteria

```text
ElevenLabs voice settings are resolved and validated before API calls.
Debug output can show final voice settings without exposing secrets.
```

## Slice 3.5: One-Speaker Batching And ElevenLabs Voice Resolution

### User Value

Multi-character scripts can be generated with ElevenLabs v3 by splitting speaker runs into separate requests.

### Changes

Use provider-aware batching:

```text
ElevenLabs max_speakers_per_request = 1.
Split each speaker run into a separate batch.
Resolve ElevenLabs voice ID for the speaker.
Use v3 tag compiler per batch.
```

Strict voice validation should be the default recommendation for ElevenLabs because voice IDs are account-specific.

### Tests

```text
Narrator/Leo alternating script becomes one-speaker batches.
Resolved ElevenLabs voice from story override wins.
Missing ElevenLabs voice fails in strict mode.
Placeholder registry voice can be detected as unresolved if strict validation is enabled.
No batch sent to ElevenLabs contains two speakers.
```

### Acceptance Criteria

```text
ElevenLabs generation plan supports multiple story speakers through separate requests.
Missing account-specific voices are caught before paid generation in strict mode.
```

## Slice 3.6: ElevenLabs Audio Normalization And Verification

### User Value

ElevenLabs v3-generated audio becomes Lunii-compatible MP3 using the same final output constraints as Gemini and Grok.

### Changes

```text
Request mp3_44100_128 from ElevenLabs.
Decode or normalize provider MP3 into the common processing path.
Concatenate batches with existing SegmentConcatenator.
Export final MP3 through MP3Exporter to strip tags and enforce mono 44.1 kHz.
Verify with MP3Verifier.
```

Command expectation:

```bash
uv run python generate_audio.py script.md -o output.mp3 --provider elevenlabs --model eleven_v3
```

### Tests

```text
Fake ElevenLabs MP3 fixture flows through export and verification path.
Final output is checked by MP3Verifier.
Progress resume stores provider/model or otherwise avoids mixing providers accidentally.
```

### Acceptance Criteria

```text
--provider elevenlabs --model eleven_v3 can generate final MP3 with a real key.
Tests use fixtures/fakes and do not call ElevenLabs.
Final MP3 requirements remain provider-neutral.
```

## Part 3 Final Acceptance

```text
uv run pytest passes.
--provider elevenlabs --model eleven_v3 is accepted by CLI.
Non-v3 ElevenLabs model selection fails clearly.
--provider elevenlabs --dry-run-voices works without API calls.
ELEVENLABS_API_KEY is required only for real generation.
Eleven v3 emotion tags compile safely.
ElevenLabs batches never exceed one speaker.
Voice settings resolve and validate.
Final ElevenLabs output goes through common MP3 export and verification.
```

## Deferred ElevenLabs Work

| Deferred item | Why deferred |
| --- | --- |
| `eleven_multilingual_v2` support | User selected Eleven v3 first. |
| Flash model support | Low-latency model choice can be a later provider mode. |
| Request stitching | Not available for v3 and not needed for first v3 slice. |
| Text to Dialogue | Separate endpoint/concept; not part of minimal provider interface. |
| Voice discovery API | Useful later, but strict validation and dry-run mapping come first. |
