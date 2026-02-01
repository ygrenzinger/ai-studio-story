---
description: Continue working on an incomplete story
---

# Continue KidStory

Resume work on an incomplete story.

## Story Name

$ARGUMENTS

## Workflow

1. **Locate the Story**
   - If story name provided: Look in `./stories/{story-name}/`
   - If not provided: List all incomplete stories and ask user to choose

2. **Load Story State**
   - Read `metadata.json` to understand current state
   - Check `generation.status` for progress
   - Identify what's been completed vs. pending

3. **Display Progress Summary**
   Show the user:
   - Story title and description
   - Outline status (approved/pending)
   - Chapters generated: X of Y
   - Characters defined
   - Audio scripts created
   - Validation status

4. **Resume from Last Point**

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

5. **Update Metadata**
   - Update `modified` timestamp
   - Update generation progress
   - Save after each significant step

## Finding Incomplete Stories

To list incomplete stories, check each `./stories/*/metadata.json` for:
```json
{
  "status": "draft",
  "generation": {
    "chaptersGenerated": X,
    "chaptersTotal": Y
  }
}
```

Where `chaptersGenerated < chaptersTotal` or `status === "draft"`

## Context Restoration

When continuing, remind the user of their original choices:
- Target age range
- Story tone
- Educational goals
- Personalization details
- Creation mode

Ask if they want to modify any of these before continuing.

## Session Continuity

Reference the original interview answers stored in `metadata.json.interview` to maintain consistency:
- Use the same voice selections
- Maintain character personalities
- Keep educational themes consistent
- Honor the ending philosophy

## Error Handling

If story directory is corrupted or files are missing:
1. Report what's missing
2. Offer to regenerate from the last valid checkpoint
3. Ask user how to proceed

## Important Notes

- Maintain the same creative vision as the original session
- Don't ask questions that were already answered
- Summarize progress clearly before resuming
- Allow user to modify direction if they've changed their mind
