# Archive Format Documentation

## Overview

Archives are `.zip` files that serve as the **editable source format** for story packs in STUdio. They're created in the browser, uploaded to the backend, and stored in `~/.studio/library/`.

The archive format is the only format that preserves "enriched metadata" (custom node names, positions, types, etc.) which enables non-destructive round-trip editing. When transferring packs to devices, archives are automatically converted to Binary (firmware v1.x) or Filesystem (firmware v2.x) formats.

---

## 1. Creation & Update Workflow

### Frontend Creation (JavaScript)

**Location:** `web-ui/javascript/src/utils/writer.js:12-274`

The archive is created entirely in the browser:

```javascript
// User clicks save in PackEditor → writeToArchive() is called

// 1. Create ZIP archive with assets folder
const zip = new JSZip();
zip.folder('assets');

// 2. Process all diagram nodes (stage, action, menu, story, cover)
// 3. Hash assets using SHA-1 and deduplicate
// 4. Store assets as separate files in assets/ directory
// 5. Build the story.json descriptor
// 6. Return Blob containing the complete .zip
```

**Workflow:**
1. User clicks save button in PackEditor (`web-ui/javascript/src/components/diagram/PackEditor.js:199-200`)
2. `writeToArchive()` creates a JSZip archive
3. All diagram nodes are processed and converted to JSON
4. Assets are hashed (SHA-1) to deduplicate them
5. Assets are stored in `assets/` directory with hash-based filenames
6. `story.json` descriptor is generated
7. Archive blob is returned

### Upload to Backend

**Location:** `web-ui/javascript/src/services/library.js:27-44`

The archive blob is uploaded via multipart form:

```javascript
uploadToLibrary(uuid, path, packBlob)
// → POST /api/library/upload
// Parameters: uuid, path, pack (file)
```

### Backend Saves to Disk

**Location:** `web-ui/src/main/java/studio/webui/service/LibraryService.java:374-392`

```java
public void addPackFile(String uuid, String path, FileUpload upload) {
    // Saves to: ~/.studio/library/{uuid}.{timestamp}.zip
    // Deletes existing file if overwriting
}
```

**Controller endpoint:** `web-ui/src/main/java/studio/webui/api/LibraryController.java:63-75`

**Filename format:** `{uuid}.{timestamp}.zip`

### Metadata Extraction & Caching

**Location:** `web-ui/src/main/java/studio/webui/service/LibraryService.java:88-156`

After saving, the backend:
1. Reads all archives using `ArchiveStoryPackReader`
2. Extracts metadata for library display
3. Caches parsed packs for 5 minutes (Caffeine cache)
4. Updates unofficial metadata database

---

## 2. Archive Content Structure

### Directory Layout

```
{uuid}.{timestamp}.zip
├── story.json              # Main descriptor (JSON format)
├── thumbnail.png           # Optional pack thumbnail image
└── assets/                 # Directory containing all media files
    ├── a3b5c7d9...t0.png  # Image files (SHA-1 hash + extension)
    ├── b4c6d8e0...u1.jpg  # Images are 320x240 pixels
    ├── xyz789ab...u2.mp3  # Audio files (mono 32kHz signed 16-bit)
    ├── def456gh...v3.ogg  # Multiple nodes can reference same asset
    └── ...
```

### Asset Naming Convention

**Location:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:93-105`

- **Format:** `{SHA-1_hash}{extension}`
- **Example:** `a3b5c7d9e1f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0.png`
- **Hashing:** SHA-1 hash of asset content (frontend and backend both use SHA-1)
- **Automatic deduplication:** Same content = same filename, stored only once

**Supported Asset Formats:**

**Images** (`core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:210-215`):
- `.bmp` - 24-bit bitmap
- `.png` - Portable Network Graphics
- `.jpg` - JPEG
- **Required dimensions:** 320x240 pixels
- Conversion handled by `ImageConversion` class

**Audio** (`core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:216-221`):
- `.mp3` - MPEG Audio Layer 3
- `.ogg` - Ogg Vorbis
- `.wav` - WAVE PCM
- **Required format:** Mono, 32kHz sample rate, signed 16-bit
- Conversion handled by `AudioConversion` class

### Asset References

Assets are referenced from `story.json` by their filename:

```json
{
  "image": "a3b5c7d9e1f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0.png",
  "audio": "xyz789abc123def456ghi789jkl012mno345pqr678.mp3"
}
```

Multiple nodes can reference the same asset file (deduplicated storage).

---

## 3. story.json Structure

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
      "type": "stage",
      "groupId": "village-chapter",
      "position": {"x": 450, "y": 320},
      "image": "a3b5c7d9e1f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0.png",
      "audio": "xyz789abc123def456ghi789jkl012mno345pqr678.mp3",
      "okTransition": {
        "actionNode": "action-choose-path",
        "optionIndex": 0
      },
      "homeTransition": {
        "actionNode": "action-go-home",
        "optionIndex": 1
      },
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
      "image": "b4c6d8e0f2g4h6i8j0k2l4m6n8o0p2q4r6s8t0u2.png",
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

### Field Reference

#### Pack-Level Fields

**Code:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:46-67`

| Field | Type | Required | Description | Enriched? |
|-------|------|----------|-------------|-----------|
| `format` | String | Yes | Always `"v1"` | No |
| `title` | String | No | Pack display title (shown in library) | **Yes** |
| `description` | String | No | Pack description text | **Yes** |
| `version` | Integer | Yes | Pack version number | No |
| `nightModeAvailable` | Boolean | Yes | Whether night mode is supported | No |
| `stageNodes` | Array | Yes | Array of stage node objects | No |
| `actionNodes` | Array | Yes | Array of action node objects | No |

#### Stage Node Fields

**Code:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:72-141`

| Field | Type | Required | Description | Enriched? |
|-------|------|----------|-------------|-----------|
| `uuid` | String | Yes | Unique identifier (UUID format) | No |
| `squareOne` | Boolean | No | Entry point marker (only on first node) | No |
| `name` | String | No | Custom node title for editor display | **Yes** |
| `type` | String | No | Node type label (see EnrichedNodeType) | **Yes** |
| `groupId` | String | No | Groups related nodes (e.g., menu question/options) | **Yes** |
| `position` | Object | No | `{x, y}` coordinates for visual diagram | **Yes** |
| `image` | String/null | Yes | Filename in `assets/` directory, or null | No |
| `audio` | String/null | Yes | Filename in `assets/` directory, or null | No |
| `okTransition` | Object/null | Yes | Transition when OK button pressed | No |
| `homeTransition` | Object/null | Yes | Transition when HOME button pressed | No |
| `controlSettings` | Object | Yes | Which device controls are enabled | No |

**Position Object:**
```json
{
  "x": 450,  // X coordinate (short integer)
  "y": 320   // Y coordinate (short integer)
}
```

**Transition Object** (`core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:140-148`):
```json
{
  "actionNode": "action-node-id",  // ID of target action node
  "optionIndex": 0                 // Index in that action's options array
}
```

**ControlSettings Object:**
```json
{
  "wheel": true,      // Allow wheel control
  "ok": true,         // Allow OK button
  "home": true,       // Allow HOME button
  "pause": true,      // Allow PAUSE button
  "autoplay": false   // Enable autoplay
}
```

#### Action Node Fields

**Code:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:143-163`

| Field | Type | Required | Description | Enriched? |
|-------|------|----------|-------------|-----------|
| `id` | String | Yes | Unique identifier | No |
| `name` | String | No | Custom node title for editor | **Yes** |
| `type` | String | No | Node type label | **Yes** |
| `groupId` | String | No | Groups related nodes | **Yes** |
| `position` | Object | No | `{x, y}` coordinates for diagram | **Yes** |
| `options` | Array | Yes | Array of stage node UUIDs (the choices) | No |

**Options Array:**
```json
"options": [
  "stage-uuid-1",  // First choice
  "stage-uuid-2",  // Second choice
  "stage-uuid-3"   // Third choice
]
```

The order in the array determines the option index used in transitions.

---

## 4. Enriched Metadata

### What Is Enriched Metadata?

**Enriched metadata** is editor-specific data that doesn't exist in device firmware formats. It's stored ONLY in Archive format and enables:
- Custom node names for easier editing
- Visual positioning in the diagram editor
- Semantic node types (cover, story, menu, etc.)
- Logical grouping of related nodes

**Key principle:** Device firmwares don't understand enriched metadata, so it's stripped out during conversion to Binary/Filesystem formats. This is why Archive is the "source of truth" for editing.

### Pack-Level Enriched Metadata

**Model:** `core/src/main/java/studio/core/v1/model/enriched/EnrichedPackMetadata.java`

Stored in the root of `story.json`:

```json
{
  "title": "My Adventure Pack",
  "description": "An exciting story about exploring a magical village"
}
```

**Fields:**
- `title` (String) - Pack display name shown in library
- `description` (String) - Pack description text
- `thumbnail` - TODO: Not yet implemented

**Code:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:50-61`

### Node-Level Enriched Metadata

**Model:** `core/src/main/java/studio/core/v1/model/enriched/EnrichedNodeMetadata.java`

Contains four optional fields added to both stage and action nodes:

```json
{
  "name": "Village Entrance",           // Custom node title
  "type": "stage",                      // Semantic node type
  "groupId": "village-chapter",         // Logical grouping
  "position": {"x": 450, "y": 320}     // Visual coordinates
}
```

**Fields:**

1. **name** (String)
   - Custom display name for the node
   - Shows in diagram editor instead of UUID
   - Example: "Village Entrance" instead of "00000000-0000-0000-0000-000000000000"

2. **type** (String)
   - Semantic node type from EnrichedNodeType enum
   - Helps editor provide appropriate UI/validation
   - See "Node Types" section below

3. **groupId** (String)
   - Groups related nodes together
   - Example: Menu question + menu options share same groupId
   - Example: All nodes in same chapter share same groupId

4. **position** (Object)
   - `x` (short) - X coordinate in diagram editor
   - `y` (short) - Y coordinate in diagram editor
   - Preserves visual layout between editing sessions

**Code:**
- Write: `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:183-206`
- Read: `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:262-280`

### Node Types (EnrichedNodeType)

**Enum:** `core/src/main/java/studio/core/v1/model/enriched/EnrichedNodeType.java:10-18`

| Type Label | Description |
|------------|-------------|
| `stage` | Basic stage node (default) |
| `action` | Basic action node (default) |
| `cover` | Pack selection/cover screen |
| `menu.questionaction` | Menu question action node |
| `menu.questionstage` | Menu question stage node |
| `menu.optionsaction` | Menu options action node |
| `menu.optionstage` | Menu option stage node |
| `story` | Story content node |
| `story.storyaction` | Story action node |

These types are semantic labels that help the editor provide appropriate UI and validation. They don't affect device behavior.

### Why Enriched Metadata Matters

**During Archive → Binary/Filesystem conversion:**
- Enriched metadata is **stripped out** (devices don't understand it)
- Only device-compatible fields are written
- Visual layout and custom names are lost

**During Binary/Filesystem → Archive conversion:**
- Enriched metadata **cannot be recovered** (it never existed in device format)
- Nodes will have default names (UUIDs)
- Visual positions will be auto-generated or randomized

**This is why:**
1. Archive format is the "source of truth" for editing
2. Always edit archives, never device formats directly
3. Store your original archives for future editing

---

## 5. Asset Processing

### Asset Hashing

**Frontend:** `web-ui/javascript/src/utils/writer.js:96, 105`
```javascript
// Computes SHA-1 hash of base64 data URL
const hash = hashDataUrl(dataUrl);
const filename = `${hash}.${extension}`;
```

**Backend:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:93, 103`
```java
// Uses Apache Commons DigestUtils
String hash = DigestUtils.sha1Hex(imageAsset);
String filename = hash + "." + extension;
```

### MIME Type to Extension Mapping

**Code:** `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:208-225`

```java
private String extensionFromMimeType(String mimeType) {
    // Images
    if ("image/bmp".equals(mimeType)) return ".bmp";
    if ("image/png".equals(mimeType)) return ".png";
    if ("image/jpeg".equals(mimeType)) return ".jpg";

    // Audio
    if ("audio/wav".equals(mimeType) || "audio/x-wav".equals(mimeType)) return ".wav";
    if ("audio/mpeg".equals(mimeType) || "audio/mp3".equals(mimeType)) return ".mp3";
    if ("audio/ogg".equals(mimeType) || "audio/x-ogg".equals(mimeType)) return ".ogg";
}
```

### Reading Assets

**Code:** `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:206-248`

1. All files in `assets/` directory are enumerated
2. Each file is loaded into memory
3. Extension determines MIME type
4. Assets are mapped to stage nodes based on filename references in JSON

---

## 6. Key Code Locations

### Writing Archives

| Component | Location | Description |
|-----------|----------|-------------|
| Main writer | `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:28-181` | Complete write() method |
| Enriched metadata writer | `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:183-206` | Writes enriched fields |
| Frontend builder | `web-ui/javascript/src/utils/writer.js:12-274` | Browser-side archive creation |
| MIME mapping | `core/src/main/java/studio/core/v1/writer/archive/ArchiveStoryPackWriter.java:208-225` | Extension from MIME type |

### Reading Archives

| Component | Location | Description |
|-----------|----------|-------------|
| Main reader | `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:81-260` | Complete read() method |
| Metadata-only reader | `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:30-79` | Fast metadata extraction |
| Enriched metadata reader | `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:262-280` | Reads enriched fields |
| Asset loader | `core/src/main/java/studio/core/v1/reader/archive/ArchiveStoryPackReader.java:206-248` | Loads assets from zip |

### Save/Upload Operations

| Component | Location | Description |
|-----------|----------|-------------|
| Save service | `web-ui/src/main/java/studio/webui/service/LibraryService.java:374-392` | addPackFile() method |
| Upload endpoint | `web-ui/src/main/java/studio/webui/api/LibraryController.java:63-75` | POST /api/library/upload |
| Frontend save | `web-ui/javascript/src/components/diagram/PackEditor.js:96-117` | Save button handler |
| Upload service | `web-ui/javascript/src/services/library.js:27-44` | uploadToLibrary() |

### Data Models

| Component | Location | Description |
|-----------|----------|-------------|
| Root pack model | `core/src/main/java/studio/core/v1/model/StoryPack.java` | Main StoryPack class |
| Pack enriched | `core/src/main/java/studio/core/v1/model/enriched/EnrichedPackMetadata.java` | Pack-level enriched metadata |
| Node enriched | `core/src/main/java/studio/core/v1/model/enriched/EnrichedNodeMetadata.java` | Node-level enriched metadata |
| Position | `core/src/main/java/studio/core/v1/model/enriched/EnrichedNodePosition.java` | X/Y coordinates |
| Node types | `core/src/main/java/studio/core/v1/model/enriched/EnrichedNodeType.java` | Node type enum |

---

## 7. Format Conversion

### Archive to Device Formats

When transferring a pack to a device, the archive is converted to the appropriate device format:

**Firmware v1.x (Binary/Raw format):**
- Writer: `core/src/main/java/studio/core/v1/writer/binary/BinaryStoryPackWriter.java`
- Sector-based USB protocol
- XXTEA encryption
- Asset compression
- **Enriched metadata is stripped**

**Firmware v2.x/v3.x (Filesystem format):**
- Writer: `core/src/main/java/studio/core/v1/writer/fs/FsStoryPackWriter.java`
- Device appears as removable storage
- AES-CBC encryption
- Hierarchical directory structure
- **Enriched metadata is stripped**

### Device Formats to Archive

When importing a pack from a device, it's converted to archive format:

**From Binary/Raw:**
- Reader: `core/src/main/java/studio/core/v1/reader/binary/BinaryStoryPackReader.java`
- **Enriched metadata cannot be recovered** (doesn't exist in device format)
- Nodes will have default names (UUIDs)
- Visual positions will be auto-generated

**From Filesystem:**
- Reader: `core/src/main/java/studio/core/v1/reader/fs/FsStoryPackReader.java`
- **Enriched metadata cannot be recovered** (doesn't exist in device format)
- Nodes will have default names (UUIDs)
- Visual positions will be auto-generated

**Important:** Always keep your original archive files if you plan to edit packs later. Device formats lose enriched metadata permanently.

---

## 8. File Storage

### Library Storage Location

**Path:** `~/.studio/library/`

Archives are stored with this naming convention:
```
{uuid}.{timestamp}.zip
```

Example:
```
abc12345-6789-def0-1234-56789abcdef0.1637856234567.zip
```

### Metadata Database

**Path:** `~/.studio/db/`

Contains cached pack metadata for fast library browsing without unpacking archives.

### Temporary Files

**Path:** `~/.studio/tmp/`

Used during format conversions (Archive ↔ Binary ↔ Filesystem).

---

## 9. Best Practices

### When Creating Archives

1. **Use descriptive enriched metadata:**
   - Add meaningful `title` and `description` to packs
   - Give nodes custom `name` values instead of leaving as UUIDs
   - Use `groupId` to organize related nodes
   - Position nodes logically in the diagram editor

2. **Optimize assets:**
   - Images: Exactly 320x240 pixels, use PNG for best quality
   - Audio: Mono, 32kHz, 16-bit signed, use MP3 for smallest size
   - Let the system deduplicate assets (same content = same hash)

3. **Test before transferring:**
   - Validate all transitions are correct
   - Ensure all asset references are valid
   - Check that squareOne is set on entry node

### When Editing Archives

1. **Always edit the archive, not device formats:**
   - Archive is the source of truth
   - Device formats lose enriched metadata
   - Round-trip editing requires archive format

2. **Keep backups:**
   - Archive files in `~/.studio/library/` are your originals
   - Back them up before making major changes
   - Device formats cannot be fully converted back to editable archives

3. **Use semantic node types:**
   - Set appropriate `type` values from EnrichedNodeType
   - Helps editor provide better UI
   - Documents node purpose for other editors

### When Converting Formats

1. **Archive → Device:** Safe, can be repeated
2. **Device → Archive:** Loses enriched metadata, cannot be fully reversed
3. **Always keep original archives** for future editing

---

## 10. Troubleshooting

### Common Issues

**Missing assets after conversion:**
- Check that asset filenames in JSON match files in `assets/` directory
- Verify SHA-1 hashes are correct
- Ensure MIME types are properly mapped to extensions

**Lost custom node names after device transfer:**
- This is expected behavior
- Enriched metadata (names, positions) doesn't exist in device formats
- Always edit the original archive, not re-imported device packs

**Archive won't upload:**
- Check file size limits
- Verify ZIP structure (must have story.json and assets/ directory)
- Ensure JSON is valid (use JSON validator)

**Nodes appear in wrong positions:**
- Check `position` field in enriched metadata
- Positions are only preserved in archive format
- Re-importing from device will lose positions

### Validation

To validate an archive manually:

1. **Unzip the archive**
2. **Check structure:**
   - `story.json` must exist at root
   - `assets/` directory must exist
   - All referenced assets must be in `assets/`
3. **Validate JSON:**
   - Must be valid JSON
   - Must have `format: "v1"`
   - Must have `stageNodes` and `actionNodes` arrays
4. **Validate transitions:**
   - All `actionNode` IDs must reference existing action nodes
   - All `optionIndex` values must be valid indices in target action's `options` array
   - All UUIDs in `options` arrays must reference existing stage nodes

---

## 11. Future Enhancements

### Planned Features

- Thumbnail support in EnrichedPackMetadata (currently TODO)
- Additional enriched metadata fields as needed
- Validation tools for archive integrity
- Migration tools for format upgrades

### Format Versioning

Current format version: `"v1"`

If the format changes in the future, the `format` field will be updated to ensure backwards compatibility. Readers will check the format version and parse accordingly.
