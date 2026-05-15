# Multi-Provider TTS Emotion Plan

## Purpose

This document explains how emotional voice control works across Gemini TTS, ElevenLabs, and xAI Grok TTS, then proposes a provider-neutral audio generation pipeline for KidStory.

The goal is not to force every provider into the same lowest-common-denominator API. The goal is to keep one story script format while compiling that script into provider-specific requests that preserve as much emotional intent as each provider can support.

## Current State

The current audio pipeline is optimized for Gemini TTS.

Current flow:

```text
audio-script.md
  -> AudioScriptParser
  -> SegmentBatcher
  -> TTSPromptBuilder
  -> SpeechConfigBuilder
  -> TTSClient
  -> SegmentConcatenator
  -> MP3Exporter
  -> MP3Verifier
```

Current script example:

```markdown
---
stageUuid: "chapter-01"
chapterRef: "01-intro"
locale: "fr-FR"
speakers:
  - name: Narrator
    voice: Sulafat
  - name: Leo
    voice: Puck
---

**Narrator:** <emotion: warm, mysterious> The attic was quiet.
**Leo:** <emotion: curious, whispering> What is this golden clock?
```

Current emotion handling:

```text
<emotion: warm, mysterious>
  -> parsed into Segment.emotion
  -> converted to Gemini Director's Notes
  -> transcript is sent without emotion markers
```

Current Gemini prompt structure:

```text
=== AUDIO PROFILE ===
Leo: curious child. Age: 7. Personality: brave, playful.

=== DIRECTOR'S NOTES ===
Make Narrator sound warm, mysterious.
Make Leo sound curious, whispering.

=== TRANSCRIPT ===
Narrator: The attic was quiet.
Leo: What is this golden clock?
```

Key limitation:

Gemini, ElevenLabs, and Grok expose emotion control differently. The pipeline needs an intermediate representation of voice direction that is richer than the current single free-text `emotion` string.

## Provider Comparison

### Summary Table

| Capability | Gemini TTS | ElevenLabs | xAI Grok TTS |
| --- | --- | --- | --- |
| Main emotion mechanism | Natural-language prompt instructions | Textual cues, voice settings, and v3 audio tags | Inline speech tags and wrapping tags |
| Voice identity | `SpeechConfig` voice names | `voice_id`, voice library, cloning, design | `voice_id`, built-in or custom voices |
| Separate spoken text from direction | Yes, with prompt sections if we build them carefully | Partially; normal textual cues may be spoken, v3 tags are non-lexical controls | Yes for supported tags; unsupported text is spoken |
| Fine-grained nonverbal sounds | Prompt-dependent, not guaranteed | Strong in Eleven v3 with tags like `[laughs]`, `[sighs]` | Explicit tags like `[laugh]`, `[sigh]`, `[breath]` |
| Pitch/speed control | Prompt-dependent; Vertex UI exposes speed, current code does not | Speed setting and v3 tags; stability affects expressiveness | Wrapping tags like `<slow>`, `<fast>`, `<higher-pitch>` |
| Pauses | Prompt/punctuation plus post-processing pauses | `<break>` for non-v3; v3 uses punctuation and audio tags | `[pause]`, `[long-pause]`, punctuation |
| Multi-speaker support | API supports multi-speaker configs with limited speakers per call; current batcher uses max 2 | v3 supports multi-speaker dialogue conceptually, but standard TTS endpoint is voice-centric; Text to Dialogue may be a separate route | Standard `/v1/tts` is one `voice_id`; use one request per speaker/segment for story production |
| Long-form continuity | Managed by our chunking and concatenation | `previous_text`, `next_text`, request IDs for stitching on supported models; not available for Eleven v3 | Use chunking, consistent tags, and post-processing; no documented request stitching equivalent |
| Output format fit for Lunii | Current code converts PCM to MP3 44.1 kHz mono no tags | Can request `mp3_44100_128`; still verify and strip tags | Can request MP3 at 44.1 kHz; still verify and strip tags |

### Gemini TTS

Gemini TTS is prompt-driven. It does not expose a stable universal API field like `emotion=happy` or `style=whisper`. The model is guided by a combination of:

- Voice selection in `SpeechConfig` or `MultiSpeakerVoiceConfig`.
- Natural-language instructions in the prompt.
- Transcript wording and punctuation.
- Optional character context supplied by our pipeline.

In this repository, emotion control is implemented as a prompt compiler:

```text
Script emotion marker
  -> Segment.emotion
  -> Director's Notes
  -> Gemini prompt
```

Example source:

```markdown
**Leo:** <emotion: nervous, quiet, breathless> I think the clock is moving.
```

Compiled Gemini prompt:

```text
=== DIRECTOR'S NOTES ===
Make Leo sound nervous, quiet, breathless.

=== TRANSCRIPT ===
Leo: I think the clock is moving.
```

This is a good fit for audiobook-style direction because the spoken transcript remains clean. The model sees the performance instruction but should only speak the transcript.

Strengths:

- Excellent for high-level acting direction: warm narrator, curious child, tense whisper, reassuring mentor.
- Good at combining character profile, scene mood, and transcript text.
- Clean separation between directions and spoken text can be enforced by prompt structure.
- Multi-speaker voice config allows speaker-specific voices in a single call, within API limits.

Weaknesses:

- Emotional precision is probabilistic.
- A direction such as `sad but brave` may be interpreted differently across generations.
- Nonverbal effects like laughs, gasps, sighs, or breaths are not guaranteed unless the model chooses to perform them.
- Provider-specific prompt failures are possible if the model reads headers or directions aloud, so verification by listening is still needed.
- Current implementation folds the system instruction into the prompt because the TTS model used here does not support `system_instruction` directly.

Best use in KidStory:

- Narration-heavy stories.
- Character acting with rich context.
- Educational content where clarity matters more than dramatic audio effects.
- Stories with 2-speaker local scenes, such as narrator plus one child.

Recommended Gemini emotion strategy:

```text
Use semantic emotion descriptors.
Keep spoken transcript clean.
Use Audio Profile for stable character identity.
Use Director's Notes for per-batch acting direction.
Use post-processing for pauses, not only prompt wording.
```

### ElevenLabs

ElevenLabs emotion control is split across model behavior, voice settings, textual prompting, and model-specific tags.

There are two major modes to account for:

1. Stable production TTS models such as Multilingual v2 and Flash v2.5.
2. Eleven v3, which is more expressive and supports audio tags, but has different constraints.

For normal TTS models, emotion is mostly inferred from the text itself. For example:

```text
"You're leaving?" she asked, her voice trembling with sadness.
"That's it!" he exclaimed triumphantly.
```

The problem is that descriptive text can be spoken aloud if included in the TTS input. That is different from our Gemini pattern where Director's Notes are separated from the transcript.

ElevenLabs also exposes `voice_settings`:

```json
{
  "stability": 0.35,
  "similarity_boost": 0.75,
  "style": 0.4,
  "speed": 0.95,
  "use_speaker_boost": true
}
```

Relevant settings:

| Setting | Effect |
| --- | --- |
| `stability` | Lower values allow broader emotional range and more variation. Higher values are more consistent but can become flatter. |
| `similarity_boost` | Keeps output closer to the original voice identity. Too high can reduce flexibility. |
| `style` | Amplifies the speaker's original style, with latency and stability tradeoffs. |
| `speed` | Slows down or speeds up the generated speech. Useful for age-specific pacing. |
| `seed` | Attempts repeatability, but determinism is not guaranteed. |

Eleven v3 adds audio tags. These are closer to direct performance controls:

```text
[whispers] I never knew it could be this way.
[sighs] I guess you're right.
[excited] We found it!
```

Eleven v3 tag examples:

```text
[laughs]
[starts laughing]
[whispers]
[sighs]
[sarcastic]
[curious]
[excited]
[crying]
[mischievously]
```

Eleven v3 also responds strongly to punctuation and capitalization:

```text
It was a VERY long day [sigh] ... nobody listens anymore.
```

Pauses differ by model:

```xml
<break time="1.5s" />
```

This is recommended for some non-v3 models, but Eleven v3 does not support SSML break tags. For v3, pauses should be compiled as punctuation, `[pause]`-style tags only if supported by the model behavior, or handled in post-processing.

Strengths:

- Very strong expressive speech quality, especially with the right voice.
- Large voice ecosystem: library voices, instant cloning, professional cloning, voice design.
- Eleven v3 audio tags provide a practical way to represent laughter, whispering, sighing, sarcasm, and other delivery details.
- `speed`, `stability`, and `style` provide knobs that can be tuned per story, speaker, or segment.
- Request stitching can improve continuity across chunks on supported models.

Weaknesses:

- Textual emotional cues may be spoken if inserted directly.
- Emotion reliability depends heavily on chosen voice and training samples.
- Eleven v3 is more expressive but can be less stable and has different feature support.
- Request stitching is not available for Eleven v3.
- Standard TTS endpoint is built around a `voice_id`; multi-character stories likely need per-speaker requests or a separate dialogue API path.

Best use in KidStory:

- Dramatic character performances.
- Stories where laughs, whispers, sighs, and expressive reactions matter.
- Packs where custom voices or cloned voices are valuable.
- Production runs where voice quality is more important than lowest cost.

Recommended ElevenLabs emotion strategy:

```text
For Eleven v3:
  Compile emotion markers into audio tags near the affected phrase.
  Use punctuation and capitalization sparingly for emphasis.
  Tune stability lower for expressive scenes and higher for narration.

For non-v3 models:
  Avoid adding spoken narrator-style emotional directions into the text.
  Prefer voice settings, punctuation, and post-processing.
  Use <break> for pauses only on models that support it.
  Use request stitching where supported for long passages.
```

### xAI Grok TTS

Grok TTS, through xAI Voice API, exposes a direct `/v1/tts` endpoint. It accepts text, a voice ID, language, output format, and optional text normalization.

Simple request shape:

```json
{
  "text": "Hello! Welcome to the story.",
  "voice_id": "eve",
  "language": "en",
  "output_format": {
    "codec": "mp3",
    "sample_rate": 44100,
    "bit_rate": 192000
  }
}
```

Grok emotion control is tag-driven. The docs define two tag families:

Inline tags:

```text
[pause]
[long-pause]
[laugh]
[chuckle]
[giggle]
[cry]
[breath]
[inhale]
[exhale]
[sigh]
```

Wrapping tags:

```text
<soft>Goodnight, little star.</soft>
<whisper>It is a secret.</whisper>
<loud>Look over there!</loud>
<slow>Listen carefully.</slow>
<fast>Run, run, run!</fast>
<higher-pitch>Really?</higher-pitch>
<lower-pitch>I am the old mountain.</lower-pitch>
<laugh-speak>That tickles!</laugh-speak>
<emphasis>This matters.</emphasis>
```

This is a different model from Gemini. Instead of compiling emotion into detached director notes, we compile emotion directly into accepted inline or wrapping markup. The tags are not meant to be spoken; they are control syntax.

Example source:

```markdown
**Leo:** <emotion: whispering, nervous> I hear something.
```

Compiled Grok text:

```text
<whisper>I hear something.</whisper>
```

Example source:

```markdown
**Leo:** <emotion: delighted, laughing> We did it!
```

Compiled Grok text:

```text
[laugh] We did it!
```

Strengths:

- Tags are explicit and easy to compile from a normalized emotion representation.
- Pauses and nonverbal sounds are directly expressible.
- Output format can be requested as MP3 at 44.1 kHz.
- Built-in voices have clear broad personalities, and custom voices are supported.
- Streaming TTS can be useful later for interactive preview tools.

Weaknesses:

- Fewer built-in voices than Gemini or ElevenLabs.
- Standard TTS request uses a single voice per request.
- Emotion vocabulary is limited to supported tags and whatever the model infers from punctuation.
- Unsupported tags or custom descriptors may degrade output or be spoken, so the compiler must whitelist tags.

Best use in KidStory:

- Stories needing explicit pauses, sighs, whispers, and laughs.
- Fast provider integration because request shape is simple.
- Preview generation where direct MP3 output simplifies the pipeline.

Recommended Grok emotion strategy:

```text
Map normalized emotion controls to a strict allowlist of xAI tags.
Use wrapping tags for sustained delivery changes.
Use inline tags for events at specific positions.
Never pass raw unsupported emotion descriptors as tags.
Fallback to punctuation or post-processing when no tag exists.
```

## Core Design Problem

The current model stores emotion as a string:

```python
Segment(
    speaker="Leo",
    text="I hear something.",
    emotion="whispering, nervous",
)
```

This is enough for Gemini because Gemini can interpret prose. It is not enough for providers that need structured tags, voice settings, speed values, or fallback behavior.

We need two layers:

1. A provider-neutral direction model that preserves story intent.
2. Provider compilers that translate the direction model into Gemini prompts, ElevenLabs tags/settings, or Grok tags.

## Proposed Intermediate Representation

Add a structured performance direction model.

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

Then update segments to carry structured direction while retaining the raw marker for compatibility:

```python
@dataclass
class Segment:
    speaker: str
    text: str
    emotion: str = ""
    direction: PerformanceDirection = field(default_factory=PerformanceDirection)
```

Direction examples:

```text
<emotion: nervous, whispering, slow>
```

Normalized form:

```json
{
  "raw": "nervous, whispering, slow",
  "emotion": ["nervous"],
  "delivery": ["whispering"],
  "pace": "slow"
}
```

Another example:

```text
<emotion: delighted, laughing, breathless>
```

Normalized form:

```json
{
  "raw": "delighted, laughing, breathless",
  "emotion": ["delighted"],
  "delivery": ["breathless"],
  "vocal_events": ["laugh"]
}
```

## Emotion Taxonomy

Use a small canonical taxonomy. Do not try to model every possible adjective at first.

### Canonical Emotion Values

| Canonical value | Synonyms to normalize |
| --- | --- |
| `happy` | joyful, glad, cheerful |
| `excited` | thrilled, enthusiastic, delighted |
| `sad` | sorrowful, disappointed |
| `scared` | afraid, frightened, fearful |
| `nervous` | anxious, unsure, worried |
| `angry` | furious, annoyed, irritated |
| `calm` | peaceful, relaxed |
| `curious` | questioning, intrigued |
| `mysterious` | secretive, enigmatic |
| `reassuring` | comforting, gentle |
| `sarcastic` | dry, ironic |
| `playful` | mischievous, silly |

### Delivery Values

| Canonical value | Meaning |
| --- | --- |
| `whispering` | Quiet whispered delivery |
| `soft` | Low volume, gentle delivery |
| `loud` | Raised voice |
| `shouting` | Very loud, urgent voice |
| `breathless` | Short breath, urgency or surprise |
| `trembling` | Shaky voice |
| `firm` | Decisive, stable voice |
| `warm` | Warm narrator tone |
| `serious` | Reduced playfulness |
| `dramatic` | Larger performance |

### Vocal Events

| Canonical value | Meaning |
| --- | --- |
| `laugh` | Laughter near this line |
| `chuckle` | Small laugh |
| `giggle` | Light childish laugh |
| `sigh` | Audible sigh |
| `gasp` | Quick surprised breath |
| `inhale` | Audible inhale |
| `exhale` | Audible exhale |
| `cry` | Crying or tearful delivery |
| `pause` | Short pause |
| `long_pause` | Longer pause |

### Prosody Values

| Dimension | Values |
| --- | --- |
| `pace` | `slow`, `normal`, `fast` |
| `volume` | `soft`, `normal`, `loud` |
| `pitch` | `lower`, `normal`, `higher` |
| `intensity` | `low`, `normal`, `building`, `high`, `decreasing` |

## Provider Compilers

### Gemini Compiler

Input:

```python
Segment(
    speaker="Leo",
    text="I hear something.",
    direction=PerformanceDirection(
        emotion=["nervous"],
        delivery=["whispering"],
        pace="slow",
    ),
)
```

Output prompt section:

```text
=== DIRECTOR'S NOTES ===
Make Leo sound nervous and whispering, with a slow pace.

=== TRANSCRIPT ===
Leo: I hear something.
```

Gemini compiler rules:

| Direction | Gemini output |
| --- | --- |
| Emotion | Natural-language acting note |
| Delivery | Natural-language acting note |
| Vocal event | Natural-language acting note, unless event is better handled by audio post-processing |
| Pace | Natural-language acting note, or future speed parameter if exposed |
| Pause | Prefer post-processing pause metadata |
| Pitch | Natural-language acting note |
| Unsupported descriptor | Include as plain prose in Director's Notes only if safe |

Important constraint:

Do not put emotion markers into the transcript. Gemini should receive only spoken text in the transcript section.

### ElevenLabs Compiler

ElevenLabs needs model-aware compilation.

For Eleven v3:

```python
PerformanceDirection(
    emotion=["excited"],
    vocal_events=["laugh"],
    pace="fast",
)
```

Compiled text:

```text
[excited] [laughs] We found it!
```

Or for sustained style:

```text
[excited] We found it! We really found it!
```

For whisper:

```text
[whispers] It is behind the clock.
```

For non-v3 models:

```text
It is behind the clock...
```

And request settings might be adjusted:

```json
{
  "voice_settings": {
    "stability": 0.35,
    "style": 0.35,
    "speed": 0.92
  }
}
```

ElevenLabs compiler rules:

| Direction | Eleven v3 output | Non-v3 output |
| --- | --- | --- |
| `whispering` | `[whispers] text` | Text/punctuation only, maybe lower volume in post |
| `laugh` | `[laughs]` | Usually avoid; optional separate SFX or text cue if acceptable |
| `sigh` | `[sighs]` | Usually avoid; optional separate SFX |
| `excited` | `[excited]` plus punctuation | Exclamation, lower stability, higher style |
| `sad` | `[sad]` if effective for voice | Lower stability, slower speed, careful punctuation |
| `slow` | Punctuation or tag if effective | `speed < 1.0` |
| `pause` | Punctuation or audio tag | `<break>` if model supports it, else post-processing |

Important constraint:

Do not insert prose like `he said sadly` unless we accept that it may be spoken. For story production, avoid spoken emotional scaffolding.

### Grok Compiler

Grok should compile to strict allowlisted tags.

Example:

```python
PerformanceDirection(
    emotion=["nervous"],
    delivery=["whispering"],
    vocal_events=["sigh"],
    pace="slow",
)
```

Compiled text:

```text
[sigh] <slow><whisper>I hear something.</whisper></slow>
```

Grok compiler rules:

| Direction | Grok output |
| --- | --- |
| `whispering` | `<whisper>text</whisper>` |
| `soft` | `<soft>text</soft>` |
| `loud` | `<loud>text</loud>` |
| `slow` | `<slow>text</slow>` |
| `fast` | `<fast>text</fast>` |
| `higher` pitch | `<higher-pitch>text</higher-pitch>` |
| `lower` pitch | `<lower-pitch>text</lower-pitch>` |
| `laugh` | `[laugh]` |
| `chuckle` | `[chuckle]` |
| `giggle` | `[giggle]` |
| `sigh` | `[sigh]` |
| `pause` | `[pause]` |
| `long_pause` | `[long-pause]` |
| `emphasis` | `<emphasis>text</emphasis>` |
| Unsupported descriptor | Drop, or convert to punctuation if safe |

Important constraint:

Never generate arbitrary bracket tags from raw emotion strings. Only emit tags documented for the provider.

## Proposed Package Architecture

Add a provider layer under `audio_generation/providers/`.

```text
audio_generation/
  providers/
    __init__.py
    base.py
    registry.py
    gemini.py
    elevenlabs.py
    grok.py
  emotion/
    __init__.py
    normalizer.py
    taxonomy.py
    compiler.py
```

Provider interface:

```python
class TTSProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...
```

Request model:

```python
@dataclass
class SynthesisRequest:
    script: AudioScript
    batch: SegmentBatch
    speaker_configs: dict[str, SpeakerConfig]
    character_profiles: dict[str, CharacterProfile]
    locale: str
    output_format: AudioFormat
    provider_options: dict[str, Any] = field(default_factory=dict)
```

Result model:

```python
@dataclass
class SynthesisResult:
    audio_bytes: bytes
    codec: str
    sample_rate: int | None
    channels: int | None
    request_id: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)
```

Capabilities model:

```python
@dataclass
class ProviderCapabilities:
    max_speakers_per_request: int
    supports_prompt_director_notes: bool
    supports_inline_tags: bool
    supports_wrapping_tags: bool
    supports_voice_settings: bool
    supports_request_stitching: bool
    supports_direct_mp3_44100: bool
    supported_vocal_events: set[str]
    supported_delivery_styles: set[str]
```

Example capabilities:

```python
GEMINI_CAPABILITIES = ProviderCapabilities(
    max_speakers_per_request=2,
    supports_prompt_director_notes=True,
    supports_inline_tags=False,
    supports_wrapping_tags=False,
    supports_voice_settings=False,
    supports_request_stitching=False,
    supports_direct_mp3_44100=False,
    supported_vocal_events=set(),
    supported_delivery_styles={"whispering", "soft", "loud", "slow", "fast"},
)
```

```python
GROK_CAPABILITIES = ProviderCapabilities(
    max_speakers_per_request=1,
    supports_prompt_director_notes=False,
    supports_inline_tags=True,
    supports_wrapping_tags=True,
    supports_voice_settings=False,
    supports_request_stitching=False,
    supports_direct_mp3_44100=True,
    supported_vocal_events={"laugh", "chuckle", "giggle", "cry", "sigh", "pause", "long_pause"},
    supported_delivery_styles={"whispering", "soft", "loud", "slow", "fast", "higher_pitch", "lower_pitch"},
)
```

## Pipeline Changes

### New High-Level Flow

```mermaid
flowchart LR
    MD[Audio Script] --> PARSE[Parse]
    PARSE --> NORMALIZE[Normalize Directions]
    NORMALIZE --> PLAN[Build Provider Plan]
    PLAN --> COMPILE[Compile Provider Request]
    COMPILE --> TTS[Provider TTS]
    TTS --> DECODE[Decode/Normalize Audio]
    DECODE --> CONCAT[Concatenate]
    CONCAT --> EXPORT[Export Lunii MP3]
    EXPORT --> VERIFY[Verify]
```

### Step 1: Parse Script

Keep the existing Markdown format. Continue to support:

```markdown
**Speaker:** <emotion: descriptor1, descriptor2> Text
```

Add optional future syntax for more precise control:

```markdown
**Leo:** <voice emotion="nervous" delivery="whispering" pace="slow"> I hear something.
```

This should be optional. The simple `<emotion: ...>` syntax is good for writers.

### Step 2: Normalize Directions

Convert raw descriptors into canonical direction fields.

Example mapping:

```python
"whispered" -> delivery=["whispering"]
"whispering" -> delivery=["whispering"]
"quiet" -> volume="soft"
"breathless" -> delivery=["breathless"]
"laughing" -> vocal_events=["laugh"]
"excited" -> emotion=["excited"]
```

Unknown descriptors should not be discarded immediately. Keep them in `raw` and optionally pass them only to providers that can safely use natural-language direction, such as Gemini.

### Step 3: Select Provider

Add CLI options:

```bash
uv run python generate_audio.py script.md -o output.mp3 --provider gemini
uv run python generate_audio.py script.md -o output.mp3 --provider elevenlabs --model eleven_v3
uv run python generate_audio.py script.md -o output.mp3 --provider grok
```

Environment variables:

```text
TTS_PROVIDER=gemini

GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_REGION=us-central1

ELEVENLABS_API_KEY=...
ELEVENLABS_MODEL=eleven_multilingual_v2

XAI_API_KEY=...
XAI_TTS_DEFAULT_VOICE=eve
```

Frontmatter override:

```yaml
---
provider: elevenlabs
model: eleven_v3
speakers:
  - name: Narrator
    voice: JBFqnCBsd6RMkjVDRZzb
---
```

Precedence:

```text
CLI option > frontmatter > environment variable > default provider
```

### Step 4: Provider-Aware Batching

Batching must move from Gemini-specific constraints to provider capabilities.

Current assumption:

```text
Max 2 speakers per batch.
```

New approach:

```python
batcher = ProviderAwareBatcher(provider.capabilities)
```

Rules:

| Provider | Batching strategy |
| --- | --- |
| Gemini | Keep current narrator plus character batching, max 2 speakers. |
| ElevenLabs standard TTS | Usually one speaker per request. Split on speaker changes. Use request stitching if model supports it. |
| ElevenLabs v3 dialogue route | If implemented later, batch multi-speaker dialogue according to that endpoint's schema. |
| Grok TTS | One speaker per request. Split on speaker changes. |

### Step 5: Compile Request

Move provider-specific prompt and payload creation behind the provider implementation.

Gemini payload:

```text
prompt: Audio Profile + Director's Notes + Transcript
speech_config: Gemini voice config
```

ElevenLabs payload:

```json
{
  "text": "[whispers] I hear something.",
  "model_id": "eleven_v3",
  "voice_settings": {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.3,
    "speed": 0.95
  }
}
```

Grok payload:

```json
{
  "text": "<whisper>I hear something.</whisper>",
  "voice_id": "ara",
  "language": "fr",
  "output_format": {
    "codec": "mp3",
    "sample_rate": 44100,
    "bit_rate": 192000
  }
}
```

### Step 6: Normalize Audio Output

Providers return different formats:

| Provider | Typical output | Required normalization |
| --- | --- | --- |
| Gemini | Raw audio bytes, currently treated as PCM at provider sample rate | Convert to `AudioSegment`, resample to 44.1 kHz mono, export MP3 |
| ElevenLabs | MP3, PCM, WAV, or stream | Decode to `AudioSegment` or pass through only after verification |
| Grok | MP3, WAV, PCM, mu-law, a-law | Decode or pass through after verification |

Always keep the final export step provider-neutral:

```text
Provider audio -> AudioSegment -> MP3Exporter -> MP3Verifier
```

Even if a provider returns a valid MP3, the pipeline should still strip ID3 tags and verify mono 44.1 kHz output.

### Step 7: Pause and Transition Handling

Emotion tags can express pauses, but Lunii story audio should not rely entirely on model-generated pause timing.

Use this policy:

```text
Semantic pauses in script -> metadata -> SegmentConcatenator
Provider tags -> local expressive pauses inside a line
Scene breaks -> post-processing pause
Speaker transitions -> post-processing pause
```

Examples:

```markdown
**Narrator:** <emotion: dramatic, long_pause_after> The clock struck midnight.
```

Normalized:

```json
{
  "emotion": ["dramatic"],
  "pause_after_ms": 1500
}
```

Gemini:

```text
Make Narrator sound dramatic.
```

Grok:

```text
The clock struck midnight.
```

Post-processing:

```text
Add 1500 ms pause after segment.
```

This keeps timing predictable across providers.

## Voice Mapping Strategy

A story currently stores provider-specific Gemini voice names like `Sulafat` and `Puck`. Multi-provider support needs either provider-specific voices or semantic voice roles.

There is no real one-to-one voice mapping across providers. A Gemini voice such as `Sulafat` is not the same asset as an ElevenLabs voice ID or a Grok voice like `ara`. The portable concept is not the provider voice name. The portable concept is the character's voice role: warm narrator, playful child, wise mentor, gruff creature, calm teacher, and so on.

Recommended principle:

```text
Story scripts choose semantic voice roles.
Provider config maps those roles to provider-specific voice IDs.
Story frontmatter can override the global mapping when a specific story needs a specific voice.
```

### Voice Identity vs Performance Direction

Keep these separate:

| Concept | Example | Where it belongs |
| --- | --- | --- |
| Voice identity | warm adult narrator, child protagonist, old wizard | `voiceRole` and provider voice mapping |
| Provider voice asset | `Sulafat`, `JBFqnCBsd6RMkjVDRZzb`, `ara` | `voices.<provider>` or voice registry |
| Emotional delivery | nervous, whispering, excited, laughing | `<emotion: ...>` / `PerformanceDirection` |
| Provider controls | ElevenLabs stability, Grok tags, Gemini Director's Notes | Provider compiler |

Do not encode emotions into voice mapping. A `warm_narrator` can still speak mysteriously or urgently. Voice mapping selects the baseline sound; emotion compilation controls the moment-by-moment performance.

Recommended frontmatter format:

```yaml
speakers:
  - name: Narrator
    voiceRole: warm_narrator
    voices:
      gemini: Sulafat
      elevenlabs: JBFqnCBsd6RMkjVDRZzb
      grok: ara
  - name: Leo
    voiceRole: curious_child
    voices:
      gemini: Puck
      elevenlabs: EXAVITQu4vr4xnSDxMaL
      grok: eve
```

Backward compatibility:

```yaml
speakers:
  - name: Narrator
    voice: Sulafat
```

If `voices.<provider>` exists, use it. Otherwise use `voice` as a provider-specific legacy value. If neither exists, use provider defaults.

### Global Voice Registry

Add a registry file that maps semantic roles to provider-specific voices.

Recommended path:

```text
config/voice-map.yaml
```

Example:

```yaml
version: 1

defaults:
  provider: gemini
  role: warm_narrator

roles:
  warm_narrator:
    description: Warm, clear adult narrator for bedtime or educational stories.
    age: adult
    tone: warm
    gender: neutral
    providers:
      gemini:
        voice: Sulafat
      elevenlabs:
        voice: JBFqnCBsd6RMkjVDRZzb
        model: eleven_multilingual_v2
        voice_settings:
          stability: 0.55
          similarity_boost: 0.75
          style: 0.15
          speed: 0.95
      grok:
        voice: ara

  playful_child:
    description: Bright, energetic child or childlike companion.
    age: child
    tone: playful
    gender: neutral
    providers:
      gemini:
        voice: Puck
      elevenlabs:
        voice: EXAVITQu4vr4xnSDxMaL
        model: eleven_v3
        voice_settings:
          stability: 0.35
          similarity_boost: 0.7
          style: 0.45
          speed: 1.02
      grok:
        voice: eve

  wise_mentor:
    description: Calm, knowledgeable guide or elder.
    age: older_adult
    tone: calm
    gender: neutral
    providers:
      gemini:
        voice: Charon
      elevenlabs:
        voice: onwK4e9ZLuTAKqWW03F9
        voice_settings:
          stability: 0.65
          similarity_boost: 0.8
          style: 0.1
          speed: 0.92
      grok:
        voice: leo

  gruff_creature:
    description: Low, textured creature voice that remains child-safe.
    age: adult
    tone: gruff
    gender: neutral
    providers:
      gemini:
        voice: Algenib
      elevenlabs:
        voice: N2lVS1w4EtoT3dr4eOWO
        voice_settings:
          stability: 0.45
          similarity_boost: 0.8
          style: 0.35
          speed: 0.9
      grok:
        voice: rex
```

Important details:

- Gemini voices are stable human-readable names from Google's voice list.
- ElevenLabs voices are opaque `voice_id` values from the ElevenLabs voice library, cloned voices, or designed voices.
- Grok built-in voices are simple IDs such as `ara`, `eve`, `rex`, `sal`, and `leo`; custom Grok voices are also opaque IDs.
- The registry should support provider-specific model and voice settings because the same role may need different settings per provider.

### Story-Level Voice Overrides

The global registry should be the default, but individual stories need overrides.

Story frontmatter can reference roles only:

```yaml
speakers:
  - name: Narrator
    voiceRole: warm_narrator
  - name: Leo
    voiceRole: playful_child
```

Or provide provider-specific overrides:

```yaml
speakers:
  - name: Grand-Mere Celeste
    voiceRole: wise_mentor
    voices:
      gemini: Sulafat
      elevenlabs: pFZP5JQG7iQjIQuC4Bku
      grok: ara
    providerSettings:
      elevenlabs:
        voice_settings:
          stability: 0.6
          style: 0.2
          speed: 0.9
```

This lets the story keep a semantic role while pinning a provider voice when needed.

### Voice Resolution Algorithm

Provider voice resolution should be deterministic.

Recommended order:

```text
1. speakers[].voices[provider]
2. speakers[].voice if it is valid for the selected provider
3. voice-map.yaml roles[voiceRole].providers[provider].voice
4. voice-map.yaml roles[voiceRole].providers[default_provider].voice if provider fallback is allowed
5. provider default voice
6. fail with a clear validation error if strict voice validation is enabled
```

Recommended implementation:

```python
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

Example sources:

```text
story.voices.gemini
story.legacy_voice
registry.role.playful_child.grok
provider.default
```

The source string is useful in debug output because voice mismatches are otherwise hard to diagnose.

### Provider-Specific Voice Constraints

| Provider | Voice identifier | Constraint |
| --- | --- | --- |
| Gemini | Human-readable voice name such as `Sulafat` | Must be one of the Gemini TTS prebuilt voices for the chosen model. |
| ElevenLabs | Opaque `voice_id` | Depends on account access, voice library availability, cloned voices, and model compatibility. |
| Grok | Built-in ID or custom voice ID | Built-ins are limited; custom voices require prior creation and account access. |

Provider compatibility is not only about voice ID. For ElevenLabs, the chosen model matters because emotion controls differ between `eleven_v3`, `eleven_multilingual_v2`, and Flash models. For Grok, the current built-in voice list is much smaller, so role mapping will be approximate unless custom voices are created.

### Voice Role Design

Start with a small role taxonomy rather than trying to map every possible character type.

Recommended initial roles:

| Role | Use case | Gemini candidate | Grok candidate |
| --- | --- | --- | --- |
| `warm_narrator` | Main narrator, bedtime, educational | `Sulafat` | `ara` |
| `clear_narrator` | Explanations and science content | `Charon`, `Iapetus` | `rex` |
| `playful_child` | Young protagonist or sidekick | `Puck`, `Leda` | `eve` |
| `gentle_child` | Shy or sensitive child | `Achird`, `Vindemiatrix` | `ara` |
| `wise_mentor` | Grandparent, teacher, guide | `Gacrux`, `Sadaltager`, `Charon` | `leo` |
| `mysterious_guide` | Magical helper, secretive guide | `Enceladus`, `Despina` | `sal` |
| `gruff_creature` | Dragon, troll, pirate, monster | `Algenib`, `Fenrir` | `leo` |
| `energetic_adventurer` | Action character | `Fenrir`, `Laomedeia`, `Sadachbia` | `eve` |
| `calm_teacher` | Pedagogical voice | `Erinome`, `Charon`, `Schedar` | `leo` |
| `soft_bedtime` | Sleep stories | `Achernar`, `Vindemiatrix`, `Despina` | `ara` |

ElevenLabs candidates should not be hardcoded in docs unless the account has known voice IDs. Instead, keep placeholders in the registry and fill them from the workspace voice library.

### Voice Discovery Commands

Add provider-specific voice discovery later.

Recommended CLI:

```bash
uv run python generate_audio.py --list-voices --provider gemini
uv run python generate_audio.py --list-voices --provider elevenlabs
uv run python generate_audio.py --list-voices --provider grok
```

Expected output:

```text
provider  voice_id                 name       tags
gemini    Sulafat                  Sulafat    warm, narrator
grok      ara                      Ara        warm, friendly
grok      eve                      Eve        energetic, upbeat
```

For ElevenLabs, the output should include account-specific voices:

```text
provider     voice_id                 name                 category
elevenlabs   JBFqnCBsd6RMkjVDRZzb     George               premade
elevenlabs   abc123...                Grandma Celeste      cloned
```

### Voice Validation

Add a validation command before generating paid audio:

```bash
uv run python generate_audio.py script.md --provider elevenlabs --validate-voices
```

Validation should check:

```text
Every speaker has a resolved voice.
Resolved voice exists for the selected provider when the provider supports lookup.
Voice is compatible with selected model where known.
Voice role exists in voice-map.yaml.
Provider-specific settings are valid.
No Gemini voice name is accidentally used as an ElevenLabs voice ID.
No Grok built-in role is used when a custom voice is required.
```

Validation output example:

```text
Voice resolution for provider elevenlabs:
  Narrator -> warm_narrator -> JBFqnCBsd6RMkjVDRZzb (registry)
  Leo -> playful_child -> EXAVITQu4vr4xnSDxMaL (story override)

Warnings:
  Dragon uses voiceRole gruff_creature but no elevenlabs voice is configured.
  Falling back to provider default voice is disabled in strict mode.
```

### Strict vs Permissive Mode

Use strict voice validation for final production and permissive mode for previews.

```bash
--voice-validation strict
--voice-validation permissive
```

Strict mode:

```text
Missing provider voice -> fail.
Unknown voice role -> fail.
Invalid provider voice -> fail.
```

Permissive mode:

```text
Missing provider voice -> warn and use provider default.
Unknown voice role -> warn and use provider default.
Invalid provider voice -> warn if lookup unavailable, fail if provider confirms invalid.
```

### Voice Mapping and Fallback Providers

Fallback providers complicate voice identity. If generation starts with ElevenLabs and falls back to Gemini, the fallback must resolve the Gemini voice for the same semantic role, not reuse the ElevenLabs voice ID.

Correct fallback:

```text
Leo -> voiceRole playful_child
  elevenlabs -> EXAVITQu4vr4xnSDxMaL
  gemini fallback -> Puck
```

Incorrect fallback:

```text
Leo -> use EXAVITQu4vr4xnSDxMaL with Gemini
```

Provider fallback must rerun voice resolution for the fallback provider.

### Debug Output

Add a dry-run mode to inspect voice mapping without generating audio:

```bash
uv run python generate_audio.py script.md --provider grok --dry-run-voices
```

Output example:

```text
Selected provider: grok

Speaker resolution:
  Narrator
    role: warm_narrator
    voice: ara
    source: registry.roles.warm_narrator.providers.grok.voice

  Leo
    role: playful_child
    voice: eve
    source: story.speakers[Leo].voices.grok
```

This should be part of the first usable multi-provider implementation because voice mistakes are expensive once API generation starts.

## Configuration Plan

Add a provider config file:

```yaml
# config/tts-providers.yaml
default_provider: gemini

providers:
  gemini:
    model: gemini-2.5-flash-preview-tts
    project_env: GOOGLE_CLOUD_PROJECT
    location_env: GOOGLE_CLOUD_REGION
    default_voice: Sulafat
    output_sample_rate: 24000

  elevenlabs:
    model: eleven_multilingual_v2
    api_key_env: ELEVENLABS_API_KEY
    default_voice: JBFqnCBsd6RMkjVDRZzb
    output_format: mp3_44100_128
    voice_settings:
      stability: 0.5
      similarity_boost: 0.75
      style: 0.0
      speed: 1.0

  grok:
    api_key_env: XAI_API_KEY
    default_voice: eve
    language: auto
    output_format:
      codec: mp3
      sample_rate: 44100
      bit_rate: 192000
```

## Error Handling and Fallbacks

Provider-specific failures should be normalized into common error types.

```python
class TTSProviderError(Exception): ...
class TTSRateLimitError(TTSProviderError): ...
class TTSAuthError(TTSProviderError): ...
class TTSValidationError(TTSProviderError): ...
class TTSEmptyAudioError(TTSProviderError): ...
```

Fallback policy should be explicit, not automatic by default.

Recommended CLI:

```bash
--provider elevenlabs
--fallback-provider gemini
```

Fallback rules:

```text
Authentication error -> do not fallback unless explicitly requested.
Rate limit -> retry, then optionally fallback.
Unsupported voice -> fail with clear message.
Unsupported emotion tag -> compile fallback, do not fail.
Empty audio -> retry, then fail.
Verification failure -> re-export if possible, otherwise fail.
```

## Testing Plan

### Unit Tests

Add tests for direction normalization:

```text
"whispered, nervous" -> delivery=["whispering"], emotion=["nervous"]
"laughing, delighted" -> vocal_events=["laugh"], emotion=["excited"] or ["happy"]
"slow, soft" -> pace="slow", volume="soft"
```

Add tests for provider compilers:

```text
Gemini compiler keeps transcript clean.
Gemini compiler places directions in Director's Notes.
Grok compiler emits only allowlisted tags.
Grok compiler drops unsupported descriptors.
Eleven v3 compiler emits audio tags.
Eleven non-v3 compiler avoids spoken direction prose.
```

Add tests for provider-aware batching:

```text
Gemini allows narrator plus character batches.
Grok splits on each speaker change.
Eleven standard splits on each speaker change.
```

### Integration Tests

Use fake providers to avoid paid API calls:

```python
class FakeProvider:
    def synthesize(self, request):
        return SynthesisResult(audio_bytes=fixture_audio, codec="wav", sample_rate=24000, channels=1)
```

Verify:

```text
Pipeline can generate output with gemini fake provider.
Pipeline can generate output with elevenlabs fake provider.
Pipeline can generate output with grok fake provider.
Progress resume still works with provider names included.
Final MP3 verifier still passes.
```

### Manual Listening Tests

Create a small emotion test script:

```markdown
---
stageUuid: "emotion-test"
locale: "en-US"
speakers:
  - name: Narrator
    voiceRole: warm_narrator
  - name: Child
    voiceRole: playful_child
---

**Narrator:** <emotion: warm, slow> The moon rose over the quiet garden.
**Child:** <emotion: whispering, nervous> Did you hear that?
**Narrator:** <emotion: mysterious, dramatic> Something tiny moved behind the flowers.
**Child:** <emotion: excited, laughing> A fairy! A real fairy!
**Narrator:** <emotion: reassuring, soft> And the fairy smiled, because she had been waiting for a friend.
```

Generate with each provider and evaluate:

| Criterion | Gemini | ElevenLabs | Grok |
| --- | --- | --- | --- |
| Directions not spoken | Pass/fail | Pass/fail | Pass/fail |
| Whisper audible | 1-5 | 1-5 | 1-5 |
| Laugh/giggle quality | 1-5 | 1-5 | 1-5 |
| Character consistency | 1-5 | 1-5 | 1-5 |
| Pause naturalness | 1-5 | 1-5 | 1-5 |
| Lunii verification | Pass/fail | Pass/fail | Pass/fail |

## Implementation Phases

### Phase 1: Refactor Without Behavior Change

Tasks:

```text
Add TTSProvider protocol.
Move current Gemini client, prompt builder, and speech config behind GeminiProvider.
Keep current CLI default behavior.
Keep current script format.
Keep existing tests passing.
```

Acceptance criteria:

```text
uv run pytest passes.
Existing generate_audio.py command still works.
Generated Gemini prompts are unchanged or intentionally equivalent.
```

### Phase 2: Add Direction Normalization

Tasks:

```text
Add PerformanceDirection model.
Add emotion normalizer.
Parse current <emotion: ...> into both raw string and structured direction.
Update Gemini prompt builder to use structured direction, with raw fallback.
```

Acceptance criteria:

```text
Existing scripts still parse.
Gemini output behavior remains compatible.
Unit tests cover canonical emotion mapping.
```

### Phase 3: Add Grok Provider

Rationale:

Grok is simpler to integrate than ElevenLabs because the TTS endpoint has explicit output format fields and documented speech tags.

Tasks:

```text
Add GrokProvider.
Add Grok emotion compiler with strict tag allowlist.
Add XAI_API_KEY config.
Add provider-aware one-speaker batching.
Decode returned MP3 through existing audio processing path.
```

Acceptance criteria:

```text
--provider grok generates a Lunii-valid MP3.
Unsupported emotion descriptors are not emitted as fake tags.
Whisper, pause, laugh, and slow examples compile correctly.
```

### Phase 4: Add ElevenLabs Provider

Tasks:

```text
Add ElevenLabsProvider.
Support model selection.
Support voice_settings.
Support output_format=mp3_44100_128 by default.
Add Eleven v3 compiler mode.
Add non-v3 compiler mode.
Optionally support previous_text or previous_request_ids for stitching where supported.
```

Acceptance criteria:

```text
--provider elevenlabs generates a Lunii-valid MP3.
Eleven v3 mode emits tags for supported emotions.
Non-v3 mode does not inject spoken emotional prose by default.
Voice settings can be configured globally and per speaker.
```

### Phase 5: Voice Role Registry

Tasks:

```text
Add voiceRole and voices.<provider> support in speaker config.
Add default voice role mapping file.
Keep legacy voice field working.
Add validation warnings for missing provider voices.
```

Acceptance criteria:

```text
One audio script can target Gemini, ElevenLabs, or Grok without editing speaker names.
Provider-specific voice IDs are resolved predictably.
Missing voice mapping has clear fallback behavior.
```

### Phase 6: Quality Tooling

Tasks:

```text
Add --dry-run-provider-payloads to inspect compiled prompts/payloads without API calls.
Add --save-provider-debug to save prompt JSON and provider metadata.
Add an emotion comparison fixture script.
Add docs for provider selection and emotion authoring.
```

Acceptance criteria:

```text
Writers can preview how a script compiles for each provider.
Provider payloads are debuggable without exposing API keys.
Manual listening test process is documented.
```

## Recommended Authoring Rules

For story writers, keep the input provider-neutral:

```markdown
**Leo:** <emotion: curious, whispering> Is anyone there?
```

Do not write provider syntax directly in story scripts:

```markdown
<!-- Avoid this in canonical scripts -->
**Leo:** [whispers] Is anyone there?
**Leo:** <whisper>Is anyone there?</whisper>
```

Use canonical directions:

```text
happy
excited
sad
scared
nervous
curious
reassuring
whispering
soft
loud
slow
fast
laughing
sighing
pause
long pause
```

Let the compiler choose provider-specific syntax.

## Risks

| Risk | Mitigation |
| --- | --- |
| Provider tags leak into spoken audio | Strict allowlists, manual listening tests, provider-specific fixtures. |
| Emotion behavior differs too much across providers | Treat provider choice as production decision; document expected differences. |
| Multi-speaker support becomes inconsistent | Use one-speaker batching for providers without reliable multi-speaker API support. |
| Voice IDs are not portable | Introduce `voiceRole` plus provider-specific `voices` mapping. |
| Long-form prosody becomes choppy | Use request stitching where available and keep post-processing crossfades. |
| Provider output MP3 differs from Lunii requirements | Always run final export and `MP3Verifier`. |
| Added abstraction makes current Gemini flow harder to maintain | Phase 1 must preserve current behavior and tests before adding new providers. |

## Recommended First Implementation Slice

Start small:

```text
1. Add ProviderCapabilities and TTSProvider protocol.
2. Wrap the existing Gemini implementation as GeminiProvider.
3. Add PerformanceDirection and normalizer, but keep current <emotion: ...> syntax.
4. Add --provider with only gemini supported.
5. Add GrokProvider second because its tag model is explicit and easy to test.
6. Add ElevenLabs after the compiler split is proven.
```

This minimizes risk because the current production path remains Gemini until the provider abstraction is proven.

## Bottom Line

Gemini is best treated as a prompt-directed actor. Emotion should be compiled into clean Director's Notes while preserving a clean transcript.

ElevenLabs is best treated as a voice-performance engine. Emotion is controlled by a mix of voice choice, stability/style/speed settings, punctuation, and model-specific tags, especially in Eleven v3.

Grok is best treated as a tag-directed TTS engine. Emotion should be compiled into a strict set of inline and wrapping speech tags.

The right KidStory architecture is a provider-neutral script plus provider-specific compilers. Writers should describe emotional intent once; the pipeline should decide whether that becomes Gemini Director's Notes, ElevenLabs audio tags and settings, Grok speech tags, or post-processing pauses.
