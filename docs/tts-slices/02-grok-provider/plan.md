# Part 2: Grok Provider

## Goal

Add xAI Grok TTS as the second provider using minimal REST support. The first Grok implementation should use `POST /v1/tts`, one speaker per request, MP3 output, environment-variable credentials, and basic allowlisted emotion tag compilation.

## Target Code Layout

```text
audio_generation/
  providers/
    grok.py
  emotion/
    grok_tags.py
tests/unit/
  test_grok_provider.py
  test_grok_emotion_compiler.py
  test_grok_provider_batching.py
```

## Assumptions

| Area | Decision |
| --- | --- |
| API | Use non-streaming REST `POST https://api.x.ai/v1/tts`. |
| Credentials | Read `XAI_API_KEY` from the environment. |
| Voices | Use resolved provider voice from Part 1. Built-ins include `ara`, `eve`, `rex`, `sal`, `leo`. |
| Output | Request MP3 at 44.1 kHz when possible. Still pass through common MP3 export and verification. |
| Speakers | One speaker per request. Split on speaker changes. |
| Emotion | Basic tag compiler with strict allowlist. |

## Slice 2.1: Grok Provider Skeleton And Registry

### User Value

`--provider grok` becomes a recognized provider, with clear auth errors before generation.

### Changes

Add `audio_generation/providers/grok.py`:

```python
class GrokProvider:
    name = "grok"
    capabilities = ProviderCapabilities(
        max_speakers_per_request=1,
        supports_prompt_director_notes=False,
        supports_inline_tags=True,
        supports_wrapping_tags=True,
        supports_voice_settings=False,
        supports_direct_mp3_44100=True,
    )
```

Update provider registry:

```text
create_provider("grok") returns GrokProvider.
```

Update CLI:

```text
--provider choices include gemini and grok.
XAI_API_KEY is required when generation is executed with grok.
Dry-run voice resolution should not require XAI_API_KEY.
```

### Tests

```text
Provider registry returns GrokProvider.
CLI accepts --provider grok.
Missing XAI_API_KEY fails only when generation would call Grok.
Dry-run voices works without XAI_API_KEY.
```

### Acceptance Criteria

```text
uv run pytest passes.
--provider grok is recognized.
No real xAI API call is required by tests.
```

## Slice 2.2: Grok REST Client With Fake HTTP Tests

### User Value

The pipeline can call Grok TTS and receive audio bytes through the provider interface.

### Changes

Implement REST request:

```json
{
  "text": "Hello from KidStory.",
  "voice_id": "ara",
  "language": "auto",
  "output_format": {
    "codec": "mp3",
    "sample_rate": 44100,
    "bit_rate": 192000
  }
}
```

Recommended implementation details:

```text
Use standard library urllib or requests if already available.
Use XAI_API_KEY from environment.
Return SynthesisResult(audio_bytes=response.content, codec="mp3", sample_rate=44100).
Map 401 to auth error, 429 to rate-limit error, 400 to validation error, 5xx to retryable provider error.
```

### Tests

```text
Fake HTTP success returns SynthesisResult.
Request payload includes text, voice_id, language, output_format.
401 maps to TTSAuthError.
429 maps to TTSRateLimitError.
500 maps to provider error with useful message.
```

### Acceptance Criteria

```text
GrokProvider.synthesize can be tested without network.
Error handling is provider-normalized.
```

## Slice 2.3: Basic Grok Emotion Tag Compiler

### User Value

Common KidStory emotion markers compile into Grok-supported tags without leaking unsupported descriptors into audio.

### Changes

Add `audio_generation/emotion/grok_tags.py`:

```text
Inline events:
  laugh -> [laugh]
  chuckle -> [chuckle]
  giggle -> [giggle]
  sigh -> [sigh]
  pause -> [pause]
  long_pause -> [long-pause]

Wrapping styles:
  whispering -> <whisper>text</whisper>
  soft -> <soft>text</soft>
  loud -> <loud>text</loud>
  slow -> <slow>text</slow>
  fast -> <fast>text</fast>
  higher_pitch -> <higher-pitch>text</higher-pitch>
  lower_pitch -> <lower-pitch>text</lower-pitch>
```

Compile examples:

```text
<emotion: whispering, nervous> I hear something.
  -> <whisper>I hear something.</whisper>

<emotion: laughing, excited> We did it!
  -> [laugh] We did it!

<emotion: slow, soft> Goodnight.
  -> <slow><soft>Goodnight.</soft></slow>
```

Unsupported descriptors:

```text
Keep out of tags.
Optionally rely on punctuation.
Do not emit [nervous] unless the provider allowlist supports it.
```

### Tests

```text
Whisper compiles to <whisper>.
Slow plus soft nests supported wrappers deterministically.
Laugh compiles to [laugh].
Unsupported descriptor is dropped.
Compiler never emits raw unknown bracket tags.
```

### Acceptance Criteria

```text
Basic Grok tags compile from PerformanceDirection.
Compiled text remains safe and allowlisted.
```

## Slice 2.4: One-Speaker Batching And Voice Resolution

### User Value

Multi-character scripts can be generated with Grok even though Grok REST TTS uses one `voice_id` per request.

### Changes

Use Part 1 provider-aware batching:

```text
Grok max_speakers_per_request = 1.
Split each speaker run into a separate batch.
Resolve voice for the single speaker in each Grok batch.
```

Update Grok provider request building:

```text
Use ResolvedVoice.voice_id for voice_id.
Use script locale converted to xAI language where possible.
Use auto if locale is not supported or if selected by CLI default.
```

### Tests

```text
Narrator/Leo alternating script becomes one-speaker batches.
Resolved Grok voice from story override wins.
Resolved Grok voice from voiceRole registry works.
No batch sent to Grok contains two speakers.
```

### Acceptance Criteria

```text
Grok generation plan supports multiple story speakers by splitting requests.
Voice resolution is provider-specific and debuggable.
```

## Slice 2.5: Grok Audio Normalization And Verification

### User Value

Grok-generated audio becomes Lunii-compatible MP3 using the same final pipeline as Gemini.

### Changes

```text
Decode provider MP3 bytes into AudioSegment or pass through controlled normalization path.
Concatenate batches with existing SegmentConcatenator.
Export final MP3 through MP3Exporter.
Verify with MP3Verifier.
```

Add command expectation:

```bash
uv run python generate_audio.py script.md -o output.mp3 --provider grok
```

### Tests

```text
Fake Grok MP3 fixture can flow through export and verification path.
Final output is checked by MP3Verifier.
Progress resume stores provider name or otherwise avoids mixing Gemini and Grok progress accidentally.
```

### Acceptance Criteria

```text
--provider grok can generate final MP3 with a real key.
Tests use fixtures/fakes and do not call xAI.
Final MP3 requirements remain provider-neutral.
```

## Part 2 Final Acceptance

```text
uv run pytest passes.
--provider grok is accepted by CLI.
--provider grok --dry-run-voices works without API calls.
Grok provider uses XAI_API_KEY only for real generation.
Basic emotion tags compile safely.
Grok batches never exceed one speaker.
Final Grok output goes through common MP3 export and verification.
```
