# Story Validation Rules

This document describes all validation rules applied to stories before export. Validation ensures the story works correctly on Lunii devices.

---

## Validation Categories

1. [Structure Validation](#structure-validation)
2. [Transition Validation](#transition-validation)
3. [Asset Validation](#asset-validation)
4. [Content Validation](#content-validation)

---

## Structure Validation

### RULE: Single Entry Point
- **Severity:** ERROR
- **Check:** Exactly one stage node has `squareOne: true`
- **Fix:** Set squareOne on the intended first stage

```javascript
// Valid
stageNodes: [
  { uuid: "stage-1", squareOne: true, ... },
  { uuid: "stage-2", ... }
]

// Invalid - multiple squareOne
stageNodes: [
  { uuid: "stage-1", squareOne: true, ... },
  { uuid: "stage-2", squareOne: true, ... }  // ERROR
]

// Invalid - no squareOne
stageNodes: [
  { uuid: "stage-1", ... },  // ERROR - missing squareOne
  { uuid: "stage-2", ... }
]
```

---

### RULE: Entry Point Position
- **Severity:** ERROR
- **Check:** The squareOne node must be first in the stageNodes array
- **Fix:** Reorder stageNodes array to put squareOne first

```javascript
// Valid
stageNodes: [
  { uuid: "cover", squareOne: true, ... },  // First!
  { uuid: "chapter-1", ... },
  { uuid: "chapter-2", ... }
]

// Invalid
stageNodes: [
  { uuid: "chapter-1", ... },
  { uuid: "cover", squareOne: true, ... },  // ERROR - not first
  { uuid: "chapter-2", ... }
]
```

---

### RULE: No Orphaned Nodes
- **Severity:** WARNING
- **Check:** All nodes are reachable from squareOne via transitions
- **Fix:** Remove orphaned nodes or create transitions to them

```
Detection algorithm:
1. Start at squareOne
2. Follow all okTransition and homeTransition paths
3. Follow all action node options
4. Mark visited nodes
5. Report unmarked nodes as orphaned
```

---

### RULE: Exit Path Exists
- **Severity:** ERROR
- **Check:** Every path eventually reaches a node with `okTransition: null` OR has `home: true` in controlSettings
- **Fix:** Add null transition to ending stages or enable home button

```javascript
// Valid - natural ending
{
  uuid: "ending",
  okTransition: null,  // Story ends here
  controlSettings: { home: true, ... }
}

// Valid - home button escape
{
  uuid: "loop-stage",
  okTransition: { actionNode: "action-loop", optionIndex: 0 },
  controlSettings: { home: true, ... }  // User can exit
}

// Invalid - trapped user
{
  uuid: "trapped",
  okTransition: { actionNode: "action-loop", optionIndex: 0 },
  controlSettings: { home: false, ... }  // ERROR - no exit
}
```

---

## Transition Validation

### RULE: Valid Action Node References
- **Severity:** ERROR
- **Check:** All `actionNode` IDs in transitions exist in actionNodes array
- **Fix:** Create missing action node or correct the ID

```javascript
// Transition references
okTransition: { actionNode: "action-next", optionIndex: 0 }

// Must have matching action node
actionNodes: [
  { id: "action-next", options: ["stage-2"] }
]
```

---

### RULE: Valid Option Index
- **Severity:** ERROR
- **Check:** optionIndex is within bounds of action node's options array
- **Exception:** optionIndex -1 is valid (random selection)
- **Fix:** Adjust optionIndex or add more options

```javascript
// Action node with 2 options
{ id: "action-choice", options: ["stage-a", "stage-b"] }

// Valid
okTransition: { actionNode: "action-choice", optionIndex: 0 }  // stage-a
okTransition: { actionNode: "action-choice", optionIndex: 1 }  // stage-b
okTransition: { actionNode: "action-choice", optionIndex: -1 } // random

// Invalid
okTransition: { actionNode: "action-choice", optionIndex: 2 }  // ERROR - out of bounds
```

---

### RULE: Valid Stage References in Options
- **Severity:** ERROR
- **Check:** All stage UUIDs in action node options exist in stageNodes
- **Fix:** Create missing stage node or correct the UUID

```javascript
// Action node options
{ id: "action-1", options: ["stage-a", "stage-b"] }

// Must have matching stages
stageNodes: [
  { uuid: "stage-a", ... },
  { uuid: "stage-b", ... }
]
```

---

### RULE: Non-Empty Options
- **Severity:** ERROR
- **Check:** Every action node has at least one option
- **Fix:** Add at least one stage UUID to options array

```javascript
// Invalid
{ id: "action-empty", options: [] }  // ERROR - no options
```

---

## Asset Validation

### RULE: Image Reference Valid
- **Severity:** WARNING
- **Check:** All image filenames reference existing files or have prompts
- **Fix:** Create image prompt file or generate placeholder

```javascript
// Stage references image
{ uuid: "stage-1", image: "forest-scene.png", ... }

// Must have either:
// - assets/images/forest-scene.png (actual file)
// - assets/images/stage-1.prompt.md (generation prompt)
```

---

### RULE: Audio Reference Valid
- **Severity:** WARNING
- **Check:** All audio filenames reference existing files or have scripts
- **Fix:** Create audio script file or generate placeholder

```javascript
// Stage references audio
{ uuid: "stage-1", audio: "chapter-1.mp3", ... }

// Must have either:
// - assets/audio/chapter-1.mp3 (actual file)
// - audio-scripts/stage-1.md (TTS script)
```

---

### RULE: Image Dimensions
- **Severity:** WARNING (if actual images exist)
- **Check:** Images are exactly 320x240 pixels
- **Fix:** Resize images to correct dimensions

---

### RULE: Audio Format
- **Severity:** WARNING (if actual audio exists)
- **Check:** Audio is mono, 32kHz sample rate, 16-bit signed
- **Fix:** Convert audio to required format

---

## Content Validation

### RULE: Age-Appropriate Vocabulary
- **Severity:** WARNING
- **Check:** Vocabulary complexity matches target age
- **Fix:** Simplify language for younger ages

```
Ages 5-6: Simple words, short sentences
Ages 7-8: Moderate vocabulary, compound sentences
Ages 9-10: Advanced vocabulary allowed
```

---

### RULE: Chapter Duration
- **Severity:** WARNING
- **Check:** Audio chapter estimated duration within limits
- **Fix:** Adjust chapter content to match target duration

```
Ages 5-6: 3-5 minutes per chapter
Ages 7-8: 5-7 minutes per chapter
Ages 9-10: 7-10 minutes per chapter
```

---

### RULE: Control Settings Consistency
- **Severity:** WARNING
- **Check:** Control settings match node type
- **Fix:** Adjust control settings

```javascript
// Choice point should have wheel enabled
{
  uuid: "choice-stage",
  okTransition: { actionNode: "action-choice", ... },
  controlSettings: { wheel: true, ... }  // Required for choice
}

// Ending should have ok disabled
{
  uuid: "ending",
  okTransition: null,
  controlSettings: { ok: false, ... }  // No action to take
}
```

---

### RULE: Bedtime Mode Consistency
- **Severity:** WARNING
- **Check:** If bedtime mode, all applicable stages have autoplay
- **Fix:** Enable autoplay on story stages

```javascript
// Bedtime mode story
{
  uuid: "chapter-1",
  controlSettings: { autoplay: true, ... }  // Auto-advance
}
```

---

## Validation Report Format

After validation, a report is generated:

```markdown
# Validation Report

**Story:** The Magic Forest Adventure
**Validated:** 2026-02-01T12:00:00Z
**Status:** PASSED with warnings

## Summary
- Errors: 0
- Warnings: 2

## Errors
None

## Warnings

### W001: Missing Image Asset
- **Node:** stage-entering-forest
- **Issue:** Image reference 'forest-scene.png' has no file or prompt
- **Fix:** Create assets/images/stage-entering-forest.prompt.md

### W002: Long Audio Segment
- **Node:** stage-dragon-encounter
- **Issue:** Estimated duration 95s exceeds limit for age 7-8 (60s)
- **Fix:** Split into two shorter segments
```

---

## Interactive Fix Flow

When errors are found:

1. **Display categorized issues** (errors first)
2. **For each error:**
   - Show the issue
   - Explain the impact
   - Offer fix options:
     - Auto-fix (if possible)
     - Manual guidance
     - Skip (mark for later)
3. **Apply selected fixes**
4. **Re-validate**
5. **Repeat until clean or user accepts warnings**

---

## Validation Command

Run validation manually:

```
/kidstory export {story-name} --validate-only
```

This runs all checks without creating the archive.
