---
description: Export story to Lunii archive format
---

# Export KidStory

Generate the final Lunii-compatible archive for a story.

## Story Name

$ARGUMENTS

## Prerequisites

Before export, verify:
1. Story exists and is complete (`status: "complete"`)
2. All chapters are generated
3. All audio scripts exist
4. Validation passes

## Workflow

1. **Locate and Validate Story**
   - Find story in `./stories/{story-name}/`
   - Run full validation
   - If errors exist, prompt for fixes before export

2. **Check Asset Status**
   
   Display asset summary:
   - Image prompts ready: X files
   - Audio scripts ready: X files
   - Actual images generated: X files (may be 0)
   - Actual audio generated: X files (may be 0)

3. **Export Options**

   Ask user what to export:

   **Option A: Source Files Only**
   - Export the current state without generated assets
   - Useful for further editing or manual asset creation

   **Option B: With Placeholder Assets**
   - Create placeholder image files (solid color with text)
   - Useful for testing story flow on device

   **Option C: Full Archive (when assets ready)**
   - Include all generated images and audio
   - Complete, device-ready archive

4. **Generate story.json**

   Transform the story structure into Lunii format:

   ```json
   {
     "format": "v1",
     "title": "{story title}",
     "description": "{story description}",
     "version": {metadata.version},
     "nightModeAvailable": true,
     
     "stageNodes": [
       // Generated from chapters
     ],
     
     "actionNodes": [
       // Generated from transitions
     ]
   }
   ```

5. **Stage Node Generation**

   For each chapter/stage:
   ```json
   {
     "uuid": "{unique-id}",
     "squareOne": true/false,
     "name": "{chapter title}",
     "type": "{cover|stage|story}",
     "image": "{asset-hash}.png",
     "audio": "{asset-hash}.mp3",
     "okTransition": {
       "actionNode": "{action-id}",
       "optionIndex": 0
     },
     "homeTransition": null,
     "controlSettings": {
       "wheel": false,
       "ok": true,
       "home": true,
       "pause": true,
       "autoplay": false
     }
   }
   ```

6. **Action Node Generation**

   For each transition:
   ```json
   {
     "id": "{action-id}",
     "name": "{transition name}",
     "type": "action",
     "options": ["{target-stage-uuid}", ...]
   }
   ```

7. **Asset Preparation**

   **For images (placeholders):**
   - Create 320x240 PNG files
   - Solid color background
   - Text with chapter name
   - Store in `assets/images/`

   **For audio (if generating):**
   - Use Gemini TTS API
   - Process each audio script
   - Convert to required format (mono, 32kHz, 16-bit)
   - Store in `assets/audio/`

8. **Create Archive**

   Generate the final ZIP:
   ```
   {story-slug}.zip
   ├── story.json
   ├── thumbnail.png (from cover image)
   └── assets/
       ├── {hash1}.png
       ├── {hash2}.png
       ├── {hash3}.mp3
       └── ...
   ```

9. **Final Validation**

   Before finalizing:
   - Verify all asset references resolve
   - Check squareOne is first node
   - Validate all transitions
   - Confirm no orphaned nodes

10. **Output**

    Save archive to: `./stories/{story-slug}/{story-slug}.zip`
    
    Report:
    - Archive location
    - File size
    - Node count
    - Asset count
    - Ready for Lunii STUdio import

## Asset Generation (Optional)

If user wants to generate actual assets:

### Image Generation

For each image prompt file:
1. Read the prompt from `assets/images/{stage}.prompt.md`
2. Call image generation API (DALL-E, Midjourney, etc.)
3. Resize to 320x240
4. Save as PNG
5. Update asset references

### Audio Generation

For each audio script:
1. Read the script from `audio-scripts/{stage}.md`
2. Extract TTS configuration
3. Call Gemini TTS API:
   ```python
   response = client.models.generate_content(
     model="gemini-2.5-flash-preview-tts",
     contents=transcript,
     config=GenerateContentConfig(
       response_modalities=["AUDIO"],
       speech_config=SpeechConfig(
         multi_speaker_voice_config=MultiSpeakerVoiceConfig(
           speaker_voice_configs=[...]
         )
       )
     )
   )
   ```
4. Convert to required format
5. Save to `assets/audio/`

## Archive Naming

Final archive: `{story-slug}.{timestamp}.zip`

Example: `magic-forest-adventure.1706789456.zip`

## Lunii STUdio Import

After export, instruct user:
1. Open Lunii STUdio application
2. Go to Library > Import
3. Select the generated .zip file
4. Verify story appears in library
5. Transfer to Lunii device

## Error Handling

If export fails:
- Report specific error
- Suggest fixes
- Offer partial export if possible
- Keep source files intact

## Important Notes

- Always validate before export
- Warn about placeholder assets
- Provide clear next steps
- Remind about audio/image generation needs
