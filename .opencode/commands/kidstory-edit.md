---
description: Edit an existing story or pack
---

# Edit KidStory

Modify an existing story or story pack - change content, add chapters, or adjust settings.

## Story/Pack Name

$ARGUMENTS

## Workflow

1. **Locate the Content**
   - If name provided: Look in `./stories/{name}/`
   - If not provided: List all stories and packs, ask user to choose

2. **Detect Content Type**
   - Read `metadata.json` and check `type` field
   - If `type: "story"`: Use single story edit options
   - If `type: "pack"`: Use pack edit options (see below)

3. **Load Content**
   - Read `metadata.json`
   - Read `outline.md`
   - Load chapter list / story list
   - Load character profiles

---

## Single Story Edit Options

Ask what the user wants to edit:

**Content Edits:**
- Edit a specific chapter
- Add a new chapter
- Remove a chapter
- Modify character dialogue
- Adjust educational moments

**Structure Edits:**
- Add/remove choice branches
- Change story flow
- Modify transitions
- Update endings

**Settings Edits:**
- Change target age (will regenerate content)
- Update voice selections
- Modify pacing/tone
- Update personalization

**Regeneration:**
- Regenerate a chapter with different direction
- Regenerate audio scripts
- Regenerate image prompts

---

## Pack Edit Options

For story packs, present organized edit options:

### Pack-Level Edits

**Pack Metadata:**
- Edit pack title or description
- Change pack theme description
- Update target age (affects all stories)

**Shared Characters:**
- Edit a shared character's name, personality, or voice
- Add a new shared character
- Remove a shared character (update all stories)

**Voice Configuration:**
- Change narrator voice (applies to all stories)
- Update character voice assignments
- Modify pacing settings

### Hub Edits

**Hub Content:**
- Edit pack cover/introduction message
- Modify story selection menu text
- Update welcome-back message
- Change goodbye message

**Hub Structure:**
- Reorder stories in the menu
- Update story teasers in menu

### Story-Level Edits

**Select Story to Edit:**
1. Present list of stories with status
2. User selects which story to edit
3. Apply single-story edit workflow to that story
4. Ensure edits maintain pack consistency

**Add New Story to Pack:**
1. Confirm pack has room (max 5 stories recommended)
2. Run brief per-story interview
3. Generate story outline
4. Generate story chapters
5. Update hub menu to include new story
6. Update story.json action nodes

**Remove Story from Pack:**
1. Confirm removal (warn about permanent deletion)
2. Update hub menu to remove story option
3. Update story.json to remove story stages/actions
4. Clean up story directory
5. Renumber if needed

**Reorder Stories:**
1. Show current order
2. Allow drag/reorder
3. Update hub menu action node options array

### Cross-Story Edits

**Shared Character Updates:**
When editing a shared character, propagate changes:
1. Update `characters/{character}.json`
2. Find all chapters mentioning this character
3. Offer to regenerate affected audio scripts
4. Update character descriptions in affected chapters

**Theme Consistency:**
- Add educational moment to specific story
- Ensure theme appears across pack
- Add cross-story reference/callback

## Edit Types (Single Story)

### Chapter Edit

1. Display current chapter content
2. Ask what to change:
   - Narrative text
   - Dialogue
   - Scene description
   - Educational moment
   - Choice options (if applicable)
3. Make changes
4. Regenerate dependent files:
   - Update `audio-scripts/{chapter}.md`
   - Update `assets/images/{chapter}.prompt.md`
   - Update `story.json` if structure changed

### Add Chapter

1. Ask where to insert the new chapter
2. Gather chapter details:
   - Chapter title
   - Key events
   - Characters involved
   - Connection to story flow
3. Generate chapter content
4. Update story.json transitions
5. Renumber affected chapters if needed

### Remove Chapter

1. Confirm removal
2. Show impact on story flow
3. Ask how to handle transitions:
   - Connect previous to next chapter
   - Modify choice branches
4. Update all references
5. Run validation

### Voice/Tone Changes

1. Show current settings
2. Allow modifications
3. If tone changed significantly:
   - Offer to regenerate audio scripts
   - Update character profiles
   - Adjust director's notes

### Personalization Updates

1. Show current personalization
2. Allow changes (name, details)
3. Find all occurrences in chapters
4. Update consistently throughout
5. Regenerate affected audio scripts

---

## Edit Types (Pack-Specific)

### Hub Edit

1. Display current hub content (cover, menu, welcome-back, goodbye)
2. Ask which hub element to edit
3. Make changes
4. Regenerate hub audio scripts
5. Update story.json hub stages if needed

### Add Story to Pack

1. Verify pack can accommodate another story
2. Run per-story interview:
   - Story title and focus
   - Length (short/medium/long)
   - Characters (from shared + new)
   - Special elements
3. Generate story outline
4. Get approval
5. Generate story chapters
6. Create story directory under `stories/{new-story-slug}/`
7. Update metadata.json:
   - Add to `pack.stories` array
   - Add to `interview.stories` array
   - Add to `generation.storiesProgress`
8. Update hub menu:
   - Add story to `hub/menu.md`
   - Update `action-choose-story` options in story.json
9. Generate story stages in story.json
10. Run validation

### Remove Story from Pack

1. Confirm removal with user
2. Warn: "This will permanently delete Story X and all its chapters"
3. If confirmed:
   - Remove from `pack.stories` array
   - Remove from `interview.stories` array
   - Remove from `generation.storiesProgress`
   - Update hub menu text
   - Remove from `action-choose-story` options
   - Remove all story stages from story.json
   - Delete `stories/{story-slug}/` directory
4. Run validation to ensure no broken references

### Shared Character Edit

1. Show shared character details
2. Allow edits:
   - Name change (update all references)
   - Voice change (regenerate audio scripts)
   - Personality change (review affected dialogue)
3. Find all stories/chapters where character appears
4. Preview impact
5. Apply changes:
   - Update `characters/{character}.json`
   - Update relevant chapters
   - Regenerate affected audio scripts
6. Maintain consistency across pack

## Validation After Edits

After any structural edit:
1. Run full validation
2. Report any new issues
3. Offer interactive fixes
4. Update validation report

### Pack-Specific Validation

After editing a pack:
1. Validate hub structure (menu, transitions)
2. Validate each story individually
3. Validate cross-story consistency:
   - Shared characters appear correctly
   - All stories accessible from menu
   - All stories return to hub properly
4. Check for orphaned content

## Version Control

When editing:
1. Increment `metadata.json.version`
2. Update `modified` timestamp
3. Optionally: Keep backup of previous version

## Regeneration Options

For significant changes, offer:
- **Soft regenerate**: Keep structure, refresh content
- **Hard regenerate**: Rebuild from outline
- **Partial regenerate**: Only affected sections

### Pack Regeneration Options

- **Regenerate single story**: Keep pack structure, regenerate one story
- **Regenerate hub only**: Refresh hub content without touching stories
- **Regenerate all stories**: Keep pack structure, regenerate all story content
- **Full pack regenerate**: Rebuild entire pack from outline

## Maintaining Consistency

When editing:
- Check for ripple effects (character names, plot points)
- Ensure educational themes remain present
- Verify age-appropriateness after changes
- Update all dependent files

### Pack Consistency

When editing a pack:
- Shared character changes must propagate to all stories
- Pack tone/theme changes may require story adjustments
- Educational themes should remain balanced across stories
- Personalization must be consistent throughout pack

## Important Notes

- Always show preview before saving changes
- Offer undo option for major changes
- Maintain backup before destructive edits
- Keep the user informed of cascading updates

### Pack-Specific Notes

- Warn when edits affect multiple stories
- Show which stories will be impacted by shared changes
- Offer to batch-apply voice/tone changes across pack
- Remind user that stories should remain independently enjoyable
