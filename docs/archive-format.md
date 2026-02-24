# Lunii Story Archive Format Specification

## Overview

The Lunii story archive is a `.zip` file that contains all the data needed for an interactive audio story playable on Lunii storyteller devices. This format serves as the editable source format and can be directly transferred to compatible devices.

The archive format preserves "enriched metadata" (custom node names, positions, types, etc.) which enables non-destructive round-trip editing.

---

## 1. Archive Structure

### Directory Layout

```
{uuid}.zip
├── story.json              # Story descriptor (required)
├── thumbnail.png           # Pack thumbnail (optional, for library display)
└── assets/                 # Media files directory (required)
    ├── {sha1-hash}.bmp     # Image assets
    ├── {sha1-hash}.mp3     # Audio assets
    └── ...
```

### Asset Naming Convention

Assets use **human-readable descriptive names** with their file extension:

- **Format:** `{descriptive-name}{extension}`
- **Examples:** `cover.bmp`, `story-01-olympe.mp3`, `hub-menu.bmp`

Multiple nodes can reference the same asset file, reducing archive size when the same image or audio is used in multiple places.

> **Source vs Device Format:** During authoring, source `story.json` files use human-readable
> slug IDs (e.g., `stage-cover`, `action-to-hub`) and descriptive asset filenames for developer
> convenience. The `export_pack.py` script transforms slug IDs to valid UUIDs when creating the
> device archive. Asset filenames are kept human-readable. The source files are never modified.

---

## 2. Asset Requirements

### Image Assets

| Property | Requirement |
|----------|-------------|
| Format | BMP (4-bit color depth, RLE compressed) |
| Dimensions | 320 x 240 pixels (exactly) |
| Color Palette | Maximum 16 colors |
| MIME Type | `image/bmp` |
| Extension | `.bmp` |

**Technical Details:**
- BMP header byte 28 must be `0x0004` (4-bit depth)
- BMP header byte 30 must be `0x00000002` (RLE compression)
- Images are quantized to 16 colors maximum
- Alpha channels are not supported (transparent pixels render as black)

### Audio Assets

| Property | Requirement |
|----------|-------------|
| Format | MP3 |
| Channels | Mono (1 channel) |
| Sample Rate | 44,100 Hz |
| ID3 Tags | Not allowed (must be stripped) |
| MIME Type | `audio/mpeg` |
| Extension | `.mp3` |

**Important:** The device firmware requires exactly these specifications. Audio files that don't meet these requirements will fail to play.

### Asset References

Assets are referenced from `story.json` by their filename in the `assets/` directory:

```json
{
  "image": "cover.bmp",
  "audio": "cover-welcome.mp3"
}
```

Use `null` for nodes without an image or audio:

```json
{
  "image": null,
  "audio": "story-01-olympe.mp3"
}
```

---

## 3. story.json Specification

### Complete Example

```json
{
  "format": "v1",
  "title": "My Adventure Pack",
  "description": "An exciting story about exploring a magical village",
  "version": 1,
  "nightModeAvailable": true,

  "stageNodes": [
    {
      "uuid": "00000000-0000-0000-0000-000000000000",
      "squareOne": true,
      "name": "Village Entrance",
      "type": "cover",
      "groupId": "village-chapter",
      "position": {"x": 450, "y": 320},
      "image": "a3b5c7d9e1f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0.bmp",
      "audio": "xyz789abc123def456ghi789jkl012mno345pqr678.mp3",
      "okTransition": {
        "actionNode": "action-choose-path",
        "optionIndex": 0
      },
      "homeTransition": null,
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "name": "Village Square",
      "type": "stage",
      "groupId": "village-chapter",
      "position": {"x": 750, "y": 420},
      "image": "b4c6d8e0f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0u2.bmp",
      "audio": null,
      "okTransition": null,
      "homeTransition": null,
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    }
  ],

  "actionNodes": [
    {
      "id": "action-choose-path",
      "name": "Choose Direction",
      "type": "action",
      "groupId": "village-chapter",
      "position": {"x": 650, "y": 320},
      "options": [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
        "33333333-3333-3333-3333-333333333333"
      ]
    }
  ]
}
```

### Pack-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | String | Yes | Format version, always `"v1"` |
| `title` | String | No | Pack display title (enriched metadata) |
| `description` | String | No | Pack description text (enriched metadata) |
| `version` | Integer | Yes | Pack version number (short integer) |
| `nightModeAvailable` | Boolean | Yes | Whether night mode is supported |
| `stageNodes` | Array | Yes | Array of stage node objects |
| `actionNodes` | Array | Yes | Array of action node objects |

### Stage Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | String | Yes | Unique identifier. Must be a valid UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) in the device archive. Source files may use human-readable slugs that are converted during export. |
| `squareOne` | Boolean | No | Entry point marker (only on first node) |
| `name` | String | No | Custom node title (enriched metadata) |
| `type` | String | No | Node type label (enriched metadata) |
| `groupId` | String | No | Groups related nodes (enriched metadata) |
| `position` | Object | No | `{x, y}` coordinates (enriched metadata) |
| `image` | String/null | Yes | Filename in `assets/` directory, or null |
| `audio` | String/null | Yes | Filename in `assets/` directory, or null |
| `okTransition` | Object/null | Yes | Transition when OK button pressed |
| `homeTransition` | Object/null | Yes | Transition when HOME button pressed |
| `controlSettings` | Object | Yes | Which device controls are enabled |

### Action Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Unique identifier. Same UUID format requirement as stage `uuid` in device archives. |
| `name` | String | No | Custom node title (enriched metadata) |
| `type` | String | No | Node type label (enriched metadata) |
| `groupId` | String | No | Groups related nodes (enriched metadata) |
| `position` | Object | No | `{x, y}` coordinates (enriched metadata) |
| `options` | Array | Yes | Array of stage node UUIDs (the choices) |

### Transition Object

```json
{
  "actionNode": "action-node-id",
  "optionIndex": 0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `actionNode` | String | ID of target action node |
| `optionIndex` | Integer | Index in that action's options array (-1 = random) |

**Special Values:**
- `optionIndex: -1` triggers random selection from the action node's options
- `optionIndex: 0` to `N` selects a specific option

### ControlSettings Object

```json
{
  "wheel": true,
  "ok": true,
  "home": true,
  "pause": true,
  "autoplay": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `wheel` | Boolean | Allow wheel rotation to browse options |
| `ok` | Boolean | Allow OK button to advance |
| `home` | Boolean | Allow HOME button to return |
| `pause` | Boolean | Allow PAUSE button during playback |
| `autoplay` | Boolean | Auto-advance when audio finishes |

### Position Object

```json
{
  "x": 450,
  "y": 320
}
```

Coordinates are short integers representing the node's position in a visual editor diagram.

---

## 4. Enriched Metadata

### What Is Enriched Metadata?

Enriched metadata is editor-specific data that enhances the editing experience but is not required for device playback. It includes:

- **Pack-level:** `title`, `description`
- **Node-level:** `name`, `type`, `groupId`, `position`

This metadata enables:
- Custom node names for easier editing
- Visual positioning in diagram editors
- Semantic node types for validation
- Logical grouping of related nodes

### Node Types Reference

| Type Label | Code | Description |
|------------|------|-------------|
| `stage` | 0x01 | Basic content stage node |
| `action` | 0x02 | Basic action/decision node |
| `cover` | 0x11 | Pack cover/entry screen |
| `menu.questionaction` | 0x21 | Menu question action node |
| `menu.questionstage` | 0x22 | Menu question stage node |
| `menu.optionsaction` | 0x23 | Menu options action node |
| `menu.optionstage` | 0x24 | Menu option stage node |
| `story` | 0x31 | Story content node |
| `story.storyaction` | 0x32 | Story action node |

These types are semantic labels that help editors provide appropriate UI and validation. They don't affect device behavior.

---

## 5. Validation Rules

### Structure Validation

1. **Single Entry Point:** Exactly one stage node must have `"squareOne": true`
2. **First Node:** The squareOne node must be the first element in `stageNodes` array
3. **Valid References:** All `actionNode` IDs in transitions must exist in `actionNodes`
4. **Valid Indices:** All `optionIndex` values must be valid indices (or -1 for random)
5. **Valid Options:** All UUIDs in action node `options` must exist in `stageNodes`

### Asset Validation

1. **File Existence:** All referenced assets must exist in `assets/` directory
2. **Image Format:** Images must be BMP, 320x240, 4-bit RLE compressed
3. **Audio Format:** Audio must be MP3, mono, 44100Hz, no ID3 tags

### Content Validation

1. **Non-Empty Options:** Action nodes must have at least one option
2. **Reachable Nodes:** All nodes should be reachable from squareOne (warning only)
3. **Exit Paths:** Stories should have at least one endpoint (`okTransition: null`)

---

## 6. Complete Minimal Example

A simple 3-node linear story:

```json
{
  "format": "v1",
  "title": "My First Story",
  "version": 1,
  "nightModeAvailable": false,

  "stageNodes": [
    {
      "uuid": "00000000-0000-0000-0000-000000000001",
      "squareOne": true,
      "name": "Introduction",
      "image": "intro.bmp",
      "audio": "intro.mp3",
      "okTransition": {
        "actionNode": "action-1",
        "optionIndex": 0
      },
      "homeTransition": null,
      "controlSettings": {
        "wheel": false,
        "ok": true,
        "home": false,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "00000000-0000-0000-0000-000000000002",
      "name": "Middle",
      "image": "middle.bmp",
      "audio": "middle.mp3",
      "okTransition": {
        "actionNode": "action-2",
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
    },
    {
      "uuid": "00000000-0000-0000-0000-000000000003",
      "name": "The End",
      "image": "end.bmp",
      "audio": "end.mp3",
      "okTransition": null,
      "homeTransition": null,
      "controlSettings": {
        "wheel": false,
        "ok": false,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    }
  ],

  "actionNodes": [
    {
      "id": "action-1",
      "options": ["00000000-0000-0000-0000-000000000002"]
    },
    {
      "id": "action-2",
      "options": ["00000000-0000-0000-0000-000000000003"]
    }
  ]
}
```

---

## 7. Best Practices

### When Creating Archives

1. **Use descriptive enriched metadata:**
   - Add meaningful `title` and `description` to packs
   - Give nodes custom `name` values instead of leaving as UUIDs
   - Use `groupId` to organize related nodes

2. **Optimize assets:**
   - Images: Exactly 320x240 pixels, use 16-color palette
   - Audio: Mono, 44100Hz, strip ID3 tags
   - Use descriptive asset filenames for readability

3. **Test before transferring:**
   - Validate all transitions are correct
   - Ensure all asset references are valid
   - Check that squareOne is set on entry node

### Control Settings Patterns

These patterns are derived from working Lunii device stories and MUST be followed.

**Cover Node (Entry Point):**
```json
{"wheel": false, "ok": true, "home": false, "pause": false, "autoplay": false}
```

**Story Chapter (Auto-Play Content):**
```json
{"wheel": false, "ok": false, "home": true, "pause": true, "autoplay": true}
```

**Menu Question Stage (Auto-Advance Prompt):**
```json
{"wheel": false, "ok": false, "home": false, "pause": false, "autoplay": true}
```

**Menu Option Stage (User Browses & Selects):**
```json
{"wheel": true, "ok": true, "home": true, "pause": false, "autoplay": false}
```

**Story Endpoint (Last Chapter, okTransition: null):**
```json
{"wheel": false, "ok": false, "home": true, "pause": true, "autoplay": true}
```

---

## 8. Troubleshooting

### Common Issues

**Missing assets:**
- Check that asset filenames in JSON match files in `assets/` directory
- Ensure file extensions match MIME types

**Audio won't play:**
- Verify MP3 is mono (not stereo)
- Verify sample rate is exactly 44100Hz
- Strip any ID3 tags from MP3 files

**Image won't display:**
- Verify BMP is 320x240 pixels exactly
- Verify BMP uses 4-bit color depth
- Verify BMP uses RLE compression

**Story won't start:**
- Ensure first stageNode has `"squareOne": true`
- Verify the squareOne node is first in the array

### Manual Validation

To validate an archive manually:

1. **Unzip the archive**
2. **Check structure:**
   - `story.json` must exist at root
   - `assets/` directory must exist
   - All referenced assets must be in `assets/`
3. **Validate JSON:**
   - Must be valid JSON syntax
   - Must have `format: "v1"`
   - Must have `stageNodes` and `actionNodes` arrays
4. **Validate transitions:**
   - All `actionNode` IDs must reference existing action nodes
   - All `optionIndex` values must be valid
   - All UUIDs in `options` arrays must reference existing stage nodes
