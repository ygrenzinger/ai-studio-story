---
description: Export story or pack to device-ready Lunii ZIP archive
---

# Export KidStory

Generate a complete, device-ready Lunii ZIP archive for a story or story pack.

This command orchestrates a **5-phase pipeline**. Each phase must succeed before the next begins. If a phase fails, the command **stops immediately** with recovery instructions. Re-running the command resumes from where it left off (generated assets are preserved).

## Target

$ARGUMENTS

Resolve to: `./stories/$ARGUMENTS/`

If `$ARGUMENTS` is empty or the directory does not exist, list available stories/packs under `./stories/` and STOP.

---

## Pipeline Overview

```
========================================
EXPORT: {title} ({slug})
========================================
Phase 1/5: Validate .............. [?]
Phase 2/5: Generate Covers ....... [?]
Phase 3/5: Generate Audio ........ [?]
Phase 4/5: Verify Assets ......... [?]
Phase 5/5: Create ZIP ............ [?]
========================================
```

Each phase reports one of: `[OK]`, `[SKIP]`, `[FAIL]`

---

## Phase 1: Validate

**Purpose**: Confirm all source material exists before any generation work.

**Always runs** (cheap file-existence checks).

### Checks (in order):

1. **Directory exists**: `./stories/{slug}/` must exist
2. **metadata.json**: Must exist, parse as valid JSON, contain `type` field (`"story"` or `"pack"`) and `title` field
3. **story.json**: Must exist at `./stories/{slug}/story.json`. Parse and confirm:
   - `format` is `"v1"`
   - `stageNodes` array is non-empty
   - `actionNodes` array exists
   - First stageNode has `"squareOne": true`
4. **story.json structural integrity**:
   - All `actionNode` IDs referenced in transitions exist in `actionNodes`
   - All stage UUIDs referenced in action `options` exist in `stageNodes`
   - No orphaned action nodes (every action node is referenced by at least one transition)
5. **Source content completeness** (depends on type):

   **For `type: "pack"`:**
   
   For each audio filename referenced in `story.json`, verify the corresponding source `.md` script exists. Use this mapping:

   | Audio filename in story.json | Expected source script |
   |------------------------------|----------------------|
   | `cover-welcome.mp3` | `hub/cover-welcome.md` |
   | `hub-menu.mp3` | `hub/menu.md` |
   | `hub-welcome-back.mp3` | `hub/welcome-back.md` |
   | `option-{name}.mp3` | `hub/option-{name}.md` |
   | `story-{nn}-{name}.mp3` | `stories/{id}/audio-script.md` |

   Specifically check:
   - `hub/cover-welcome.md` exists
   - `hub/menu.md` exists
   - `hub/welcome-back.md` exists
   - For each `option-*.mp3` in story.json: corresponding `hub/option-*.md` exists
   - For each story listed in metadata: `stories/{id}/audio-script.md` exists
   - For each story listed in metadata: `stories/{id}/chapter.md` exists

   **For `type: "story"`:**
   - Audio scripts exist in `audio-scripts/` directory
   - Story content files exist

### On success:
```
Phase 1/5: Validate .............. [OK]
  Type:        pack
  Title:       Le Petit Explorateur des Croyances
  Stages:      17 stage nodes
  Actions:     10 action nodes
  Images needed: 16
  Audio needed:  17
```

### On failure -- STOP:
```
Phase 1/5: Validate .............. [FAIL]

Validation errors:
  - stories/explorateur-croyances/story.json: missing
  - stories/explorateur-croyances/stories/03-guerriers-nord/audio-script.md: missing

STOPPED. Fix the above issues, then re-run:
  /kidstory export {slug}
```

---

## Phase 2: Generate Covers

**Purpose**: Produce all BMP image assets referenced in `story.json`.

### Before running:

1. Extract all unique non-null `image` values from `story.json` `stageNodes[].image`
2. Ensure `./stories/{slug}/assets/` directory exists (create if needed)
3. Check which image files already exist in `./stories/{slug}/assets/`
4. If **ALL** image files already exist:
   ```
   Phase 2/5: Generate Covers ....... [SKIP] (16/16 already exist)
   ```
   Proceed to Phase 3.

### Execution:

Invoke the **cover-generator** subagent via the **Task tool**.

The prompt to the subagent MUST include:
- The full path to the story/pack directory: `./stories/{slug}/`
- The output directory: `./stories/{slug}/assets/`
- For each required image, a description to generate from:
  - **Cover image**: Use pack/story title and description from `metadata.json`
  - **Hub menu image**: Derive from hub description or outline
  - **Option images**: Use each story's title and theme from `metadata.json`
  - **Story images**: Use chapter description from first paragraph of `chapter.md`
- Explicit instruction: output filenames MUST match exactly what `story.json` references (e.g., `cover.bmp`, `option-olympe.bmp`, `story-01-olympe.bmp`)
- Explicit instruction: skip any file that already exists

### Checking the result:

After the subagent returns, inspect its final summary for the **"Failed"** count.

### Thumbnail Generation

After cover images are generated, check for `thumbnail.png`:

1. Check if `./stories/{slug}/thumbnail.png` exists and is a valid PNG (use `file` command)
2. If missing or invalid:
   - Invoke the **thumbnail-generator** subagent via the **Task tool**
   - Use the pack/story title and description from `metadata.json`
   - Output: `./stories/{slug}/thumbnail.png`
3. If already exists and is valid PNG: Skip

### On success (Failed: 0):
```
Phase 2/5: Generate Covers ....... [OK] (16/16)
  Thumbnail: [OK] (300x300 PNG)
```

### On failure (Failed > 0) -- STOP:
```
Phase 2/5: Generate Covers ....... [FAIL]

Cover generation failed for 2 files:
  - option-nord.bmp: API error - rate limit exceeded
  - story-03-nord.bmp: Authentication error

STOPPED. Fix the issue, then re-run:
  /kidstory export {slug}
  (Successfully generated covers will be preserved)
```

---

## Phase 3: Generate Audio

**Purpose**: Produce all MP3 audio assets referenced in `story.json`.

### Before running:

1. Extract all unique non-null `audio` values from `story.json` `stageNodes[].audio`
2. Ensure `./stories/{slug}/assets/` directory exists
3. Check which audio files already exist in `./stories/{slug}/assets/`
4. If **ALL** audio files already exist:
   ```
   Phase 3/5: Generate Audio ........ [SKIP] (17/17 already exist)
   ```
   Proceed to Phase 4.

### Execution:

Invoke the **audio-generator** subagent via the **Task tool**.

The prompt to the subagent MUST include:
- The full path to the story/pack directory: `./stories/{slug}/`
- The output directory: `./stories/{slug}/assets/`
- The explicit mapping from source audio-script to output filename:

  **For packs:**
  ```
  Hub audio:
    hub/menu.md           -> assets/hub-menu.mp3
    hub/welcome-back.md   -> assets/hub-welcome-back.mp3
    hub/{script}.md       -> assets/{script}.mp3

  Story audio:
    stories/{id}/audio-script.md -> assets/story-{nn}-{short-name}.mp3
  ```

  Build this mapping by cross-referencing:
  - The audio filenames from `story.json`
  - The source `.md` files discovered in the directory structure
  - The story IDs from `metadata.json`

- Explicit instruction: output filenames MUST match exactly what `story.json` references
- Explicit instruction: skip any file that already exists

### Checking the result:

After the subagent returns, inspect its final summary for the **"Failed"** count.

### On success (Failed: 0):
```
Phase 3/5: Generate Audio ........ [OK] (17/17)
```

### On failure (Failed > 0) -- STOP:
```
Phase 3/5: Generate Audio ........ [FAIL]

Audio generation failed for 3 files:
  - story-01-olympe.mp3: Rate limit exceeded (429)
  - story-02-nil.mp3: Rate limit exceeded (429)
  - option-olympe.mp3: Missing source script

STOPPED. Fix the issue, then re-run:
  /kidstory export {slug}
  (Successfully generated audio will be preserved)
```

---

## Phase 4: Verify All Assets

**Purpose**: Cross-reference every asset in `story.json` against files on disk. Safety gate before ZIP creation.

**Always runs** (cheap file-existence checks).

### Checks:

1. Extract all unique non-null `image` values from `story.json` `stageNodes[]`
2. Extract all unique non-null `audio` values from `story.json` `stageNodes[]`
3. For each referenced file, confirm it exists at `./stories/{slug}/assets/{filename}`
4. Build two lists: `present` and `missing`

### On success:
```
Phase 4/5: Verify Assets ......... [OK]
  Thumbnail: present (300x300 PNG)
  Images: 16/16 present
  Audio:  17/17 present
  Total:  33/33 assets verified
```

### On failure -- STOP:
```
Phase 4/5: Verify Assets ......... [FAIL]

Missing assets referenced by story.json:
  Images (2 missing):
    - option-nord.bmp (referenced by stage "stage-option-nord")
    - story-03-nord.bmp (referenced by stage "stage-story-03-nord")
  Audio (1 missing):
    - story-03-nord.mp3 (referenced by stage "stage-story-03-nord")

STOPPED. Re-run to regenerate missing assets:
  /kidstory export {slug}
```

---

## Phase 5: Create ZIP

**Purpose**: Transform source story.json for device compatibility and assemble the final Lunii archive.

### Before running:

1. If a previous ZIP exists in `./stories/{slug}/`, delete it (always rebuild)

### Steps:

1. **Run the export script**:
   ```bash
   uv run python stories/{slug}/export_pack.py
   ```

   The script performs these transformations automatically:

   **Step 5a: UUID Conversion**
   - Builds a mapping of every slug ID to a UUID v5
   - Uses a fixed project namespace UUID with `uuid.uuid5(namespace, slug)`
   - Same slug always produces the same UUID (deterministic/reproducible)
   - If an ID is already a valid UUID, it is kept as-is
   - The pack UUID = UUID of the first (squareOne) stage node
   - The Lunii device firmware calls `java.util.UUID.fromString()` on every `uuid` and `id` field -- non-UUID values crash the device

   **Step 5b: Story.json Transformation**
   - Deep-copies the source story.json (source file is NEVER modified)
   - Replaces all stage `uuid` fields with their UUID v5 equivalents
   - Replaces all action `id` fields with their UUID v5 equivalents
   - Updates all `actionNode` references in transitions
   - Updates all stage UUID references in action `options` arrays
   - Asset filenames (`image`, `audio`) are kept as-is (human-readable)

   **Step 5c: ZIP Filename**
   - Reads the `title` field from `metadata.json`
   - Slugifies it: lowercase, strip accents/diacritics, replace spaces and special characters with hyphens, collapse consecutive hyphens, trim leading/trailing hyphens
   - Uses the result as the ZIP filename: `{title-slug}.zip`

   **Step 5d: Archive Assembly**
   - Writes transformed `story.json` to ZIP root
   - Writes `thumbnail.bmp` (copy of cover image) to ZIP root
   - Writes all assets to `assets/` directory

2. **Verify ZIP** was created and is non-empty.

### Archive structure:
```
{title-slug}.zip
├── story.json              # Transformed: valid UUIDs for all node IDs
├── thumbnail.png           # 300x300 pack/story thumbnail
└── assets/
    ├── cover.bmp
    ├── hub-menu.bmp
    ├── option-olympe.bmp
    ├── ...
    ├── cover-welcome.mp3
    ├── hub-menu.mp3
    └── ...
```

> **ZIP filename**: `{title-slug}` is derived by slugifying the `title` field from `metadata.json`:
> lowercase, strip accents/diacritics, replace spaces and special characters with hyphens, collapse consecutive hyphens, trim leading/trailing hyphens.
> Example: `"Le Petit Explorateur des Croyances"` → `le-petit-explorateur-des-croyances.zip`

### Important: Source files are never modified

The UUID transformation is applied only to the copy written into the ZIP. The source `story.json` on disk retains human-readable slug IDs for easy editing.

### On success:
```
Phase 5/5: Create ZIP ............ [OK]
```

### On failure -- STOP:
```
Phase 5/5: Create ZIP ............ [FAIL]

ZIP creation failed: {error message}

STOPPED. Check disk space and permissions, then re-run:
  /kidstory export {slug}
```

---

## Final Report

After all 5 phases succeed, print:

```
========================================
EXPORT COMPLETE
========================================
Pack:       {title}
Archive:    stories/{slug}/{title-slug}.zip
Size:       {file size}

Contents:
  story.json      (1 file)
  thumbnail.png   (1 file, or "skipped" if not generated)
  Images:         {N} BMP files
  Audio:          {M} MP3 files
  Total assets:   {N+M} files

Stage nodes:      {count}
Action nodes:     {count}

Next steps:
  1. Open Lunii STUdio
  2. Go to Library > Import
  3. Select: stories/{slug}/{title-slug}.zip
  4. Transfer to Lunii device
========================================
```

---

## Restart Behavior

This command is **safe to re-run** at any point:

| Phase | On re-run behavior |
|-------|-------------------|
| Phase 1: Validate | Always runs (cheap) |
| Phase 2: Generate Covers | Skips existing BMP files, only generates missing ones |
| Phase 3: Generate Audio | Skips existing MP3 files, only generates missing ones |
| Phase 4: Verify Assets | Always runs (cheap safety check) |
| Phase 5: Create ZIP | Always rebuilds (derived artifact) |

If a previous run failed at Phase 3 with 2 audio files failing, re-running will:
- Phase 1: Re-validate (fast)
- Phase 2: SKIP (all covers already exist)
- Phase 3: Generate only the 2 missing audio files
- Phase 4: Verify everything
- Phase 5: Create fresh ZIP

---

## Environment Requirements

Before running, ensure:

- **For cover generation (Phase 2):**
  - `GOOGLE_CLOUD_PROJECT` environment variable is set
  - Authenticated via `gcloud auth application-default login`

- **For audio generation (Phase 3):**
  - `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable is set

---

## Important Rules

1. **Never generate or modify story.json** -- it is a pre-existing input
2. **Never modify source files** (audio-scripts, chapters, metadata)
3. **Always delegate** cover generation to the cover-generator subagent
4. **Always delegate** audio generation to the audio-generator subagent
5. **Stop immediately** on any phase failure -- never continue to the next phase
6. **Always report** which specific files failed and how to recover
7. **Source asset filenames must match** what the source story.json references. During export, the script converts slug IDs to valid UUIDs for device compatibility. Asset filenames are kept human-readable.
