---
description: Export story or pack to Lunii archive format
---

# Export KidStory

Generate the final Lunii-compatible archive for a story or story pack.

## Story/Pack Name

$ARGUMENTS

## Prerequisites

Before export, verify:

### For Single Stories:
1. Story exists and is complete (`status: "complete"`)
2. All chapters are generated
3. All audio scripts exist
4. Validation passes

### For Story Packs:
1. Pack exists and is complete (`status: "complete"`)
2. Hub is complete (cover, menu, welcome-back, goodbye)
3. All stories in pack are complete
4. All audio scripts exist for hub and all stories
5. Pack-wide validation passes

## Workflow

1. **Locate and Detect Type**
   - Find content in `./stories/{name}/`
   - Read `metadata.json` to check `type` field
   - If `type: "story"`: Use single story export
   - If `type: "pack"`: Use pack export workflow

2. **Validate Content**
   - Run full validation (story or pack-specific)
   - If errors exist, prompt for fixes before export

3. **Check Asset Status**
   
   Display asset summary:

   **For Single Stories:**
   - Image prompts ready: X files
   - Audio scripts ready: X files
   - Actual images generated: X files (may be 0)
   - Actual audio generated: X files (may be 0)

   **For Story Packs:**
   - Hub assets: X image prompts, X audio scripts
   - Per-story breakdown:
     - Story 1: X images, X audio files
     - Story 2: X images, X audio files
     - ...
   - Total: X image prompts, X audio scripts
   - Generated: X images, X audio files

4. **Export Options**

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
     "title": "{story/pack title}",
     "description": "{story/pack description}",
     "version": {metadata.version},
     "nightModeAvailable": true,
     
     "stageNodes": [
       // Generated from chapters (story) or hub + all stories (pack)
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

---

## Pack-Specific Export

### Pack story.json Structure

For story packs, generate a hub-based structure:

```json
{
  "format": "v1",
  "title": "Pack Title",
  "description": "Pack description",
  "version": 1,
  "nightModeAvailable": true,

  "stageNodes": [
    // Hub nodes (4 stages)
    {"uuid": "hub-cover", "squareOne": true, ...},
    {"uuid": "hub-menu", "type": "menu.questionstage", ...},
    {"uuid": "hub-welcome-back", ...},
    {"uuid": "hub-goodbye", ...},
    
    // Story 1 nodes
    {"uuid": "story1-ch1", ...},
    {"uuid": "story1-ch2", ...},
    {"uuid": "story1-ending", ...},
    
    // Story 2 nodes
    {"uuid": "story2-ch1", ...},
    // ... etc
  ],

  "actionNodes": [
    // Hub navigation
    {"id": "action-to-menu", "options": ["hub-menu"]},
    {"id": "action-choose-story", "type": "menu.optionsaction", 
     "options": ["story1-ch1", "story2-ch1", "story3-ch1", "hub-goodbye"]},
    {"id": "action-return-menu", "options": ["hub-menu"]},
    {"id": "action-return-welcome", "options": ["hub-welcome-back"]},
    
    // Story 1 navigation
    {"id": "action-story1-ch2", "options": ["story1-ch2"]},
    // ... etc
  ]
}
```

### Hub Stage Generation

Generate hub-specific stages:

1. **Hub Cover** (`hub-cover`)
   - `squareOne: true` - Entry point
   - `type: "cover"`
   - Wheel disabled, OK to continue
   - `okTransition` → `action-to-menu`

2. **Hub Menu** (`hub-menu`)
   - `type: "menu.questionstage"`
   - **Wheel enabled** for story selection
   - `okTransition` → `action-choose-story`
   - Options include all story entry points + goodbye

3. **Welcome Back** (`hub-welcome-back`)
   - Shown after completing a story
   - Encourages exploring more stories
   - `okTransition` → `action-to-menu`

4. **Goodbye** (`hub-goodbye`)
   - Exit message
   - `okTransition: null` (ends pack)

### Per-Story Stage Generation

For each story in the pack:

1. **Story Entry** (first chapter)
   - `homeTransition` → `action-return-menu` (returns to hub)
   - `okTransition` → next chapter

2. **Story Chapters**
   - `homeTransition` → `action-return-menu`
   - `okTransition` → next chapter or ending

3. **Story Ending** (last chapter)
   - `okTransition` → `action-return-welcome` (go to welcome-back)
   - `homeTransition` → `action-return-menu`

### Pack Action Nodes

Generate navigation actions:

1. **`action-to-menu`**: Routes to hub-menu
2. **`action-choose-story`**: Menu selection (type: `menu.optionsaction`)
   - Options: [story1-ch1, story2-ch1, story3-ch1, ..., hub-goodbye]
3. **`action-return-menu`**: Direct return to hub-menu
4. **`action-return-welcome`**: Return via welcome-back message
5. **`action-storyX-chY`**: Per-story chapter transitions

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

   **For Packs:**
   - Generate hub assets first (cover, menu, welcome-back, goodbye)
   - Generate per-story assets in order
   - Use consistent visual style across all assets

8. **Create Archive**

   Generate the final ZIP:

   **For Single Stories:**
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

   **For Story Packs:**
   ```
   {pack-slug}.zip
   ├── story.json
   ├── thumbnail.png (from hub cover)
   └── assets/
       ├── hub-cover.png
       ├── hub-menu.png
       ├── hub-welcome-back.png
       ├── hub-goodbye.png
       ├── hub-cover.mp3
       ├── hub-menu.mp3
       ├── story1-ch1.png
       ├── story1-ch1.mp3
       ├── story1-ch2.png
       ├── story1-ch2.mp3
       └── ... (all story assets)
   ```

9. **Final Validation**

   Before finalizing:

   **Common validations:**
   - Verify all asset references resolve
   - Check squareOne is first node
   - Validate all transitions
   - Confirm no orphaned nodes

   **Pack-specific validations:**
   - Hub cover is squareOne
   - Hub menu has wheel enabled
   - All stories accessible from menu action node
   - All story endings return to hub
   - Home button on all story stages returns to menu

10. **Output**

    Save archive to: `./stories/{slug}/{slug}.zip`
    
    **Report for Single Stories:**
    - Archive location
    - File size
    - Node count (stages + actions)
    - Asset count
    - Ready for Lunii STUdio import

    **Report for Story Packs:**
    - Archive location
    - File size
    - Hub nodes: 4
    - Story nodes: X stages, Y actions
    - Total nodes: Z stages, W actions
    - Stories included: N
    - Asset count: X images, Y audio files
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

For each audio script, use the `generate_audio.py` tool which handles:
- Per-segment TTS generation (supports unlimited speakers)
- Parallel batch processing for speed
- Automatic 300ms pauses between segments
- Silence normalization for clean audio

**Command:**
```bash
python generate_audio.py audio-scripts/{stage}.md -o assets/audio/{stage}.mp3
```

**With debug output (saves intermediate files):**
```bash
python generate_audio.py audio-scripts/{stage}.md -o assets/audio/{stage}.mp3 --debug
```

**Audio Script Format (new):**
```markdown
---
stageUuid: "stage-uuid"
chapterRef: "chapter-ref"
locale: "en-US"
speakers:
  - name: Narrator
    voice: Sulafat
    profile: "Warm storyteller..."
  - name: Emma
    voice: Leda
    profile: "8-year-old girl..."
---

**Narrator:** <emotion: warm> Text with inline emotional markers...

**Emma:** <emotion: curious> "Dialogue with emotion guidance"
```

The tool automatically:
1. Parses segments from the transcript
2. Batches Narrator + Character pairs (max 2 speakers per TTS call)
3. Generates audio in parallel (up to 5 concurrent calls)
4. Combines segments with 300ms pauses
5. Outputs mono 44100Hz MP3 without ID3 tags

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
