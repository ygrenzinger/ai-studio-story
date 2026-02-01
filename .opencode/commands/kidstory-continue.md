---
description: Continue working on an incomplete story or pack
---

# Continue KidStory

Resume work on an incomplete story or story pack.

## Story/Pack Name

$ARGUMENTS

## Workflow

1. **Locate the Content**
   - If name provided: Look in `./stories/{name}/`
   - If not provided: List all incomplete stories and packs, ask user to choose

2. **Detect Content Type**
   - Read `metadata.json` and check `type` field
   - If `type: "story"`: Use single story workflow
   - If `type: "pack"`: Use pack workflow (see below)

3. **Load State**
   - Read `metadata.json` to understand current state
   - Check `generation` object for progress
   - Identify what's been completed vs. pending

---

## Single Story Workflow

### Display Progress Summary
Show the user:
- Story title and description
- Outline status (approved/pending)
- Chapters generated: X of Y
- Characters defined
- Audio scripts created
- Validation status

### Resume from Last Point

Based on status, continue from the appropriate phase:

**If outline not approved:**
- Display current outline
- Ask for approval or modifications
- Once approved, proceed to chapter generation

**If chapters incomplete:**
- Show which chapters are done
- Continue generating from next chapter
- Follow the original creation mode (quick/guided/manual)

**If chapters complete but audio scripts missing:**
- Generate audio scripts for remaining chapters
- Create character audio profiles if missing

**If validation pending:**
- Run validation
- Present issues for interactive fixing

---

## Pack Workflow

### Display Pack Progress Summary
Show the user:
- Pack title, theme, and description
- Hub status: Complete / Pending
- Stories progress: "2 of 4 stories complete"
- Per-story breakdown:
  ```
  1. Owl's Night Adventure    [Complete] 4/4 chapters
  2. Beaver's Big Dam         [In Progress] 2/5 chapters
  3. Squirrel's Acorn Hunt    [Pending] 0/3 chapters
  4. Deer's Meadow Visit      [Pending] 0/4 chapters
  ```
- Overall validation status

### Pack Resume Options

Present the user with options:

1. **Continue next incomplete story**
   - Automatically resume the first in-progress or pending story
   
2. **Choose specific story to work on**
   - List all stories with status
   - Let user select which to continue
   
3. **Complete hub menu** (if incomplete)
   - Generate or refine hub content
   
4. **Jump to validation**
   - Run pack-wide validation
   - Fix any issues

### Per-Story Continuation in Pack Context

When continuing a specific story within a pack:

1. **Load pack context**
   - Load shared character profiles from `characters/`
   - Load pack-level interview answers
   - Ensure consistency with pack tone and theme

2. **Load story-specific state**
   - Read story interview answers from `metadata.json.interview.stories[i]`
   - Check chapter progress in `generation.storiesProgress[slug]`

3. **Display story progress**
   - Story title and focus
   - Chapters: X of Y complete
   - Pattern: linear/branching/loop

4. **Resume story generation**
   - Follow original creation mode
   - Use shared characters with their defined voices
   - Maintain pack-level educational themes

5. **After story completion**
   - Mark story as complete in metadata
   - Ask: "Story complete! Would you like to continue with the next story?"
   - Update pack progress

### Hub Continuation

If hub is incomplete:

1. **Check hub files**
   - `hub/cover.md` - Pack introduction
   - `hub/menu.md` - Story selection
   - `hub/welcome-back.md` - Return message

2. **Generate missing hub content**
   - Create missing files
   - Ensure menu references all stories

3. **Update story.json hub nodes**
   - Hub cover as squareOne
   - Menu with wheel navigation
   - Action nodes for story selection

---

## Update Metadata

After any progress:
- Update `modified` timestamp
- Update `generation.storiesProgress` for packs
- Update individual story status
- Save after each significant step

## Finding Incomplete Content

To list incomplete stories and packs, check each `./stories/*/metadata.json`:

### For Single Stories (`type: "story"`):
```json
{
  "type": "story",
  "status": "draft",
  "generation": {
    "chaptersGenerated": X,
    "chaptersTotal": Y
  }
}
```
Incomplete if: `chaptersGenerated < chaptersTotal` or `status === "draft"`

### For Story Packs (`type: "pack"`):
```json
{
  "type": "pack",
  "status": "draft",
  "pack": {
    "stories": [
      {"slug": "story-1", "status": "complete"},
      {"slug": "story-2", "status": "in-progress"},
      {"slug": "story-3", "status": "pending"}
    ]
  },
  "generation": {
    "hubComplete": true,
    "storiesProgress": {
      "story-1": {"chapters": 4, "chaptersComplete": 4, "status": "complete"},
      "story-2": {"chapters": 5, "chaptersComplete": 2, "status": "in-progress"},
      "story-3": {"chapters": 3, "chaptersComplete": 0, "status": "pending"}
    }
  }
}
```
Incomplete if: Any story has `status !== "complete"` or `hubComplete === false`

## Context Restoration

When continuing, remind the user of their original choices:

### For Single Stories:
- Target age range
- Story tone
- Educational goals
- Personalization details
- Creation mode

### For Story Packs:
- Pack theme
- Target age range
- Pack tone (shared across stories)
- Shared characters and their voices
- Educational goals (pack-wide)
- Personalization details
- Creation mode
- Which stories are complete/pending

Ask if they want to modify any of these before continuing.

## Session Continuity

Reference the original interview answers stored in `metadata.json.interview` to maintain consistency:

### For Single Stories:
- Use the same voice selections
- Maintain character personalities
- Keep educational themes consistent
- Honor the ending philosophy

### For Story Packs:
- Use shared character profiles from `characters/` directory
- Reference `interview.packLevel` for pack-wide settings
- Reference `interview.stories[i]` for story-specific choices
- Ensure stories maintain pack cohesion
- Keep shared characters consistent across stories

## Error Handling

If story/pack directory is corrupted or files are missing:
1. Report what's missing
2. Offer to regenerate from the last valid checkpoint
3. Ask user how to proceed

### Pack-Specific Error Handling

If pack has issues:
- Missing hub files: Offer to regenerate hub
- Missing story directory: Offer to regenerate that story
- Inconsistent character files: Offer to sync from metadata
- Orphaned story files: Report and offer cleanup

## Important Notes

- Maintain the same creative vision as the original session
- Don't ask questions that were already answered
- Summarize progress clearly before resuming
- Allow user to modify direction if they've changed their mind

### Pack-Specific Notes

- When continuing a pack, maintain consistency with already-completed stories
- Shared characters must behave consistently across all stories
- After completing each story, prompt to continue with next
- Keep track of which educational themes have been covered
