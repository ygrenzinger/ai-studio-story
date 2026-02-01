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

For stories with dialogue, the TTS supports up to 2 speakers per audio segment:

```python
speaker_voice_configs=[
    SpeakerVoiceConfig(
        speaker='Narrator',
        voice_name='Sulafat'
    ),
    SpeakerVoiceConfig(
        speaker='Luna',
        voice_name='Leda'
    )
]
```

---

## Director's Notes for Voice Control

Beyond voice selection, Gemini TTS responds to natural language direction:

### Style Control
```
Style: Warm and inviting, like a beloved aunt telling a bedtime story
```

### Pacing Control
```
Pacing: Slow and deliberate, with natural pauses for dramatic effect
```

### Emotional Guidance
```
Style: 
* Build gentle suspense without being scary
* "Vocal smile" on descriptions of beauty
* Voice rises with excitement during discoveries
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

## Tips for Best Results

1. **Match voice to character personality** - Don't use a breathy voice for an energetic character

2. **Keep narrator consistent** - Use the same narrator voice throughout the story

3. **Differentiate dialogue** - Use distinct voices for characters to help children follow

4. **Consider bedtime mode** - Softer, slower voices for sleep-time stories

5. **Test combinations** - Some voice pairs work better together than others
