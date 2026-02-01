---
description: Edit an existing story
---

# Edit KidStory

Modify an existing story - change content, add chapters, or adjust settings.

## Story Name

$ARGUMENTS

## Workflow

1. **Locate the Story**
   - If story name provided: Look in `./stories/{story-name}/`
   - If not provided: List all stories and ask user to choose

2. **Load Story**
   - Read `metadata.json`
   - Read `outline.md`
   - Load chapter list
   - Load character profiles

3. **Present Edit Options**

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

## Edit Types

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

## Validation After Edits

After any structural edit:
1. Run full validation
2. Report any new issues
3. Offer interactive fixes
4. Update validation report

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

## Maintaining Consistency

When editing:
- Check for ripple effects (character names, plot points)
- Ensure educational themes remain present
- Verify age-appropriateness after changes
- Update all dependent files

## Important Notes

- Always show preview before saving changes
- Offer undo option for major changes
- Maintain backup before destructive edits
- Keep the user informed of cascading updates
