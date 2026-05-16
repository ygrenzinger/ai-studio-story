# Voice Selection Guide for KidStory

## Gemini 3.1 TTS Voice Options

The `/kidstory` command uses Google's Gemini 3.1 Flash TTS by default for high-quality, expressive French story narration. This guide helps you understand the available voices and how they're used in story generation.

---

## Available Voices (30 Options)

### Female Voices

| Voice Name | Characteristic | Best For |
|------------|---------------|----------|
| **Zephyr** | Bright | Cheerful narration, fairy characters |
| **Kore** | Firm | Young protagonists, determined heroes |
| **Leda** | Youthful | Child characters, energetic storytelling |
| **Aoede** | Breezy | Musical moments, lyrical narration |
| **Callirrhoe** | Easy-going | Casual dialogue, friendly characters |
| **Autonoe** | Bright | Optimistic characters, happy scenes |
| **Despina** | Smooth | Calm narration, gentle characters |
| **Erinome** | Clear | Educational content, clear explanations |
| **Gacrux** | Mature | Wise mentors, grandmother figures |
| **Pulcherrima** | Forward | Confident characters, bold statements |
| **Achernar** | Soft | Bedtime stories, soothing narration |
| **Vindemiatrix** | Gentle | Comforting moments, nurturing characters |
| **Laomedeia** | Upbeat | Excited characters, celebrations |
| **Sulafat** | Warm | Primary narrators, welcoming tone |

### Male Voices

| Voice Name | Characteristic | Best For |
|------------|---------------|----------|
| **Puck** | Upbeat | Playful sidekicks, animal friends |
| **Charon** | Informative | Wise narrators, educational content |
| **Fenrir** | Excitable | Adventure stories, action scenes |
| **Orus** | Firm | Authority figures, teachers |
| **Enceladus** | Breathy | Mysterious atmosphere, whispered secrets |
| **Iapetus** | Clear | Clear narration, explanations |
| **Umbriel** | Easy-going | Relaxed characters, casual scenes |
| **Algieba** | Smooth | Smooth narration, storytelling |
| **Algenib** | Gravelly | Gruff but friendly characters |
| **Rasalgethi** | Informative | Narrator, factual content |
| **Alnilam** | Firm | Strong characters, decisive moments |
| **Schedar** | Even | Balanced narration, neutral tone |
| **Achird** | Friendly | Friendly characters, warm interactions |
| **Zubenelgenubi** | Casual | Informal characters, everyday scenes |
| **Sadachbia** | Lively | Energetic characters, exciting moments |
| **Sadaltager** | Knowledgeable | Expert characters, wise figures |

---

## Grok TTS Voice Options

When using `--provider grok`, the built-in voice IDs are smaller and map to broad role archetypes:

| Voice ID | Characteristic | Best For |
|----------|----------------|----------|
| **eve** | Female; energetic, upbeat; engaging and enthusiastic; default voice | Playful children, energetic adventurers |
| **ara** | Female; warm, friendly; balanced and conversational | Warm narrators, gentle children, bedtime stories |
| **rex** | Male; confident, clear; professional and articulate | Clear narration, business-like explanations |
| **leo** | Male; authoritative, strong; decisive and commanding | Wise mentors, teachers, commanding creatures |
| **sal** | Neutral; smooth, balanced; versatile | Mysterious guides, neutral supporting roles |

---

## ElevenLabs TTS Voice Options

When using `--provider elevenlabs`, the registry uses real `voice_id` values rather than placeholders. ElevenLabs documents `JBFqnCBsd6RMkjVDRZzb` as the `eleven_v3` quickstart voice and recommends listing account voices with `GET /v2/voices` for account-specific replacements.

| Role | Voice ID | Voice |
|------|----------|-------|
| `warm_narrator` | `JBFqnCBsd6RMkjVDRZzb` | George |
| `clear_narrator` | `nPczCjzI2devNBz1zQrb` | Brian |
| `playful_child` | `Xb7hH8MSUJpSbSDYk0k2` | Alice |
| `gentle_child` | `XrExE9yKIg1WjnnlVkGX` | Matilda |
| `wise_mentor` | `onwK4e9ZLuTAKqWW03F9` | Daniel |
| `mysterious_guide` | `XB0fDUnXU5powFXDhCwa` | Charlotte |
| `gruff_creature` | `N2lVS1w4EtoT3dr4eOWO` | Callum |
| `energetic_adventurer` | `TX3LPaxmHKxFdv7VOQHJ` | Liam |
| `calm_teacher` | `nPczCjzI2devNBz1zQrb` | Brian |
| `soft_bedtime` | `pFZP5JQG7iQjIQuC4Bku` | Lily |

---

## Voice Selection by Story Tone

The command should select semantic `voiceRole` values based on your chosen story tone. The registry maps those roles to Gemini voices, plus provider-specific equivalents for Grok and ElevenLabs.

### Warm & Gentle
- **Narrator roles:** `warm_narrator`, `soft_bedtime`
- **Character roles:** `gentle_fairy`, `friendly_parent`, `breathy_ghost`
- **Best for:** Bedtime stories, comfort tales, reassuring narratives

### Exciting & Adventurous
- **Narrator roles:** `lively_adventurer`, `clear_male_narrator`
- **Character roles:** `comic_trickster`, `bold_heroine`, `energetic_adventurer`
- **Best for:** Action stories, quests, discovery adventures

### Mysterious & Magical
- **Narrator roles:** `breathy_ghost`, `steady_longform_narrator`
- **Character roles:** `bright_child_narrator`, `queen_or_elder`, `gentle_fairy`
- **Best for:** Fantasy tales, fairy stories, magical journeys

### Playful & Fun
- **Narrator roles:** `comic_trickster`, `bright_optimist`
- **Character roles:** `playful_child`, `cheerful_companion`, `lively_adventurer`
- **Best for:** Comedy, silly stories, animal adventures

### Educational & Calm
- **Narrator roles:** `clear_narrator`, `scholarly_mentor`
- **Character roles:** `calm_teacher`, `lore_wizard`, `mature_elder_narrator`
- **Best for:** Learning content, science exploration, history tales

---

## Character Voice Archetypes

Common story characters and suggested voices:

### Young Protagonist
- `playful_child`, `gentle_child`, `bright_child_narrator`, `firm_heroine`, `breezy_young_hero`

### Wise Mentor
- `mature_elder_narrator`, `scholarly_mentor`, `lore_wizard`, `documentary_mentor`

### Playful Sidekick
- `comic_trickster`, `cheerful_companion`, `lively_adventurer`, `breezy_young_hero`

### Mysterious Guide
- `breathy_ghost`, `queen_or_elder`, `elegant_mentor`, `mysterious_guide`

### Gentle Parent/Guardian
- `warm_narrator`, `soft_bedtime`, `friendly_parent`, `casual_adult_friend`

---

## Multi-Speaker Configuration

The pipeline generates one speaker per request for Gemini to stay compatible with Vertex AI, then assembles narrator + character exchanges locally. Write rich dialogue in the script, but do not rely on Gemini multi-speaker request payloads.

### New Audio Script Format

Speaker configuration is now in the YAML frontmatter with voice selection:

```yaml
---
stageUuid: "stage-entering-forest"
chapterRef: "02-entering-forest"
locale: "fr-FR"
speakers:
  - name: Narrator
    voiceRole: warm_narrator
  - name: Emma
    voiceRole: playful_child
  - name: Dragon
    voiceRole: gruff_creature
---
```

---

## Inline Emotional Markers

Instead of separate Director's Notes, use **inline emotional markers** for precise voice control:

### Marker Format
```
**Speaker:** <emotion: descriptor1, descriptor2> "Dialogue text"
```

### Common Emotion Descriptors

| Category | Descriptors |
|----------|-------------|
| Volume | whispered, soft, loud, shouting |
| Pace | rushed, slow, hesitant, deliberate |
| Feeling | happy, sad, scared, excited, nervous, angry, calm, mysterious |
| Quality | trembling, firm, gentle, harsh, playful, serious, warm, cold |

For Gemini 3.1, supported descriptors are automatically compiled into safe English audio tags such as `[whispers]`, `[excited]`, `[sighs]`, `[laughs]`, and `[very slow]`. Keep scripts provider-neutral with `<emotion: ...>` markers; the provider compiler decides the final syntax.

### Examples

```markdown
**Emma:** <emotion: nervous, quiet> "Is someone there?"
**Dragon:** <emotion: gentle, rumbling> "Do not fear, little one."
**Narrator:** <emotion: tense, hushed> The door creaked open slowly...
**Finn:** <emotion: excited, breathless> "We found it! We actually found it!"
```

### Narrator Context Inheritance

When the narrator describes how a character speaks, that context automatically transfers:

```markdown
**Narrator:** Emma whispered urgently.
**Emma:** "We have to go now!"  <!-- Inherits "whispered urgently" emotion -->
```

### Voice as Baseline

When no emotion marker is present, the selected voice provides the baseline tone:

```yaml
speakers:
  - name: Thorin
    voiceRole: gravelly_villain
```

```markdown
**Thorin:** "Let's get moving."  <!-- Uses Algenib's gravelly baseline -->
**Thorin:** <emotion: annoyed, grumbling> "Not another swamp..."  <!-- Overrides with specific emotion -->
```

---

## Age-Appropriate Voice Direction

### Ages 5-6
- Simple style directions
- Slower pacing (0.75x-0.85x)
- Clear enunciation
- Warm, reassuring tone

### Ages 7-8
- Moderate complexity
- Normal pacing (0.9x-1.0x)
- Some emotional variation
- Engaging but not overwhelming

### Ages 9-10
- Nuanced direction allowed
- Flexible pacing (1.0x-1.1x)
- Full emotional range
- Professional techniques ("vocal smile", dynamic range)

---

## Supported Languages

Gemini TTS supports 24 languages for story generation:

| Language | Code | Language | Code |
|----------|------|----------|------|
| English (US) | en-US | English (India) | en-IN |
| French (France) | fr-FR | German (Germany) | de-DE |
| Spanish (US) | es-US | Italian (Italy) | it-IT |
| Japanese (Japan) | ja-JP | Korean (Korea) | ko-KR |
| Portuguese (Brazil) | pt-BR | Hindi (India) | hi-IN |
| Bengali (Bangladesh) | bn-BD | Tamil (India) | ta-IN |
| Telugu (India) | te-IN | Marathi (India) | mr-IN |
| Dutch (Netherlands) | nl-NL | Polish (Poland) | pl-PL |
| Russian (Russia) | ru-RU | Turkish (Turkey) | tr-TR |
| Thai (Thailand) | th-TH | Vietnamese (Vietnam) | vi-VN |
| Arabic (Egyptian) | ar-EG | Romanian (Romania) | ro-RO |
| Ukrainian (Ukraine) | uk-UA | Indonesian (Indonesia) | id-ID |

---

## Character Voice Selection Guide

Use these archetypes when choosing voices for speakers:

| Character Type | Suggested Roles |
|----------------|-----------------|
| Young Child (5-8) | `playful_child`, `gentle_child`, `bright_child_narrator` |
| Brave Young Hero | `firm_heroine`, `bold_heroine`, `breezy_young_hero` |
| Wise Mentor/Elder | `mature_elder_narrator`, `scholarly_mentor`, `lore_wizard` |
| Playful Sidekick | `comic_trickster`, `cheerful_companion`, `lively_adventurer` |
| Mysterious Being | `breathy_ghost`, `gentle_fairy`, `queen_or_elder` |
| Friendly Monster | `gruff_creature`, `gravelly_villain` |
| Warm Parent | `warm_narrator`, `friendly_parent`, `casual_adult_friend` |
| Story Narrator | `warm_narrator`, `clear_narrator`, `clear_male_narrator`, `steady_longform_narrator` |

---

## Tips for Best Results

1. **Match voice to character personality** - Don't use a breathy voice for an energetic character

2. **Keep narrator consistent** - Use the same narrator voice throughout the story

3. **Differentiate dialogue** - Use distinct voices for characters to help children follow

4. **Consider bedtime mode** - Softer, slower voices for sleep-time stories

5. **Test combinations** - Some voice pairs work better together than others

6. **Use emotion markers sparingly** - Not every line needs a marker; the selected voice provides the baseline tone

7. **Choose voices carefully** - The voice selection determines the character's baseline sound and personality

8. **Keep segments reasonable** - Target 300-800 French words per generated clip and split long scenes at natural boundaries

---

## Audio Generation Command

Generate audio from scripts using:

```bash
# Basic usage
python generate_audio.py script.md -o output.mp3

# With debug output (saves intermediate segment files)
python generate_audio.py script.md -o output.mp3 --debug

# Override voice for testing
python generate_audio.py script.md -o output.mp3 --voice Puck
```

The tool automatically:
- Parses segments with emotion markers
- Generates one speaker per request for Vertex AI-compatible Gemini output
- Generates audio in parallel (up to 5 concurrent calls)
- Combines segments with 300ms pauses and normalized silence
- Outputs mono 44100Hz MP3 without ID3 tags
