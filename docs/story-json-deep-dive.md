# story.json Deep Dive: Structure, Patterns & Possibilities

## Table of Contents

1. [Core Structure & Graph Model](#1-core-structure--graph-model)
2. [Transitions: The Graph Edges](#2-transitions-the-graph-edges)
3. [Story Patterns & Pathways](#3-story-patterns--pathways)
4. [Node Types & Behaviors](#4-node-types--behaviors)
5. [Control Flow Details](#5-control-flow-details)
6. [Device Controls Explained](#6-device-controls-explained)
7. [Real Examples](#7-real-examples)
8. [Graph Theory Concepts](#8-graph-theory-concepts)
9. [Visual Diagrams](#9-visual-diagrams-of-common-patterns)
10. [Edge Cases & Constraints](#10-edge-cases--constraints)

> **Source vs Device Format:** Throughout this document, examples use human-readable
> slug IDs (e.g., `"stage-cover"`, `"action-choose-path"`) for clarity. In the final
> device archive, the export script converts all IDs to valid UUIDs (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
> parseable by `java.util.UUID.fromString()`. See the export documentation for details.
>
> **Cross-pack uniqueness:** The cover stage UUID (the `squareOne` node) becomes the
> pack UUID on the device. It must be globally unique across all stories/packs.
> Use `"stage-cover-{story-slug}"` to avoid collisions.

---

## 1. Core Structure & Graph Model

### Graph Theory Foundation

The story.json format represents a **directed graph** with two types of nodes:

```
Story Graph = (StageNodes, ActionNodes, Transitions)

Where:
- StageNodes = Content nodes (images + audio)
- ActionNodes = Decision/branching nodes
- Transitions = Directed edges between nodes
```

### The Two-Node Architecture

#### 1. STAGE NODES

**Purpose:** Display content (image + audio) to the user

**Properties:**
- `uuid` - Unique identifier
- `image` - Visual asset (320x240 BMP), or null
- `audio` - Sound asset (mono MP3, 44100Hz), or null
- `okTransition` - Where to go when OK button pressed
- `homeTransition` - Where to go when HOME button pressed
- `controlSettings` - Which device controls are enabled

**Example:**
```json
{
  "uuid": "00000000-0000-0000-0000-000000000000",
  "squareOne": true,
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
}
```

#### 2. ACTION NODES

**Purpose:** Branch the story flow (choose next path)

**Properties:**
- `id` - Unique identifier
- `options` - Array of StageNode UUIDs (the possible next stages)

**Example:**
```json
{
  "id": "action-choose-path",
  "options": [
    "stage-uuid-left",
    "stage-uuid-middle",
    "stage-uuid-right"
  ]
}
```

### Graph Traversal Model

```
                  ┌─────────────┐
    squareOne →   │ StageNode 1 │  (Entry point)
                  │ Image+Audio │
                  └──────┬──────┘
                         │ okTransition
                         ↓
                  ┌─────────────┐
                  │ ActionNode  │  (Decision point)
                  │ 3 options   │
                  └──────┬──────┘
                         │
           ┌─────────────┼─────────────┐
           ↓             ↓             ↓
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Stage 2  │  │ Stage 3  │  │ Stage 4  │
    │ Path A   │  │ Path B   │  │ Path C   │
    └──────────┘  └──────────┘  └──────────┘
```

### Playback Flow

1. Device starts at `squareOne` (the stage node with `"squareOne": true`)
2. Plays image + audio of current stage node
3. User presses OK button → follows `okTransition`
4. Transition points to an `ActionNode` with an `optionIndex`
5. ActionNode selects next stage from its `options` array
6. Jumps to that stage node
7. Repeat from step 2

---

## 2. Transitions: The Graph Edges

### Transition Object Structure

```json
{
  "actionNode": "action-id-123",
  "optionIndex": 0
}
```

**Fields:**
- `actionNode` (String) - ID of the target ActionNode
- `optionIndex` (short) - Index in that ActionNode's `options` array

### How Transitions Work

```javascript
// Stage node has an okTransition:
okTransition = {
    actionNode: "action-choose-path",  // Look up this action node
    optionIndex: 0                     // Use options[0] from that action
}

// The action node determines the actual destination:
actionNodes["action-choose-path"] = {
    options: [
        "stage-uuid-A",  // ← optionIndex 0 points here
        "stage-uuid-B",
        "stage-uuid-C"
    ]
}

// Result: Transition leads to "stage-uuid-A"
```

### Special optionIndex Values

- `optionIndex: -1` → **Random choice** from action node's options
- `optionIndex: 0 to N` → Specific option from the array

### okTransition vs homeTransition

**okTransition:**
- Triggered by OK button press
- Moves story forward
- Can be `null` (story endpoint)

**homeTransition:**
- Triggered by HOME button press
- Returns to pack selection or previous menu
- Can be `null` (returns to device home screen)

---

## 3. Story Patterns & Pathways

### Pattern 1: Linear Story (A → B → C)

**Use case:** Simple sequential storytelling

```json
{
  "stageNodes": [
    {
      "uuid": "stage-1",
      "squareOne": true,
      "audio": "intro.mp3",
      "okTransition": {"actionNode": "action-1", "optionIndex": 0}
    },
    {
      "uuid": "stage-2",
      "audio": "middle.mp3",
      "okTransition": {"actionNode": "action-2", "optionIndex": 0}
    },
    {
      "uuid": "stage-3",
      "audio": "end.mp3",
      "okTransition": null
    }
  ],
  "actionNodes": [
    {
      "id": "action-1",
      "options": ["stage-2"]
    },
    {
      "id": "action-2",
      "options": ["stage-3"]
    }
  ]
}
```

**Diagram:**
```
┌─────────┐   OK   ┌─────────┐   OK   ┌─────────┐   OK   ┌─────────┐
│ Stage 1 ├────────►Action 1 ├────────►Stage 2  ├────────►Action 2 ├───────┐
│(Start)  │        │[stage-2]│        │         │        │[stage-3]│       │
└─────────┘        └─────────┘        └─────────┘        └─────────┘       ↓
                                                                     ┌─────────┐
                                                                     │ Stage 3 │
                                                                     │  (END)  │
                                                                     └─────────┘
```

### Pattern 2: Branching Story (Choices)

**Use case:** Give the user choices that lead to different paths

```json
{
  "stageNodes": [
    {
      "uuid": "stage-question",
      "squareOne": true,
      "audio": "which-path.mp3",
      "okTransition": {"actionNode": "action-choose", "optionIndex": 0},
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": false,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "stage-left-path",
      "audio": "you-went-left.mp3",
      "okTransition": null
    },
    {
      "uuid": "stage-right-path",
      "audio": "you-went-right.mp3",
      "okTransition": null
    }
  ],
  "actionNodes": [
    {
      "id": "action-choose",
      "options": [
        "stage-left-path",
        "stage-right-path"
      ]
    }
  ]
}
```

**Diagram:**
```
                    ┌──────────────┐
                    │Stage Question│
                    │ "Which path?"│
                    └───────┬───────┘
                            │ OK
                            ↓
                    ┌──────────────┐
                    │Action Choose │
                    │  2 options   │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              ↓                           ↓
      ┌──────────────┐            ┌──────────────┐
      │  Stage Left  │            │ Stage Right  │
      │ "You went    │            │ "You went    │
      │  left"       │            │  right"      │
      └──────────────┘            └──────────────┘
```

**How it works:** The device uses wheel rotation to select optionIndex (0 or 1), then user presses OK to follow that branch.

#### Menu Audio Experience

The menu/branching pattern creates an interactive audio browsing experience:

1. **Question Stage plays**: Child hears "Which path do you choose?"
2. **Child rotates wheel**: Device cycles through Option Stages
3. **Each Option Stage plays its audio**: Child hears "Left path" → scroll → "Right path"
4. **Child presses OK**: Selected option's `okTransition` is followed

This allows children to "browse" options by listening before making a choice. Each option stage can have:
- Its own **audio** (name/description of the choice)
- Its own **image** (visual representation of the choice)

### Pattern 3: Loops (Revisiting Nodes)

**Use case:** Repeatable content, continuous stories

**YES, loops are possible!** Transitions can point back to earlier nodes.

```json
{
  "stageNodes": [
    {
      "uuid": "stage-loop-start",
      "squareOne": true,
      "audio": "story-begins.mp3",
      "okTransition": {"actionNode": "action-continue", "optionIndex": 0}
    },
    {
      "uuid": "stage-loop-end",
      "audio": "listen-again.mp3",
      "okTransition": {"actionNode": "action-repeat", "optionIndex": 0}
    },
    {
      "uuid": "stage-exit",
      "audio": "goodbye.mp3",
      "okTransition": null
    }
  ],
  "actionNodes": [
    {
      "id": "action-continue",
      "options": ["stage-loop-end"]
    },
    {
      "id": "action-repeat",
      "options": [
        "stage-loop-start",
        "stage-exit"
      ]
    }
  ]
}
```

**Diagram:**
```
    ┌─────────────────────────────────────┐
    │                                     │
    ↓                                     │ Loop back
┌──────────┐        ┌──────────┐    ┌─────────┐
│  Start   ├───────►│   End    ├───►│ Action  │
└──────────┘        └──────────┘    │ Repeat  │
                                    └────┬────┘
                                         │ Exit
                                         ↓
                                    ┌─────────┐
                                    │  Exit   │
                                    └─────────┘
```

### Pattern 4: Menu Structure

**Use case:** Let user choose from multiple options with visual/audio feedback

Menus use **grouped nodes** - a question stage followed by option stages:

**Simplified concept:**
```
MenuNode {
  questionAudio: "Choose your favorite color",
  options: [
    {name: "Red", image: red.bmp, audio: "red.mp3"},
    {name: "Blue", image: blue.bmp, audio: "blue.mp3"},
    {name: "Green", image: green.bmp, audio: "green.mp3"}
  ]
}
```

**Expands to story.json as:**

```json
{
  "stageNodes": [
    {
      "uuid": "menu-abc123-222222222222",
      "type": "menu.questionstage",
      "groupId": "menu-abc123",
      "audio": "choose-color.mp3",
      "okTransition": {
        "actionNode": "menu-abc123-333333333333",
        "optionIndex": 0
      },
      "controlSettings": {
        "wheel": false,
        "ok": false,
        "home": false,
        "pause": false,
        "autoplay": true
      }
    },
    {
      "uuid": "menu-abc123-444444440000",
      "type": "menu.optionstage",
      "groupId": "menu-abc123",
      "name": "Red",
      "image": "red.bmp",
      "audio": "red.mp3",
      "okTransition": {"actionNode": "next-action", "optionIndex": 0},
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": false,
        "autoplay": false
      }
    },
    {
      "uuid": "menu-abc123-444444440001",
      "type": "menu.optionstage",
      "groupId": "menu-abc123",
      "name": "Blue",
      "image": "blue.bmp",
      "audio": "blue.mp3",
      "okTransition": {"actionNode": "next-action", "optionIndex": 0},
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": false,
        "autoplay": false
      }
    },
    {
      "uuid": "menu-abc123-444444440002",
      "type": "menu.optionstage",
      "groupId": "menu-abc123",
      "name": "Green",
      "image": "green.bmp",
      "audio": "green.mp3",
      "okTransition": {"actionNode": "next-action", "optionIndex": 0},
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": false,
        "autoplay": false
      }
    }
  ],
  "actionNodes": [
    {
      "id": "menu-abc123-111111111111",
      "type": "menu.questionaction",
      "groupId": "menu-abc123",
      "options": ["menu-abc123-222222222222"]
    },
    {
      "id": "menu-abc123-333333333333",
      "type": "menu.optionsaction",
      "groupId": "menu-abc123",
      "options": [
        "menu-abc123-444444440000",
        "menu-abc123-444444440001",
        "menu-abc123-444444440002"
      ]
    }
  ]
}
```

**UUID Generation Pattern:**
- Base UUID: `menu-abc123-000000000000`
- Question action: `menu-abc123-111111111111`
- Question stage: `menu-abc123-222222222222`
- Options action: `menu-abc123-333333333333`
- Option stages: `menu-abc123-44444444NNNN` (where NNNN = 0000, 0001, 0002...)

### Pattern 5: Hub-and-Spoke (Central Menu)

**Use case:** Main menu with multiple stories that return to the menu

```
         ┌─────────┐
    ┌───►│ Story 1 ├────┐
    │    └─────────┘    │
    │                   │ homeTransition
┌────────┐              ↓
│  Hub   │         ┌─────────┐
│  Menu  │◄────────┤ Action  │
└────────┘         │  Home   │
    │              └─────────┘
    │                   ↑
    │    ┌─────────┐    │ homeTransition
    └───►│ Story 2 ├────┘
         └─────────┘
```

Each story uses `homeTransition` to return to the central hub menu.

### Pattern 6: Random Branching

**Use case:** Add variability, surprise elements

```json
{
  "stageNodes": [
    {
      "uuid": "start",
      "squareOne": true,
      "audio": "mysterious-portal.mp3",
      "okTransition": {
        "actionNode": "random-destination",
        "optionIndex": -1
      }
    },
    {
      "uuid": "destination-forest",
      "audio": "dark-forest.mp3"
    },
    {
      "uuid": "destination-castle",
      "audio": "grand-castle.mp3"
    },
    {
      "uuid": "destination-ocean",
      "audio": "underwater.mp3"
    }
  ],
  "actionNodes": [
    {
      "id": "random-destination",
      "options": [
        "destination-forest",
        "destination-castle",
        "destination-ocean"
      ]
    }
  ]
}
```

**Key:** `optionIndex: -1` makes the device randomly choose one of the three destinations.

### Pattern 7: Story Endpoints

**Three ways to end a story:**

#### 1. Null okTransition - Hard Stop
```json
{
  "uuid": "final-stage",
  "audio": "the-end.mp3",
  "okTransition": null,
  "homeTransition": null
}
```
Story ends, device returns to pack selection.

#### 2. Loop Back to Start - Continuous Replay
```json
{
  "uuid": "final-stage",
  "audio": "listen-again.mp3",
  "okTransition": {
    "actionNode": "action-restart",
    "optionIndex": 0
  }
}
```
Where `action-restart` points back to the `squareOne` stage.

#### 3. Transition to Credits/End Screen
```
Stage A → Action → Stage B (The End) → null
```

---

## 4. Node Types & Behaviors

### EnrichedNodeType Reference

| Type | Code | Label | Purpose |
|------|------|-------|---------|
| STAGE | 0x01 | `"stage"` | Basic content node |
| ACTION | 0x02 | `"action"` | Basic decision node |
| COVER | 0x11 | `"cover"` | Pack selection screen (squareOne) |
| MENU_QUESTION_STAGE | 0x22 | `"menu.questionstage"` | Menu question audio |
| MENU_QUESTION_ACTION | 0x21 | `"menu.questionaction"` | Menu question routing |
| MENU_OPTIONS_ACTION | 0x23 | `"menu.optionsaction"` | Menu options routing |
| MENU_OPTION_STAGE | 0x24 | `"menu.optionstage"` | Individual menu option |
| STORY | 0x31 | `"story"` | Story content node |
| STORY_ACTION | 0x32 | `"story.storyaction"` | Story routing node |

**Important:** These types are **enriched metadata only** - they help the editor UI but don't affect device behavior. Devices only care about the graph structure.

### Cover Node Behavior

- Special stage node marked with `"squareOne": true`
- **Must be first node** in `stageNodes` array
- Entry point when pack is selected on device
- Typically displays pack thumbnail + intro audio

**Example:**
```json
{
  "uuid": "00000000-0000-0000-0000-000000000000",
  "squareOne": true,
  "type": "cover",
  "name": "Pack Cover",
  "image": "thumbnail.bmp",
  "audio": "welcome.mp3",
  "okTransition": {"actionNode": "start-story", "optionIndex": 0}
}
```

### Story Node Behavior

- Simplified UI concept for story chapters
- Has single audio asset (typically no image)
- Can disable HOME button to prevent interruption
- Default transitions redirect to first content node

---

## 5. Control Flow Details

### What Happens When a Stage Node is Played?

```
1. Device displays image (if present)
2. Device plays audio (if present)
3. Device enables controls based on controlSettings
4. Device waits for user input:

   If OK button pressed AND ok=true:
     → Follow okTransition
     → Look up actionNode
     → Select option based on optionIndex (or random if -1)
     → Jump to that stage

   If HOME button pressed AND home=true:
     → Follow homeTransition
     → Or return to pack selection if null

   If autoplay=true AND audio finishes:
     → Automatically follow okTransition
     → No button press needed
```

### How Action Nodes Make Choices

#### Method 1: Fixed Selection
```
Transition: {actionNode: "action-1", optionIndex: 2}
→ Device looks up action-1
→ Device uses options[2]
→ Device jumps to that stage
```

#### Method 2: Random Selection
```
Transition: {actionNode: "action-1", optionIndex: -1}
→ Device looks up action-1
→ Device randomly picks from options array
→ Device jumps to that stage
```

#### Method 3: User Wheel Selection
```
→ User rotates wheel on previous stage
→ Device tracks current option index
→ User presses OK
→ Transition uses selected index: {actionNode: "menu-options", optionIndex: currentIndex}
→ Device follows that path
```

---

## 6. Device Controls Explained

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

### Wheel Control

**When enabled (`wheel: true`):**
- User can rotate wheel to cycle through action node options
- Displays different option stages in menus
- Common in menus and choice points

**When disabled (`wheel: false`):**
- Wheel rotation has no effect
- Used in linear stories or cutscenes

**Example use case:**
```json
{
  "uuid": "menu-options",
  "controlSettings": {
    "wheel": true,
    "ok": true,
    "home": true,
    "pause": false,
    "autoplay": false
  }
}
```

### OK Button

**When enabled (`ok: true`):**
- User can press OK to follow okTransition
- Advances story forward

**When disabled (`ok: false`):**
- OK button has no effect
- Used with autoplay for continuous playback

**Example use case:**
```json
{
  "uuid": "cutscene",
  "controlSettings": {
    "wheel": false,
    "ok": false,
    "home": true,
    "pause": true,
    "autoplay": true
  }
}
```

### HOME Button

**When enabled (`home: true`):**
- User can press HOME to follow homeTransition
- Returns to previous menu or pack selection

**When disabled (`home: false`):**
- HOME button has no effect
- Prevents escape from current story segment
- Use sparingly - users expect HOME to always work

### Pause Button

**When enabled (`pause: true`):**
- User can pause/resume audio playback
- Recommended for all audio-containing nodes

**When disabled (`pause: false`):**
- Audio plays continuously without pause option
- Rarely used

### Autoplay

**When enabled (`autoplay: true`):**
- Stage automatically follows okTransition when audio ends
- No button press needed
- Creates continuous flow

**When disabled (`autoplay: false`):**
- Stage waits for user input (OK button)
- Gives user control over pacing
- **Default and most common setting**

### Control Settings Patterns

These patterns are derived from working Lunii device stories and MUST be followed.

#### Cover Node (Entry Point)
```json
{
  "wheel": false,
  "ok": true,
  "home": false,
  "pause": false,
  "autoplay": false
}
```
Cover is the entry point — `home: false` because there's nowhere to go back to.

#### Story Chapter (Auto-Play Content)
```json
{
  "wheel": false,
  "ok": false,
  "home": true,
  "pause": true,
  "autoplay": true
}
```
Story content plays automatically. Child listens without pressing buttons.

#### Menu Question Stage (Auto-Advance Prompt)
```json
{
  "wheel": false,
  "ok": false,
  "home": false,
  "pause": false,
  "autoplay": true
}
```
Plays "Choose your story" prompt, then auto-transitions to options display.

#### Menu Option Stage (User Browses & Selects)
```json
{
  "wheel": true,
  "ok": true,
  "home": true,
  "pause": false,
  "autoplay": false
}
```
Child rotates wheel to browse options, presses OK to select.

#### Story Endpoint (Last Chapter, okTransition: null)
```json
{
  "wheel": false,
  "ok": false,
  "home": true,
  "pause": true,
  "autoplay": true
}
```
Same as story chapter. After audio finishes, null transition ends the story.

---

## 7. Real Examples

### Example 1: Complete Minimal Story

**3-node linear story with proper structure:**

```json
{
  "format": "v1",
  "title": "My First Story",
  "version": 1,
  "nightModeAvailable": true,

  "stageNodes": [
    {
      "uuid": "00000000-0000-0000-0000-000000000001",
      "squareOne": true,
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

### Example 2: Branching Story with 2 Endings

```json
{
  "format": "v1",
  "title": "Choose Your Adventure",
  "version": 1,
  "nightModeAvailable": true,

  "stageNodes": [
    {
      "uuid": "start",
      "squareOne": true,
      "audio": "fork-in-road.mp3",
      "okTransition": {
        "actionNode": "choose-path",
        "optionIndex": 0
      },
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": false,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "left-path",
      "audio": "found-treasure.mp3",
      "okTransition": null,
      "controlSettings": {
        "wheel": false,
        "ok": false,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "right-path",
      "audio": "met-dragon.mp3",
      "okTransition": null,
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
      "id": "choose-path",
      "options": ["left-path", "right-path"]
    }
  ]
}
```

### Example 3: Repeating Loop with Exit

```json
{
  "format": "v1",
  "title": "Bedtime Story Loop",
  "version": 1,
  "nightModeAvailable": true,

  "stageNodes": [
    {
      "uuid": "intro",
      "squareOne": true,
      "audio": "once-upon-a-time.mp3",
      "okTransition": {"actionNode": "a1", "optionIndex": 0},
      "controlSettings": {
        "wheel": false,
        "ok": true,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "story",
      "audio": "story-continues.mp3",
      "okTransition": {"actionNode": "a2", "optionIndex": 0},
      "controlSettings": {
        "wheel": false,
        "ok": true,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "ask-repeat",
      "audio": "hear-again.mp3",
      "okTransition": {"actionNode": "repeat-choice", "optionIndex": 0},
      "controlSettings": {
        "wheel": true,
        "ok": true,
        "home": true,
        "pause": true,
        "autoplay": false
      }
    },
    {
      "uuid": "goodbye",
      "audio": "goodnight.mp3",
      "okTransition": null,
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
      "id": "a1",
      "options": ["story"]
    },
    {
      "id": "a2",
      "options": ["ask-repeat"]
    },
    {
      "id": "repeat-choice",
      "options": [
        "intro",
        "goodbye"
      ]
    }
  ]
}
```

---

## 8. Graph Theory Concepts

### Directed Acyclic Graph (DAG) vs Cyclic

**STUdio stories can be CYCLIC** - transitions can point back to earlier nodes, creating loops.

**Example cycle:**
```
Stage A → Action 1 → Stage B → Action 2 → Stage A (loop!)
```

**Use cases for cycles:**
- Repeatable stories
- Menu systems (always return to menu)
- Continuous playback

### Graph Connectivity

**Strongly connected components:**
- Group of nodes where every node is reachable from every other node
- Common in menu systems (all options lead back to menu)

**Weakly connected components:**
- Group of nodes connected by edges (ignoring direction)
- Each story path forms a weakly connected component

### Entry Point (squareOne)

**Rules:**
- Only **ONE** node should have `"squareOne": true`
- **MUST** be the first node in `stageNodes` array
- Entry point when pack is selected on device
- Typically a "cover" type node

### Sink Nodes (Endpoints)

**Stage nodes with `okTransition: null`:**
- No outgoing edges
- Story ends here
- Device returns to pack selection
- Can have `homeTransition` for manual exit

### Reachability

**All nodes should be reachable from squareOne:**
- Otherwise they're "orphaned" (never played)
- Not invalid, but wasteful
- Editor can detect and warn about orphaned nodes

---

## 9. Visual Diagrams of Common Patterns

### Pattern: Simple Linear Story

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Cover   │ OK  │ Action 1 │     │ Chapter1 │ OK  │ Action 2 │
│ (square  ├────►│          ├────►│          ├────►│          ├───┐
│  One)    │     │[chapter1]│     │          │     │[chapter2]│   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘   │
                                                                   │
                                                                   ↓
                                  ┌──────────┐     ┌──────────┐
                                  │ Chapter2 │ OK  │  Action  │
                                  │          ├────►│          ├───┐
                                  │          │     │  [end]   │   │
                                  └──────────┘     └──────────┘   │
                                                                   ↓
                                                           ┌──────────┐
                                                           │   End    │
                                                           │  (null)  │
                                                           └──────────┘
```

### Pattern: Binary Choice Tree

```
                            ┌──────────┐
                            │ Question │
                            │          │
                            └─────┬────┘
                                  │ OK
                                  ↓
                            ┌──────────┐
                            │  Action  │
                            │2 options │
                            └─────┬────┘
                                  │
                    ┌─────────────┴─────────────┐
             Option 0                    Option 1
                    ↓                            ↓
            ┌──────────┐                 ┌──────────┐
            │ Choice A │                 │ Choice B │
            └─────┬────┘                 └─────┬────┘
                  │                            │
        ┌─────────┴────────┐        ┌─────────┴────────┐
        ↓                  ↓        ↓                  ↓
   ┌────────┐         ┌────────┐ ┌────────┐       ┌────────┐
   │ Path A1│         │ Path A2│ │ Path B1│       │ Path B2│
   └────────┘         └────────┘ └────────┘       └────────┘
```

### Pattern: Menu with Return to Hub

```
              ┌──────────────┐
       ┌─────►│ Menu Question│◄─────┐
       │      │ "Choose one" │      │
       │      └──────┬───────┘      │
       │             │ OK            │
       │             ↓               │
       │      ┌──────────────┐      │
       │      │ Menu Options │      │
       │      │  3 options   │      │
       │      └──────┬───────┘      │
       │             │               │
       │   ┌─────────┼─────────┐    │
       │   ↓         ↓         ↓    │
       │ ┌────┐   ┌────┐   ┌────┐  │
       │ │ Op1│   │ Op2│   │ Op3│  │
       │ └─┬──┘   └─┬──┘   └─┬──┘  │
       │   │ OK     │ OK     │ OK   │
       │   ↓        ↓        ↓      │
       │ ┌────┐   ┌────┐   ┌────┐  │
       │ │Con1│   │Con2│   │Con3│  │
       │ └─┬──┘   └─┬──┘   └─┬──┘  │
       │   │ HOME   │ HOME   │ HOME │
       └───┴────────┴────────┴──────┘
```

### Pattern: Loop with Exit Condition

```
    ┌──────────────────────────────────┐
    │                                  │ Repeat (Option 0)
    ↓                                  │
┌────────┐        ┌────────┐     ┌─────────┐
│ Intro  ├───────►│ Story  ├────►│ Action  │
│(square │   OK   │        │ OK  │ Repeat? │
│  one)  │        │        │     └────┬────┘
└────────┘        └────────┘          │
                                      │ Exit (Option 1)
                                      ↓
                                 ┌─────────┐
                                 │   End   │
                                 │  (null) │
                                 └─────────┘
```

### Pattern: Hub-and-Spoke Navigation

```
                         ┌──────────┐
                    ┌───►│ Story 1  ├────┐
                    │    │          │    │
                    │ OK └──────────┘    │ HOME
                    │                    │
    ┌───────────┐   │    ┌──────────┐   │    ┌─────────┐
    │   Cover   ├───┼───►│ Story 2  ├───┼───►│ Action  │
    │ (square   │   │ OK │          │   │ HOME│  Home   │
    │   one)    │   │    └──────────┘   │    └────┬────┘
    └───────────┘   │                   │         │
                    │    ┌──────────┐   │         │
                    └───►│ Story 3  ├───┘         │
                      OK │          │ HOME        │
                         └──────────┘             │
                              ▲                   │
                              └───────────────────┘
                                    Return to hub
```

### Pattern: Random Branching

```
                    ┌──────────┐
                    │  Start   │
                    │          │
                    └─────┬────┘
                          │ OK
                          ↓
                    ┌──────────┐
                    │  Action  │
                    │ Random   │ optionIndex: -1
                    │3 options │
                    └─────┬────┘
                          │
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
        (random)      (random)      (random)
            ↓             ↓             ↓
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ Path A  │   │ Path B  │   │ Path C  │
      │         │   │         │   │         │
      └─────────┘   └─────────┘   └─────────┘
```

---

## 10. Edge Cases & Constraints

### Constraint 1: First Node Must Be Entry Point

**Rule:** The node with `"squareOne": true` **must** be the first element in the `stageNodes` array.

### Constraint 2: Unique squareOne

**Only ONE node** should have `"squareOne": true`. Multiple squareOne nodes will cause undefined behavior.

### Edge Case: Missing Transitions

**okTransition: null**
- Story endpoint
- Device returns to pack selection
- Valid and intentional

**homeTransition: null**
- Default behavior: returns to pack selection
- Or HOME button has no effect if `home: false` in controlSettings

### Edge Case: Invalid References

**If actionNode ID doesn't exist:**
- Validation should catch this error
- Device may crash or skip to pack selection
- **Always validate references**

**If optionIndex out of bounds:**
- Array index out of range
- Device behavior undefined (likely crashes)
- Validate during save

**Example validation:**
```javascript
// Check if optionIndex is valid
if (transition.optionIndex >= actionNode.options.length) {
  throw new Error(`optionIndex ${transition.optionIndex} exceeds options array length`);
}
```

### Edge Case: Orphaned Nodes

**Stage nodes not reachable from squareOne:**
- Still included in archive file
- Never played during normal flow
- Waste of space but not invalid
- Editor can detect and warn

**Detection:**
```
1. Start at squareOne
2. Traverse all reachable nodes via transitions
3. Mark all visited nodes
4. Any unmarked nodes are orphaned
```

### Edge Case: Infinite Loops

**Structure:**
```json
Stage A → Action → Stage A (loops forever)
```

**Effect:**
- Story never ends naturally
- User **must** press HOME button to exit
- Valid pattern for continuous stories
- Ensure `home: true` in controlSettings!

### Edge Case: No Audio or Image

**Stage node with both null:**
```json
{
  "uuid": "silent-stage",
  "image": null,
  "audio": null,
  "okTransition": {"actionNode": "next", "optionIndex": 0}
}
```

**Effect:**
- Device displays nothing
- Instantly advances if autoplay enabled
- Can be used as routing/logic nodes
- Not recommended for user experience

### Constraint: Asset Deduplication

Multiple nodes can reference the same asset file:
- If two stages use the same image or audio, they reference the same filename
- This is intentional and reduces archive size

### Constraint: Action Node Must Have Options

**Empty options array:**
```json
{
  "id": "broken-action",
  "options": []
}
```

**Effect:**
- No valid transitions
- Device may crash
- **Always include at least one option**

### Best Practice: Always Provide Exit Path

**Every story should have a way to exit:**
- `okTransition: null` at story end
- `homeTransition` to return to menu
- `home: true` in controlSettings for emergencies

**Bad example (trapped user):**
```json
{
  "uuid": "trap",
  "audio": "stuck.mp3",
  "okTransition": {"actionNode": "loop-back", "optionIndex": 0},
  "homeTransition": null,
  "controlSettings": {
    "wheel": false,
    "ok": true,
    "home": false,
    "pause": false,
    "autoplay": false
  }
}
```

**Good example (always escapable):**
```json
{
  "uuid": "safe",
  "audio": "content.mp3",
  "okTransition": {"actionNode": "next", "optionIndex": 0},
  "homeTransition": {"actionNode": "return-menu", "optionIndex": 0},
  "controlSettings": {
    "wheel": false,
    "ok": true,
    "home": true,
    "pause": true,
    "autoplay": false
  }
}
```

---

## Summary

The story.json format is a **directed graph** that enables:

### Core Concepts
- **Two node types:** Stage nodes (content) + Action nodes (decisions)
- **Transitions:** Edges connecting nodes (OK button, HOME button)
- **Entry point:** squareOne (first stage node)
- **Graph structure:** Can be cyclic (loops allowed)

### Story Patterns
1. **Linear:** A→B→C (sequential storytelling)
2. **Branching:** User choices with multiple paths
3. **Loops:** Repeatable content (A→B→A)
4. **Menus:** Question + option stages
5. **Hub-and-spoke:** Central menu with sub-stories
6. **Random:** Surprise branching (optionIndex: -1)

### Control Flow
- Stage nodes display content and wait for input
- Transitions point to action nodes with option indices
- Action nodes resolve to specific stage nodes
- Control settings determine available buttons

### Best Practices
- Always provide exit path (HOME button or null transition)
- Validate all references (actionNode IDs, optionIndex values)
- Use enriched metadata for editor organization
- Test all paths for reachability
- Avoid trapping users (always enable HOME or provide okTransition: null)

### Device Playback
1. Start at squareOne
2. Display image, play audio
3. Wait for input (or autoplay)
4. Follow transition → action node
5. Select option from array
6. Jump to target stage
7. Repeat until okTransition: null
