# ADR 0001: Pi-Compatible KidStory Workflow

## Status

Accepted

## Context

The project is Python-first: story export, audio generation, image generation,
validation, and tests all run through `uv` and Python packages. The existing
AI-assisted workflow is implemented as OpenCode-specific `/kidstory` commands
and subagents, which makes the authoring flow harder to reuse from Pi Agent or
another compatible coding agent.

Pi Agent provides a native TypeScript SDK for embedded applications and a
terminal prompt-template workflow. It can also be driven through JSONL RPC, but
the current need is terminal-first authoring, not a custom application.

## Decision

Use Pi Agent prompt templates plus a generic KidStory workflow document as the
primary agent interface. Keep story-domain automation in Python.

Agents may create and edit source story files directly under
`stories/{slug}/src/` and `stories/{slug}/story.json`. Asset generation and ZIP
export must be performed by a deterministic Python build command:

```bash
uv run python build_story.py stories/{slug}
```

For Pi and generic agent workflows, the build command owns validation, missing
asset generation, asset verification, and archive creation. The previous
OpenCode command and subagent setup remains available for backward
compatibility.

## Consequences

### Positive

- Keeps the implementation aligned with the existing Python package structure.
- Makes asset generation resumable and testable without relying on agent-to-agent
  delegation.
- Lets Pi and other compatible agents share the same repository instructions
  while preserving the restored OpenCode workflow.
- Avoids adding TypeScript infrastructure before there is a custom UI or deeply
  embedded Pi integration.

### Negative

- Pi-specific session hooks and SDK-level controls are not used in this version.
- Prompt templates remain a terminal workflow, not a full application API.
- Agents can still produce weak story content; Python only validates structure,
  source completeness, and assets.
- The Python build command becomes critical infrastructure and must stay well
  tested.

## Alternatives Considered

- Use the Pi TypeScript SDK for the whole workflow. This gives stronger native
  Pi integration, but adds a second application stack and still needs Python for
  the existing story tools.
- Keep only OpenCode subagents. This preserves the old workflow but does not meet
  the goal of making KidStory mainly compatible with Pi Agent.
- Build a Python RPC wrapper around Pi. This remains viable later for automation,
  but is unnecessary for a terminal-first guided authoring flow.
