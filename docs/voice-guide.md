# Voice Selection Guide for KidStory

## Gemini 2.5 TTS Voice Options

The `/kidstory` command uses Google's Gemini 2.5 TTS for high-quality, expressive audio generation. This guide helps you understand the available voices and how they're used in story generation.

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

## Voice Selection by Story Tone

The command automatically selects voices based on your chosen story tone:

### Warm & Gentle
- **Narrator:** Sulafat (Warm)
- **Characters:** Vindemiatrix (Gentle), Enceladus (Breathy)
- **Best for:** Bedtime stories, comfort tales, reassuring narratives

### Exciting & Adventurous
- **Narrator:** Fenrir (Excitable)
- **Characters:** Puck (Upbeat), Charon (Informative)
- **Best for:** Action stories, quests, discovery adventures

### Mysterious & Magical
- **Narrator:** Enceladus (Breathy)
- **Characters:** Zephyr (Bright), Despina (Smooth)
- **Best for:** Fantasy tales, fairy stories, magical journeys

### Playful & Fun
- **Narrator:** Puck (Upbeat)
- **Characters:** Leda (Youthful), Sadachbia (Lively)
- **Best for:** Comedy, silly stories, animal adventures

### Educational & Calm
- **Narrator:** Charon (Informative)
- **Characters:** Kore (Firm), Gacrux (Mature)
- **Best for:** Learning content, science exploration, history tales

---

## Character Voice Archetypes

Common story characters and suggested voices:

### Young Protagonist
- **Female:** Leda (Youthful) or Kore (Firm)
- **Male:** Puck (Upbeat) or Achird (Friendly)

### Wise Mentor
- **Female:** Gacrux (Mature) or Vindemiatrix (Gentle)
- **Male:** Charon (Informative) or Sadaltager (Knowledgeable)

### Playful Sidekick
- **Female:** Laomedeia (Upbeat) or Aoede (Breezy)
- **Male:** Puck (Upbeat) or Sadachbia (Lively)

### Mysterious Guide
- **Female:** Zephyr (Bright) or Despina (Smooth)
- **Male:** Enceladus (Breathy) or Algieba (Smooth)

### Gentle Parent/Guardian
- **Female:** Sulafat (Warm) or Achernar (Soft)
- **Male:** Umbriel (Easy-going) or Schedar (Even)

---

## Multi-Speaker Configuration

The TTS system now supports **unlimited speakers** through per-segment generation. Each segment is generated with at most 2 speakers (typically Narrator + one character), then combined with 300ms pauses.

### New Audio Script Format

Speaker configuration is now in the YAML frontmatter with voice profiles:

```yaml
---
stageUuid: "stage-entering-forest"
chapterRef: "02-entering-forest"
locale: "en-US"
speakers:
  - name: Narrator
    voice: Sulafat
    profile: "Warm storyteller, like a beloved aunt, vocal smile on beautiful moments"
  - name: Emma
    voice: Leda
    profile: "8-year-old girl, curious and brave, speaks with wonder"
  - name: Dragon
    voice: Fenrir
    profile: "Ancient but friendly dragon, deep rumbling voice, wise and patient"
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

### Voice Profile as Baseline

When no emotion marker is present, the character's voice profile provides the baseline tone:

```yaml
speakers:
  - name: Thorin
    voice: Algenib
    profile: "Gruff dwarf warrior, warmhearted beneath the grumbles"
```

```markdown
**Thorin:** "Let's get moving."  <!-- Uses gruff, warmhearted baseline -->
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

## Character Voice Profile Templates

Use these archetypes when defining speaker profiles:

| Character Type | Profile Template | Suggested Voices |
|----------------|------------------|------------------|
| Young Child (5-8) | "Young child, speaks with wonder and curiosity, simple vocabulary, enthusiastic" | Leda (F), Puck (M) |
| Brave Young Hero | "Determined young hero, curious and brave, speaks clearly with growing confidence" | Kore (F), Achird (M) |
| Wise Mentor/Elder | "Wise elder, patient and kind, speaks slowly with weight and warmth" | Gacrux (F), Charon (M) |
| Playful Sidekick | "Playful companion, energetic and loyal, quick wit, expressive reactions" | Laomedeia (F), Sadachbia (M) |
| Mysterious Being | "Enigmatic presence, speaks with otherworldly quality, hints at ancient knowledge" | Zephyr (F), Enceladus (M) |
| Friendly Monster | "Large but gentle creature, deep voice, surprisingly kind, slightly formal" | Fenrir (M), Algenib (M) |
| Warm Parent | "Loving caregiver, warm and reassuring, protective, gentle encouragement" | Sulafat (F), Umbriel (M) |
| Story Narrator | "Warm storyteller, engaging and expressive, guides listener through the tale" | Sulafat (F), Charon (M) |

---

## Tips for Best Results

1. **Match voice to character personality** - Don't use a breathy voice for an energetic character

2. **Keep narrator consistent** - Use the same narrator voice throughout the story

3. **Differentiate dialogue** - Use distinct voices for characters to help children follow

4. **Consider bedtime mode** - Softer, slower voices for sleep-time stories

5. **Test combinations** - Some voice pairs work better together than others

6. **Use emotion markers sparingly** - Not every line needs a marker; let the profile handle baseline tone

7. **Write descriptive profiles** - The more specific the profile, the more consistent the character voice

8. **Keep segments reasonable** - Avoid monologues over 500 words; break with narrator interjections

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
- Batches Narrator + Character pairs (max 2 speakers per API call)
- Generates audio in parallel (up to 5 concurrent calls)
- Combines segments with 300ms pauses and normalized silence
- Outputs mono 44100Hz MP3 without ID3 tags
